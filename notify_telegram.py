from datetime import datetime
import json
import os
import sys
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

GIORNI_MAP = {
    0: "lunedì",
    1: "martedì",
    2: "mercoledì",
    3: "giovedì",
    4: "venerdì",
}


def send_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Token Telegram o Chat ID non impostati.")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Messaggio inviato con successo su Telegram!")
    else:
        print(f"❌ Errore invio Telegram: {response.text}")


def main():
    if not os.path.exists("menu.json"):
        print("⚠️ File menu.json non trovato.")
        return

    with open("menu.json", "r", encoding="utf-8") as f:
        menu_data = json.load(f)

    # Identifica il giorno della settimana corrente
    today_index = datetime.now().weekday()
    today_name = GIORNI_MAP.get(today_index, "lunedì")

    giorni = menu_data.get("giorni", {})

    # Se è sabato o domenica, o il giorno non è presente nel JSON
    if today_name notin giorni or not giorni[today_name]:
        print(f"ℹ️ Nessun menù specifico trovato per {today_name}.")
        return

    piatti = giorni[today_name]
    menu_testo = "\n".join([f"• {p}" for p in piatti])

    messaggio = (
        f"🍽️ *MENÙ DELLA MENSA - {today_name.upper()}*\n\n" f"{menu_testo}"
    )

    send_message(messaggio)


if __name__ == "__main__":
    main()
