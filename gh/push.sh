#!/bin/bash

# --- KONFIGURATION ---
REMOTE_URL="https://github.com/wired87/lighter1_back"
BRANCH_NAME="master"

# --- PRÜFUNGEN ---
if [ ! -f .env ]; then
    echo "❌ Fehler: Keine .env Datei im aktuellen Verzeichnis gefunden!"
    exit 1
fi

if ! command -v gh &> /dev/null; then
    echo "❌ Fehler: Die GitHub CLI ('gh') ist nicht installiert."
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "❌ Fehler: Bitte zuerst mit 'gh auth login' bei GitHub einloggen."
    exit 1
fi

echo "=================================================="
echo "🚀 START: Automatischer Git Setup & Secret-Upload"
echo "=================================================="

# --- SCHRITT 1: GIT INLINE AUFRÄUMEN & SETZEN (Wichtig für GH CLI!) ---
echo "📦 Bereite Repository vor..."
# Interne .git Ordner entfernen
rm -rf gem_core/.git
rm -rf utils/.git
rm -rf file_manager/file/.git
rm -f .gitmodules

# Git komplett frisch aufsetzen BEVOR die Secrets hochgeladen werden
rm -rf .git
git init

# Remote sofort hinzufügen (Verhindert "no git remotes found")
git remote add l1b "$REMOTE_URL"
# Git Bash/GH CLI austricksen, damit er l1b als Standard erkennt
git remote rename l1b origin 2>/dev/null || git remote add origin "$REMOTE_URL"

# --- SCHRITT 2: GITIGNORE ABSICHERN ---
echo "🔒 Stelle sicher, dass .env und dieses Skript ignoriert werden..."
if [ ! -f .gitignore ]; then touch .gitignore; fi
for item in ".env" "deploy_all.sh" "upload_secrets.sh"; do
    if ! grep -q "^$item" .gitignore; then
        echo "$item" >> .gitignore
    fi
done

# --- SCHRITT 3: SECRETS HOCHLADEN ---
echo "⚙️  Lese .env ein und setze GitHub Secrets..."
count=0
while IFS='=' read -r key value || [ -n "$key" ]; do
    key=$(echo "$key" | xargs)
    [[ -z "$key" || "$key" =~ ^# ]] && continue

    # Anführungszeichen entfernen
    value="${value#\"}"
    value="${value%\"}"
    value="${value#\'}"
    value="${value%\'}"

    # --- NEU: Prüfen, ob der Wert ein lokaler Dateipfad ist ---
    if [[ -f "$value" ]]; then
        echo "📂 Erkenne Dateipfad für $key. Lese Inhalt von: $value..."
        # Lies den tatsächlichen Dateiinhalt in die Variable
        secret_content=$(cat "$value")
    else
        # Es ist ein ganz normaler Text-Wert
        secret_content="$value"
    fi

    echo "➡️  Hinzufügen zu GH Secrets: $key"
    # Sende den echten Inhalt (entweder Text oder Datei-Inhalt) an GitHub
    echo "$secret_content" | gh secret set "$key"

    if [ $? -eq 0 ]; then ((count++)); else echo "⚠️  Fehler bei $key"; fi
done < .env
echo "✅ $count Secrets erfolgreich zu GitHub hinzugefügt."
echo "--------------------------------------------------"

# --- SCHRITT 4: COMMIT & FORCE PUSH ---
echo "📤 Committe und starte Force-Push nach GitHub..."
git add .
git rm --cached .env 2>/dev/null

git commit -m "chore: flatten project and prepare cloud run deployment"

# Push über den korrigierten "origin" Remote
git push origin "$BRANCH_NAME" --force

# Remote wieder für dich lesbar auf l1b biegen, falls gewünscht
git remote rename origin l1b 2>/dev/null

echo "--------------------------------------------------"
echo "✅ PUSH ERFOLGREICH UND SECRETS GESETZT!"
echo "=================================================="