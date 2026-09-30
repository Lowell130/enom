# 🍷 EnotecaMolise - Estensione Chrome "Wine Importer Side Panel 2.0"

L'estensione Chrome **EnotecaMolise Wine Importer Side Panel 2.0** permette di **creare nuovi vini** oppure **aggiornare vini già presenti nel catalogo** direttamente dai siti web dei produttori molisani.

---

## ✨ Funzionalità Principali

1. **⚡ Auto-Estrazione 1-Click**: analizza automaticamente la pagina web del produttore ed estrae Nome, Tipologia, Denominazione, Annata, Riserva, Alcol, Descrizione e Foto.
2. **🎯 Modalità Point & Click (Ispezione Visiva)**: cliccando sui pulsanti `🎯 Pick` o `🖼️ Pick Foto` accanto a qualsiasi campo o caratteristica personalizzata, ti basta cliccare su un testo, numero o immagine del sito web per inserire o correggere il valore nel Side Panel!
3. **✏️ Modalità Aggiornamento Vino Esistente**:
   - Quando selezioni una Cantina Produttrice, nel menu **`OPERAZIONE CATALOGO`** vengono caricati tutti i vini già salvati per quella cantina.
   - Selezionando un vino esistente dall'elenco (es. `✏️ Modifica: Tintilia del Molise 2022 Riserva`), l'estensione **carica istantaneamente tutti i dati già salvati** nel Side Panel.
   - Puoi quindi navigare su nuove pagine web o schede online e cliccare sui tasti **`🎯 Pick`** per aggiungere le informazioni mancanti (es. note di degustazione, scheda PDF, o caratteristiche extra).
   - Cliccando su **`💾 AGGIORNA VINO ESISTENTE IN ENOTECAMOLISE`**, il vino già presente viene aggiornato con la chiamata `PUT /api/v1/products/{id}` senza creare duplicati!

---

## 🔐 Accesso

Dalla versione 2.1 l'estensione **non contiene più credenziali**: all'apertura del pannello ogni utente accede con il **proprio account** EnotecaMolise (email e password).

- **Amministratore**: può scegliere qualsiasi cantina, incluse quelle in attesa di approvazione.
- **Produttore**: lavora solo sulla propria cantina (selezionata automaticamente).
- Il token di sessione è salvato in `chrome.storage.session` e viene cancellato alla chiusura del browser; il pulsante **Esci** lo rimuove subito.
- Nel riquadro di accesso puoi indicare l'**Indirizzo API** (predefinito `http://localhost:8000/api/v1`).

---

## ⚡ Come installare o aggiornare l'estensione su Google Chrome

1. Apri **Google Chrome** e naviga su `chrome://extensions`.
2. In alto a destra attiva la **`Modalità sviluppatore`** (toggle ON).
3. Clicca su **`Ricarica 🔄`** sul riquadro dell'estensione **EnotecaMolise Wine Importer**.
4. Apri l'estensione cliccando sull'icona **EnotecaMolise** 🍷 nella barra delle estensioni di Chrome.
