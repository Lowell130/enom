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

- **Node.js:** `v18.x` o superiore
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
SECRET_KEY=tua_chiave_segreta_jwt_super_sicura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=4320
UPLOAD_DIR=uploads
```

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

Installa le dipendenze ed avvia il server di sviluppo Nuxt:

```bash
npm install
npm run dev
```

- **Applicazione Web:** `http://localhost:3000`
- **Osservatorio Enologico:** `http://localhost:3000/report`

---

### 4. Installazione Estensione Chrome (Opzionale)

1. Apri Google Chrome e naviga su `chrome://extensions/`.
2. Attiva la **Modalità sviluppatore** (toggle in alto a destra).
3. Clicca su **Carica estensione non spacchettata** (Load unpacked).
4. Seleziona la cartella `chrome-extension` presente nella radice del progetto.

---

## 📁 Struttura del Progetto

```text
enoM/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints Auth, Products, Producers, Reports, Admin, Uploads
│   │   ├── core/            # Configurazione Pydantic & Gestione JWT
│   │   ├── db/              # Driver Motor & Connessione MongoDB
│   │   └── schemas/         # Schemi di validazione Pydantic v2
│   ├── uploads/             # Storage Immagini WebP e documenti
│   ├── .env.example         # Modello variabili d'ambiente backend
│   ├── main.py              # Inizializzazione FastAPI & Seed dati
│   └── requirements.txt
│
├── frontend/
│   ├── components/          # Componenti Vue (Navbar, Footer, Cards, Toast)
│   ├── composables/         # Hooks Nuxt (useApi, useAuth, useToast)
│   ├── pages/
│   │   ├── index.vue        # Home Page
│   │   ├── vini/            # Catalogo & Scheda Vino Pubblica
    │   ├── produttori/      # Elenco & Scheda Cantine
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

## 📄 Licenza

Proprietà riservata - Progetto EnotecaMolise.
