import feedparser
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone
import email.utils
import urllib.parse
import ollama_client

def clean_html(text):
    """Strips HTML tags from a text string."""
    if not text:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).strip()

def format_date_italian(pub_date_str):
    """
    Parses the pubDate from RSS (e.g., 'Sun, 24 May 2026 12:00:00 GMT')
    and returns a user-friendly Italian string like 'Oggi alle 12:00' or 'Ieri alle 12:00'.
    """
    try:
        dt = email.utils.parsedate_to_datetime(pub_date_str)
        # Convert to local timezone
        dt_local = dt.astimezone()
        now = datetime.now(timezone.utc).astimezone()
        
        diff = now.date() - dt_local.date()
        
        time_str = dt_local.strftime("%H:%M")
        
        if diff.days == 0:
            return f"Oggi alle {time_str}"
        elif diff.days == 1:
            return f"Ieri alle {time_str}"
        else:
            months = {
                1: "Gen", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mag", 6: "Giu",
                7: "Lug", 8: "Ago", 9: "Set", 10: "Ott", 11: "Nov", 12: "Dic"
            }
            day = dt_local.day
            month = months.get(dt_local.month, "")
            year = dt_local.year
            return f"{day} {month} {year}, {time_str}"
    except Exception:
        return pub_date_str

from googlenewsdecoder import gnewsdecoder

def fetch_article_details(google_link):
    """
    Decodes the Google News link and tries to scrape the meta description
    or the first paragraphs of the destination page.
    Returns (cleaned_snippet, final_url).
    """
    # 1. Resolve the original URL using googlenewsdecoder
    try:
        decoded = gnewsdecoder(google_link)
        if decoded.get("status"):
            final_url = decoded.get("decoded_url")
        else:
            final_url = google_link
    except Exception:
        final_url = google_link

    # If it still points to news.google.com, don't try to fetch and scrape to avoid consent/blocks
    if "news.google.com" in final_url:
        return None, final_url

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        # Request with a short timeout to prevent hanging the app
        response = requests.get(final_url, headers=headers, timeout=3.0, allow_redirects=True)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find the description meta tag
            meta_desc = (
                soup.find('meta', attrs={'name': 'description'}) or
                soup.find('meta', attrs={'property': 'og:description'}) or
                soup.find('meta', attrs={'name': 'twitter:description'})
            )
            
            if meta_desc and meta_desc.get('content'):
                desc = meta_desc.get('content').strip()
                if len(desc) > 30:
                    return desc, final_url
            
            # Fallback to the first two paragraphs
            paragraphs = soup.find_all('p')
            p_texts = []
            for p in paragraphs:
                text = p.get_text().strip()
                # Filter out very short paragraphs or cookies banners
                if len(text) > 40 and not any(kw in text.lower() for kw in ["cookies", "cookie", "privacy policy", "acconsento"]):
                    p_texts.append(text)
                if len(p_texts) >= 2:
                    break
            
            if p_texts:
                return " ".join(p_texts)[:400], final_url
                
        return None, final_url
    except Exception:
        return None, final_url

def get_news(topic, days=2, feeds_to_use=None, max_news_count=15, model=None, server_url=None):
    """
    Fetches news from various continental feeds based on the search topic.
    topic: the keyword/phrase to search for.
    days: 1 (today) or 2 (today and yesterday).
    feeds_to_use: list of feed keys to fetch, e.g. ["europe", "north_america", ...].
    max_news_count: maximum number of news items to return.
    model: Ollama model for query translation.
    server_url: Ollama server URL.
    """
    if feeds_to_use is None:
        feeds_to_use = ["europe", "north_america"]

    # Pre-translate query for each target language needed
    translated_queries = {
        "IT": topic,
        "EN": topic,
        "ZH": topic,
        "ES": topic,
        "JA": topic,
        "RU": topic,
        "FR": topic,
        "DE": topic,
        "AR": topic
    }
    
    if model and server_url:
        # Determine which target languages we need based on selected feeds
        languages_needed = set()
        for feed_key in feeds_to_use:
            if feed_key in ["north_america", "oceania"]:
                languages_needed.add("EN")
            elif feed_key == "africa":
                languages_needed.add("EN")
                languages_needed.add("AR")
            elif feed_key == "europe":
                languages_needed.add("EN")
                languages_needed.add("ES")
                languages_needed.add("FR")
                languages_needed.add("DE")
                languages_needed.add("RU")
            elif feed_key == "asia":
                languages_needed.add("ZH")
                languages_needed.add("JA")
                languages_needed.add("RU")
            elif feed_key == "south_america":
                languages_needed.add("ES")
        
        for lang in languages_needed:
            try:
                translated = ollama_client.translate_query(topic, lang, model, server_url)
                if translated:
                    translated_queries[lang] = translated
            except Exception as e:
                print(f"Errore nella traduzione per la lingua {lang}: {e}")

    # Feed configurations mapping
    feed_configs = {
        "north_america": [
            {
                "lang": "EN",
                "url": "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en",
                "default_source_lang": "EN"
            }
        ],
        "south_america": [
            {
                "lang": "ES",
                "url": "https://news.google.com/rss/search?q={query}&hl=es-419&gl=US&ceid=US:es-419",
                "default_source_lang": "ES"
            }
        ],
        "europe": [
            {
                "lang": "IT",
                "url": "https://news.google.com/rss/search?q={query}&hl=it&gl=IT&ceid=IT:it",
                "default_source_lang": "IT"
            },
            {
                "lang": "EN",
                "url": "https://news.google.com/rss/search?q={query}&hl=en-GB&gl=GB&ceid=GB:en",
                "default_source_lang": "EN"
            },
            {
                "lang": "ES",
                "url": "https://news.google.com/rss/search?q={query}&hl=es-ES&gl=ES&ceid=ES:es",
                "default_source_lang": "ES"
            },
            {
                "lang": "FR",
                "url": "https://news.google.com/rss/search?q={query}&hl=fr&gl=FR&ceid=FR:fr",
                "default_source_lang": "FR"
            },
            {
                "lang": "DE",
                "url": "https://news.google.com/rss/search?q={query}&hl=de&gl=DE&ceid=DE:de",
                "default_source_lang": "DE"
            },
            {
                "lang": "RU",
                "url": "https://news.google.com/rss/search?q={query}&hl=ru&gl=RU&ceid=RU:ru",
                "default_source_lang": "RU"
            }
        ],
        "asia": [
            {
                "lang": "ZH",
                "url": "https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh",
                "default_source_lang": "ZH"
            },
            {
                "lang": "JA",
                "url": "https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP:ja",
                "default_source_lang": "JA"
            },
            {
                "lang": "RU",
                "url": "https://news.google.com/rss/search?q={query}&hl=ru&gl=RU&ceid=RU:ru",
                "default_source_lang": "RU"
            }
        ],
        "africa": [
            {
                "lang": "EN",
                "url": "https://news.google.com/rss/search?q={query}&hl=en-ZA&gl=ZA&ceid=ZA:en",
                "default_source_lang": "EN"
            },
            {
                "lang": "AR",
                "url": "https://news.google.com/rss/search?q={query}&hl=ar&gl=EG&ceid=EG:ar",
                "default_source_lang": "AR"
            }
        ],
        "oceania": [
            {
                "lang": "EN",
                "url": "https://news.google.com/rss/search?q={query}&hl=en-AU&gl=AU&ceid=AU:en",
                "default_source_lang": "EN"
            }
        ]
    }

    news_list = []
    seen_titles = set()
    seen_links = set()

    def normalize_title(t):
        return re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', t).lower()

    def parse_pub_date(pub_date_str):
        try:
            return email.utils.parsedate_to_datetime(pub_date_str)
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    # Fetch and parse feeds
    for feed_key in feeds_to_use:
        if feed_key not in feed_configs:
            continue
        
        for cfg in feed_configs[feed_key]:
            lang = cfg["lang"]
            query_text = translated_queries.get(lang, topic)
            
            # Format search query: url-encode and append time range constraint
            query_param = urllib.parse.quote_plus(query_text) + f"+when:{days}d"
            url = cfg["url"].format(query=query_param)

            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title_raw = entry.get("title", "")
                    
                    # Split title and source
                    parts = title_raw.rsplit(" - ", 1)
                    if len(parts) == 2:
                        title = parts[0]
                        source = parts[1]
                    else:
                        title = title_raw
                        source = "Fonte Sconosciuta"

                    norm_title = normalize_title(title)
                    google_link = entry.get("link", "")

                    # De-duplicate checks
                    if norm_title in seen_titles or google_link in seen_links:
                        continue

                    seen_titles.add(norm_title)
                    seen_links.add(google_link)

                    pub_date = entry.get("published", "")
                    formatted_date = format_date_italian(pub_date)
                    summary_raw = entry.get("summary", "")
                    rss_snippet = clean_html(summary_raw)

                    news_list.append({
                        "title_original": title,
                        "source": source,
                        "pub_date_raw": pub_date,
                        "pub_date_italian": formatted_date,
                        "google_link": google_link,
                        "rss_snippet": rss_snippet,
                        "resolved_link": google_link, # Default
                        "full_snippet": rss_snippet,  # Default
                        "lang": cfg["default_source_lang"]
                    })
            except Exception as e:
                # Silently ignore feed-specific parse issues to prevent complete app crashes
                print(f"Errore nel recupero del feed {feed_key} (lingua {lang}): {e}")

    # Sort all items by publication date (newest first)
    news_list.sort(key=lambda x: parse_pub_date(x["pub_date_raw"]), reverse=True)

    # Limit to max_news_count
    return news_list[:max_news_count]

def get_ai_news(days=2, feeds_to_use=None, max_news_count=15):
    """Fallback compatibility wrapper for AI news fetching."""
    mapped_feeds = []
    if feeds_to_use:
        for f in feeds_to_use:
            if f == "global_en":
                mapped_feeds.append("north_america")
            elif f == "asia_zh":
                mapped_feeds.append("asia")
            elif f == "italy_it":
                mapped_feeds.append("europe")
            else:
                mapped_feeds.append(f)
    else:
        mapped_feeds = ["europe", "north_america"]
    return get_news(topic="Intelligenza Artificiale", days=days, feeds_to_use=mapped_feeds, max_news_count=max_news_count)
