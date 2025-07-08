import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import json
from datetime import datetime
import re

TELEGRAM_URLS = [
    "https://t.me/s/kpszsu?embed=1",
    "https://t.me/s/AMK_Mapping?embed=1"
]
ACTIVATION_WORDS = ["У ніч", "Tu-22M3"]

def scrape_messages(url):
    print(f"Accesăm URL-ul: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    print(f"Status cod răspuns: {response.status_code}")
    soup = BeautifulSoup(response.text, "html.parser")
    messages = []
    for div in soup.find_all("div", class_=lambda c: c and "tgme_widget_message_text" in c):
        text = div.get_text(separator="\n").strip()
        if any(word.lower() in text.lower() for word in ACTIVATION_WORDS):
            try:
                translated_text = GoogleTranslator(source='auto', target='en').translate(text)
                messages.append({
                    "original": text,
                    "translated": translated_text,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
                print(f"Mesaj tradus: {translated_text}")
            except Exception as e:
                print(f"Eroare la traducere: {e}")
                continue
    return messages

def main():
    all_messages = []
    for url in TELEGRAM_URLS:
        all_messages.extend(scrape_messages(url))

    # Adaugă data și ora rulării scriptului
    script_run_time = datetime.utcnow().isoformat() + "Z"
    data = {
        "messages": all_messages,
        "script_run_time": script_run_time
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_messages)} messages to data.json")

if __name__ == "__main__":
    main()
