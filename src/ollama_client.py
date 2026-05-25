import requests
import json

def get_local_models(server_url="http://localhost:11434"):
    """
    Fetches the list of installed models from the local Ollama instance.
    Returns a list of model names (strings).
    Raises ConnectionError if the server is unreachable.
    """
    try:
        response = requests.get(f"{server_url}/api/tags", timeout=3)
        if response.status_code == 200:
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            return models
        else:
            return []
    except Exception as e:
        raise ConnectionError(f"Impossibile connettersi a Ollama su {server_url}: {e}")

def translate_query(query, target_lang, model, server_url="http://localhost:11434"):
    """
    Translates the search query into the target language using Ollama.
    target_lang is a code like: 'EN', 'ZH', 'ES', 'FR', 'DE', 'PT', 'JA'.
    """
    if not model or not query:
        return query
        
    if target_lang == "IT":
        return query

    # Pre-defined mapping for the default topic "Intelligenza Artificiale" or "AI"
    # to avoid Ollama calls for the default search term
    defaults = {
        "intelligenza artificiale": {
            "EN": "Artificial Intelligence",
            "ZH": "人工智能",
            "ES": "Inteligencia Artificial",
            "JA": "人工知能",
            "RU": "Искусственный интеллект",
            "FR": "Intelligence artificielle",
            "DE": "Künstliche Intelligenz",
            "AR": "الذكاء الاصطناعي"
        },
        "ai": {
            "EN": "AI",
            "ZH": "AI",
            "ES": "IA",
            "JA": "AI",
            "RU": "ИИ",
            "FR": "IA",
            "DE": "KI",
            "AR": "الذكاء الاصطناعي"
        }
    }
    
    q_lower = query.lower().strip()
    if q_lower in defaults:
        return defaults[q_lower].get(target_lang, query)
        
    # Translate via Ollama
    lang_names = {
        "EN": "English",
        "ZH": "Chinese",
        "ES": "Spanish",
        "JA": "Japanese",
        "RU": "Russian",
        "FR": "French",
        "DE": "German",
        "AR": "Arabic"
    }
    lang_name = lang_names.get(target_lang, "English")
    
    prompt = f"""Traduci questa parola o frase di ricerca dall'italiano in {lang_name}.
Testo: {query}

Rispondi con la sola traduzione finale, senza virgolette, senza spiegazioni e senza punteggiatura.
"""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    }
    try:
        response = requests.post(f"{server_url}/api/generate", json=payload, timeout=5)
        if response.status_code == 200:
            translation = response.json().get("response", "").strip()
            # Clean up quotes if the model put them
            translation = translation.replace('"', '').replace("'", "").strip()
            if translation:
                return translation
    except Exception:
        pass
    
    return query

def get_prompt_lang_name(autonym):
    mapping = {
        "English": "english",
        "Italiano": "italiano",
        "Deutsch": "deutsch",
        "Français": "français",
        "Español": "español",
        "中文": "cinese",
        "日本語": "giapponese",
        "Русский": "russo",
        "العربية": "arabo"
    }
    return mapping.get(autonym, autonym.lower())

def summarize_news(title, text_content, model, topic="Intelligenza Artificiale", target_lang="English", server_url="http://localhost:11434"):
    """
    Uses the selected local Ollama model to translate the title and summarize
    the content in the specified target language.
    Returns a dictionary: {"titolo_italiano": ..., "riassunto_italiano": ...}
    """
    lang_name = get_prompt_lang_name(target_lang)
    prompt = f"""Sei un assistente AI esperto in notizie sul tema "{topic}". Il tuo compito è tradurre in {lang_name} il titolo e riassumere il contenuto della seguente notizia riguardante "{topic}".

Titolo originale: {title}
Contenuto della notizia: {text_content}

Rispondi ESCLUSIVAMENTE in formato JSON con questa esatta struttura:
{{
  "titolo_tradotto": "Traduzione del titolo in {lang_name}",
  "riassunto_tradotto": "Un riassunto conciso in {lang_name} di 2-3 frasi chiare e scorrevoli che descriva la notizia."
}}
"""

    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.3
        }
    }

    try:
        response = requests.post(f"{server_url}/api/generate", json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "").strip()
            thinking_text = result.get("thinking", "").strip()
            
            def extract_json(text):
                if not text:
                    return None
                text_strip = text.strip()
                try:
                    return json.loads(text_strip)
                except json.JSONDecodeError:
                    pass
                
                # Try to find JSON block using regex
                import re
                match = re.search(r'\{.*\}', text_strip, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except json.JSONDecodeError:
                        pass
                return None

            parsed = extract_json(response_text) or extract_json(thinking_text)
            
            if parsed:
                # Support both new "titolo_tradotto" / "riassunto_tradotto" and old "titolo_italiano" / "riassunto_italiano"
                t_key = "titolo_tradotto" if "titolo_tradotto" in parsed else "titolo_italiano"
                r_key = "riassunto_tradotto" if "riassunto_tradotto" in parsed else "riassunto_italiano"
                
                if t_key in parsed and r_key in parsed:
                    return {
                        "titolo_italiano": parsed[t_key],
                        "riassunto_italiano": parsed[r_key]
                    }
            
            # Fallback if JSON format was not followed or parsing failed
            # Try a simple text fallback
            fallback_text = response_text if response_text else thinking_text
            return {
                "titolo_italiano": title,
                "riassunto_italiano": fallback_text if fallback_text else "Riassunto non disponibile."
            }
        else:
            return {
                "titolo_italiano": title,
                "riassunto_italiano": f"Errore Ollama (Codice {response.status_code})"
            }
    except Exception as e:
        return {
            "titolo_italiano": title,
            "riassunto_italiano": f"Errore di connessione a Ollama: {str(e)}"
        }

def generate_social_post(news_items, platform, tone, length, include_hashtags, include_emojis, model, topic="Intelligenza Artificiale", target_lang="English", server_url="http://localhost:11434"):
    """
    Generates a social media post based on a list of selected news items.
    """
    # Build prompt
    news_details = ""
    for idx, item in enumerate(news_items):
        news_details += f"\nNotizia {idx+1}:\n- Titolo: {item.get('title_translated', item.get('title_original'))}\n- Riassunto: {item.get('summary_italian', '')}\n- Fonte: {item.get('source', '')}\n"

    # Settings description
    length_desc = {
        "Breve": "molto conciso (adatto per post rapidi o social come Twitter/X)",
        "Medio": "di media lunghezza (bilanciato, ideale per LinkedIn)",
        "Dettagliato": "più lungo e approfondito (adatto per un articolo o newsletter)"
    }.get(length, "di media lunghezza")
    
    lang_name = get_prompt_lang_name(target_lang)
    
    prompt = f"""Sei un Social Media Manager professionista ed esperto del settore. Il tuo compito è creare un post/articolo professionale in {lang_name} da pubblicare sui social network, basandoti sulle seguenti notizie recenti sul tema "{topic}":

{news_details}

Caratteristiche del post da generare:
- Piattaforma di destinazione: {platform}
- Tono di voce: {tone}
- Lunghezza del testo: {length_desc}
- Uso di Emojis: {'Abilitato (inserisci emoji pertinenti per rendere il testo attraente e leggibile)' if include_emojis else 'Disabilitato (non usare alcuna emoji)'}
- Hashtag: {'Abilitati (aggiungi hashtag pertinenti a fine post)' if include_hashtags else 'Disabilitati (non aggiungere alcun hashtag)'}
- Lingua: {lang_name}

Linee guida per la scrittura:
1. Crea un'introduzione accattivante sul tema "{topic}" basandoti sulle notizie fornite. Scrivi l'introduzione nella lingua selezionata ({lang_name}).
2. Combina o elenca le notizie in modo fluido ed organico, evidenziando i punti chiave e le implicazioni principali. Il tutto nella lingua selezionata ({lang_name}).
3. Concludi con una domanda aperta o una chiamata all'azione (CTA) per stimolare l'interazione dei follower nella lingua selezionata ({lang_name}).
4. Non inventare dettagli non presenti nei riassunti delle notizie fornite.
5. Rispondi ESCLUSIVAMENTE con il testo finale del post, pronto per essere pubblicato (senza messaggi introduttivi tipo "Ecco il post generato:").

Testo del post:
"""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7
        }
    }

    try:
        response = requests.post(f"{server_url}/api/generate", json=payload, timeout=300)
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "").strip()
            # If model is a reasoning model, filter thinking blocks
            import re
            response_text = re.sub(r'<thinking>.*?</thinking>', '', response_text, flags=re.DOTALL).strip()
            return response_text
        else:
            return f"Errore Ollama (Codice {response.status_code}): Impossibile generare il post."
    except Exception as e:
        return f"Errore di connessione a Ollama: {str(e)}"

