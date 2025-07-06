import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import json

TELEGRAM_URL = "https://t.me/s/kpszsu"
ACTIVATION_WORD = "У ніч"

def main():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(TELEGRAM_URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    messages = []
    for div in soup.find_all("div", class_="tgme_widget_message_text"):
        text = div.get_text(separator="\n")
        if ACTIVATION_WORD.lower() in text.lower():
            try:
                translated = GoogleTranslator(source='auto', target='en').translate(text)
                messages.append(translated)
            except:
                continue

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
