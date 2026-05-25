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
        
        # Checkbox for selecting for social post
        self.select_var = ctk.BooleanVar(value=self.app.is_news_selected(self.news_item))
        self.select_checkbox = ctk.CTkCheckBox(
            self.actions_frame,
            text="Seleziona per Post",
            variable=self.select_var,
            command=self.toggle_select,
            font=ctk.CTkFont(size=11, weight="bold"),
            checkbox_width=18,
            checkbox_height=18
        )
        self.select_checkbox.grid(row=0, column=0, sticky="w")
        
        # Pin/Archive button
        is_pinned = self.app.is_news_pinned(self.news_item)
        pin_text = "📌 Rimuovi" if is_pinned else "📌 Salva"
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
            text="Apri Fonte ↗", 
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
        
    def open_source(self):
        url = self.news_item.get("resolved_link", self.news_item.get("google_link"))
        webbrowser.open(url)
        
    def toggle_pin(self):
        is_pinned = self.app.is_news_pinned(self.news_item)
        if is_pinned:
            self.app.remove_from_archive(self.news_item)
            self.pin_button.configure(
                text="📌 Salva",
                fg_color=("#3B82F6", "#2563EB"),
                hover_color=("#2563EB", "#1D4ED8")
            )
        else:
            self.app.add_to_archive(self.news_item)
            self.pin_button.configure(
                text="📌 Rimuovi",
                fg_color=("#EF4444", "#DC2626"),
                hover_color=("#DC2626", "#B91C1C")
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
        
        # Initial check for Ollama status
        self.check_ollama_status()
        
        # Update badge counts initially
        self.update_archive_badge()
        self.update_generator_badge()
        
    def create_sidebar(self):
        # Sidebar Frame
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(13, weight=1)  # Spacer row
        
        # App Title
        self.title_label = ctk.CTkLabel(
            self.sidebar, 
            text="Smart News AI", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 5))
        
        self.subtitle_label = ctk.CTkLabel(
            self.sidebar, 
            text="Aggregatore di notizie e creatore di post", 
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
            text="Navigazione:", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.nav_label.grid(row=3, column=0, padx=20, pady=(10, 2), sticky="w")
        
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.nav_frame.columnconfigure(0, weight=1)
        
        self.nav_recent_btn = ctk.CTkButton(
            self.nav_frame,
            text="📰  Notizie Recenti",
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
            text="📌  Notizie Salvate (0)",
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
            text="✍️  Generatore Post (0)",
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
            text="Ollama: Rilevamento...", 
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
            text="Seleziona Modello:", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.model_label.grid(row=7, column=0, padx=20, pady=(10, 2), sticky="w")
        
        self.model_dropdown = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Rilevamento..."],
            command=self.on_model_change
        )
        self.model_dropdown.grid(row=7, column=0, padx=20, pady=(25, 5), sticky="ew")
        
        # Time range selection
        self.range_label = ctk.CTkLabel(
            self.sidebar, 
            text="Intervallo temporale:", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.range_label.grid(row=8, column=0, padx=20, pady=(10, 2), sticky="w")
        
        # Segmented button for time range
        self.range_var = ctk.StringVar(value="Oggi e Ieri" if self.app_config.get("time_range") == 2 else "Solo Oggi")
        self.range_segmented = ctk.CTkSegmentedButton(
            self.sidebar,
            values=["Solo Oggi", "Oggi e Ieri"],
            variable=self.range_var,
            command=self.on_range_change
        )
        self.range_segmented.grid(row=8, column=0, padx=20, pady=(25, 5), sticky="ew")
        
        # Geographics feeds checkboxes
        self.feeds_label = ctk.CTkLabel(
            self.sidebar, 
            text="Seleziona Continenti:", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.feeds_label.grid(row=9, column=0, padx=20, pady=(10, 2), sticky="w")
        
        self.feeds_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.feeds_frame.grid(row=10, column=0, padx=15, pady=0, sticky="ew")
        
        self.feed_vars = {}
        feed_options = [
            ("europe", "Europa"),
            ("north_america", "N. America"),
            ("south_america", "S. America"),
            ("asia", "Asia"),
            ("africa", "Africa"),
            ("oceania", "Oceania")
        ]
        enabled_feeds = self.app_config.get("feeds", ["europe", "north_america"])
        for idx, (feed_key, label_text) in enumerate(feed_options):
            var = ctk.BooleanVar(value=(feed_key in enabled_feeds))
            chk = ctk.CTkCheckBox(
                self.feeds_frame,
                text=label_text,
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
            
        # Max news count selection
        self.max_news_label = ctk.CTkLabel(
            self.sidebar,
            text="Max Notizie da mostrare:",
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
            text="Tema Interfaccia:", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.theme_label.grid(row=12, column=0, padx=20, pady=(10, 2), sticky="w")
        
        self.theme_dropdown = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Dark", "Light", "System"],
            command=self.on_theme_change
        )
        self.theme_dropdown.set(self.app_config.get("theme", "Dark"))
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
        # 1. RECENT VIEW FRAME
        self.recent_view_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.recent_view_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.recent_view_frame.grid_columnconfigure(0, weight=1)
        self.recent_view_frame.grid_rowconfigure(1, weight=1)
        
        # Header actions
        self.header_frame = ctk.CTkFrame(self.recent_view_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.header_frame.columnconfigure(1, weight=1)
        
        self.section_title = ctk.CTkLabel(
            self.header_frame, 
            text="Notizie:", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.section_title.grid(row=0, column=0, sticky="w")

        # Search Bar
        self.search_entry = ctk.CTkEntry(
            self.header_frame,
            placeholder_text="Cosa vuoi cercare? (es. Energie Rinnovabili, Spazio, AI...)",
            height=36,
            font=ctk.CTkFont(size=13)
        )
        self.search_entry.insert(0, self.app_config.get("last_search_topic", "Intelligenza Artificiale"))
        self.search_entry.grid(row=0, column=1, padx=(15, 10), sticky="ew")
        self.search_entry.bind("<Return>", lambda event: self.start_fetch_news())
        
        self.update_btn = ctk.CTkButton(
            self.header_frame,
            text="Cerca Notizie 🔍",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            height=36,
            command=self.start_fetch_news
        )
        self.update_btn.grid(row=0, column=2, sticky="e")
        
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
        
        # Scrollable News List
        self.news_scroll = ctk.CTkScrollableFrame(self.recent_view_frame, fg_color="transparent")
        self.news_scroll.grid(row=1, column=0, sticky="nsew")
        self.news_scroll.columnconfigure(0, weight=1)
        
        # Empty state message
        self.empty_label = ctk.CTkLabel(
            self.news_scroll,
            text="Nessuna notizia caricata.\nScrivi un argomento e clicca su 'Cerca Notizie' per iniziare.",
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
            text="Notizie Salvate", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.saved_title.grid(row=0, column=0, sticky="w")
        
        self.saved_subtitle = ctk.CTkLabel(
            self.saved_header_frame,
            text="Archivio locale (max 7 giorni)",
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
            text="Generatore Social Post", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.generator_title.grid(row=0, column=0, sticky="w")
        
        # LEFT COLUMN: Config Pane
        self.left_pane = ctk.CTkFrame(self.generator_view_frame, fg_color=("#F3F4F6", "#1F2937"), corner_radius=12)
        self.left_pane.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=0)
        self.left_pane.columnconfigure(0, weight=1)
        
        self.sources_title = ctk.CTkLabel(
            self.left_pane,
            text="1. Fonti Selezionate:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.sources_title.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        self.selected_news_scroll = ctk.CTkScrollableFrame(self.left_pane, height=130, fg_color="transparent")
        self.selected_news_scroll.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.selected_news_scroll.columnconfigure(0, weight=1)
        
        self.settings_title = ctk.CTkLabel(
            self.left_pane,
            text="2. Opzioni Generazione:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.settings_title.grid(row=2, column=0, sticky="w", padx=15, pady=(15, 5))
        
        # Platform menu
        self.platform_label = ctk.CTkLabel(self.left_pane, text="Piattaforma:", font=ctk.CTkFont(size=11, weight="bold"))
        self.platform_label.grid(row=3, column=0, sticky="w", padx=15, pady=(5, 0))
        
        self.platform_var = ctk.StringVar(value="LinkedIn")
        self.platform_menu = ctk.CTkOptionMenu(
            self.left_pane,
            values=["LinkedIn", "X / Twitter", "Facebook", "Blog / Articolo"],
            variable=self.platform_var
        )
        self.platform_menu.grid(row=4, column=0, sticky="ew", padx=15, pady=(2, 10))
        
        # Tone menu
        self.tone_label = ctk.CTkLabel(self.left_pane, text="Tono di voce:", font=ctk.CTkFont(size=11, weight="bold"))
        self.tone_label.grid(row=5, column=0, sticky="w", padx=15, pady=(5, 0))
        
        self.tone_var = ctk.StringVar(value="Professionale")
        self.tone_menu = ctk.CTkOptionMenu(
            self.left_pane,
            values=["Professionale", "Informativo", "Coinvolgente", "Tecnico"],
            variable=self.tone_var
        )
        self.tone_menu.grid(row=6, column=0, sticky="ew", padx=15, pady=(2, 10))
        
        # Length
        self.length_label = ctk.CTkLabel(self.left_pane, text="Lunghezza post:", font=ctk.CTkFont(size=11, weight="bold"))
        self.length_label.grid(row=7, column=0, sticky="w", padx=15, pady=(5, 0))
        
        self.length_var = ctk.StringVar(value="Medio")
        self.length_segmented = ctk.CTkSegmentedButton(
            self.left_pane,
            values=["Breve", "Medio", "Dettagliato"],
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
            text="Genera Post ⚡",
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
        self.output_textbox.insert("1.0", "Il post generato comparirà qui.\n\nSeleziona una o più notizie dalle altre schede ed inserisci i parametri a sinistra, quindi clicca su 'Genera Post ⚡'.")
        
        self.output_actions_frame = ctk.CTkFrame(self.right_pane, fg_color="transparent")
        self.output_actions_frame.grid(row=1, column=0, sticky="ew")
        self.output_actions_frame.columnconfigure(0, weight=1)
        
        self.copy_btn = ctk.CTkButton(
            self.output_actions_frame,
            text="Copia negli appunti 📋",
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
            text="Pulisci Selezione 🧹",
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
        self.nav_saved_btn.configure(text=f"📌  Notizie Salvate ({count})")
        
    def update_generator_badge(self):
        count = len(self.selected_news)
        self.nav_generator_btn.configure(text=f"✍️  Generatore Post ({count})")

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
        for widget in self.news_scroll.winfo_children():
            if isinstance(widget, NewsCard):
                widget.select_var.set(self.is_news_selected(widget.news_item))
                is_pinned = self.is_news_pinned(widget.news_item)
                pin_text = "📌 Rimuovi" if is_pinned else "📌 Salva"
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
            empty_lbl = ctk.CTkLabel(
                self.saved_news_scroll,
                text="Nessuna notizia salvata.\n\nSalva le notizie importanti cliccando su '📌 Salva'\nnelle schede delle Notizie Recenti.",
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
            empty_lbl = ctk.CTkLabel(
                self.selected_news_scroll,
                text="Nessuna notizia selezionata.\nSeleziona le notizie dalle altre schede.",
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
            
        selected_model = self.app_config.get("selected_model")
        if not selected_model:
            self.show_generator_error("Seleziona un modello Ollama valido nella barra laterale.")
            return
            
        # Disable controls
        self.generate_post_btn.configure(state="disabled", text="Generazione...")
        self.platform_menu.configure(state="disabled")
        self.tone_menu.configure(state="disabled")
        self.length_segmented.configure(state="disabled")
        self.emoji_chk.configure(state="disabled")
        self.hashtag_chk.configure(state="disabled")
        self.clear_sel_btn.configure(state="disabled")
        
        self.output_textbox.delete("1.0", "end")
        self.output_textbox.insert("1.0", "Generazione del post social in corso con Ollama locale...\nAttendere prego (può richiedere diversi secondi)...")
        
        platform = self.platform_var.get()
        tone = self.tone_var.get()
        length = self.length_var.get()
        include_emojis = self.emoji_var.get()
        include_hashtags = self.hashtag_var.get()
        server_url = self.app_config.get("ollama_url")
        
        topic = self.search_entry.get().strip() or "Intelligenza Artificiale"
        
        threading.Thread(
            target=self.run_post_generation,
            args=(self.selected_news.copy(), platform, tone, length, include_hashtags, include_emojis, selected_model, topic, server_url),
            daemon=True
        ).start()
        
    def run_post_generation(self, news_items, platform, tone, length, include_hashtags, include_emojis, model, topic, server_url):
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
                server_url=server_url
            )
            self.after(0, lambda: self.finish_post_generation(post_content))
        except Exception as e:
            self.after(0, lambda: self.finish_post_generation(f"Errore durante la generazione: {str(e)}"))
            
    def finish_post_generation(self, content):
        self.generate_post_btn.configure(state="normal", text="Genera Post ⚡")
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
        self.status_label.configure(text="Ollama: Connessione...", text_color="#F59E0B")
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
        if connected:
            self.status_label.configure(text="Ollama: Connesso", text_color="#10B981")
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
                self.model_dropdown.configure(values=["Nessun modello trovato"], state="disabled")
                self.model_dropdown.set("Scarica un modello!")
        else:
            self.status_label.configure(text="Ollama: Disconnesso", text_color="#EF4444")
            self.model_dropdown.configure(values=["Ollama offline"], state="disabled")
            self.model_dropdown.set("Controlla server")
            
    def on_model_change(self, selected_model):
        self.app_config["selected_model"] = selected_model
        config.save_config(self.app_config)
        
    def on_range_change(self, selected_range):
        val = 2 if selected_range == "Oggi e Ieri" else 1
        self.app_config["time_range"] = val
        config.save_config(self.app_config)
        
    def on_theme_change(self, selected_theme):
        self.app_config["theme"] = selected_theme
        config.save_config(self.app_config)
        ctk.set_appearance_mode(selected_theme)
        
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
        
    def start_fetch_news(self):
        if self.is_fetching:
            return
            
        if not self.models:
            self.show_error_message("Errore: Ollama disconnesso o nessun modello installato. Avvia Ollama e riprova.")
            return
            
        selected_feeds = self.app_config.get("feeds", ["europe", "north_america"])
        if not selected_feeds:
            self.show_error_message("Errore: Seleziona almeno un continente nella barra laterale.")
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
        
        threading.Thread(
            target=self.fetch_and_process_news,
            args=(topic, days, selected_model, server_url, selected_feeds, max_news),
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

    def fetch_and_process_news(self, topic, days, model, server_url, selected_feeds, max_news):
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
                self.after(0, lambda: self.finish_fetching("Nessuna notizia trovata per questo intervallo temporale o per i continenti selezionati."))
                return
                
            total_items = len(news_items)
            self.after(0, lambda: self.progress_label.configure(text=f"Trovate {total_items} notizie. Generazione riassunti in corso..."))
            
            # Step 2: Loop and process each item
            for index, item in enumerate(news_items):
                # Update progress label
                prog_val = (index + 0.1) / total_items
                self.after(0, lambda v=prog_val, idx=index, tot=total_items: self.update_progress(v, f"Analisi articolo {idx+1}/{tot}..."))
                
                # Fetch full snippet from destination webpage
                cleaned_snippet, final_url = news_fetcher.fetch_article_details(item["google_link"])
                if cleaned_snippet:
                    item["full_snippet"] = cleaned_snippet
                item["resolved_link"] = final_url
                
                # Update progress for Ollama step
                prog_val = (index + 0.6) / total_items
                self.after(0, lambda v=prog_val, idx=index, tot=total_items: self.update_progress(v, f"Riassunto con Ollama ({model}) {idx+1}/{tot}..."))
                
                # Query Ollama to summarize
                ollama_res = ollama_client.summarize_news(
                    title=item["title_original"],
                    text_content=item["full_snippet"][:500],
                    model=model,
                    topic=topic,
                    server_url=server_url
                )
                
                item["title_translated"] = ollama_res.get("titolo_italiano", item["title_original"])
                item["summary_italian"] = ollama_res.get("riassunto_italiano", "Errore nel riassunto.")
                
                # Add card to GUI immediately
                self.after(0, self.add_news_card, item)
                
            # Finish up
            self.after(0, lambda: self.finish_fetching(None))
            
        except Exception as e:
            self.after(0, lambda: self.finish_fetching(f"Errore durante l'elaborazione: {str(e)}"))

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

