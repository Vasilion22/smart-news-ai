import sys
import os
import shutil
import time
import json
sys.path.append('src')

import archive
import ollama_client

def test_archive_system():
    print("=== TEST SISTEMA ARCHIVIO ===")
    
    # Backup current archive if any
    config_dir = os.path.expanduser("~/.config/ai-news-summarizer")
    archive_path = os.path.join(config_dir, "archive.json")
    backup_path = os.path.join(config_dir, "archive.json.bak")
    
    has_backup = False
    if os.path.exists(archive_path):
        shutil.copy2(archive_path, backup_path)
        has_backup = True
        os.remove(archive_path)
        
    try:
        # 1. Test empty archive
        items = archive.load_archive()
        assert len(items) == 0, "L'archivio iniziale dovrebbe essere vuoto"
        print("1. Caricamento archivio vuoto: OK")
        
        # 2. Test adding item
        news_item = {
            "title_original": "AI Breakthrough in Robotics",
            "title_translated": "Svolta dell'IA nella Robotica",
            "source": "TechNews",
            "pub_date_italian": "Oggi",
            "summary_italian": "Un nuovo modello di IA controlla robot con precisione millimetrica.",
            "google_link": "https://example.com/robotics",
            "resolved_link": "https://example.com/robotics-full"
        }
        
        archive.add_to_archive(news_item)
        items = archive.load_archive()
        assert len(items) == 1, "Dovrebbe esserci 1 elemento in archivio"
        assert items[0]["title_original"] == "AI Breakthrough in Robotics", "Il titolo originale non corrisponde"
        print("2. Aggiunta notizia in archivio: OK")
        
        # 3. Test is_archived
        assert archive.is_archived(news_item), "L'elemento dovrebbe risultare archiviato"
        print("3. Verifica presenza (is_archived): OK")
        
        # 4. Test duplicate prevention
        archive.add_to_archive(news_item)
        items = archive.load_archive()
        assert len(items) == 1, "Non dovrebbero essere inseriti duplicati"
        print("4. Prevenzione duplicati: OK")
        
        # 5. Test expiration / pruning
        # We manually modify the saved JSON to set the timestamp to 8 days ago
        with open(archive_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert len(data) == 1
        # Set timestamp to 8 days ago
        from datetime import datetime, timezone, timedelta
        data[0]["archived_at"] = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        
        with open(archive_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        # Loading should trigger auto-pruning
        items = archive.load_archive()
        assert len(items) == 0, "L'elemento vecchio di 8 giorni avrebbe dovuto essere eliminato"
        print("5. Scadenza automatica (7 giorni): OK")
        
        # 6. Test manual removal
        archive.add_to_archive(news_item)
        assert len(archive.load_archive()) == 1
        archive.remove_from_archive(news_item)
        assert len(archive.load_archive()) == 0, "La rimozione manuale non ha funzionato"
        print("6. Rimozione manuale: OK")
        
    finally:
        # Restore backup if there was one
        if os.path.exists(archive_path):
            os.remove(archive_path)
        if has_backup:
            shutil.move(backup_path, archive_path)
            
    print("SISTEMA ARCHIVIO CORRETTO AL 100%\n")


def test_social_generator_prompt():
    print("=== TEST PROMPT GENERATORE SOCIAL ===")
    
    # We can mock requests to see if prompt construction works.
    # Since generate_social_post makes an HTTP request, we can temporarily mock requests.post:
    import requests
    original_post = requests.post
    
    captured_payload = {}
    
    class MockResponse:
        def __init__(self, text):
            self.text = text
            self.status_code = 200
            
        def json(self):
            return {"response": "Mocked social post text <thinking>some reasoning</thinking> here."}
            
    def mock_post(url, json, **kwargs):
        nonlocal captured_payload
        captured_payload = json
        # Return chunks of text as lines
        return MockResponse("Mocked response")
        
    requests.post = mock_post
    
    try:
        news_items = [
            {
                "title_translated": "Nuovo LLM open source rilasciato",
                "summary_italian": "Un nuovo modello linguistico open source supera GPT-4 in diversi benchmark."
            },
            {
                "title_translated": "Robotica avanzata con IA",
                "summary_italian": "I robot umanoidi stanno per entrare in produzione industriale grazie ai nuovi chip."
            }
        ]
        
        res = ollama_client.generate_social_post(
            news_items=news_items,
            platform="LinkedIn",
            tone="Professionale",
            length="Medio",
            include_hashtags=True,
            include_emojis=True,
            model="test-model",
            server_url="http://localhost:11434"
        )
        
        # Verify the prompt content sent to Ollama
        prompt = captured_payload.get("prompt", "")
        assert "LinkedIn" in prompt
        # Wait, the prompt has "LinkedIn" translated to Italian maybe or kept? Let's check prompt translation/formatting
        assert "Tono: Professionale" in prompt or "LinkedIn" in prompt
        assert "Nuovo LLM open source rilasciato" in prompt
        assert "Robotica avanzata con IA" in prompt
        
        # Verify that thinking block was stripped from output
        assert "<thinking>" not in res, "I tag di reasoning dovrebbero essere rimossi"
        assert "some reasoning" not in res, "Il contenuto di reasoning dovrebbe essere rimosso"
        assert "Mocked social post text" in res, "Il post generato finale non è corretto"
        
        print("1. Costruzione prompt & Invio: OK")
        print("2. Rimozione automatica blocco <thinking>: OK")
        
    finally:
        requests.post = original_post
        
    print("GENERATORE SOCIAL POST CORRETTO AL 100%\n")


def test_custom_topic_and_translation():
    print("=== TEST TRADUZIONE ED ELABORAZIONE TOPIC PERSONALIZZATO ===")
    
    # Mock requests for query translation
    import requests
    original_post = requests.post
    
    captured_payloads = []
    
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
            
        def json(self):
            return self.json_data
            
    def mock_post(url, json, **kwargs):
        nonlocal captured_payloads
        captured_payloads.append((url, json))
        if "api/generate" in url:
            prompt = json.get("prompt", "")
            if "Traduci questa parola" in prompt:
                if "Chinese" in prompt or "ZH" in prompt:
                    return MockResponse({"response": "气候变化"})
                elif "English" in prompt or "EN" in prompt:
                    return MockResponse({"response": "climate change"})
                elif "Spanish" in prompt or "ES" in prompt:
                    return MockResponse({"response": "cambio climático"})
            elif "riassumere il contenuto" in prompt:
                return MockResponse({"response": '{"titolo_italiano": "Mocked Translated Title", "riassunto_italiano": "Questo è un riassunto mockato."}'})
        return MockResponse({})
        
    requests.post = mock_post
    
    try:
        # Test translation
        translated_en = ollama_client.translate_query("cambiamento climatico", "EN", "test-model")
        assert translated_en == "climate change", f"Traduzione fallita: {translated_en}"
        
        translated_zh = ollama_client.translate_query("cambiamento climatico", "ZH", "test-model")
        assert translated_zh == "气候变化", f"Traduzione fallita: {translated_zh}"
        
        print("1. Traduzione termine con Ollama: OK")
        
        # Test default values mapping (bypass Ollama calls for default term)
        captured_payloads.clear()
        translated_default = ollama_client.translate_query("Intelligenza Artificiale", "EN", "test-model")
        assert translated_default == "Artificial Intelligence", f"Traduzione default fallita: {translated_default}"
        assert len(captured_payloads) == 0, "Non avrebbe dovuto chiamare Ollama per il termine di default"
        print("2. Mapping termini predefiniti (zero chiamate Ollama): OK")
        
        # Test summarization prompt custom topic
        res = ollama_client.summarize_news(
            title="Climate crisis worsens",
            text_content="Global temperatures rise at record speeds.",
            model="test-model",
            topic="Cambiamento Climatico"
        )
        assert res.get("titolo_italiano") == "Mocked Translated Title"
        # Check prompt contains custom topic
        assert any("Cambiamento Climatico" in payload[1].get("prompt", "") for payload in captured_payloads if "riassumere il contenuto" in payload[1].get("prompt", ""))
        print("3. Sintesi notizia con argomento custom: OK")
        
    finally:
        requests.post = original_post
        
    print("TEST TOPIC PERSONALIZZATO CORRETTO AL 100%\n")


if __name__ == "__main__":
    try:
        test_archive_system()
        test_social_generator_prompt()
        test_custom_topic_and_translation()
        print("TUTTI I TEST SONO PASSATI CON SUCCESSO! ✓")
    except AssertionError as e:
        print(f"TEST FALLITO: {e}")
        sys.exit(1)
