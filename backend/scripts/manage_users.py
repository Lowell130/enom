"""Gestione account da riga di comando (eseguire dalla cartella backend/).

Esempi:
  python scripts/manage_users.py create-admin admin@enotecamolise.it
  python scripts/manage_users.py set-password admin@enotecamolise.it
  python scripts/manage_users.py list
"""
import argparse
import asyncio
import getpass
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.db.mongodb import connect_to_mongo, close_mongo_connection, db  # noqa: E402


def ask_password(min_len: int) -> str:
    while True:
        pwd = getpass.getpass(f"Nuova password (min. {min_len} caratteri): ")
        if len(pwd) < min_len:
            print("Password troppo corta.")
            continue
        if pwd != getpass.getpass("Ripeti la password: "):
            print("Le password non coincidono.")
            continue
        return pwd


async def main():
    parser = argparse.ArgumentParser(description="Gestione utenti EnotecaMolise")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_admin = sub.add_parser("create-admin", help="Crea un nuovo amministratore")
    p_admin.add_argument("email")
    p_pwd = sub.add_parser("set-password", help="Imposta una nuova password")
    p_pwd.add_argument("email")
    sub.add_parser("list", help="Elenca gli utenti")
    args = parser.parse_args()

    await connect_to_mongo()
    database = db.client[settings.DATABASE_NAME]
    try:
        if args.cmd == "list":
            async for u in database.users.find({}, {"password_hash": 0}).sort("created_at", 1):
                print(f"{u.get('email'):40} {u.get('role'):9} attivo={u.get('is_active', True)}")
        elif args.cmd == "create-admin":
            email = args.email.lower()
            if await database.users.find_one({"email": email}):
                print("Esiste già un utente con questa email: usa set-password.")
                return
            pwd = ask_password(12)
            await database.users.insert_one({
                "email": email, "password_hash": get_password_hash(pwd), "role": "ADMIN",
                "producer_id": None, "is_active": True, "created_at": datetime.utcnow()
            })
            print(f"Amministratore {email} creato.")
        elif args.cmd == "set-password":
            user = await database.users.find_one({"email": args.email.lower()}) or await database.users.find_one({"email": args.email})
            if not user:
                print("Utente non trovato.")
                return
            pwd = ask_password(12 if user.get("role") == "ADMIN" else 8)
            await database.users.update_one({"_id": user["_id"]}, {"$set": {"password_hash": get_password_hash(pwd)}})
            print(f"Password aggiornata per {user['email']}.")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
