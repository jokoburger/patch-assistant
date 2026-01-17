# Digitaler Patchday Assistent

Ein interaktives, webbasiertes Protokoll für IT-Systemadministratoren zur Dokumentation von Patchdays, Wartungsarbeiten und Updates.

Die Anwendung ersetzt statische Excel/Word-Protokolle durch einen geführten Assistenten, der den Sicherungs-, Update- und Test-Prozess strukturiert.

## 🚀 Features

*   **Workflow-Basiert**: Geführter Prozess von Backup über Updates bis hin zur Qualitätsprüfung.
*   **Persistenz**: Alle Eingaben (Texte, Checkboxen, neue Zeilen) werden automatisch in einer lokalen SQLite-Datenbank gespeichert.
*   **Dynamisch**:
    *   Systeme und Dienste können umbenannt werden.
    *   Neue Zeilen für Backup-Steps, Host-Updates oder Docker-Container können hinzugefügt werden.
*   **Reporting**: Generiert automatisch einen textbasierten Bericht für Ticketsysteme.
*   **Dockerized**: Einfache Bereitstellung via Docker Compose.

## 🛠️ Installation & Start

### Voraussetzung
*   Docker & Docker Compose installiert.

### Starten
Navigieren Sie in das Projektverzeichnis und starten Sie den Container:

```bash
docker-compose up -d --build
```

Die Anwendung ist anschließend unter **[http://localhost:8080](http://localhost:8080)** erreichbar.

### Daten-Speicherung
Die Daten werden im Unterordner `./data` in einer SQLite-Datenbank (`patchweb.db`) gespeichert. Dieser Ordner wird als Docker-Volume eingebunden, sodass die Daten auch nach einem Container-Neustart erhalten bleiben.

Um die Daten vollständig zurückzusetzen, nutzen Sie den "Daten zurücksetzen"-Link in der Seitenleiste oder löschen Sie die Datei `./data/patchweb.db`.

## 🏗️ Technologie-Stack

*   **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
*   **Backend**: Python (FastAPI)
*   **Datenbank**: SQLite (SQLAlchemy)
*   **Icons**: Phosphor Icons
*   **Charts**: Chart.js

## 📝 Lizenz
Open Source / Interne Nutzung.
