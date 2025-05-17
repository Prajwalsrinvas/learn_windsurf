import sys
from collections import Counter

import nltk
import requests
from nltk.corpus import stopwords

from wiki_cache_utils import load_result_cache, save_result_cache


def download_nltk_resources():
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords")
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")
    # Try to download punkt_tab if available (for new NLTK versions)
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        try:
            nltk.download("punkt_tab")
        except Exception:
            print("Could not download 'punkt_tab'. Proceeding anyway.")


def get_category_members(category, cmcontinue=None):
    """Fetch all page titles in a Wikipedia category, handling continuation."""
    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"
    PARAMS = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmlimit": "500",
        "format": "json",
    }
    if cmcontinue:
        PARAMS["cmcontinue"] = cmcontinue
    response = S.get(url=URL, params=PARAMS)
    data = response.json()
    members = data["query"]["categorymembers"]
    titles = [
        m["title"] for m in members if m["ns"] == 0
    ]  # ns=0 means main/article namespace
    next_continue = data.get("continue", {}).get("cmcontinue")
    return titles, next_continue


def get_all_category_members(category):
    titles = []
    cmcontinue = None
    while True:
        batch, cmcontinue = get_category_members(category, cmcontinue)
        titles.extend(batch)
        if not cmcontinue:
            break
    return titles


def get_page_text(title):
    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"
    PARAMS = {
        "action": "query",
        "prop": "extracts",
        "explaintext": True,
        "titles": title,
        "format": "json",
    }
    response = S.get(url=URL, params=PARAMS)
    data = response.json()
    pages = data["query"]["pages"]
    for page_id in pages:
        return pages[page_id].get("extract", "")
    return ""


def main():
    if len(sys.argv) != 2:
        print("Usage: python wiki_category_word_freq.py <Wikipedia_Category>")
        sys.exit(1)
    category = sys.argv[1]
    # Try to load cached result
    cached = load_result_cache(category)
    if cached:
        print(f"Loaded cached results for category: {category}\n")
        for word, count in cached["freq"][:50]:
            print(f"{word}: {count}")
        return
    download_nltk_resources()
    stop_words = set(stopwords.words("english"))
    all_text = []
    print(f"Fetching pages in category: {category}")
    titles = get_all_category_members(category)
    print(f"Found {len(titles)} pages. Downloading text...")
    for idx, title in enumerate(titles, 1):
        print(f"[{idx}/{len(titles)}] {title}")
        text = get_page_text(title)
        all_text.append(text)
    print("Tokenizing and counting word frequencies...")
    words = []
    for idx, text in enumerate(all_text):
        try:
            tokens = nltk.word_tokenize(text)
            tokens = [
                w.lower() for w in tokens if w.isalpha() and w.lower() not in stop_words
            ]
            words.extend(tokens)
        except Exception as e:
            print(f"Tokenization failed for page {idx+1}: {e}")
    freq = Counter(words)
    # Save result to cache
    save_result_cache(category, {"freq": freq.most_common()})
    print("\nCumulative frequency of non-common words:")
    for word, count in freq.most_common(50):
        print(f"{word}: {count}")


if __name__ == "__main__":
    main()
