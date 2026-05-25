import os
import sys
import threading
import webbrowser
import customtkinter as ctk

# Import local modules
import config
import news_fetcher
import ollama_client
import archive

def get_asset_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    
    # Check if the asset is in the current directory (like in PyInstaller temp dir)
    path_direct = os.path.join(base_path, relative_path)
    if os.path.exists(path_direct):
        return path_direct
        
    # Check if the asset is in the parent directory (like in src/ for dev mode)
    path_parent = os.path.join(os.path.dirname(base_path), relative_path)
    if os.path.exists(path_parent):
        return path_parent
        
    # Fallback to local path
    return os.path.join(os.path.abspath("."), relative_path)


# Localized strings for all 9 supported languages
LOCALIZATION = {
    "English": {
        "title": "Smart News AI",
        "subtitle": "News aggregator and social post creator",
        "nav_label": "Navigation:",
        "nav_recent": "📰  Recent News",
        "nav_saved": "📌  Saved News",
        "nav_generator": "✍️  Post Generator",
        "status_detecting": "Ollama: Detecting...",
        "status_connected": "Ollama: Connected",
        "status_disconnected": "Ollama: Disconnected",
        "model_label": "Select Model:",
        "range_label": "Time range:",
        "range_today": "Today Only",
        "range_yesterday": "Today & Yesterday",
        "feeds_label": "Select Continents:",
        "feed_europe": "Europe",
        "feed_na": "N. America",
        "feed_sa": "S. America",
        "feed_asia": "Asia",
        "feed_africa": "Africa",
        "feed_oceania": "Oceania",
        "max_news_label": "Max news to show:",
        "theme_label": "Interface Theme:",
        "theme_dark": "Dark",
        "theme_light": "Light",
        "theme_system": "System",
        "recent_title": "News:",
        "recent_search_placeholder": "What do you want to search for? (e.g. Space, AI, Green Energy...)",
        "recent_search_btn": "Search News 🔍",
        "recent_empty": "No news loaded.\nType a topic and click 'Search News' to start.",
        "saved_title": "Saved News",
        "saved_subtitle": "Local archive (max 7 days)",
        "saved_empty": "Your archive is empty.\nSave news items with the 📌 button!",
        "gen_title": "Social Post Generator",
        "gen_sources_title": "1. Selected Sources:",
        "gen_options_title": "2. Generation Options:",
        "gen_platform_label": "Platform:",
        "gen_platforms": ["LinkedIn", "X / Twitter", "Facebook", "Blog / Article"],
        "gen_tone_label": "Tone of voice:",
        "gen_tones": ["Professional", "Informative", "Engaging", "Technical"],
        "gen_length_label": "Post length:",
        "gen_lengths": ["Short", "Medium", "Detailed"],
        "gen_btn": "Generate Post ⚡",
        "gen_btn_generating": "Generating... ⏳",
        "gen_empty": "Select one or more news items from other tabs using the 'Select for Post' checkbox.",
        "gen_output_placeholder": "The generated post will appear here.\n\nSelect one or more articles from the other tabs, configure the settings on the left, and click 'Generate Post ⚡'.",
        "gen_copy_btn": "Copy to clipboard 📋",
        "gen_clear_btn": "Clear Selection 🧹",
        "toast_copied": "Copied to clipboard!",
        "toast_generating": "Generating social post with local Ollama...\nPlease wait (may take several seconds)...",
        "err_model": "Error: Ollama disconnected or no models installed. Start Ollama and try again.",
        "err_feeds": "Error: Select at least one continent in the sidebar.",
        "err_no_news": "No news found for this time range or continents.",
        "err_generation": "Error during processing: ",
        "progress_fetch": "Downloading news from Google News RSS...",
        "progress_found": "Found {total} articles. Generating summaries...",
        "progress_analyze": "Analyzing article {index}/{total}...",
        "progress_ollama": "Summarizing with Ollama ({model}) {index}/{total}...",
        "btn_save": "📌 Save",
        "btn_saved": "📌 Pinned",
        "btn_remove": "❌ Remove",
        "chk_select_post": "Select for Post",
        "link_source": "Source 🌐"
    },
    "Italiano": {
        "title": "Smart News AI",
        "subtitle": "Aggregatore di notizie e creatore di post",
        "nav_label": "Navigazione:",
        "nav_recent": "📰  Notizie Recenti",
        "nav_saved": "📌  Notizie Salvate",
        "nav_generator": "✍️  Generatore Post",
        "status_detecting": "Ollama: Rilevamento...",
        "status_connected": "Ollama: Connesso",
        "status_disconnected": "Ollama: Disconnesso",
        "model_label": "Seleziona Modello:",
        "range_label": "Intervallo temporale:",
        "range_today": "Solo Oggi",
        "range_yesterday": "Oggi e Ieri",
        "feeds_label": "Seleziona Continenti:",
        "feed_europe": "Europa",
        "feed_na": "N. America",
        "feed_sa": "S. America",
        "feed_asia": "Asia",
        "feed_africa": "Africa",
        "feed_oceania": "Oceania",
        "max_news_label": "Max Notizie da mostrare:",
        "theme_label": "Tema Interfaccia:",
        "theme_dark": "Scuro",
        "theme_light": "Chiaro",
        "theme_system": "Sistema",
        "recent_title": "Notizie:",
        "recent_search_placeholder": "Cosa vuoi cercare? (es. Spazio, AI, Energie Rinnovabili...)",
        "recent_search_btn": "Cerca Notizie 🔍",
        "recent_empty": "Nessuna notizia caricata.\nScrivi un argomento e clicca su 'Cerca Notizie' per iniziare.",
        "saved_title": "Notizie Salvate",
        "saved_subtitle": "Archivio locale (max 7 giorni)",
        "saved_empty": "L'archivio è vuoto.\nSalva le notizie con il pulsante 📌!",
        "gen_title": "Generatore Social Post",
        "gen_sources_title": "1. Fonti Selezionate:",
        "gen_options_title": "2. Opzioni Generazione:",
        "gen_platform_label": "Piattaforma:",
        "gen_platforms": ["LinkedIn", "X / Twitter", "Facebook", "Blog / Articolo"],
        "gen_tone_label": "Tono di voce:",
        "gen_tones": ["Professionale", "Informativo", "Coinvolgente", "Tecnico"],
        "gen_length_label": "Lunghezza post:",
        "gen_lengths": ["Breve", "Medio", "Dettagliato"],
        "gen_btn": "Genera Post ⚡",
        "gen_btn_generating": "Generazione... ⏳",
        "gen_empty": "Seleziona una o più notizie usando la casella 'Seleziona per Post' per usarle come fonti.",
        "gen_output_placeholder": "Il post generato comparirà qui.\n\nSeleziona una o più notizie dalle altre schede ed inserisci i parametri a sinistra, quindi clicca su 'Genera Post ⚡'.",
        "gen_copy_btn": "Copia negli appunti 📋",
        "gen_clear_btn": "Pulisci Selezione 🧹",
        "toast_copied": "Copiato negli appunti!",
        "toast_generating": "Generazione del post social in corso con Ollama locale...\nAttendere prego (può richiedere diversi secondi)...",
        "err_model": "Errore: Ollama disconnesso o nessun modello installato. Avvia Ollama e riprova.",
        "err_feeds": "Errore: Seleziona almeno un continente nella barra laterale.",
        "err_no_news": "Nessuna notizia trovata per questo intervallo temporale o per i continenti selezionati.",
        "err_generation": "Errore durante l'elaborazione: ",
        "progress_fetch": "Scaricamento notizie da Google News RSS...",
        "progress_found": "Trovate {total} notizie. Generazione riassunti in corso...",
        "progress_analyze": "Analisi articolo {index}/{total}...",
        "progress_ollama": "Riassunto con Ollama ({model}) {index}/{total}...",
        "btn_save": "📌 Salva",
        "btn_saved": "📌 Salvato",
        "btn_remove": "❌ Rimuovi",
        "chk_select_post": "Seleziona per Post",
        "link_source": "Fonte 🌐"
    },
    "Deutsch": {
        "title": "Smart News AI",
        "subtitle": "News-Aggregator und Post-Ersteller",
        "nav_label": "Navigation:",
        "nav_recent": "📰  Neuigkeiten",
        "nav_saved": "📌  Gespeichert",
        "nav_generator": "✍️  Post-Generator",
        "status_detecting": "Ollama: Suche...",
        "status_connected": "Ollama: Verbunden",
        "status_disconnected": "Ollama: Getrennt",
        "model_label": "Modell wählen:",
        "range_label": "Zeitraum:",
        "range_today": "Nur Heute",
        "range_yesterday": "Heute & Gestern",
        "feeds_label": "Kontinente wählen:",
        "feed_europe": "Europa",
        "feed_na": "N. Amerika",
        "feed_sa": "S. Amerika",
        "feed_asia": "Asien",
        "feed_africa": "Afrika",
        "feed_oceania": "Ozeanien",
        "max_news_label": "Max. Nachrichten:",
        "theme_label": "Oberflächendesign:",
        "theme_dark": "Dunkel",
        "theme_light": "Hell",
        "theme_system": "System",
        "recent_title": "Nachrichten:",
        "recent_search_placeholder": "Wonach suchen Sie? (z.B. Weltall, KI, Erneuerbare Energien...)",
        "recent_search_btn": "Suchen 🔍",
        "recent_empty": "Keine Nachrichten geladen.\nGeben Sie ein Thema ein und klicken Sie auf 'Suchen'.",
        "saved_title": "Gespeicherte Nachrichten",
        "saved_subtitle": "Lokales Archiv (max. 7 Tage)",
        "saved_empty": "Ihr Archiv ist leer.\nSpeichern Sie Nachrichten mit dem 📌 Button!",
        "gen_title": "Social Post Generator",
        "gen_sources_title": "1. Ausgewählte Quellen:",
        "gen_options_title": "2. Generator-Optionen:",
        "gen_platform_label": "Plattform:",
        "gen_platforms": ["LinkedIn", "X / Twitter", "Facebook", "Blog / Artikel"],
        "gen_tone_label": "Tonfall:",
        "gen_tones": ["Professionell", "Informativ", "Ansprechend", "Technisch"],
        "gen_length_label": "Post-Länge:",
        "gen_lengths": ["Kurz", "Mittel", "Detailliert"],
        "gen_btn": "Beitrag erstellen ⚡",
        "gen_btn_generating": "Erstellen... ⏳",
        "gen_empty": "Wählen Sie eine oder mehrere Nachrichten aus anderen Tabs aus.",
        "gen_output_placeholder": "Der erstellte Beitrag wird hier angezeigt.\n\nWählen Sie Nachrichten aus anderen Tabs, stellen Sie die Optionen ein und klicken Sie auf 'Beitrag erstellen'.",
        "gen_copy_btn": "In Zwischenablage kopieren 📋",
        "gen_clear_btn": "Auswahl löschen 🧹",
        "toast_copied": "In Zwischenablage kopiert!",
        "toast_generating": "Social Post wird mit lokalem Ollama erstellt...\nBitte warten...",
        "err_model": "Fehler: Ollama nicht verbunden. Starten Sie Ollama und versuchen Sie es erneut.",
        "err_feeds": "Fehler: Wählen Sie mindestens einen Kontinent aus.",
        "err_no_news": "Keine Nachrichten gefunden.",
        "err_generation": "Fehler bei der Generierung: ",
        "progress_fetch": "Nachrichten von Google News RSS herunterladen...",
        "progress_found": "{total} Artikel gefunden. Zusammenfassungen werden erstellt...",
        "progress_analyze": "Analysiere Artikel {index}/{total}...",
        "progress_ollama": "Zusammenfassung mit Ollama ({model}) {index}/{total}...",
        "btn_save": "📌 Speichern",
        "btn_saved": "📌 Gespeichert",
        "btn_remove": "❌ Entfernen",
        "chk_select_post": "Für Post wählen",
        "link_source": "Quelle 🌐"
    },
    "Français": {
        "title": "Smart News AI",
        "subtitle": "Agrégateur de nouvelles et créateur de posts",
        "nav_label": "Navigation:",
        "nav_recent": "📰  Actualités",
        "nav_saved": "📌  Enregistrées",
        "nav_generator": "✍️  Générateur",
        "status_detecting": "Ollama: Détection...",
        "status_connected": "Ollama: Connecté",
        "status_disconnected": "Ollama: Déconnecté",
        "model_label": "Choisir le modèle:",
        "range_label": "Période:",
        "range_today": "Aujourd'hui",
        "range_yesterday": "Aujourd'hui & Hier",
        "feeds_label": "Choisir les continents:",
        "feed_europe": "Europe",
        "feed_na": "Amérique du N.",
        "feed_sa": "Amérique du S.",
        "feed_asia": "Asie",
        "feed_africa": "Afrique",
        "feed_oceania": "Océanie",
        "max_news_label": "Max nouvelles à afficher:",
        "theme_label": "Thème de l'interface:",
        "theme_dark": "Sombre",
        "theme_light": "Clair",
        "theme_system": "Système",
        "recent_title": "Nouvelles:",
        "recent_search_placeholder": "Que voulez-vous chercher? (ex. Espace, IA, Énergie renouvelable...)",
        "recent_search_btn": "Rechercher 🔍",
        "recent_empty": "Aucune nouvelle chargée.\nEntrez un sujet et cliquez sur 'Rechercher'.",
        "saved_title": "Nouvelles Enregistrées",
        "saved_subtitle": "Archive locale (max 7 jours)",
        "saved_empty": "Votre archive est vide.\nEnregistrez des nouvelles avec le bouton 📌 !",
        "gen_title": "Générateur de Posts Sociaux",
        "gen_sources_title": "1. Sources sélectionnées:",
        "gen_options_title": "2. Options de génération:",
        "gen_platform_label": "Plateforme:",
        "gen_platforms": ["LinkedIn", "X / Twitter", "Facebook", "Blog / Article"],
        "gen_tone_label": "Ton de voix:",
        "gen_tones": ["Professionnel", "Informatif", "Engageant", "Technique"],
        "gen_length_label": "Longueur du post:",
        "gen_lengths": ["Court", "Moyen", "Détaillé"],
        "gen_btn": "Générer le post ⚡",
        "gen_btn_generating": "Génération... ⏳",
        "gen_empty": "Sélectionnez une ou plusieurs nouvelles à l'aide de la case à cocher.",
        "gen_output_placeholder": "Le post généré s'affichera ici.\n\nSélectionnez des articles dans les autres onglets, configurez à gauche, puis cliquez sur 'Générer le post'.",
        "gen_copy_btn": "Copier dans le presse-papiers 📋",
        "gen_clear_btn": "Effacer la sélection 🧹",
        "toast_copied": "Copié dans le presse-papiers !",
        "toast_generating": "Génération du post avec Ollama local en cours...\nVeuillez patienter...",
        "err_model": "Erreur : Ollama déconnecté. Démarrez Ollama et réessayez.",
        "err_feeds": "Erreur : Sélectionnez au moins un continent.",
        "err_no_news": "Aucune nouvelle trouvée.",
        "err_generation": "Erreur lors de la génération: ",
        "progress_fetch": "Téléchargement des nouvelles de Google News...",
        "progress_found": "{total} articles trouvés. Génération des résumés...",
        "progress_analyze": "Analyse de l'article {index}/{total}...",
        "progress_ollama": "Résumé avec Ollama ({model}) {index}/{total}...",
        "btn_save": "📌 Enregistrer",
        "btn_saved": "📌 Enregistré",
        "btn_remove": "❌ Retirer",
        "chk_select_post": "Choisir pour post",
        "link_source": "Source 🌐"
    },
    "Español": {
        "title": "Smart News AI",
        "subtitle": "Agregador de noticias y creador de posts",
        "nav_label": "Navegación:",
        "nav_recent": "📰  Noticias Recientes",
        "nav_saved": "📌  Noticias Guardadas",
        "nav_generator": "✍️  Generador Post",
        "status_detecting": "Ollama: Detectando...",
        "status_connected": "Ollama: Conectado",
        "status_disconnected": "Ollama: Desconectado",
        "model_label": "Seleccionar Modelo:",
        "range_label": "Rango de tiempo:",
        "range_today": "Solo Hoy",
        "range_yesterday": "Hoy y Ayer",
        "feeds_label": "Seleccionar Continentes:",
        "feed_europe": "Europa",
        "feed_na": "N. América",
        "feed_sa": "S. América",
        "feed_asia": "Asia",
        "feed_africa": "África",
        "feed_oceania": "Oceanía",
        "max_news_label": "Max noticias a mostrar:",
        "theme_label": "Tema de Interfaz:",
        "theme_dark": "Oscuro",
        "theme_light": "Claro",
        "theme_system": "Sistema",
        "recent_title": "Noticias:",
        "recent_search_placeholder": "¿Qué desea buscar? (ej. Espacio, IA, Energía Renovable...)",
        "recent_search_btn": "Buscar Noticias 🔍",
        "recent_empty": "No hay noticias cargadas.\nEscriba un tema y haga clic en 'Buscar Noticias'.",
        "saved_title": "Noticias Guardadas",
        "saved_subtitle": "Archivo local (máx 7 días)",
        "saved_empty": "El archivo está vacío.\n¡Guarde noticias con el botón 📌!",
        "gen_title": "Generador de Posts",
        "gen_sources_title": "1. Fuentes Seleccionadas:",
        "gen_options_title": "2. Opciones de Generación:",
        "gen_platform_label": "Piattaforma:",
        "gen_platforms": ["LinkedIn", "X / Twitter", "Facebook", "Blog / Artículo"],
        "gen_tone_label": "Tono de voz:",
        "gen_tones": ["Profesional", "Informativo", "Atractivo", "Técnico"],
        "gen_length_label": "Longitud del post:",
        "gen_lengths": ["Corto", "Medio", "Detallado"],
        "gen_btn": "Generar Post ⚡",
        "gen_btn_generating": "Generando... ⏳",
        "gen_empty": "Seleccione una o más noticias usando la casilla correspondiente.",
        "gen_output_placeholder": "El post generado aparecerá aquí.\n\nSeleccione noticias de otras pestañas, configure a la izquierda y haga clic en 'Generar Post'.",
        "gen_copy_btn": "Copiar al portapapeles 📋",
        "gen_clear_btn": "Limpiar Selección 🧹",
        "toast_copied": "¡Copiado al portapapeles!",
        "toast_generating": "Generando post con Ollama local...\nPor favor, espere...",
        "err_model": "Error: Ollama desconectado. Inicie Ollama e inténtelo de nuevo.",
        "err_feeds": "Error: Seleccione al menos un continente.",
        "err_no_news": "No se encontraron noticias.",
        "err_generation": "Error durante la generación: ",
        "progress_fetch": "Descargando noticias de Google News...",
        "progress_found": "Se encontraron {total} artículos. Generando resúmenes...",
        "progress_analyze": "Analizando artículo {index}/{total}...",
        "progress_ollama": "Resumen con Ollama ({model}) {index}/{total}...",
        "btn_save": "📌 Guardar",
        "btn_saved": "📌 Guardado",
        "btn_remove": "❌ Eliminar",
        "chk_select_post": "Elegir para Post",
        "link_source": "Fuente 🌐"
    },
    "中文": {
        "title": "Smart News AI",
        "subtitle": "新闻聚合与社交帖子生成器",
        "nav_label": "导航栏:",
        "nav_recent": "📰  最新新闻",
        "nav_saved": "📌  已存新闻",
        "nav_generator": "✍️  帖子生成",
        "status_detecting": "Ollama: 检测中...",
        "status_connected": "Ollama: 已连接",
        "status_disconnected": "Ollama: 未连接",
        "model_label": "选择模型:",
        "range_label": "时间范围:",
        "range_today": "仅限今天",
        "range_yesterday": "今天和昨天",
        "feeds_label": "选择大陆:",
        "feed_europe": "欧洲",
        "feed_na": "北美洲",
        "feed_sa": "南美洲",
        "feed_asia": "亚洲",
        "feed_africa": "非洲",
        "feed_oceania": "大洋洲",
        "max_news_label": "最大显示条数:",
        "theme_label": "界面主题:",
        "theme_dark": "深色",
        "theme_light": "浅色",
        "theme_system": "系统默认",
        "recent_title": "新闻:",
        "recent_search_placeholder": "您想搜索什么主题？ (例如：航天、人工智能、新能源...)",
        "recent_search_btn": "搜索新闻 🔍",
        "recent_empty": "暂无新闻加载。\n请输入主题并点击“搜索新闻”。",
        "saved_title": "已保存的新闻",
        "saved_subtitle": "本地归档 (最多保留7天)",
        "saved_empty": "您的归档为空。\n请使用 📌 按钮保存新闻项目！",
        "gen_title": "社交帖子生成器",
        "gen_sources_title": "1. 已选新闻源:",
        "gen_options_title": "2. 生成设置选项:",
        "gen_platform_label": "发布平台:",
        "gen_platforms": ["LinkedIn", "X / Twitter", "Facebook", "博客 / 文章"],
        "gen_tone_label": "内容语气:",
        "gen_tones": ["专业", "资讯性", "引人入胜", "技术性"],
        "gen_length_label": "帖子长度:",
        "gen_lengths": ["简短", "中等", "详细"],
        "gen_btn": "生成帖子 ⚡",
        "gen_btn_generating": "正在生成... ⏳",
        "gen_empty": "请使用复选框选择一则或多则新闻作为素材源。",
        "gen_output_placeholder": "生成的社交媒体帖子将在此处显示。\n\n请在其他标签页中选择新闻，设置左侧选项，然后点击“生成帖子 ⚡”。",
        "gen_copy_btn": "复制到剪贴板 📋",
        "gen_clear_btn": "清除选择 🧹",
        "toast_copied": "已复制到剪贴板！",
        "toast_generating": "正在使用本地 Ollama 生成帖子...\n请稍候（可能需要数秒）...",
        "err_model": "错误：Ollama 未连接或未安装模型。请启动 Ollama 并重试。",
        "err_feeds": "错误：请在侧边栏选择至少一个大陆区域。",
        "err_no_news": "未找到相关新闻。",
        "err_generation": "生成过程中出错: ",
        "progress_fetch": "正在从 Google 新闻 RSS 下载数据...",
        "progress_found": "找到 {total} 篇报道。正在生成摘要...",
        "progress_analyze": "正在分析报道 {index}/{total}...",
        "progress_ollama": "正在使用 Ollama ({model}) 总结 {index}/{total}...",
        "btn_save": "📌 保存",
        "btn_saved": "📌 已保存",
        "btn_remove": "❌ 删除",
        "chk_select_post": "选为帖子素材",
        "link_source": "新闻来源 🌐"
    },
    "日本語": {
        "title": "Smart News AI",
        "subtitle": "ニュースアグリゲーター＆ポスト作成",
        "nav_label": "ナビゲーション:",
        "nav_recent": "📰  最近のニュース",
        "nav_saved": "📌  保存されたニュース",
        "nav_generator": "✍️  ポスト作成",
        "status_detecting": "Ollama: 検出中...",
        "status_connected": "Ollama: 接続完了",
        "status_disconnected": "Ollama: 未接続",
        "model_label": "モデル選択:",
        "range_label": "検索対象期間:",
        "range_today": "今日のみ",
        "range_yesterday": "今日と昨日",
        "feeds_label": "対象地域選択:",
        "feed_europe": "ヨーロッパ",
        "feed_na": "北米",
        "feed_sa": "南米",
        "feed_asia": "アジア",
        "feed_africa": "アフリカ",
        "feed_oceania": "オセアニア",
        "max_news_label": "最大表示件数:",
        "theme_label": "画面テーマ:",
        "theme_dark": "ダーク",
        "theme_light": "ライト",
        "theme_system": "システム",
        "recent_title": "ニュース:",
        "recent_search_placeholder": "検索したいキーワードは？ (例：宇宙、AI、再生可能エネルギー...)",
        "recent_search_btn": "ニュース検索 🔍",
        "recent_empty": "ニュースが読み込まれていません。\nキーワードを入力して「ニュース検索」をクリックしてください。",
        "saved_title": "保存されたニュース",
        "saved_subtitle": "ローカルアーカイブ (最大7日間保持)",
        "saved_empty": "アーカイブは空です。\n📌ボタンでニュースを保存してください。",
        "gen_title": "ソーシャルポスト作成",
        "gen_sources_title": "1. 選択したニュースソース:",
        "gen_options_title": "2. 作成オプション設定:",
        "gen_platform_label": "投稿先プラットフォーム:",
        "gen_platforms": ["LinkedIn", "X / Twitter", "Facebook", "ブログ / 記事"],
        "gen_tone_label": "文章のトーン:",
        "gen_tones": ["プロフェッショナル", "インフォーマティブ", "魅力的", "テクニカル"],
        "gen_length_label": "文章の長さ:",
        "gen_lengths": ["短い", "中くらい", "詳細"],
        "gen_btn": "ポストを生成 ⚡",
        "gen_btn_generating": "生成中... ⏳",
        "gen_empty": "チェックボックスを使ってニュースソースを選択してください。",
        "gen_output_placeholder": "生成されたソーシャルメディア用の文章がここに表示されます。\n\n他のタブでニュースを選択し、左側のオプションを設定後、「ポストを生成 ⚡」をクリックしてください。",
        "gen_copy_btn": "クリップボードにコピー 📋",
        "gen_clear_btn": "選択をクリア 🧹",
        "toast_copied": "クリップボードにコピーされました！",
        "toast_generating": "ローカルの Ollama でポストを生成しています...\n少々お待ちください（数秒かかる場合があります）...",
        "err_model": "エラー：Ollama が未接続か、モデルがインストールされていません。Ollama を起動して再試行してください。",
        "err_feeds": "エラー：サイドバーで地域を少なくとも1つ選択してください。",
        "err_no_news": "ニュースが見つかりませんでした。",
        "err_generation": "生成中のエラー: ",
        "progress_fetch": "Google ニュース RSS からニュースを取得中...",
        "progress_found": "{total} 件の記事が見つかりました。要約を生成中...",
        "progress_analyze": "記事を解析中 {index}/{total}...",
        "progress_ollama": "Ollama ({model}) で要約中 {index}/{total}...",
        "btn_save": "📌 保存",
        "btn_saved": "📌 保存済み",
        "btn_remove": "❌ 削除",
        "chk_select_post": "ポスト素材に選択",
        "link_source": "ニュース元 🌐"
    },
    "Русский": {
        "title": "Smart News AI",
        "subtitle": "Агрегатор новостей и генератор постов",
        "nav_label": "Навигация:",
        "nav_recent": "📰  Свежие новости",
        "nav_saved": "📌  Сохраненные",
        "nav_generator": "✍️  Создать пост",
        "status_detecting": "Ollama: Поиск...",
        "status_connected": "Ollama: Подключено",
        "status_disconnected": "Ollama: Отключено",
        "model_label": "Выберите модель:",
        "range_label": "Период времени:",
        "range_today": "Только сегодня",
        "range_yesterday": "Сегодня и вчера",
        "feeds_label": "Выберите регионы:",
        "feed_europe": "Европа",
        "feed_na": "Сев. Америка",
        "feed_sa": "Юж. Америка",
        "feed_asia": "Азия",
        "feed_africa": "Африка",
        "feed_oceania": "Океания",
        "max_news_label": "Макс. новостей:",
        "theme_label": "Тема оформления:",
        "theme_dark": "Темная",
        "theme_light": "Светлая",
        "theme_system": "Системная",
        "recent_title": "Новости:",
        "recent_search_placeholder": "Что вы хотите найти? (например, Космос, ИИ, Энергетика...)",
        "recent_search_btn": "Найти новости 🔍",
        "recent_empty": "Новости не загружены.\nВведите тему и нажмите кнопку «Найти новости».",
        "saved_title": "Сохраненные новости",
        "saved_subtitle": "Локальный архив (макс. 7 дней)",
        "saved_empty": "Ваш архив пуст.\nСохраняйте новости с помощью кнопки 📌!",
        "gen_title": "Генератор постов",
        "gen_sources_title": "1. Выбранные источники:",
        "gen_options_title": "2. Настройки генерации:",
        "gen_platform_label": "Платформа:",
        "gen_platforms": ["LinkedIn", "X / Twitter", "Facebook", "Блог / Статья"],
        "gen_tone_label": "Стиль текста:",
        "gen_tones": ["Профессиональный", "Информативный", "Увлекательный", "Технический"],
        "gen_length_label": "Длина поста:",
        "gen_lengths": ["Краткий", "Средний", "Подробный"],
        "gen_btn": "Создать пост ⚡",
        "gen_btn_generating": "Создание... ⏳",
        "gen_empty": "Выберите одну или несколько новостей на других вкладках.",
        "gen_output_placeholder": "Созданный пост появится здесь.\n\nВыберите новости на других вкладках, укажите настройки слева и нажмите «Создать пост».",
        "gen_copy_btn": "Копировать в буфер 📋",
        "gen_clear_btn": "Очистить выбор 🧹",
        "toast_copied": "Скопировано в буфер обмена!",
        "toast_generating": "Пост генерируется локальной моделью Ollama...\nПожалуйста, подождите...",
        "err_model": "Ошибка: Ollama не подключен. Запустите Ollama и повторите попытку.",
        "err_feeds": "Ошибка: Выберите хотя бы один регион в панели слева.",
        "err_no_news": "Новости не найдены.",
        "err_generation": "Ошибка при генерации: ",
        "progress_fetch": "Скачивание новостей из Google News RSS...",
        "progress_found": "Найдено {total} статей. Создание аннотаций...",
        "progress_analyze": "Анализ статьи {index}/{total}...",
        "progress_ollama": "Аннотация через Ollama ({model}) {index}/{total}...",
        "btn_save": "📌 Сохранить",
        "btn_saved": "📌 Сохранено",
        "btn_remove": "❌ Удалить",
        "chk_select_post": "Выбрать для поста",
        "link_source": "Источник 🌐"
    },
    "العربية": {
        "title": "Smart News AI",
        "subtitle": "مجمع الأخبار ومنشئ المنشورات",
        "nav_label": "التنقل:",
        "nav_recent": "📰  الأخبار الأخيرة",
        "nav_saved": "📌  الأخبار المحفوظة",
        "nav_generator": "✍️  منشئ المنشورات",
        "status_detecting": "أولاما: كشف...",
        "status_connected": "أولاما: متصل",
        "status_disconnected": "أولاما: غير متصل",
        "model_label": "اختر النموذج:",
        "range_label": "النطاق الزمني:",
        "range_today": "اليوم فقط",
        "range_yesterday": "اليوم وأمس",
        "feeds_label": "اختر القارات:",
        "feed_europe": "أوروبا",
        "feed_na": "أمريكا الشمالية",
        "feed_sa": "أمريكا الجنوبية",
        "feed_asia": "آسيا",
        "feed_africa": "أفريقيا",
        "feed_oceania": "أوقيانوسيا",
        "max_news_label": "أقصى عدد للأخبار المعروضة:",
        "theme_label": "سمة الواجهة:",
        "theme_dark": "داكن",
        "theme_light": "فاتح",
        "theme_system": "النظام",
        "recent_title": "أخبار:",
        "recent_search_placeholder": "ما الذي تريد البحث عنه؟ (مثال: الفضاء، الذكاء الاصطناعي...)",
        "recent_search_btn": "البحث عن الأخبار 🔍",
        "recent_empty": "لم يتم تحميل أي أخبار بعد.\nاكتب موضوعًا واضغط على 'البحث عن الأخبار' للبدء.",
        "saved_title": "الأخبار المحفوظة",
        "saved_subtitle": "الأرشيف المحلي (بحد أقصى 7 أيام)",
        "saved_empty": "أرشيفك فارغ.\nقم بحفظ الأخبار باستخدام الزر 📌!",
        "gen_title": "منشئ منشورات التواصل",
        "gen_sources_title": "1. المصادر المحددة:",
        "gen_options_title": "2. خيارات الإنشاء:",
        "gen_platform_label": "المنصة:",
        "gen_platforms": ["LinkedIn", "X / Twitter", "Facebook", "مدونة / مقال"],
        "gen_tone_label": "نبرة الصوت:",
        "gen_tones": ["مهني", "معلوماتي", "جذاب", "تقني"],
        "gen_length_label": "طول المنشور:",
        "gen_lengths": ["قصير", "متوسط", "مفصل"],
        "gen_btn": "إنشاء المنشور ⚡",
        "gen_btn_generating": "جاري الإنشاء... ⏳",
        "gen_empty": "اختر خبرًا واحدًا أو أكثر باستخدام خانة الاختيار.",
        "gen_output_placeholder": "سيظهر المنشور المنشأ هنا.\n\nاختر الأخبار من علامات التبويب الأخرى، واضبط الخيارات على اليسار، ثم اضغط على 'إنشاء المنشور'.",
        "gen_copy_btn": "نسخ إلى الحافظة 📋",
        "gen_clear_btn": "مسح التحديد 🧹",
        "toast_copied": "تم النسخ إلى الحافظة!",
        "toast_generating": "جاري إنشاء المنشور باستخدام نموذج أولاما المحلي...\nيرجى الانتظار...",
        "err_model": "خطأ: أولاما غير متصل أو لم يتم تثبيت أي نموذج. قم بتشغيل أولاما وحاول مجددًا.",
        "err_feeds": "خطأ: اختر قارة واحدة على الأقل من الشريط الجانبي.",
        "err_no_news": "لم يتم العثور على أي أخبار.",
        "err_generation": "خطأ أثناء الإنشاء: ",
        "progress_fetch": "جاري تنزيل الأخبار من Google News RSS...",
        "progress_found": "تم العثور على {total} أخبار. جاري كتابة الملخصات...",
        "progress_analyze": "جاري تحليل الخبر {index}/{total}...",
        "progress_ollama": "جاري التلخيص باستخدام أولاما ({model}) {index}/{total}...",
        "btn_save": "📌 حفظ",
        "btn_saved": "📌 تم الحفظ",
        "btn_remove": "❌ إزالة",
        "chk_select_post": "اختر للمنشور",
        "link_source": "المصدر 🌐"
    }
}


class NewsCard(ctk.CTkFrame):
    """A widget displaying a single news item with title, source, summary, actions, and selection."""
    def __init__(self, master, news_item, app, **kwargs):
        super().__init__(master, fg_color=("#F3F4F6", "#1F2937"), corner_radius=12, **kwargs)
        self.news_item = news_item
        self.app = app
        
        # Configure layout grid
        self.columnconfigure(0, weight=1)
        
        # Source & Date header
        header_text = f"{news_item.get('source', 'Fonte')}  •  {news_item.get('pub_date_italian', '')}"
        self.header_label = ctk.CTkLabel(
            self, 
            text=header_text, 
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#6B7280", "#9CA3AF"),
            anchor="w"
        )
        self.header_label.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")
        
        # Title (translated)
        self.title_label = ctk.CTkLabel(
            self, 
            text=news_item.get("title_translated", news_item.get("title_original")), 
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("#111827", "#F9FAFB"),
            justify="left",
            anchor="w",
            wraplength=520
        )
        self.title_label.grid(row=1, column=0, padx=16, pady=4, sticky="w")
        
        # Summary (in Italian)
        summary_text = news_item.get("summary_italian", "Nessun riassunto disponibile.")
        self.summary_label = ctk.CTkLabel(
            self, 
            text=summary_text, 
            font=ctk.CTkFont(size=13),
            text_color=("#374151", "#D1D5DB"),
            justify="left",
            anchor="w",
            wraplength=520
        )
        self.summary_label.grid(row=2, column=0, padx=16, pady=8, sticky="w")
        
        # Actions bar
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=3, column=0, padx=16, pady=(4, 12), sticky="ew")
        self.actions_frame.columnconfigure(0, weight=1)
        
        lang = self.app.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        
        # Checkbox for selecting for social post
        self.select_var = ctk.BooleanVar(value=self.app.is_news_selected(self.news_item))
        self.select_checkbox = ctk.CTkCheckBox(
            self.actions_frame,
            text=texts["chk_select_post"],
            variable=self.select_var,
            command=self.toggle_select,
            font=ctk.CTkFont(size=11, weight="bold"),
            checkbox_width=18,
            checkbox_height=18
        )
        self.select_checkbox.grid(row=0, column=0, sticky="w")
        
        # Pin/Archive button
        is_pinned = self.app.is_news_pinned(self.news_item)
        pin_text = texts["btn_remove"] if is_pinned else texts["btn_save"]
        self.pin_button = ctk.CTkButton(
            self.actions_frame,
            text=pin_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            width=90,
            height=28,
            fg_color=("#EF4444" if is_pinned else "#3B82F6", "#DC2626" if is_pinned else "#2563EB"),
            text_color="white",
            hover_color=("#DC2626" if is_pinned else "#2563EB", "#B91C1C" if is_pinned else "#1D4ED8"),
            command=self.toggle_pin
        )
        self.pin_button.grid(row=0, column=1, padx=(0, 8), sticky="e")
        
        # Open source button
        self.open_button = ctk.CTkButton(
            self.actions_frame, 
            text=texts["link_source"], 
            font=ctk.CTkFont(size=11, weight="bold"),
            width=100,
            height=28,
            fg_color=("#E5E7EB", "#374151"),
            text_color=("#374151", "#E5E7EB"),
            hover_color=("#D1D5DB", "#4B5563"),
            command=self.open_source
        )
        self.open_button.grid(row=0, column=2, sticky="e")
        
        # Bind resize to update wraplength dynamically
        self.bind("<Configure>", self.on_resize)
        
    def update_texts(self):
        lang = self.app.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        self.select_checkbox.configure(text=texts["chk_select_post"])
        is_pinned = self.app.is_news_pinned(self.news_item)
        pin_text = texts["btn_remove"] if is_pinned else texts["btn_save"]
        self.pin_button.configure(text=pin_text)
        self.open_button.configure(text=texts["link_source"])
        
    def open_source(self):
        url = self.news_item.get("resolved_link", self.news_item.get("google_link"))
        webbrowser.open(url)
        
    def toggle_pin(self):
        lang = self.app.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        is_pinned = self.app.is_news_pinned(self.news_item)
        if is_pinned:
            self.app.remove_from_archive(self.news_item)
            self.pin_button.configure(
                text=texts["btn_save"],
                fg_color=("#3B82F6", "#2563EB"),
                hover_color=("#2563EB", "#1D4ED8")
            )
        else:
            self.app.add_to_archive(self.news_item)
            self.pin_button.configure(
                text=texts["btn_remove"],
                fg_color=("#EF4444", "#DC2626"),
                hover_color=("#DC2626", "#B91C1C")
            )
            
    def update_localization(self):
        lang = self.app.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        
        self.select_checkbox.configure(text=texts["chk_select_post"])
        self.open_button.configure(text=texts["link_source"])
        
        is_pinned = self.app.is_news_pinned(self.news_item)
        pin_text = texts["btn_remove"] if is_pinned else texts["btn_save"]
        self.pin_button.configure(
            text=pin_text,
            fg_color=("#EF4444" if is_pinned else "#3B82F6", "#DC2626" if is_pinned else "#2563EB"),
            hover_color=("#DC2626" if is_pinned else "#2563EB", "#B91C1C" if is_pinned else "#1D4ED8")
        )
            
    def toggle_select(self):
        if self.select_var.get():
            self.app.select_news(self.news_item)
        else:
            self.app.deselect_news(self.news_item)
        
    def on_resize(self, event):
        # Subtract some padding from the frame width to set wrap length
        wrap_w = max(200, event.width - 32)
        self.title_label.configure(wraplength=wrap_w)
        self.summary_label.configure(wraplength=wrap_w)



class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.app_config = config.load_config()
        
        # Set theme
        ctk.set_appearance_mode(self.app_config.get("theme", "Dark"))
        ctk.set_default_color_theme("blue")
        
        # Configure window
        self.title("Smart News AI")
        self.geometry("900x650")
        self.minimum_size = (750, 500)
        self.minsize(self.minimum_size[0], self.minimum_size[1])
        
        # Set window icon if available
        try:
            import tkinter as tk
            icon_path = get_asset_path("icon.png")
            if os.path.exists(icon_path):
                self.iconphoto(True, tk.PhotoImage(file=icon_path))
        except Exception:
            pass
        
        # Layout grid configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # App state
        self.models = []
        self.is_fetching = False
        self.selected_news = []
        self.current_view = "recent"
        
        # Create Sidebar
        self.create_sidebar()
        
        # Create Main Area
        self.create_main_area()
        
        # Initialize dynamic localized UI state
        self.update_ui_text()
        
    def create_sidebar(self):
        # Load localization
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        
        # Sidebar Frame
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(13, weight=1)  # Spacer row
        
        # App Title
        self.title_label = ctk.CTkLabel(
            self.sidebar, 
            text=texts["title"], 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 5))
        
        self.subtitle_label = ctk.CTkLabel(
            self.sidebar, 
            text=texts["subtitle"], 
            font=ctk.CTkFont(size=12),
            text_color=("#6B7280", "#9CA3AF")
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 15))
        
        # Separator line
        self.sep = ctk.CTkFrame(self.sidebar, height=2, fg_color=("#E5E7EB", "#374151"))
        self.sep.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        
        # Navigation
        self.nav_label = ctk.CTkLabel(
            self.sidebar, 
            text=texts["nav_label"], 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.nav_label.grid(row=3, column=0, padx=20, pady=(10, 2), sticky="w")
        
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.nav_frame.columnconfigure(0, weight=1)
        
        self.nav_recent_btn = ctk.CTkButton(
            self.nav_frame,
            text=texts["nav_recent"],
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            height=36,
            fg_color="#6366F1",
            text_color="white",
            hover_color="#4F46E5",
            command=lambda: self.switch_view("recent")
        )
        self.nav_recent_btn.grid(row=0, column=0, pady=3, sticky="ew")
        
        self.nav_saved_btn = ctk.CTkButton(
            self.nav_frame,
            text=f"{texts['nav_saved']} (0)",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            height=36,
            fg_color="transparent",
            text_color=("#374151", "#E5E7EB"),
            hover_color=("#E5E7EB", "#374151"),
            command=lambda: self.switch_view("saved")
        )
        self.nav_saved_btn.grid(row=1, column=0, pady=3, sticky="ew")
        
        self.nav_generator_btn = ctk.CTkButton(
            self.nav_frame,
            text=f"{texts['nav_generator']} (0)",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            height=36,
            fg_color="transparent",
            text_color=("#374151", "#E5E7EB"),
            hover_color=("#E5E7EB", "#374151"),
            command=lambda: self.switch_view("generator")
        )
        self.nav_generator_btn.grid(row=2, column=0, pady=3, sticky="ew")
        
        # Second Separator
        self.sep2 = ctk.CTkFrame(self.sidebar, height=2, fg_color=("#E5E7EB", "#374151"))
        self.sep2.grid(row=5, column=0, padx=15, pady=5, sticky="ew")
        
        # Status Ollama
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        self.status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text=texts["status_detecting"], 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F59E0B"
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        
        self.refresh_models_btn = ctk.CTkButton(
            self.status_frame,
            text="🔄",
            width=28,
            height=28,
            fg_color=("#E5E7EB", "#374151"),
            text_color=("#374151", "#E5E7EB"),
            hover_color=("#D1D5DB", "#4B5563"),
            command=self.check_ollama_status
        )
        self.refresh_models_btn.grid(row=0, column=1, sticky="e")
        
        # Model Selection
        self.model_label = ctk.CTkLabel(
            self.sidebar, 
            text=texts["model_label"], 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.model_label.grid(row=7, column=0, padx=20, pady=(10, 2), sticky="w")
        
        self.model_dropdown = ctk.CTkOptionMenu(
            self.sidebar,
            values=[texts["status_detecting"]],
            command=self.on_model_change
        )
        self.model_dropdown.grid(row=7, column=0, padx=20, pady=(25, 5), sticky="ew")
        
        # Time range selection
        self.range_label = ctk.CTkLabel(
            self.sidebar, 
            text=texts["range_label"], 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.range_label.grid(row=8, column=0, padx=20, pady=(10, 2), sticky="w")
        
        # Segmented button for time range
        self.range_var = ctk.StringVar(value=texts["range_yesterday"] if self.app_config.get("time_range") == 2 else texts["range_today"])
        self.range_segmented = ctk.CTkSegmentedButton(
            self.sidebar,
            values=[texts["range_today"], texts["range_yesterday"]],
            variable=self.range_var,
            command=self.on_range_change
        )
        self.range_segmented.grid(row=8, column=0, padx=20, pady=(25, 5), sticky="ew")
        
        # Geographics feeds checkboxes
        self.feeds_label = ctk.CTkLabel(
            self.sidebar, 
            text=texts["feeds_label"], 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.feeds_label.grid(row=9, column=0, padx=20, pady=(10, 2), sticky="w")
        
        self.feeds_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.feeds_frame.grid(row=10, column=0, padx=15, pady=0, sticky="ew")
        
        self.feed_vars = {}
        self.feed_checkboxes = {}
        feed_options = [
            ("europe", "feed_europe"),
            ("north_america", "feed_na"),
            ("south_america", "feed_sa"),
            ("asia", "feed_asia"),
            ("africa", "feed_africa"),
            ("oceania", "feed_oceania")
        ]
        enabled_feeds = self.app_config.get("feeds", ["europe", "north_america"])
        for idx, (feed_key, trans_key) in enumerate(feed_options):
            var = ctk.BooleanVar(value=(feed_key in enabled_feeds))
            chk = ctk.CTkCheckBox(
                self.feeds_frame,
                text=texts[trans_key],
                variable=var,
                command=self.on_feeds_change,
                font=ctk.CTkFont(size=11),
                checkbox_width=16,
                checkbox_height=16
            )
            row = idx // 2
            col = idx % 2
            chk.grid(row=row, column=col, sticky="w", pady=4, padx=5)
            self.feed_vars[feed_key] = var
            self.feed_checkboxes[feed_key] = chk
            
        # Max news count selection
        self.max_news_label = ctk.CTkLabel(
            self.sidebar,
            text=texts["max_news_label"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.max_news_label.grid(row=11, column=0, padx=20, pady=(10, 2), sticky="w")
        
        self.max_news_dropdown = ctk.CTkOptionMenu(
            self.sidebar,
            values=["5", "10", "15", "20", "25", "30"],
            command=self.on_max_news_change
        )
        self.max_news_dropdown.set(str(self.app_config.get("max_news_count", 15)))
        self.max_news_dropdown.grid(row=11, column=0, padx=20, pady=(25, 5), sticky="ew")
        
        # Theme switcher
        self.theme_label = ctk.CTkLabel(
            self.sidebar, 
            text=texts["theme_label"], 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.theme_label.grid(row=12, column=0, padx=20, pady=(10, 2), sticky="w")
        
        theme_rev_map = {
            "Dark": texts["theme_dark"],
            "Light": texts["theme_light"],
            "System": texts["theme_system"]
        }
        self.theme_dropdown = ctk.CTkOptionMenu(
            self.sidebar,
            values=[texts["theme_dark"], texts["theme_light"], texts["theme_system"]],
            command=self.on_theme_change
        )
        self.theme_dropdown.set(theme_rev_map.get(self.app_config.get("theme", "Dark"), texts["theme_dark"]))
        self.theme_dropdown.grid(row=12, column=0, padx=20, pady=(25, 5), sticky="ew")
        
        # Spacer frame to push footer down
        self.spacer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=10)
        self.spacer_frame.grid(row=13, column=0, sticky="nsew")
        
        # Version and Footer
        self.version_label = ctk.CTkLabel(
            self.sidebar, 
            text="v1.2.0 (Archivio & Post)", 
            font=ctk.CTkFont(size=10),
            text_color=("#9CA3AF", "#4B5563")
        )
        self.version_label.grid(row=14, column=0, padx=20, pady=15, sticky="s")
        
    def create_main_area(self):
        # Load localization
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        
        # 1. RECENT VIEW FRAME
        self.recent_view_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.recent_view_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.recent_view_frame.grid_columnconfigure(0, weight=1)
        self.recent_view_frame.grid_rowconfigure(1, weight=1)
        
        self.header_frame = ctk.CTkFrame(self.recent_view_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.header_frame.columnconfigure(1, weight=1)
        self.header_frame.columnconfigure(2, weight=0)
        self.header_frame.columnconfigure(3, weight=0)
        
        self.section_title = ctk.CTkLabel(
            self.header_frame, 
            text=texts["recent_title"], 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.section_title.grid(row=0, column=0, sticky="w")

        # Search Bar
        self.search_entry = ctk.CTkEntry(
            self.header_frame,
            placeholder_text=texts["recent_search_placeholder"],
            height=36,
            font=ctk.CTkFont(size=13)
        )
        self.search_entry.insert(0, self.app_config.get("last_search_topic", "Intelligenza Artificiale"))
        self.search_entry.grid(row=0, column=1, padx=(15, 10), sticky="ew")
        self.search_entry.bind("<Return>", lambda event: self.start_fetch_news())
        
        # Target Language Dropdown Selector
        self.lang_var = ctk.StringVar(value=lang)
        self.lang_dropdown = ctk.CTkOptionMenu(
            self.header_frame,
            values=["English", "Italiano", "Deutsch", "Français", "Español", "中文", "日本語", "Русский", "العربية"],
            variable=self.lang_var,
            width=120,
            height=36,
            font=ctk.CTkFont(size=13),
            command=self.on_lang_change
        )
        self.lang_dropdown.grid(row=0, column=2, padx=(0, 10), sticky="ew")
        
        self.update_btn = ctk.CTkButton(
            self.header_frame,
            text=texts["recent_search_btn"],
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            height=36,
            command=self.start_fetch_news
        )
        self.update_btn.grid(row=0, column=3, sticky="e")
        
        # Status details & Progress bar (hidden initially)
        self.progress_frame = ctk.CTkFrame(self.recent_view_frame, fg_color="transparent")
        self.progress_frame.columnconfigure(0, weight=1)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame, 
            text="Caricamento...", 
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.grid(row=0, column=0, sticky="w", pady=2)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=8, progress_color="#6366F1")
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=4)
        self.progress_bar.set(0)
        
        # Scrollable News List
        self.news_scroll = ctk.CTkScrollableFrame(self.recent_view_frame, fg_color="transparent")
        self.news_scroll.grid(row=1, column=0, sticky="nsew")
        self.news_scroll.columnconfigure(0, weight=1)
        
        # Empty state message
        self.empty_label = ctk.CTkLabel(
            self.news_scroll,
            text=texts["recent_empty"],
            font=ctk.CTkFont(size=14),
            text_color=("#6B7280", "#9CA3AF"),
            pady=100
        )
        self.empty_label.grid(row=0, column=0, sticky="nsew")
        
        # 2. SAVED VIEW FRAME (Initially hidden)
        self.saved_view_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.saved_view_frame.grid_columnconfigure(0, weight=1)
        self.saved_view_frame.grid_rowconfigure(1, weight=1)
        
        # Saved view header
        self.saved_header_frame = ctk.CTkFrame(self.saved_view_frame, fg_color="transparent")
        self.saved_header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.saved_header_frame.columnconfigure(0, weight=1)
        
        self.saved_title = ctk.CTkLabel(
            self.saved_header_frame, 
            text=texts["saved_title"], 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.saved_title.grid(row=0, column=0, sticky="w")
        
        self.saved_subtitle = ctk.CTkLabel(
            self.saved_header_frame,
            text=texts["saved_subtitle"],
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=("#6B7280", "#9CA3AF")
        )
        self.saved_subtitle.grid(row=0, column=1, sticky="e")
        
        # Scrollable saved news
        self.saved_news_scroll = ctk.CTkScrollableFrame(self.saved_view_frame, fg_color="transparent")
        self.saved_news_scroll.grid(row=1, column=0, sticky="nsew")
        self.saved_news_scroll.columnconfigure(0, weight=1)
        
        # 3. GENERATOR VIEW FRAME (Initially hidden)
        self.generator_view_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.generator_view_frame.grid_rowconfigure(1, weight=1)
        self.generator_view_frame.grid_columnconfigure(0, weight=2)
        self.generator_view_frame.grid_columnconfigure(1, weight=3)
        
        # Generator Header
        self.gen_header_frame = ctk.CTkFrame(self.generator_view_frame, fg_color="transparent")
        self.gen_header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        self.gen_header_frame.columnconfigure(0, weight=1)
        
        self.generator_title = ctk.CTkLabel(
            self.gen_header_frame, 
            text=texts["gen_title"], 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.generator_title.grid(row=0, column=0, sticky="w")
        
        # LEFT COLUMN: Config Pane
        self.left_pane = ctk.CTkFrame(self.generator_view_frame, fg_color=("#F3F4F6", "#1F2937"), corner_radius=12)
        self.left_pane.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=0)
        self.left_pane.columnconfigure(0, weight=1)
        
        self.sources_title = ctk.CTkLabel(
            self.left_pane,
            text=texts["gen_sources_title"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.sources_title.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        self.selected_news_scroll = ctk.CTkScrollableFrame(self.left_pane, height=130, fg_color="transparent")
        self.selected_news_scroll.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.selected_news_scroll.columnconfigure(0, weight=1)
        
        self.settings_title = ctk.CTkLabel(
            self.left_pane,
            text=texts["gen_options_title"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.settings_title.grid(row=2, column=0, sticky="w", padx=15, pady=(15, 5))
        
        # Platform menu
        self.platform_label = ctk.CTkLabel(self.left_pane, text=texts["gen_platform_label"], font=ctk.CTkFont(size=11, weight="bold"))
        self.platform_label.grid(row=3, column=0, sticky="w", padx=15, pady=(5, 0))
        
        self.platform_var = ctk.StringVar(value=texts["gen_platforms"][0])
        self.platform_menu = ctk.CTkOptionMenu(
            self.left_pane,
            values=texts["gen_platforms"],
            variable=self.platform_var
        )
        self.platform_menu.grid(row=4, column=0, sticky="ew", padx=15, pady=(2, 10))
        
        # Tone menu
        self.tone_label = ctk.CTkLabel(self.left_pane, text=texts["gen_tone_label"], font=ctk.CTkFont(size=11, weight="bold"))
        self.tone_label.grid(row=5, column=0, sticky="w", padx=15, pady=(5, 0))
        
        self.tone_var = ctk.StringVar(value=texts["gen_tones"][0])
        self.tone_menu = ctk.CTkOptionMenu(
            self.left_pane,
            values=texts["gen_tones"],
            variable=self.tone_var
        )
        self.tone_menu.grid(row=6, column=0, sticky="ew", padx=15, pady=(2, 10))
        
        # Length
        self.length_label = ctk.CTkLabel(self.left_pane, text=texts["gen_length_label"], font=ctk.CTkFont(size=11, weight="bold"))
        self.length_label.grid(row=7, column=0, sticky="w", padx=15, pady=(5, 0))
        
        self.length_var = ctk.StringVar(value=texts["gen_lengths"][1])
        self.length_segmented = ctk.CTkSegmentedButton(
            self.left_pane,
            values=texts["gen_lengths"],
            variable=self.length_var
        )
        self.length_segmented.grid(row=8, column=0, sticky="ew", padx=15, pady=(2, 10))
        
        # Checkboxes
        self.checkboxes_frame = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        self.checkboxes_frame.grid(row=9, column=0, sticky="ew", padx=15, pady=5)
        self.checkboxes_frame.columnconfigure(0, weight=1)
        self.checkboxes_frame.columnconfigure(1, weight=1)
        
        self.emoji_var = ctk.BooleanVar(value=True)
        self.emoji_chk = ctk.CTkCheckBox(self.checkboxes_frame, text="Emoji 😊", variable=self.emoji_var, font=ctk.CTkFont(size=11))
        self.emoji_chk.grid(row=0, column=0, sticky="w")
        
        self.hashtag_var = ctk.BooleanVar(value=True)
        self.hashtag_chk = ctk.CTkCheckBox(self.checkboxes_frame, text="Hashtag #", variable=self.hashtag_var, font=ctk.CTkFont(size=11))
        self.hashtag_chk.grid(row=0, column=1, sticky="w")
        
        # Generate Button
        self.generate_post_btn = ctk.CTkButton(
            self.left_pane,
            text=texts["gen_btn"],
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            height=36,
            command=self.start_generate_post
        )
        self.generate_post_btn.grid(row=10, column=0, sticky="ew", padx=15, pady=(15, 15))
        
        # RIGHT COLUMN: Output Pane
        self.right_pane = ctk.CTkFrame(self.generator_view_frame, fg_color="transparent")
        self.right_pane.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=0)
        self.right_pane.columnconfigure(0, weight=1)
        self.right_pane.rowconfigure(0, weight=1)
        
        self.output_textbox = ctk.CTkTextbox(
            self.right_pane,
            font=ctk.CTkFont(size=13),
            wrap="word",
            border_width=1,
            border_color=("#D1D5DB", "#374151")
        )
        self.output_textbox.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.output_textbox.insert("1.0", texts["gen_output_placeholder"])
        
        self.output_actions_frame = ctk.CTkFrame(self.right_pane, fg_color="transparent")
        self.output_actions_frame.grid(row=1, column=0, sticky="ew")
        self.output_actions_frame.columnconfigure(0, weight=1)
        
        self.copy_btn = ctk.CTkButton(
            self.output_actions_frame,
            text=texts["gen_copy_btn"],
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#E5E7EB", "#374151"),
            text_color=("#374151", "#E5E7EB"),
            hover_color=("#D1D5DB", "#4B5563"),
            height=32,
            command=self.copy_to_clipboard
        )
        self.copy_btn.grid(row=0, column=1, padx=(0, 10), sticky="e")
        
        self.clear_sel_btn = ctk.CTkButton(
            self.output_actions_frame,
            text=texts["gen_clear_btn"],
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent",
            text_color=("#EF4444", "#F87171"),
            hover_color=("#FEE2E2", "#7F1D1D"),
            height=32,
            command=self.clear_selection
        )
        self.clear_sel_btn.grid(row=0, column=2, sticky="e")

    # View navigation helpers
    def switch_view(self, view_name):
        self.current_view = view_name
        self.update_nav_buttons()
        
        # Hide all frames
        self.recent_view_frame.grid_forget()
        self.saved_view_frame.grid_forget()
        self.generator_view_frame.grid_forget()
        
        # Show selected frame
        if view_name == "recent":
            self.recent_view_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.refresh_recent_news_states()
        elif view_name == "saved":
            self.saved_view_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.show_saved_news()
        elif view_name == "generator":
            self.generator_view_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.show_generator_interface()
            
    def update_nav_buttons(self):
        # Recent Button
        if self.current_view == "recent":
            self.nav_recent_btn.configure(fg_color="#6366F1", text_color="white", hover_color="#4F46E5")
        else:
            self.nav_recent_btn.configure(fg_color="transparent", text_color=("#374151", "#E5E7EB"), hover_color=("#E5E7EB", "#374151"))
            
        # Saved Button
        if self.current_view == "saved":
            self.nav_saved_btn.configure(fg_color="#6366F1", text_color="white", hover_color="#4F46E5")
        else:
            self.nav_saved_btn.configure(fg_color="transparent", text_color=("#374151", "#E5E7EB"), hover_color=("#E5E7EB", "#374151"))
            
        # Generator Button
        if self.current_view == "generator":
            self.nav_generator_btn.configure(fg_color="#6366F1", text_color="white", hover_color="#4F46E5")
        else:
            self.nav_generator_btn.configure(fg_color="transparent", text_color=("#374151", "#E5E7EB"), hover_color=("#E5E7EB", "#374151"))

    def update_archive_badge(self):
        count = len(archive.load_archive())
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        self.nav_saved_btn.configure(text=f"{texts['nav_saved']} ({count})")
        
    def update_generator_badge(self):
        count = len(self.selected_news)
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        self.nav_generator_btn.configure(text=f"{texts['nav_generator']} ({count})")

    # Archiving hooks
    def is_news_pinned(self, news_item):
        return archive.is_archived(news_item)
        
    def add_to_archive(self, news_item):
        archive.add_to_archive(news_item)
        self.update_archive_badge()
        
    def remove_from_archive(self, news_item):
        archive.remove_from_archive(news_item)
        self.update_archive_badge()
        if self.current_view == "saved":
            self.show_saved_news()
            
    # Selection hooks
    def is_news_selected(self, news_item):
        link = news_item.get("resolved_link") or news_item.get("google_link")
        title = news_item.get("title_original")
        for item in self.selected_news:
            item_link = item.get("resolved_link") or item.get("google_link")
            if item_link == link or item.get("title_original") == title:
                return True
        return False
        
    def select_news(self, news_item):
        if not self.is_news_selected(news_item):
            self.selected_news.append(news_item)
            self.update_generator_badge()
            
    def deselect_news(self, news_item):
        link = news_item.get("resolved_link") or news_item.get("google_link")
        title = news_item.get("title_original")
        self.selected_news = [
            item for item in self.selected_news 
            if (item.get("resolved_link") or item.get("google_link")) != link and item.get("title_original") != title
        ]
        self.update_generator_badge()
        
    def refresh_recent_news_states(self):
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        for widget in self.news_scroll.winfo_children():
            if isinstance(widget, NewsCard):
                widget.select_var.set(self.is_news_selected(widget.news_item))
                is_pinned = self.is_news_pinned(widget.news_item)
                pin_text = texts["btn_remove"] if is_pinned else texts["btn_save"]
                widget.pin_button.configure(
                    text=pin_text,
                    fg_color=("#EF4444" if is_pinned else "#3B82F6", "#DC2626" if is_pinned else "#2563EB"),
                    hover_color=("#DC2626" if is_pinned else "#2563EB", "#B91C1C" if is_pinned else "#1D4ED8")
                )

    def show_saved_news(self):
        # Clear saved scroll frame
        for widget in self.saved_news_scroll.winfo_children():
            widget.destroy()
            
        saved_items = archive.load_archive()
        
        if not saved_items:
            lang = self.app_config.get("translation_lang", "English")
            texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
            empty_lbl = ctk.CTkLabel(
                self.saved_news_scroll,
                text=texts["saved_empty"],
                font=ctk.CTkFont(size=14),
                text_color=("#6B7280", "#9CA3AF"),
                pady=100
            )
            empty_lbl.grid(row=0, column=0, sticky="nsew")
            return
            
        for index, item in enumerate(saved_items):
            card = NewsCard(self.saved_news_scroll, item, self)
            card.grid(row=index, column=0, padx=10, pady=8, sticky="ew")

    def show_generator_interface(self):
        # Re-populate selected sources
        for widget in self.selected_news_scroll.winfo_children():
            widget.destroy()
            
        if not self.selected_news:
            lang = self.app_config.get("translation_lang", "English")
            texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
            empty_lbl = ctk.CTkLabel(
                self.selected_news_scroll,
                text=texts["gen_empty"],
                font=ctk.CTkFont(size=11, slant="italic"),
                text_color=("#6B7280", "#9CA3AF"),
                anchor="center"
            )
            empty_lbl.grid(row=0, column=0, sticky="ew", pady=20)
            self.generate_post_btn.configure(state="disabled")
        else:
            self.generate_post_btn.configure(state="normal")
            for idx, item in enumerate(self.selected_news):
                row_frame = ctk.CTkFrame(self.selected_news_scroll, fg_color="transparent")
                row_frame.grid(row=idx, column=0, sticky="ew", pady=2)
                row_frame.columnconfigure(0, weight=1)
                
                title_lbl = ctk.CTkLabel(
                    row_frame,
                    text=f"• {item.get('title_translated', item.get('title_original'))}",
                    font=ctk.CTkFont(size=11),
                    justify="left",
                    anchor="w",
                    wraplength=180
                )
                title_lbl.grid(row=0, column=0, sticky="w", padx=(2, 5))
                
                remove_btn = ctk.CTkButton(
                    row_frame,
                    text="✕",
                    width=20,
                    height=20,
                    fg_color="transparent",
                    text_color=("#EF4444", "#F87171"),
                    hover_color=("#FEE2E2", "#7F1D1D"),
                    command=lambda it=item: self.deselect_news_from_generator(it)
                )
                remove_btn.grid(row=0, column=1, sticky="e")
                
    def deselect_news_from_generator(self, item):
        self.deselect_news(item)
        self.show_generator_interface()
        
    def copy_to_clipboard(self):
        text = self.output_textbox.get("1.0", "end-1c")
        if text.strip() and not text.startswith("Il post generato comparirà qui."):
            self.clipboard_clear()
            self.clipboard_append(text)
            
            # Temporary Copied notification
            orig_text = self.copy_btn.cget("text")
            self.copy_btn.configure(text="Copiato! ✓", fg_color="#10B981")
            self.after(2000, lambda: self.copy_btn.configure(text=orig_text, fg_color=("#E5E7EB", "#374151")))
            
    def clear_selection(self):
        self.selected_news = []
        self.update_generator_badge()
        self.show_generator_interface()
        self.refresh_recent_news_states()
        
    def start_generate_post(self):
        if not self.selected_news:
            return
            
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        
        selected_model = self.app_config.get("selected_model")
        if not selected_model:
            self.show_generator_error(texts["err_model"])
            return
            
        # Disable controls
        self.generate_post_btn.configure(state="disabled", text=texts["gen_btn_generating"])
        self.platform_menu.configure(state="disabled")
        self.tone_menu.configure(state="disabled")
        self.length_segmented.configure(state="disabled")
        self.emoji_chk.configure(state="disabled")
        self.hashtag_chk.configure(state="disabled")
        self.clear_sel_btn.configure(state="disabled")
        
        self.output_textbox.delete("1.0", "end")
        self.output_textbox.insert("1.0", texts["toast_generating"])
        
        platform = self.platform_var.get()
        tone = self.tone_var.get()
        length = self.length_var.get()
        include_emojis = self.emoji_var.get()
        include_hashtags = self.hashtag_var.get()
        server_url = self.app_config.get("ollama_url")
        target_lang = lang
        
        # Map values back to Italian for backend / LLM prompt context
        it_texts = LOCALIZATION["Italiano"]
        
        # Platform
        try:
            plat_idx = texts["gen_platforms"].index(platform)
            platform_it = it_texts["gen_platforms"][plat_idx]
        except ValueError:
            platform_it = platform
            
        # Tone
        try:
            tone_idx = texts["gen_tones"].index(tone)
            tone_it = it_texts["gen_tones"][tone_idx]
        except ValueError:
            tone_it = tone
            
        # Length
        try:
            len_idx = texts["gen_lengths"].index(length)
            length_it = it_texts["gen_lengths"][len_idx]
        except ValueError:
            length_it = length
            
        topic = self.search_entry.get().strip() or "Intelligenza Artificiale"
        
        threading.Thread(
            target=self.run_post_generation,
            args=(self.selected_news.copy(), platform_it, tone_it, length_it, include_hashtags, include_emojis, selected_model, topic, target_lang, server_url),
            daemon=True
        ).start()
        
    def run_post_generation(self, news_items, platform, tone, length, include_hashtags, include_emojis, model, topic, target_lang, server_url):
        try:
            post_content = ollama_client.generate_social_post(
                news_items=news_items,
                platform=platform,
                tone=tone,
                length=length,
                include_hashtags=include_hashtags,
                include_emojis=include_emojis,
                model=model,
                topic=topic,
                target_lang=target_lang,
                server_url=server_url
            )
            self.after(0, lambda: self.finish_post_generation(post_content))
        except Exception as e:
            lang = self.app_config.get("translation_lang", "English")
            texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
            self.after(0, lambda: self.finish_post_generation(f"{texts['err_generation']}{str(e)}"))
            
    def finish_post_generation(self, content):
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        self.generate_post_btn.configure(state="normal", text=texts["gen_btn"])
        self.platform_menu.configure(state="normal")
        self.tone_menu.configure(state="normal")
        self.length_segmented.configure(state="normal")
        self.emoji_chk.configure(state="normal")
        self.hashtag_chk.configure(state="normal")
        self.clear_sel_btn.configure(state="normal")
        
        self.output_textbox.delete("1.0", "end")
        self.output_textbox.insert("1.0", content)
        
    def show_generator_error(self, message):
        self.output_textbox.delete("1.0", "end")
        self.output_textbox.insert("1.0", message)

    def check_ollama_status(self):
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        
        self.status_label.configure(text=texts["status_detecting"], text_color="#F59E0B")
        self.update()
        
        def run_check():
            try:
                models = ollama_client.get_local_models(self.app_config.get("ollama_url"))
                self.models = models
                self.after(0, lambda: self.update_ollama_status(True, models))
            except ConnectionError:
                self.after(0, lambda: self.update_ollama_status(False, []))
                
        threading.Thread(target=run_check, daemon=True).start()
        
    def update_ollama_status(self, connected, models):
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        
        if connected:
            self.status_label.configure(text=texts["status_connected"], text_color="#10B981")
            if models:
                self.model_dropdown.configure(values=models, state="normal")
                
                # Check if currently saved model is in the retrieved models
                saved_model = self.app_config.get("selected_model")
                if saved_model in models:
                    self.model_dropdown.set(saved_model)
                else:
                    # Select the first model as default
                    self.model_dropdown.set(models[0])
                    self.app_config["selected_model"] = models[0]
                    config.save_config(self.app_config)
            else:
                self.model_dropdown.configure(values=[texts["model_none_found"]], state="disabled")
                self.model_dropdown.set(texts["model_download"])
        else:
            self.status_label.configure(text=texts["status_disconnected"], text_color="#EF4444")
            self.model_dropdown.configure(values=[texts["status_disconnected"]], state="disabled")
            self.model_dropdown.set("Controlla server")
            
    def on_model_change(self, selected_model):
        self.app_config["selected_model"] = selected_model
        config.save_config(self.app_config)
        
    def on_range_change(self, selected_range):
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        val = 2 if selected_range == texts["range_yesterday"] else 1
        self.app_config["time_range"] = val
        config.save_config(self.app_config)
        
    def on_theme_change(self, selected_theme):
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        
        # Map localized theme back to English system values: Dark, Light, System
        theme_map = {
            texts["theme_dark"]: "Dark",
            texts["theme_light"]: "Light",
            texts["theme_system"]: "System"
        }
        theme_val = theme_map.get(selected_theme, "Dark")
        self.app_config["theme"] = theme_val
        config.save_config(self.app_config)
        ctk.set_appearance_mode(theme_val)
        
    def on_feeds_change(self):
        enabled_feeds = [feed_key for feed_key, var in self.feed_vars.items() if var.get()]
        self.app_config["feeds"] = enabled_feeds
        config.save_config(self.app_config)
        
    def on_max_news_change(self, selected_value):
        try:
            self.app_config["max_news_count"] = int(selected_value)
            config.save_config(self.app_config)
        except Exception:
            pass
        
    def on_lang_change(self, selected_lang):
        self.app_config["translation_lang"] = selected_lang
        config.save_config(self.app_config)
        self.update_ui_text()
        
    def update_ui_text(self):
        # Load localization
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        
        # Update sidebar
        self.title_label.configure(text=texts["title"])
        self.subtitle_label.configure(text=texts["subtitle"])
        self.nav_label.configure(text=texts["nav_label"])
        self.nav_recent_btn.configure(text=texts["nav_recent"])
        self.update_archive_badge()
        self.update_generator_badge()
        
        self.model_label.configure(text=texts["model_label"])
        self.range_label.configure(text=texts["range_label"])
        self.range_segmented.configure(values=[texts["range_today"], texts["range_yesterday"]])
        if self.app_config.get("time_range") == 2:
            self.range_segmented.set(texts["range_yesterday"])
        else:
            self.range_segmented.set(texts["range_today"])
            
        self.feeds_label.configure(text=texts["feeds_label"])
        feed_trans_keys = {
            "europe": "feed_europe",
            "north_america": "feed_na",
            "south_america": "feed_sa",
            "asia": "feed_asia",
            "africa": "feed_africa",
            "oceania": "feed_oceania"
        }
        for feed_key, chk in self.feed_checkboxes.items():
            trans_key = feed_trans_keys[feed_key]
            chk.configure(text=texts[trans_key])
            
        self.max_news_label.configure(text=texts["max_news_label"])
        self.theme_label.configure(text=texts["theme_label"])
        self.theme_dropdown.configure(values=[texts["theme_dark"], texts["theme_light"], texts["theme_system"]])
        theme_rev_map = {
            "Dark": texts["theme_dark"],
            "Light": texts["theme_light"],
            "System": texts["theme_system"]
        }
        self.theme_dropdown.set(theme_rev_map.get(self.app_config.get("theme", "Dark"), texts["theme_dark"]))
        
        # Update main area views
        self.section_title.configure(text=texts["recent_title"])
        self.search_entry.configure(placeholder_text=texts["recent_search_placeholder"])
        self.update_btn.configure(text=texts["recent_search_btn"])
        self.empty_label.configure(text=texts["recent_empty"])
        
        self.saved_title.configure(text=texts["saved_title"])
        self.saved_subtitle.configure(text=texts["saved_subtitle"])
        
        self.generator_title.configure(text=texts["gen_title"])
        self.sources_title.configure(text=texts["gen_sources_title"])
        self.settings_title.configure(text=texts["gen_options_title"])
        
        self.platform_label.configure(text=texts["gen_platform_label"])
        # Map selected platform index
        plat_idx = 0
        current_plat = self.platform_var.get()
        for l in LOCALIZATION.values():
            if current_plat in l["gen_platforms"]:
                plat_idx = l["gen_platforms"].index(current_plat)
                break
        self.platform_menu.configure(values=texts["gen_platforms"])
        self.platform_menu.set(texts["gen_platforms"][plat_idx])
        
        self.tone_label.configure(text=texts["gen_tone_label"])
        tone_idx = 0
        current_tone = self.tone_var.get()
        for l in LOCALIZATION.values():
            if current_tone in l["gen_tones"]:
                tone_idx = l["gen_tones"].index(current_tone)
                break
        self.tone_menu.configure(values=texts["gen_tones"])
        self.tone_menu.set(texts["gen_tones"][tone_idx])
        
        self.length_label.configure(text=texts["gen_length_label"])
        len_idx = 1
        current_len = self.length_var.get()
        for l in LOCALIZATION.values():
            if current_len in l["gen_lengths"]:
                len_idx = l["gen_lengths"].index(current_len)
                break
        self.length_segmented.configure(values=texts["gen_lengths"])
        self.length_segmented.set(texts["gen_lengths"][len_idx])
        
        self.generate_post_btn.configure(text=texts["gen_btn"])
        self.copy_btn.configure(text=texts["gen_copy_btn"])
        self.clear_sel_btn.configure(text=texts["gen_clear_btn"])
        
        # Output textbox placeholder
        current_out = self.output_textbox.get("1.0", "end-1c").strip()
        is_placeholder = False
        for l in LOCALIZATION.values():
            if current_out == l["gen_output_placeholder"].strip() or current_out == "":
                is_placeholder = True
                break
        if is_placeholder:
            self.output_textbox.delete("1.0", "end")
            self.output_textbox.insert("1.0", texts["gen_output_placeholder"])
            
        # Update dynamically created NewsCard components currently on screen
        for frame in [self.news_scroll, self.saved_news_scroll]:
            for child in frame.winfo_children():
                if isinstance(child, NewsCard):
                    child.update_texts()
                    
        # Update sources generator screen if generator view is active
        if self.current_view == "generator":
            self.show_generator_interface()
            
        # Re-trigger status checks to translate Ollama status label
        self.check_ollama_status()
        
    def start_fetch_news(self):
        if self.is_fetching:
            return
            
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        
        if not self.models:
            self.show_error_message(texts["err_model"])
            return
            
        selected_feeds = self.app_config.get("feeds", ["europe", "north_america"])
        if not selected_feeds:
            self.show_error_message(texts["err_feeds"])
            return
            
        topic = self.search_entry.get().strip()
        if not topic:
            topic = "Intelligenza Artificiale"
            self.search_entry.insert(0, topic)

        # Save topic to config
        self.app_config["last_search_topic"] = topic
        config.save_config(self.app_config)

        self.is_fetching = True
        self.update_btn.configure(state="disabled")
        self.model_dropdown.configure(state="disabled")
        self.lang_dropdown.configure(state="disabled")
        self.range_segmented.configure(state="disabled")
        
        # Disable feed checkboxes and max news dropdown while fetching
        for chk in self.feeds_frame.winfo_children():
            chk.configure(state="disabled")
        self.max_news_dropdown.configure(state="disabled")
        
        # Clear main list
        for widget in self.news_scroll.winfo_children():
            widget.destroy()
            
        # Show progress frame
        self.progress_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.progress_bar.set(0)
        self.progress_label.configure(text="Scaricamento notizie da Google News RSS...")
        
        # Start background thread
        days = self.app_config.get("time_range", 2)
        selected_model = self.app_config.get("selected_model")
        server_url = self.app_config.get("ollama_url")
        max_news = self.app_config.get("max_news_count", 15)
        target_lang = self.app_config.get("translation_lang", "Italiano")
        
        threading.Thread(
            target=self.fetch_and_process_news,
            args=(topic, days, selected_model, server_url, selected_feeds, max_news, target_lang),
            daemon=True
        ).start()
        
    def show_error_message(self, message):
        for widget in self.news_scroll.winfo_children():
            widget.destroy()
        err_label = ctk.CTkLabel(
            self.news_scroll,
            text=message,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#EF4444",
            pady=100
        )
        err_label.grid(row=0, column=0, sticky="nsew")

    def fetch_and_process_news(self, topic, days, model, server_url, selected_feeds, max_news, target_lang):
        lang = self.app_config.get("translation_lang", "English")
        texts = LOCALIZATION.get(lang, LOCALIZATION["English"])
        try:
            # Step 1: Fetch news RSS
            news_items = news_fetcher.get_news(
                topic=topic,
                days=days,
                feeds_to_use=selected_feeds,
                max_news_count=max_news,
                model=model,
                server_url=server_url
            )
            
            if not news_items:
                self.after(0, lambda: self.finish_fetching(texts["err_no_news"]))
                return
                
            total_items = len(news_items)
            self.after(0, lambda: self.progress_label.configure(text=texts["progress_found"].format(total=total_items)))
            
            # Step 2: Loop and process each item
            for index, item in enumerate(news_items):
                # Update progress label
                prog_val = (index + 0.1) / total_items
                msg_analyze = texts["progress_analyze"].format(index=index+1, total=total_items)
                self.after(0, lambda v=prog_val, msg=msg_analyze: self.update_progress(v, msg))
                
                # Fetch full snippet from destination webpage
                cleaned_snippet, final_url = news_fetcher.fetch_article_details(item["google_link"])
                if cleaned_snippet:
                    item["full_snippet"] = cleaned_snippet
                item["resolved_link"] = final_url
                
                # Update progress for Ollama step
                prog_val = (index + 0.6) / total_items
                msg_ollama = texts["progress_ollama"].format(model=model, index=index+1, total=total_items)
                self.after(0, lambda v=prog_val, msg=msg_ollama: self.update_progress(v, msg))
                
                # Query Ollama to summarize
                ollama_res = ollama_client.summarize_news(
                    title=item["title_original"],
                    text_content=item["full_snippet"][:500],
                    model=model,
                    topic=topic,
                    target_lang=target_lang,
                    server_url=server_url
                )
                
                item["title_translated"] = ollama_res.get("titolo_italiano", item["title_original"])
                item["summary_italian"] = ollama_res.get("riassunto_italiano", "Errore nel riassunto.")
                
                # Add card to GUI immediately
                self.after(0, self.add_news_card, item)
                
            # Finish up
            self.after(0, lambda: self.finish_fetching(None))
            
        except Exception as e:
            self.after(0, lambda: self.finish_fetching(f"{texts['err_generation']}{str(e)}"))

    def update_progress(self, val, text):
        self.progress_bar.set(val)
        self.progress_label.configure(text=text)
        
    def add_news_card(self, news_item):
        if hasattr(self, 'empty_label') and self.empty_label.winfo_exists():
            self.empty_label.grid_forget()
            
        card = NewsCard(self.news_scroll, news_item, self)
        card.grid(row=self.news_scroll.grid_size()[1], column=0, padx=10, pady=8, sticky="ew")
        
    def finish_fetching(self, error_message):
        self.is_fetching = False
        self.update_btn.configure(state="normal")
        self.model_dropdown.configure(state="normal")
        self.lang_dropdown.configure(state="normal")
        self.range_segmented.configure(state="normal")
        
        # Re-enable checkboxes and max news dropdown
        for chk in self.feeds_frame.winfo_children():
            chk.configure(state="normal")
        self.max_news_dropdown.configure(state="normal")
        
        # Hide progress frame
        self.progress_frame.grid_forget()
        
        if error_message:
            self.show_error_message(error_message)
        elif self.news_scroll.grid_size()[1] == 0:
            self.show_error_message("Nessuna notizia caricata.")


if __name__ == "__main__":
    app = App()
    app.mainloop()

