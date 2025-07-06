import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import json

# Listă de linkuri Telegram
TELEGRAM_URLS = [
    "https://t.me/s/kpszsu",
    "https://t.me/s/AMK_Mapping"
]

# Listă de cuvinte de activare
ACTIVATION_WORDS = ["У ніч", "Tu-22M3"]

def scrape_messages(url):
    """Extrage mesajele de pe un canal Telegram dat."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    messages = []
    for div in soup.find_all("div", class_="tgme_widget_message_text"):
        text = div.get_text(separator="\n")
        if any(word.lower() in text.lower() for word in ACTIVATION_WORDS):
            try:
                translated_text = GoogleTranslator(source='auto', target='en').translate(text)
                messages.append(translated_text)
            except Exception as e:
                print(f"Error translating message: {e}")
                continue
    return messages

def main():
    all_messages = []
    for url in TELEGRAM_URLS:
        print(f"Scraping {url}...")
        messages = scrape_messages(url)
        all_messages.extend(messages)

    if all_messages:
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(all_messages, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(all_messages)} messages to data.json")
    else:
        print("No messages found.")

if __name__ == "__main__":
    main()
