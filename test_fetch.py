import sys
sys.path.append('src')

import news_fetcher
import ollama_client

print("Test di recupero notizie...")
news = news_fetcher.get_ai_news(days=1, feeds_to_use=["global_en", "asia_zh"], max_news_count=5)
print(f"Recuperate {len(news)} notizie.")

if news:
    first = news[0]
    print(f"Prima notizia: {first['title_original']} da {first['source']} [Lingua: {first.get('lang')}]")
    print(f"URL: {first['google_link']}")
    print("Tentativo di estrazione snippet...")
    snippet, resolved_url = news_fetcher.fetch_article_details(first['google_link'])
    print(f"URL Risolto: {resolved_url}")
    print(f"Snippet ottenuto: {snippet[:150] if snippet else 'Nessuno (uso RSS)'}")
    
    print("\nVerifica connessione Ollama...")
    try:
        models = ollama_client.get_local_models()
        print(f"Modelli Ollama disponibili: {models}")
        
        if models:
            test_model = "qwen3.5:9b" if "qwen3.5:9b" in models else next((m for m in models if "cloud" not in m), models[0])
            print(f"Tentativo di riassunto con modello '{test_model}'...")
            text_to_summarize = snippet if snippet else first['rss_snippet']
            res = ollama_client.summarize_news(first['title_original'], text_to_summarize[:300], test_model)
            print(f"Titolo tradotto: {res.get('titolo_italiano')}")
            print(f"Riassunto: {res.get('riassunto_italiano')}")
        else:
            print("Nessun modello installato su Ollama.")
    except ConnectionError as e:
        print(f"Connessione a Ollama fallita (il server è attivo?): {e}")
else:
    print("Nessuna notizia trovata.")
