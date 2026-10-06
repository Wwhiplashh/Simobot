import json
import os
import sys
import urllib.request

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Ordine di visualizzazione dei giorni
GIORNI_ORDINE = [
    "lunedì",
    "martedì",
    "mercoledì",
    "giovedì",
    "venerdì",
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


def main():
    if not os.path.exists("menu.json"):
        print("⚠️ File menu.json non trovato.")
        return

    with open("menu.json", "r", encoding="utf-8") as f:
        menu_data = json.load(f)

    giorni_dict = menu_data.get("giorni", {})

    if not giorni_dict:
        print("⚠️ Nessun dato trovato in menu.json.")
        return

    # Intestazione del messaggio
    titolo = menu_data.get("titolo_documento", "MENÙ SCOLASTICO SETTIMANALE")
    messaggio_blocks = [f"📋 *{titolo.upper()}*\n"]

    # Ordiniamo i giorni secondo la settimana lavorativa
    chiavi_giorni = list(giorni_dict.keys())

    def sort_key(day_name):
        day_lower = day_name.lower()
        if day_lower in GIORNI_ORDINE:
            return GIORNI_ORDINE.index(day_lower)
        return 99

    chiavi_ordinate = sorted(chiavi_giorni, key=sort_key)

    giorni_trovati = False
    for giorno in chiavi_ordinate:
        piatti = giorni_dict[giorno]
        if not piatti or giorno == "generale":
            continue

        giorni_trovati = True
        piatti_formatted = "\n".join([f"• {p}" for p in piatti])
        messaggio_blocks.append(
            f"📌 *{giorno.upper()}*\n{piatti_formatted}\n"
        )

    # Fallback se non ci sono giorni formattati distinti
    if not giorni_trovati and "generale" in giorni_dict:
        piatti_formatted = "\n".join([f"• {p}" for p in giorni_dict["generale"]])
        messaggio_blocks.append(piatti_formatted)

    messaggio_finale = "\n".join(messaggio_blocks)

    send_message(messaggio_finale)


if __name__ == "__main__":
    main()
