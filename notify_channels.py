import json
import os
from pathlib import Path
import sys
import requests

# Variable d'ambiente Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Variabili d'ambiente WhatsApp
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
WHATSAPP_CHANNEL_ID = os.getenv("WHATSAPP_CHANNEL_ID")

DOWNLOADS_DIR = Path("./downloads")

GIORNI_KEYWORDS = [
    "lunedì",
    "martedì",
    "mercoledì",
    "giovedì",
    "venerdì",
]

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


def find_menu_photo() -> Path | None:
    """Cerca nella cartella downloads la foto reale del menù,

    ignorando immagini di firma/logo (es. image001.png) o file piccoli.
    """
    if not DOWNLOADS_DIR.exists():
        return None

    image_extensions = [".jpg", ".jpeg", ".png"]

    for file_path in DOWNLOADS_DIR.iterdir():
        if file_path.suffix.lower() in image_extensions:
            filename_lower = file_path.name.lower()

            if filename_lower.startswith("image0") or "logo" in filename_lower:
                continue

            if file_path.stat().st_size < 30000:
                continue

            print(
                f"📸 Trovata foto del menù da allegare: {file_path.name}",
                flush=True,
            )
            return file_path

    return None


def send_telegram_post(text: str, photo_path: Path | None = None):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            "❌ Errore: TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID non"
            " configurati nei Secrets.",
            flush=True,
        )
        return

    if photo_path and photo_path.exists():
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        try:
            with open(photo_path, "rb") as photo_file:
                payload = {
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": text,
                    "parse_mode": "Markdown",
                }
                files = {"photo": photo_file}
                response = requests.post(url, data=payload, files=files)

            if response.status_code == 200:
                print(
                    "✅ Foto e menù inviati con successo su Telegram!",
                    flush=True,
                )
                return
            else:
                print(
                    "⚠️ Impossibile inviare la foto su Telegram (fallback a solo"
                    f" testo): {response.text}",
                    flush=True,
                )
        except Exception as e:
            print(
                f"⚠️ Errore invio foto Telegram: {e}. Tento invio solo testo.",
                flush=True,
            )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(
            "✅ Messaggio di testo inviato con successo su Telegram!",
            flush=True,
        )
    else:
        print(
            f"❌ Errore durante l'invio su Telegram: {response.text}", flush=True
        )


def send_whatsapp_post(text: str, photo_path: Path | None = None):
    if not WHATSAPP_API_TOKEN or not WHATSAPP_CHANNEL_ID:
        print(
            "ℹ️ Secrets WhatsApp non configurati. Salto l'invio su WhatsApp.",
            flush=True,
        )
        return

    headers = {"Authorization": f"Bearer {WHATSAPP_API_TOKEN}"}

    try:
        if photo_path and photo_path.exists():
            url = "https://gate.whapi.cloud/messages/image"
            with open(photo_path, "rb") as f:
                files = {"media": f}
                data = {"to": WHATSAPP_CHANNEL_ID, "caption": text}
                res = requests.post(
                    url, headers=headers, data=data, files=files
                )
        else:
            url = "https://gate.whapi.cloud/messages/text"
            payload = {"to": WHATSAPP_CHANNEL_ID, "body": text}
            res = requests.post(url, headers=headers, json=payload)

        if res.status_code in [200, 201]:
            print(
                "✅ Post inviato con successo sul canale/gruppo WhatsApp!",
                flush=True,
            )
        else:
            print(
                f"❌ Errore durante l'invio su WhatsApp: {res.text}", flush=True
            )
    except Exception as e:
        print(f"❌ Errore HTTP durante l'invio su WhatsApp: {e}", flush=True)


def is_header_line(line: str) -> bool:
    line_lower = line.lower().strip()
    return any(kw in line_lower for kw in HEADER_EXCLUDE_KEYWORDS)


def is_day_line(line: str) -> bool:
    line_lower = line.lower().strip()
    return any(line_lower.startswith(giorno) for giorno in GIORNI_KEYWORDS)


def main():
    if not os.path.exists("menu.json"):
        print("⚠️ File menu.json non trovato.", flush=True)
        return

    with open("menu.json", "r", encoding="utf-8") as f:
        menu_data = json.load(f)

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

    output_lines = ["🍽 *MENU MENSE SCOLASTICHE*\n"]

    for line in lines:
        if is_header_line(line):
            continue

        if is_day_line(line):
            day_title = line.strip().capitalize()
            output_lines.append(f"\n📌 *{day_title}*")
        else:
            output_lines.append(line.strip())

    messaggio_finale = "\n".join(output_lines).strip()

    photo_path = find_menu_photo()

    # Invio disaccoppiato su Telegram
    print("\n--- Invio Telegram ---", flush=True)
    send_telegram_post(messaggio_finale, photo_path)

    # Invio disaccoppiato su WhatsApp
    print("\n--- Invio WhatsApp ---", flush=True)
    send_whatsapp_post(messaggio_finale, photo_path)


if __name__ == "__main__":
    main()
