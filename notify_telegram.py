import json
import os
import sys
import urllib.request

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

GIORNI_KEYWORDS = [
    "lunedì",
    "martedì",
    "mercoledì",
    "giovedì",
    "venerdì",
]

# Parole chiave delle righe di intestazione da filtrare ed ignorare
HEADER_EXCLUDE_KEYWORDS = [
    "scuole dell'infanzia",
    "scuole primarie",
    "menù primavera",
    "menu primavera",
    "menù autunno",
    "menu autunno",
    "menù inverno",
    "menu inverno",
    "a.s. 20",
    "settimana:",
]


def send_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            "❌ Errore: TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID non"
            " configurati nei Secrets."
        )
        sys.exit(1)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps(
        {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print(
                    "✅ Menù settimanale inviato con successo sul canale"
                    " Telegram!"
                )
            else:
                print(
                    "❌ Errore durante l'invio su Telegram: codice"
                    f" {response.status}"
                )
                sys.exit(1)
    except Exception as e:
        print(f"❌ Errore HTTP durante la chiamata a Telegram: {e}")
        sys.exit(1)


def is_header_line(line: str) -> bool:
    """Verifica se la riga fa parte dell'intestazione da ignorare."""
    line_lower = line.lower().strip()
    return any(kw in line_lower for kw in HEADER_EXCLUDE_KEYWORDS)


def is_day_line(line: str) -> bool:
    """Verifica se la riga inizia con un giorno della settimana."""
    line_lower = line.lower().strip()
    return any(line_lower.startswith(giorno) for giorno in GIORNI_KEYWORDS)


def main():
    if not os.path.exists("menu.json"):
        print("⚠️ File menu.json non trovato.")
        return

    with open("menu.json", "r", encoding="utf-8") as f:
        menu_data = json.load(f)

    # Estrae il testo grezzo estratto dal PDF
    lines = []
    if "testo_integrale" in menu_data:
        lines = [
            l.strip()
            for l in menu_data["testo_integrale"].split("\n")
            if l.strip()
        ]
    else:
        for g, items in menu_data.get("giorni", {}).items():
            if g != "generale":
                lines.append(g)
            lines.extend(items)

    output_lines = ["🍽️️ *MENU MENSE SCOLASTICHE*\n"]

    for line in lines:
        # 1. Ignora le intestazioni indesiderate
        if is_header_line(line):
            continue

        # 2. Se è una riga con il giorno (es. "Lunedì 5 Ottobre")
        if is_day_line(line):
            day_title = line.strip().capitalize()
            output_lines.append(f"\n📌 *{day_title}*")
        else:
            # 3. Aggiunge i piatti/spuntini senza elenchi puntati
            output_lines.append(line.strip())

    messaggio_finale = "\n".join(output_lines).strip()

    send_message(messaggio_finale)


if __name__ == "__main__":
    main()
