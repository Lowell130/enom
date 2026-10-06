"""MongoDB finto in memoria per i test: implementa solo il sottoinsieme di Motor
usato dall'applicazione (nessuna dipendenza esterna)."""
import copy
import re
from typing import Any, Dict, List

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

_MISSING = object()


def _get_values(doc: Any, path: str) -> List[Any]:
    """Restituisce tutti i valori raggiungibili con un percorso puntato (espandendo le liste)."""
    parts = path.split(".")
    current = [doc]
    for part in parts:
        nxt = []
        for item in current:
            if isinstance(item, dict):
                if part in item:
                    nxt.append(item[part])
            elif isinstance(item, list):
                for el in item:
                    if isinstance(el, dict) and part in el:
                        nxt.append(el[part])
        current = nxt
    return current


def _regex_match(pattern, options, value) -> bool:
    if not isinstance(value, str):
        return False
    flags = re.IGNORECASE if options and "i" in options else 0
    return re.search(pattern, value, flags) is not None


def _match_value(cond: Any, values: List[Any]) -> bool:
    expanded = []
    for v in values:
        expanded.append(v)
        if isinstance(v, list):
            expanded.extend(v)

    if isinstance(cond, dict) and any(k.startswith("$") for k in cond):
        for op, arg in cond.items():
            if op == "$regex":
                if not any(_regex_match(arg, cond.get("$options"), v) for v in expanded):
                    return False
            elif op == "$options":
                continue
            elif op == "$in":
                if not any(v in arg for v in expanded) and not (not values and None in arg):
                    return False
            elif op == "$nin":
                if any(v in arg for v in expanded):
                    return False
            elif op == "$ne":
                if any(v == arg for v in expanded) or (arg is None and not values):
                    return False
            elif op == "$exists":
                if bool(values) != bool(arg):
                    return False
            elif op == "$elemMatch":
                arrays = [v for v in values if isinstance(v, list)]
                ok = False
                for arr in arrays:
                    for el in arr:
                        if isinstance(el, dict) and not any(k.startswith("$") for k in arg):
                            if matches(el, arg):
                                ok = True
                        elif _match_value(arg, [el]):
                            ok = True
                if not ok:
                    return False
            elif op in ("$gt", "$gte", "$lt", "$lte"):
                cmp = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b,
                       "$lt": lambda a, b: a < b, "$lte": lambda a, b: a <= b}[op]
                if not any(v is not None and cmp(v, arg) for v in expanded):
                    return False
            else:
                raise NotImplementedError(op)
        return True

    if cond is None:
        return not values or any(v is None for v in expanded)
    return any(v == cond for v in expanded)


def matches(doc: Dict, query: Dict) -> bool:
    for key, cond in (query or {}).items():
        if key == "$or":
            if not any(matches(doc, q) for q in cond):
                return False
        elif key == "$and":
            if not all(matches(doc, q) for q in cond):
                return False
        else:
            if not _match_value(cond, _get_values(doc, key)):
                return False
    return True


def _project(doc: Dict, projection) -> Dict:
    doc = copy.deepcopy(doc)
    if not projection:
        return doc
    include = {k for k, v in projection.items() if v}
    exclude = {k for k, v in projection.items() if not v}
    if include:
        out = {k: doc[k] for k in include if k in doc}
        if "_id" not in exclude and "_id" in doc:
            out["_id"] = doc["_id"]
        return out
    return {k: v for k, v in doc.items() if k not in exclude}


def _set_path(doc: Dict, path: str, value: Any) -> None:
    parts = path.split(".")
    for p in parts[:-1]:
        doc = doc.setdefault(p, {})
    doc[parts[-1]] = value


class FakeResult:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class FakeCursor:
    def __init__(self, docs: List[Dict]):
        self._docs = docs
        self._skip = 0
        self._limit = 0

    def sort(self, key, direction=1):
        def sort_key(d):
            v = d.get(key)
            return (v is None, v if v is not None else 0)
        self._docs = sorted(self._docs, key=sort_key, reverse=direction == -1)
        return self

    def skip(self, n):
        self._skip = n
        return self

    def limit(self, n):
        self._limit = n
        return self

    def _result(self):
        docs = self._docs[self._skip:]
        return docs[: self._limit] if self._limit else docs

    async def to_list(self, length=None):
        docs = self._result()
        return docs[:length] if length else docs

    def __aiter__(self):
        self._iter = iter(self._result())
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class FakeCollection:
    def __init__(self, name: str):
        self.name = name
        self.docs: List[Dict] = []
        self.unique_fields = set()

    def _check_unique(self, doc, exclude_id=None):
        for field in self.unique_fields:
            val = doc.get(field, _MISSING)
            if val is _MISSING:
                continue
            for other in self.docs:
                if other["_id"] != exclude_id and other.get(field) == val:
                    raise DuplicateKeyError(f"E11000 duplicate key error {self.name}.{field}: {val}")

    async def create_index(self, field, unique=False, **kw):
        if unique:
            self.unique_fields.add(field)
        return f"{field}_1"

    async def drop_index(self, name):
        return None

    async def insert_one(self, doc):
        doc.setdefault("_id", ObjectId())
        self._check_unique(doc)
        self.docs.append(copy.deepcopy(doc))
        return FakeResult(inserted_id=doc["_id"])

    async def insert_many(self, docs):
        ids = []
        for d in docs:
            ids.append((await self.insert_one(d)).inserted_id)
        return FakeResult(inserted_ids=ids)

    async def find_one(self, query=None, projection=None):
        for d in self.docs:
            if matches(d, query or {}):
                return _project(d, projection)
        return None

    def find(self, query=None, projection=None):
        return FakeCursor([_project(d, projection) for d in self.docs if matches(d, query or {})])

    async def count_documents(self, query):
        return sum(1 for d in self.docs if matches(d, query))

    async def _update(self, query, update, many):
        count = 0
        for d in self.docs:
            if matches(d, query):
                new = copy.deepcopy(d)
                for path, value in update.get("$set", {}).items():
                    _set_path(new, path, copy.deepcopy(value))
                for path, value in update.get("$inc", {}).items():
                    current = _get_values(new, path)
                    _set_path(new, path, (current[0] if current and isinstance(current[0], (int, float)) else 0) + value)
                for path in update.get("$unset", {}):
                    parts = path.split(".")
                    target = new
                    for part in parts[:-1]:
                        target = target.get(part) if isinstance(target, dict) else None
                        if target is None:
                            break
                    if isinstance(target, dict):
                        target.pop(parts[-1], None)
                for path, value in update.get("$pull", {}).items():
                    current = _get_values(new, path)
                    if current and isinstance(current[0], list):
                        _set_path(new, path, [x for x in current[0] if x != value])
                for path, value in update.get("$addToSet", {}).items():
                    current = _get_values(new, path)
                    arr = list(current[0]) if current and isinstance(current[0], list) else []
                    if value not in arr:
                        arr.append(copy.deepcopy(value))
                    _set_path(new, path, arr)
                self._check_unique(new, exclude_id=d["_id"])
                d.clear()
                d.update(new)
                count += 1
                if not many:
                    break
        return FakeResult(matched_count=count, modified_count=count)

    async def update_one(self, query, update, upsert=False):
        result = await self._update(query, update, many=False)
        if upsert and result.matched_count == 0:
            # come MongoDB: il documento nuovo parte dai campi di uguaglianza del filtro
            doc = {k: copy.deepcopy(v) for k, v in query.items() if not k.startswith("$") and not isinstance(v, dict)}
            for path, value in update.get("$set", {}).items():
                _set_path(doc, path, copy.deepcopy(value))
            for path, value in update.get("$inc", {}).items():
                _set_path(doc, path, value)
            await self.insert_one(doc)
        return result

    async def update_many(self, query, update):
        return await self._update(query, update, many=True)

    async def delete_one(self, query):
        for i, d in enumerate(self.docs):
            if matches(d, query):
                del self.docs[i]
                return FakeResult(deleted_count=1)
        return FakeResult(deleted_count=0)

    async def delete_many(self, query):
        before = len(self.docs)
        self.docs = [d for d in self.docs if not matches(d, query)]
        return FakeResult(deleted_count=before - len(self.docs))

    def aggregate(self, pipeline):
        docs = [copy.deepcopy(d) for d in self.docs]
        for stage in pipeline:
            if "$match" in stage:
                docs = [d for d in docs if matches(d, stage["$match"])]
            elif "$group" in stage:
                spec = stage["$group"]
                key_expr = spec["_id"]
                groups: Dict[Any, Dict] = {}
                for d in docs:
                    key = d.get(key_expr[1:]) if isinstance(key_expr, str) else key_expr
                    g = groups.setdefault(key, {"_id": key})
                    for field, acc in spec.items():
                        if field == "_id":
                            continue
                        if "$sum" in acc:
                            inc = acc["$sum"] if isinstance(acc["$sum"], (int, float)) else d.get(acc["$sum"][1:], 0)
                            g[field] = g.get(field, 0) + inc
                docs = list(groups.values())
            else:
                raise NotImplementedError(stage)
        return FakeCursor(docs)


class FakeDatabase:
    def __init__(self):
        self._collections: Dict[str, FakeCollection] = {}

    def __getattr__(self, name) -> FakeCollection:
        if name.startswith("_"):
            raise AttributeError(name)
        return self[name]

    def __getitem__(self, name) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection(name)
        return self._collections[name]


class FakeAdmin:
    async def command(self, *args, **kwargs):
        return {"ok": 1}


class FakeClient:
    def __init__(self):
        self._dbs: Dict[str, FakeDatabase] = {}
        self.admin = FakeAdmin()

    def __getitem__(self, name) -> FakeDatabase:
        if name not in self._dbs:
            self._dbs[name] = FakeDatabase()
        return self._dbs[name]

    def close(self):
        pass
