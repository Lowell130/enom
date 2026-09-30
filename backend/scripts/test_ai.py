"""Prova l'estrazione IA su un PDF o un'immagine (JPG, PNG, WebP) senza toccare il database.

Uso (dalla cartella backend/, con il virtualenv attivo):
    python scripts/test_ai.py "C:\\percorso\\scheda.pdf"
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai_extractor import AIExtractionError, provider_status  # noqa: E402
from app.services.pdf_importer import CANONICAL_PAIRINGS, VALID_SINGLE_GRAPES, process_document  # noqa: E402

MASTER_ATTRIBUTES = ["Uvaggio", "Vinificazione", "Allevamento", "Vendemmia", "Allergeni", "Formato",
                     "Zona di Produzione", "Affinamento", "Altitudine Vigneto"]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    status = provider_status()
    if not status["configured"]:
        print("IA non configurata: aggiungi GEMINI_API_KEY o ANTHROPIC_API_KEY nel file backend/.env")
        sys.exit(1)
    print(f"IA: {status['provider']} - modello {status['model']}")
    print(f"Analisi di {os.path.basename(path)}...\n")
    with open(path, "rb") as f:
        pdf_bytes = f.read()
    try:
        result = process_document(pdf_bytes, os.path.basename(path), MASTER_ATTRIBUTES, VALID_SINGLE_GRAPES, CANONICAL_PAIRINGS)
    except AIExtractionError as e:
        print(f"ERRORE: {e}")
        sys.exit(2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nOK: {len(result['wines'])} vini estratti con metodo '{result['method']}'.")


if __name__ == "__main__":
    main()
