import email
from email.header import decode_header
import imaplib
import os
from pathlib import Path
import sys

# --- CONFIGURAZIONE VIA VARIABILI D'AMBIENTE ---
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")  # Default per Gmail
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
SEARCH_KEYWORD = os.getenv("SEARCH_KEYWORD", "menù")  # Parola chiave nell'oggetto


def decode_mime_text(text: str) -> str:
    """Decodifica correttamente i caratteri speciali dagli oggetti o dai nomi dei file."""
    if not text:
        return ""
    decoded_fragments = decode_header(text)
    result = ""
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            result += fragment.decode(encoding or "utf-8", errors="replace")
        else:
            result += str(fragment)
    return result


def fetch_latest_menu_attachments():
    # Verifico presenza credenziali
    if not EMAIL_USER or not EMAIL_PASS:
        print("❌ ERRORE: Le variabili EMAIL_USER e EMAIL_PASS devono essere impostate.")
        sys.exit(1)

    # Creo la cartella di destinazione se non esiste
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    print(f"🔌 Connessione al server IMAP {IMAP_SERVER}...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # Ricerca Gmail convertendo esplicitamente la stringa in byte UTF-8
        print(f"🔍 Ricerca email con oggetto contenente '{SEARCH_KEYWORD}'...")
        query = f'X-GM-RAW "subject:{SEARCH_KEYWORD}"'.encode('utf-8')
        status, response = mail.search('UTF-8', query)

        if status != "OK":
            print("❌ Errore durante la ricerca nella casella di posta.")
            return []

        email_ids = response[0].split()
        if not email_ids:
            print("⚠️ Nessuna email trovata con i criteri specificati.")
            return []

        # Prende l'ultima email ricevuta in ordine cronologico (ID più alto)
        latest_email_id = email_ids[-1]
        print(f"📧 Trovate {len(email_ids)} email. Elaborazione della più recente...")

        status, data = mail.fetch(latest_email_id, "(RFC822)")
        if status != "OK":
            print("❌ Errore nel recupero del contenuto della mail.")
            return []

        msg = email.message_from_bytes(data[0][1])
        subject = decode_mime_text(msg.get("Subject"))
        sender = decode_mime_text(msg.get("From"))
        print(f"📩 Oggetto: '{subject}' | Da: {sender}")

        downloaded_files = []

        # Scansiona le componenti MIME della mail per estrarre gli allegati
        for part in msg.walk():
            # Salta contenitori generici o messaggi senza disposition
            if part.get_content_maintype() == "multipart":
                continue
            if part.get("Content-Disposition") is None:
                continue

            filename = part.get_filename()
            if filename:
                filename = decode_mime_text(filename)
                ext = Path(filename).suffix.lower()

                # Filtra solo PDF e formati immagine
                if ext in [".pdf", ".jpg", ".jpeg", ".png"]:
                    filepath = DOWNLOAD_DIR / filename
                    
                    # Salva il file in binario
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    
                    print(f"💾 Allegato scaricato: {filepath}")
                    downloaded_files.append(filepath)

        if not downloaded_files:
            print("⚠️ Nessun allegato PDF o immagine trovato nell'email selezionata.")

        mail.close()
        mail.logout()
        return downloaded_files

    except Exception as e:
        print(f"❌ Si è verificato un errore: {e}")
        sys.exit(1)


if __name__ == "__main__":
    files = fetch_latest_menu_attachments()
    print(f"\n✅ Operazione completata. File scaricati: {len(files)}")
