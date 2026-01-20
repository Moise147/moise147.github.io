import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import json
from datetime import datetime
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


TELEGRAM_URLS = [
    "https://t.me/s/kpszsu?embed=1",
    "https://t.me/s/AMK_Mapping?embed=1",
    "https://t.me/s/southfronteng?embed=1"
]

translator_en_ro = pipeline("translation", model="Helsinki-NLP/opus-mt-en-ro")
translator_ru_ro = pipeline("translation", model="Helsinki-NLP/opus-mt-ru-ro")

summarizer = pipeline(
    "summarization",
    model="sshleifer/distilbart-cnn-12-6"
)

def detect_language(text):
    if any("а" <= c <= "я" or "А" <= c <= "Я" for c in text):
        return "ru"
    return "en"

def translate_to_ro(text):
    lang = detect_language(text)
    if lang == "ru":
        return translator_ru_ro(text, max_length=512)[0]["translation_text"]
    return translator_en_ro(text, max_length=512)[0]["translation_text"]
    
def generate_events(text):
    summary = summarizer(
        text,
        max_length=120,
        min_length=40,
        do_sample=False
    )[0]["summary_text"]

    # separă în liniuțe
    events = [
        f"- {s.strip()}"
        for s in summary.replace("•", ".").split(".")
        if len(s.strip()) > 20
    ]
    return events

def remove_duplicates(events, threshold=0.85):
    if not events:
        return []

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(events)
    similarity = cosine_similarity(vectors)

    unique = []
    for i, e in enumerate(events):
        if not any(similarity[i][j] > threshold for j in unique):
            unique.append(i)

    return [events[i] for i in unique]


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
    all_events = []

    for url in TELEGRAM_URLS:
        messages = scrape_messages(url)

        for msg in messages:
            translated = translate_to_ro(msg["original"])
            events = generate_events(translated)
            all_events.extend(events)

    unique_events = remove_duplicates(all_events)

    data = {
        "events": unique_events,
        "script_run_time": datetime.utcnow().isoformat() + "Z"
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(unique_events)} unique events")

if __name__ == "__main__":
    main()

