#!/bin/bash
# Script per compilare l'app e creare il pacchetto .deb su Linux Mint

set -e

echo "=== 1. Pulizia directory precedenti ==="
rm -rf build dist pkg_dir *.deb *.spec

echo "=== 2. Compilazione eseguibile con PyInstaller ==="
# --collect-all customtkinter è necessario per includere i temi e gli asset di customtkinter
venv/bin/pyinstaller --onefile --windowed --noconsole \
    --name "smart-news-ai" \
    --add-data "src/icon.png:." \
    --collect-all customtkinter \
    src/main.py

echo "=== 3. Creazione struttura pacchetto Debian ==="
mkdir -p pkg_dir/DEBIAN
mkdir -p pkg_dir/usr/bin
mkdir -p pkg_dir/usr/share/applications
mkdir -p pkg_dir/usr/share/pixmaps

# Copia l'eseguibile compilato
cp dist/smart-news-ai pkg_dir/usr/bin/

# Copia l'icona dell'app
cp src/icon.png pkg_dir/usr/share/pixmaps/smart-news-ai.png

echo "=== 4. Creazione file DEBIAN/control ==="
cat <<EOT > pkg_dir/DEBIAN/control
Package: smart-news-ai
Version: 1.2.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Antigravity <antigravity@gemini.ai>
Description: Aggregatore di notizie e creatore di post usando Ollama locale.
EOT

echo "=== 5. Creazione file .desktop per il menu delle applicazioni ==="
cat <<EOT > pkg_dir/usr/share/applications/smart-news-ai.desktop
[Desktop Entry]
Name=Smart News AI
Comment=Aggregatore di notizie e creatore di post
Exec=/usr/bin/smart-news-ai
Icon=smart-news-ai
Terminal=false
Type=Application
Categories=Utility;News;
EOT

# Imposta i permessi corretti per il pacchetto
chmod 755 pkg_dir/usr/bin/smart-news-ai
chmod 644 pkg_dir/usr/share/applications/smart-news-ai.desktop
chmod 644 pkg_dir/usr/share/pixmaps/smart-news-ai.png
chmod -R 755 pkg_dir/DEBIAN

echo "=== 6. Generazione pacchetto .deb ==="
dpkg-deb --build pkg_dir smart-news-ai.deb

echo "=== 7. Pulizia file temporanei ==="
rm -rf pkg_dir build dist

echo "=========================================================="
echo "Pacchetto creato con successo: smart-news-ai.deb"
echo "Puoi installarlo usando: sudo dpkg -i smart-news-ai.deb"
echo "=========================================================="
