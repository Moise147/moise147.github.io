import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from langdetect import detect
from functools import lru_cache

# Constante
MAX_MESSAGES = 20
MAX_NEWS_ITEMS = 10
TELEGRAM_URLS = [
    "https://t.me/s/kpszsu?embed=1",
    "https://t.me/s/AMK_Mapping?embed=1",
    "https://t.me/s/southfronteng?embed=1",
    "https://t.me/s/kiber_boroshno?embed=1"
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

def generate_summary(text):
    try:
        if len(text.split()) < 30:
            return text.strip()
        summary = summarizer(text, max_length=120, min_length=40, do_sample=False)
        return summary[0]["summary_text"].strip()
    except Exception as e:
        print(f"Eroare la rezumare: {e}")
        return text.strip()

def remove_duplicates(news_items):
    if not news_items:
        return []
    unique_items = []
    seen = set()
    for item in news_items:
        summary = item.get("summary", "").strip().lower()
        if summary and summary not in seen:
            seen.add(summary)
            unique_items.append(item)
    return unique_items

def scrape_messages(url):
    print(f"Accesăm URL-ul: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        messages = []
        for message in soup.find_all("div", class_=lambda c: c and "tgme_widget_message" in c):
            text_div = message.find("div", class_=lambda c: c and "tgme_widget_message_text" in c)
            if not text_div:
                continue
            text = text_div.get_text(separator="\n").strip()
            link_tag = message.find("a", class_=lambda c: c and "tgme_widget_message_date" in c)
            link = link_tag["href"] if link_tag and link_tag.has_attr("href") else None
            messages.append({
                "original": text,
                "link": link,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        return messages
    except Exception as e:
        print(f"Eroare la scrapare: {e}")
        return []

def main():
    news_items = []

    for url in TELEGRAM_URLS:
        messages = scrape_messages(url)[:MAX_MESSAGES]
        for msg in messages:
            try:
                summary_base = generate_summary(msg["original"])
                summary_text = translate_to_ro(summary_base)
                if not summary_text:
                    continue
                importance_score = len(msg["original"].split())
                news_items.append({
                    "summary": summary_text,
                    "link": msg.get("link"),
                    "importance_score": importance_score
                })
            except Exception as e:
                print(f"Eroare la traducere mesaj: {e}")

    if not news_items:
        print("Nu există rezumate disponibile.")
        return

    unique_items = remove_duplicates(news_items)
    ranked_items = sorted(unique_items, key=lambda item: item["importance_score"], reverse=True)
    ranked_items = ranked_items[:MAX_NEWS_ITEMS]
    for idx, item in enumerate(ranked_items, start=1):
        item["rank"] = idx

    data = {
        "news": ranked_items,
        "script_run_time": datetime.utcnow().isoformat() + "Z"
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Salvate {len(ranked_items)} știri ordonate după importanță.")

if __name__ == "__main__":
    main()
