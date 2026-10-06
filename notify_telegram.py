from datetime import datetime
import json
import os
import sys
import urllib.parse
import urllib.request

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
                print("✅ Messaggio inviato con successo sul canale Telegram!")
            else:
                print(
                    "❌ Errore durante l'invio su Telegram: codice"
                    f" {response.status}"
                )
                sys.exit(1)
    except Exception as e:
        print(f"❌ Errore HTTP durante la chiamata a Telegram: {e}")
        sys.exit(1)


def main():
    if not os.path.exists("menu.json"):
        print("⚠️ File menu.json non trovato.")
        return

    with open("menu.json", "r", encoding="utf-8") as f:
        menu_data = json.load(f)

    today_index = datetime.now().weekday()
    today_name = GIORNI_MAP.get(today_index, "lunedì")

    giorni = menu_data.get("giorni", {})

    if today_name not in giorni or not giorni[today_name]:
        print(f"ℹ️ Nessun menù trovato per {today_name}.")
        return

    piatti = giorni[today_name]
    menu_testo = "\n".join([f"• {p}" for p in piatti])

    messaggio = (
        f"🍽️ *MENÙ DELLA MENSA - {today_name.upper()}*\n\n{menu_testo}"
    )

    send_message(messaggio)


if __name__ == "__main__":
    main()
