# Messa online di prova

Backend (FastAPI) su Google Cloud Run, frontend (Nuxt) su Vercel, database su MongoDB Atlas.

## Ordine consigliato

1. **Atlas** > Network Access: aggiungi `0.0.0.0/0` (Cloud Run non ha un IP fisso).
2. **Bucket per le foto**: crea un bucket Cloud Storage (es. `enotecamolise-uploads`, regione europe-west8 o europe-west1)
   e copia dentro il contenuto di `backend/uploads` del PC.
3. **Backend**: copia `deploy/cloudrun.env.example.yaml` in `deploy/cloudrun.env.yaml`, compila i valori e lancia
   dalla cartella del progetto:

   ```
   gcloud run deploy enotecamolise-api --source backend --region europe-west8 --allow-unauthenticated ^
     --env-vars-file deploy/cloudrun.env.yaml ^
     --add-volume name=uploads,type=cloud-storage,bucket=enotecamolise-uploads ^
     --add-volume-mount volume=uploads,mount-path=/mnt/uploads ^
     --execution-environment gen2 --max-instances 1 --memory 1Gi --timeout 300
   ```

   (in PowerShell usa ` al posto di ^ per andare a capo). Annota l'indirizzo `https://...run.app` che ti restituisce.
4. **Frontend**: su Vercel importa il repository con *Root Directory* = `frontend`, imposta le due variabili di
   `deploy/vercel.env.example` con l'indirizzo del punto 3 e fai il deploy. Annota l'indirizzo `https://...vercel.app`.
5. **Ritorno al backend**: metti l'indirizzo Vercel in `CORS_ORIGINS` e `SITE_URL` e ripeti il deploy del punto 3.
6. **Prova**: `https://...run.app/docs` deve aprirsi; sul sito vercel accedi come admin e controlla foto e Osservatorio.

## Note

- `--max-instances 1`: i limiti anti-abuso (tentativi di accesso, richieste) sono tenuti in memoria.
- Quando arriva il dominio: aggiorna `CORS_ORIGINS`, `SITE_URL` e le variabili Vercel con il nuovo indirizzo.
- Per i dati sensibili (MONGODB_URL, SECRET_KEY, chiavi IA, SMTP_PASSWORD) puoi usare Secret Manager al posto
  delle variabili in chiaro: `--set-secrets SECRET_KEY=secret-key:latest`.
