import json
from pathlib import Path
import pdfplumber

DOWNLOADS_DIR = Path("./downloads")
OUTPUT_JSON = Path("menu.json")

GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Estrae tutto il testo leggibile da un file PDF."""
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n".join(full_text)


def parse_raw_text_to_menu(text: str) -> dict:
    """Organizza il testo estratto in una struttura base divisa per giorni."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    menu_data = {
        "titolo_documento": lines[0] if lines else "Menù Scolastico",
        "giorni": {},
        "testo_integrale": text,  # Manteniamo il testo grezzo per debug/fallback
    }

    giorno_corrente = "generale"
    menu_data["giorni"][giorno_corrente] = []

    for line in lines:
        line_lower = line.lower()
        # Verifica se la riga definisce un giorno della settimana
        found_day = next((g for g in GIORNI if g in line_lower), None)

        if found_day:
            giorno_corrente = found_day
            if giorno_corrente not in menu_data["giorni"]:
                menu_data["giorni"][giorno_corrente] = []
        else:
            menu_data["giorni"][giorno_corrente].append(line)

    return menu_data


def main():
    # Cerca il primo file PDF presente nella cartella downloads
    pdf_files = list(DOWNLOADS_DIR.glob("*.pdf"))

    if not pdf_files:
        print("⚠️ Nessun file PDF trovato nella cartella downloads.")
        return

    latest_pdf = pdf_files[0]
    print(f"📖 Lettura ed estrazione da: {latest_pdf.name}...")

    raw_text = extract_text_from_pdf(latest_pdf)

    if not raw_text.strip():
        print(
            "⚠️ Il PDF non contiene testo selezionabile (potrebbe essere una scansione/immagine)."
        )
        print(
            "💡 Nota: Per PDF scansionati servirà un motore OCR o un'API Vision."
        )
        return

    # Strutturazione dei dati
    parsed_menu = parse_raw_text_to_menu(raw_text)

    # Salvataggio del risultato in menu.json
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(parsed_menu, f, ensure_ascii=False, indent=2)

    print(f"✅ Estrazione completata con successo! Salvato in {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
