# Smart News AI

Smart News AI è un'applicazione desktop nativa per Linux Mint sviluppata in Python. Il suo scopo è raccogliere, analizzare e riassumere in tempo reale notizie su **qualsiasi argomento scelto dall'utente**, dividendole su base continentale (Europa, Nord America, Sud America, Asia, Africa, Oceania) e offrendo riassunti e traduzioni automatiche in lingua italiana. Il tutto avviene **in modo completamente locale e privato**, appoggiandosi a un'istanza locale di Ollama.

L'applicazione include un sistema di archiviazione temporanea offline e un generatore intelligente di articoli e post per i social media basati sulle notizie selezionate.

---

## 📂 Struttura del Progetto

Il codice sorgente è organizzato nella directory `src/`:
*   **`src/config.py`**: Gestisce la lettura e la scrittura delle preferenze dell'utente in `~/.config/ai-news-summarizer/config.json`. Salva il modello selezionato, l'URL del server Ollama, l'arco temporale di ricerca, i continenti abilitati, l'ultimo argomento cercato (`last_search_topic`) e il limite massimo di notizie.
*   **`src/archive.py`**: Gestisce il salvataggio persistente locale delle notizie appuntate dall'utente in `~/.config/ai-news-summarizer/archive.json`. Include una logica di auto-pulizia per rimuovere automaticamente le notizie salvate da più di 7 giorni.
*   **`src/news_fetcher.py`**: Si occupa di interrogare i feed RSS di Google News per i vari continenti. Traduce dinamicamente il termine di ricerca inserito dall'utente nella lingua del feed continentale, decodifica i link tracciati di Google RSS e scarica lo snippet o la descrizione della pagina di destinazione usando BeautifulSoup4. Implementa inoltre la rimozione dei duplicati e l'ordinamento cronologico.
*   **`src/ollama_client.py`**: Gestisce l'interazione asincrona con l'API locale di Ollama (`http://localhost:11434`). Gestisce la traduzione dei termini di ricerca, la sintesi degli articoli basandosi sul tema specificato e la generazione strutturata di post per i social media (con supporto ai tag `<thinking>` dei modelli di ragionamento tipo Qwen 2.5/3.5 o DeepSeek R1).
*   **`src/main.py`**: Punto di ingresso grafico dell'applicazione, realizzato con `customtkinter`. Implementa il layout a schede (Notizie Recenti, Notizie Salvate, Generatore Post), la barra di ricerca in alto, la griglia a due colonne dei continenti e la gestione dei thread in background per mantenere fluida l'interfaccia.
*   **`build_deb.sh`**: Script Bash automatizzato per compilare il codice con `PyInstaller` e generare il pacchetto di installazione nativo `smart-news-ai.deb` per Debian/Linux Mint.

---

## ✨ Funzionalità Chiave

1.  **Ricerca Libera per Argomento**:
    L'utente può digitare qualsiasi argomento nella barra di ricerca principale (es. "Energie rinnovabili", "Esplorazione Spaziale", "Robotica"). L'applicazione traduce automaticamente l'argomento per i feed in lingua straniera prima di effettuare la ricerca.
2.  **Suddivisione per Continente**:
    I feed sono raggruppati in 6 continenti: Europa, Nord America, Sud America, Asia, Africa e Oceania. Questo permette all'utente di selezionare aree geografiche specifiche per le sue ricerche.
3.  **Archiviazione Locale (📌)**:
    Ogni card presenta un pulsante `📌 Salva` per inserire la notizia in un archivio locale permanente per un massimo di 7 giorni. Gli elementi scaduti vengono ripuliti in automatico. È possibile consultare l'archivio nella scheda **Notizie Salvate**.
4.  **Generatore di Post Social**:
    Selezionando una o più notizie tramite la checkbox `Seleziona per Post`, l'utente le aggiunge come fonti del generatore. Nella scheda **Generatore Post**, è possibile configurare:
    *   **Piattaforma**: LinkedIn, X / Twitter, Facebook, Blog / Articolo.
    *   **Tono di voce**: Professionale, Informativo, Coinvolgente, Tecnico.
    *   **Lunghezza**: Breve, Medio, Dettagliato.
    *   **Opzioni aggiuntive**: Abilitare/disabilitare l'uso di Emoji e Hashtag.
    
    Il post viene redatto in italiano da Ollama in modo asincrono, rimanendo fedele al tema di ricerca originario.

---

## 🛠️ Tecnologie Utilizzate

1.  **Python 3.12**
2.  **CustomTkinter & Tkinter**: Per la GUI moderna e reattiva con caricamento nativo delle immagini PNG.
3.  **Feedparser & BeautifulSoup4**: Per il download e l'estrazione intelligente del testo dei siti di notizie.
4.  **googlenewsdecoder**: Fondamentale per risalire all'URL originale partendo dall'RSS cifrato di Google.
5.  **Ollama**: Integrazione locale con modelli LLM tramite API.

---

## 🚀 Installazione e Avvio

### Pacchetto pre-compilato (.deb)
Se hai già generato il pacchetto, puoi installarlo direttamente con:
```bash
sudo dpkg -i smart-news-ai.deb
```
L'applicazione verrà aggiunta al menu di sistema di Linux Mint con la sua icona personalizzata in `/usr/share/pixmaps/smart-news-ai.png` e descrizione "Aggregatore di notizie e creatore di post".

### Esecuzione da sorgente (Sviluppo)
1.  Crea l'ambiente virtuale e installa le dipendenze:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```
2.  Avvia l'applicazione:
     ```bash
     python3 src/main.py
     ```

---

## 🔍 Criteri di Ricerca e Lingue
L'applicazione supporta la ricerca multilingua combinata e de-duplicata su 6 continenti, traducendo dinamicamente l'argomento cercato nelle seguenti lingue di destinazione dei feed:
*   **Inglese (EN)**: Usato nei feed di Nord America, Africa (Sudafrica), Oceania ed Europa (UK).
*   **Cinese (ZH)**: Usato nel feed dell'Asia (Cina/Taiwan).
*   **Giapponese (JA)**: Usato nel feed dell'Asia (Giappone).
*   **Spagnolo (ES)**: Usato nei feed di Sud America ed Europa (Spagna).
*   **Francese (FR)**: Usato nel feed dell'Europa (Francia).
*   **Tedesco (DE)**: Usato nel feed dell'Europa (Germania).
*   **Russo (RU)**: Usato nei feed eurasiatici di Europa e Asia (Russia).
*   **Arabo (AR)**: Usato nel feed dell'Africa (Egitto/Nord Africa).
*   **Italiano (IT)**: Usato nel feed dell'Europa (Italia).

All'avvio, l'applicazione interroga Ollama per scoprire quali modelli sono installati localmente sulla GPU/CPU e li presenta in un menu a tendina.
