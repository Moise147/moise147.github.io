import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import json
from datetime import datetime

TELEGRAM_URLS = [
    "https://t.me/s/kpszsu?embed=1",
    "https://t.me/s/AMK_Mapping?embed=1",
    "https://t.me/s/southfronteng?embed=1"
]


def scrape_messages(url):
    print(f"Accesăm URL-ul: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    print(f"Status cod răspuns: {response.status_code}")
    soup = BeautifulSoup(response.text, "html.parser")
    messages = []
    for div in soup.find_all("div", class_=lambda c: c and "tgme_widget_message_text" in c):
        text = div.get_text(separator="\n").strip()
        messages.append({
            "original": text,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    return messages

def main():
    all_messages = []
    for url in TELEGRAM_URLS:
        all_messages.extend(scrape_messages(url))

    data = {
        "messages": all_messages,
        "script_run_time": datetime.utcnow().isoformat() + "Z"
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_messages)} messages to data.json")

if __name__ == "__main__":
    main()

