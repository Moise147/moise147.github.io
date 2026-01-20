import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from langdetect import detect
from functools import lru_cache

# Constante
MAX_MESSAGES = 20
MAX_CHARS = 3000
TELEGRAM_URLS = [
    "https://t.me/s/kpszsu?embed=1",
    "https://t.me/s/AMK_Mapping?embed=1",
    "https://t.me/s/southfronteng?embed=1",
    "t.me/s/kiber_boroshno?embed=1"
]

# Încărcare modele locale pentru traducere (engleză → română și rusă → română)
tokenizer_en_ro = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-ro")
model_en_ro = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-en-ro")
translator_en_ro = pipeline("translation", model=model_en_ro, tokenizer=tokenizer_en_ro)

tokenizer_ru_ro = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-ru-ro")
model_ru_ro = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-ru-ro")
translator_ru_ro = pipeline("translation", model=model_ru_ro, tokenizer=tokenizer_ru_ro)

# Încărcare model local pentru rezumare
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

@lru_cache(maxsize=100)
def translate_to_ro(text):
    try:
        lang = detect_language(text)
        if lang == "ru":
            result = translator_ru_ro(text, max_length=512)
            return result[0]["translation_text"]
        else:
            result = translator_en_ro(text, max_length=512)
            return result[0]["translation_text"]
    except Exception as e:
        print(f"Eroare la traducere: {e}")
        return text

def detect_language(text):
    try:
        lang = detect(text)
        if lang == "ru":
            return "ru"
        return "en"
    except:
        return "en"

def generate_events(text):
    try:
        summary = summarizer(text, max_length=120, min_length=40, do_sample=False)
        summary_text = summary[0]["summary_text"]
        events = [f"- {line}" for line in summary_text.split(".") if len(line.strip()) > 20]
        return events
    except Exception as e:
        print(f"Eroare la rezumare: {e}")
        return []

def remove_duplicates(events, threshold=0.85):
    if not events:
        return []
    unique_events = []
    seen = set()
    for event in events:
        if event not in seen:
            seen.add(event)
            unique_events.append(event)
    return unique_events

def scrape_messages(url):
    print(f"Accesăm URL-ul: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        messages = []
        for div in soup.find_all("div", class_=lambda c: c and "tgme_widget_message_text" in c):
            text = div.get_text(separator="\n").strip()
            messages.append({
                "original": text,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        return messages
    except Exception as e:
        print(f"Eroare la scrapare: {e}")
        return []

def main():
    translated_texts = []

    for url in TELEGRAM_URLS:
        messages = scrape_messages(url)[:MAX_MESSAGES]
        for msg in messages:
            try:
                translated = translate_to_ro(msg["original"])
                translated_texts.append(translated)
            except Exception as e:
                print(f"Eroare la traducere mesaj: {e}")

    if not translated_texts:
        print("Nu există texte traduse.")
        return

    combined_text = " ".join(translated_texts)[:MAX_CHARS]

    try:
        events = generate_events(combined_text)
    except Exception as e:
        print(f"Eroare la generare evenimente: {e}")
        events = []

    unique_events = remove_duplicates(events)

    data = {
        "events": unique_events,
        "script_run_time": datetime.utcnow().isoformat() + "Z"
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Salvate {len(unique_events)} evenimente unice.")

if __name__ == "__main__":
    main()
