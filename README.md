# 🍷 EnotecaMolise - Portale dei Produttori & Osservatorio Enologico del Molise

EnotecaMolise è una piattaforma web completa ideata per raccogliere, catalogare, promuovere e valorizzare l'intera produzione vinicola del Molise (Tintilia del Molise DOC, Biferno DOC, Pentro DOC, Spumanti Metodo Classico, Passiti e Liquori autoctoni).

Il progetto include un **Backend REST API (FastAPI)**, un **Frontend SSR/SPA (Nuxt 3 & TailwindCSS)**, un **Osservatorio Enologico / Analytics** ed un'**Estensione Chrome** per il data entry rapido direttamente dai siti web dei produttori.

---

## 🚀 Architettura & Stack Tecnologico

- **Frontend:** Nuxt 3 (Vue 3, TailwindCSS, Pinia, Lucide Icons, SSR/SPA).
- **Backend:** FastAPI (Python 3.11+, Pydantic v2, Auth JWT con Ruoli, Motor Async MongoDB Driver).
- **Database:** MongoDB (NoSQL, ideale per la gestione flessibile di schede tecniche e attributi enologici).
- **Estensione Chrome:** Manifest V3 (Sidepanel & Inspector con estrazione smart e suggerimenti automatici).

---

## ⚡ Caratteristiche Principali

1. **Vetrina Pubblica & Catalogo Vini:**
   - Scheda dettagliata per ciascun vino (profilo organolettico, vitigni, abbinamenti, temperatura di servizio, affinamento, vinificazione).
   - Scheda dettagliata per ciascuna Cantina / Produttore con contatti e catalogo vini associato.
   - Filtri avanzati per Tipologia (Rosso, Bianco, Rosato, Passito, Spumante), Denominazione (DOC, IGT, DOP) e ricerca testuale.

2. **📊 Osservatorio Enologico del Molise (`/report`):**
   - Dashboard executive con KPI dinamici in tempo reale.
   - Ripartizione percentuale per tipologie enologiche e certificazioni di origine.
   - Leaderboard dei vitigni più diffusi e mappa dei comuni molisani ad alta vocazione vitivinicola.
   - Analisi tecnica del terroir (vinificazione, affinamento, altitudine, forme di allevamento).

3. **Dashboard Riservata (Admin & Produttori):**
   - **Clonazione 1-Click:** Duplicazione istantanea di qualsiasi scheda vino per creare rapidamente nuove annate o varianti.
   - **Gestione Cantine, Vitigni, Abbinamenti ed Attributi:** Sistema di amministrazione dinamico.
   - **Notifiche Toast Personalizzate:** Feedback visivo in tempo reale per ogni azione di salvataggio o modifica.

4. **Estensione Chrome per Data Entry:**
   - Estrazione automatica di attributi (gradazione alcolica, altitudine, affinamento, temperatura di servizio).
   - Picker visivo dagli elementi delle pagine web dei produttori.
   - Suggerimenti rapidi e completamento automatico basati sui valori inseriti in precedenza nel database.

---

## 🛠️ Requisiti di Sistema

- **Node.js:** `v18.x` o superiore, con **yarn 1.x**
- **Python:** `v3.10` o superiore
- **MongoDB:** Istanza locale (`mongodb://localhost:27017`) oppure MongoDB Atlas cluster

---

## ⚙️ Configurazione & Installazione

### 1. Clona il Repository

```bash
git clone https://github.com/Lowell130/enom.git
cd enom
```

### 2. Configurazione Backend (FastAPI)

Crea il file `.env` all'interno della cartella `backend/` partendo da `.env.example`:

```bash
cd backend
cp .env.example .env
```

Modifica `backend/.env` con le tue configurazioni locali (ad es. la stringa di connessione a MongoDB):

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=enoteca_molise
SECRET_KEY=<chiave casuale lunga, vedi sotto>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=4320
UPLOAD_DIR=uploads
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ADMIN_EMAIL=admin@enotecamolise.it
ADMIN_PASSWORD=<password dell'admin iniziale, min. 12 caratteri>
AUTO_APPROVE_PRODUCERS=false
SEED_SAMPLE_DATA=false
```

- **`SECRET_KEY`** è obbligatoria in produzione. Generala con:
  `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- **`ADMIN_PASSWORD`** serve solo al primo avvio, per creare l'amministratore se nel database non ne esiste nessuno. In alternativa: `python scripts/manage_users.py create-admin <email>`.
- **`AUTO_APPROVE_PRODUCERS`**: con `false` (predefinito) le cantine che si registrano restano *in attesa di approvazione* e non sono visibili al pubblico finché l'admin non le approva da **Dashboard → Cantine**.
- **`SEED_SAMPLE_DATA=true`** inserisce una cantina e due vini di esempio se il database è vuoto (solo sviluppo).

Crea il virtual environment ed installa le dipendenze:

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Avvia il server backend FastAPI:

```bash
uvicorn main:app --reload --port 8000
```

- **Documentazione Swagger API:** `http://localhost:8000/docs`

#### Gestione utenti da riga di comando

```bash
python scripts/manage_users.py list                         # elenco utenti
python scripts/manage_users.py set-password <email>         # cambia password
python scripts/manage_users.py create-admin <email>         # nuovo amministratore
```

#### Test automatici

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

I test usano un database finto in memoria (`tests/fake_mongo.py`): non serve MongoDB.

---

### 3. Configurazione Frontend (Nuxt 3)

In una nuova finestra di terminale, entra nella cartella `frontend/`:

```bash
cd frontend
cp .env.example .env
```

Modifica `frontend/.env` se necessario:

```env
NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
NUXT_PUBLIC_MEDIA_BASE=http://localhost:8000
```

Installa le dipendenze ed avvia il server di sviluppo Nuxt. Il progetto usa **yarn** (il lockfile di riferimento è `yarn.lock`; non usare `npm install`, che creerebbe un secondo lockfile):

```bash
npm install -g yarn   # solo la prima volta
yarn install
yarn dev
```

- **Applicazione Web:** `http://localhost:3000`
- **Osservatorio Enologico:** `http://localhost:3000/report`

---

### 4. Installazione Estensione Chrome (Opzionale)

1. Apri Google Chrome e naviga su `chrome://extensions/`.
2. Attiva la **Modalità sviluppatore** (toggle in alto a destra).
3. Clicca su **Carica estensione non spacchettata** (Load unpacked).
4. Seleziona la cartella `chrome-extension` presente nella radice del progetto.
5. Apri il pannello e accedi con il **tuo account** (admin o produttore): l'estensione non contiene credenziali.

---

## 📁 Struttura del Progetto

```text
enoM/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints Auth, Products (CRUD), Product I/O (import/export), Producers, Reports, Admin, Uploads
│   │   ├── core/            # Configurazione Pydantic & Gestione JWT
│   │   ├── db/              # Driver Motor & Connessione MongoDB
│   │   ├── schemas/         # Schemi di validazione Pydantic v2
│   │   └── services/        # Logica di dominio: catalogo, tassonomie, scraping, import PDF
│   ├── uploads/             # Immagini e PDF caricati (non versionati in git)
│   ├── scripts/             # Gestione utenti e correzioni dati una tantum
│   ├── tests/               # Test automatici (DB finto in memoria)
│   ├── .env.example         # Modello variabili d'ambiente backend
│   ├── main.py              # Inizializzazione FastAPI & Seed dati
│   └── requirements.txt
│
├── frontend/
│   ├── components/          # Componenti Vue (Navbar, Footer, Cards, Toast)
│   ├── composables/         # Hooks Nuxt (useApi, useAuth, useToast)
│   ├── middleware/          # Protezione delle pagine /dashboard
│   ├── pages/
│   │   ├── index.vue        # Home Page
│   │   ├── vini/            # Catalogo & Scheda Vino Pubblica
│   │   ├── produttori/      # Elenco & Scheda Cantine
│   │   ├── report.vue       # 📊 Osservatorio Enologico del Molise
│   │   ├── login.vue        # Autenticazione Admin & Cantine
│   │   └── dashboard/       # Dashboard Gestione Catalogo & Cantine
│   ├── .env.example         # Modello variabili d'ambiente frontend
│   └── nuxt.config.ts
│
├── chrome-extension/        # Estensione Chrome Manifest V3 per data entry
├── .gitignore               # Ignora node_modules, venv, file .env e temporanei
└── README.md
```

---

## 🤖 Importazione vini da PDF con IA

**Dashboard → Gestione Prodotti → Importa schede (AI)** (solo amministratore) crea le schede dei vini a partire da:
- schede tecniche PDF dei produttori;
- pagine web dei produttori salvate in PDF (anche screenshot, es. FireShot), con uno o più vini.

Come funziona:
1. Scegli la cantina oppure lascia **"Riconosci automaticamente"** (dal nome o dal sito web presenti nel documento).
2. Carica uno o più PDF: ogni file viene analizzato dall'IA, che compila nome, tipologia, denominazione, gradazione, vitigni,
   abbinamenti, temperatura, prezzo, descrizione, note di degustazione e **tutte le caratteristiche tecniche** presenti
   (zona, altitudine, terreno, resa, allevamento, vendemmia, vinificazione, affinamento...). I dati assenti restano vuoti:
   l'IA non li inventa. I "prodotti correlati" delle pagine web vengono ignorati.
3. Nella revisione puoi correggere ogni campo. I vini già presenti nel catalogo vengono riconosciuti e proposti in
   **aggiornamento** (non distruttivo: foto e dati esistenti non vengono cancellati).
4. Scegli se pubblicare subito o salvare come bozza, e se allegare il PDF come scheda tecnica scaricabile.

**Configurazione** (in `backend/.env`, basta una delle due chiavi, poi riavvia il backend):

```env
GEMINI_API_KEY=...        # https://aistudio.google.com/apikey
# oppure
ANTHROPIC_API_KEY=...     # https://console.anthropic.com
```

Senza chiave si possono importare solo PDF con testo selezionabile, tramite un parser più semplice.
Da riga di comando: `python import_pdfs.py --dir cartella_pdf [--producer "Nome"] [--publish]`.

---

## 📦 File caricati (`backend/uploads`)

Le immagini e i PDF caricati dagli utenti **non sono più salvati in git**: sono dati, non codice, e cambiano a ogni modifica del catalogo. La cartella resta sul server (con un file `.gitkeep`). Quando sposti il progetto su un altro server, copia la cartella `backend/uploads` insieme al backup del database.

---

## 🔒 Note di sicurezza

- La registrazione pubblica crea sempre account **PRODUCER**; gli amministratori si creano solo da `.env` o con `scripts/manage_users.py`.
- Le bozze e le cantine non approvate sono visibili solo all'amministratore e al proprietario.
- Gli upload di immagini vengono sempre ricodificati in WebP; gli SVG non sono accettati.
- Login, registrazione e modulo contatti hanno un limite di richieste per indirizzo IP. Dietro un reverse proxy avvia uvicorn con `--proxy-headers --forwarded-allow-ips=<ip del proxy>`.
- La pulizia del catalogo (titoli, slug, annate "Senza Annata") non gira più a ogni avvio: si esegue su richiesta dall'admin con `POST /api/v1/products/cleanup-slugs-and-titles`.

---

## 📄 Licenza

Proprietà riservata - Progetto EnotecaMolise.
