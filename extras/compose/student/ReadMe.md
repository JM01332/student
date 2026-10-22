# Anwendung mit Docker Compose

`app.toml` enthält die Konfiguration für die Student-Anwendung im gemeinsamen
Docker-Netz `acme-network`. Die Datei wird beim lokalen Start mit `uv run student`
nicht verwendet. `compose.yml` bindet den Backend-Einstieg ein und startet
PostgreSQL, Keycloak und die Anwendung im Compose-Projekt `student`. Das Dockerfile
liegt im Projektverzeichnis und verwendet das offizielle Image `python:3.15-trixie`.

## Image bauen

Im Projektverzeichnis mit laufendem Docker Desktop (Linux-Container):

```powershell
docker build --tag student:local .
```

Build und Laufzeit verwenden dieselbe Python-3.15-Basis. uv 0.12.23 installiert
die Laufzeitabhängigkeiten aus `uv.lock` und das Paket ohne Editable-Modus.
Entwicklungs-, Dokumentations- und Lint-Abhängigkeiten werden nicht installiert.
Das Laufzeit-Image übernimmt nur die fertige `.venv`; die Anwendung läuft als
Benutzer `app` mit UID/GID 10000. `/opt/app/log` ist für ihn schreibbar.
Bei einem späteren Bind-Mount gelten die Berechtigungen des Host-Verzeichnisses.

`.dockerignore` beschränkt den Build-Kontext auf Quellcode und Build-Metadaten.
Der private TLS-Schlüssel und `.env` werden nicht ins Image kopiert.
Die öffentlichen Zertifikate, SQL-Dateien und die Standard-TOML werden als
Paketressourcen installiert. Der Tag `3.15-trixie` folgt den Python-3.15-Updates;
`PYTHON_IMAGE` kann beim Build auf einen konkreten Tag oder Digest gesetzt werden.

Nach erfolgreichem Build lässt sich der Interpreter ohne App-Start prüfen:

```powershell
docker run --rm --entrypoint python student:local --version
```

Der Image-Build als `student:local` und der Interpreter-Aufruf im Container
sind erfolgreich geprüft; das gebaute Image verwendet Python 3.15.1.
Die sechs Paketressourcen (TOML, drei Zertifikate und zwei SQL-Dateien) sind
im Image lesbar; UID/GID 10000 und Schreibzugriff auf `/opt/app/log` sind geprüft.
Privater TLS-Schlüssel und `.env` sind im Image nicht vorhanden.
Der App-Start mit deaktiviertem Daten-Neuladen ist erfolgreich geprüft. Für den App-Start
werden zusätzlich die unten beschriebenen Mounts, das Secret und die
Backend-Dienste benötigt; auch der gemeinsame Compose-Start ist erfolgreich geprüft.

Die Anwendung bindet im Container an `0.0.0.0:8000`. PostgreSQL ist dort unter
`postgres:5432`, Keycloak unter `https://keycloak:8443` erreichbar. `student` ist
der Compose-Projektname sowie der Datenbank-, Benutzer- und Realmname; der
Datenbank-Hostname bleibt `postgres`.

Die Dev-Einstellungen entsprechen dem lokalen Betrieb: Bei jedem App-Start
werden Datenbanktabellen und Testdaten sowie Keycloak-Benutzer außer `admin`
neu geladen. Die Konfiguration ist für die lokale Entwicklungsumgebung gedacht.

## Mounts des App-Service

Wie im Beispiel ist die Anwendung unter `/opt/app` mit einer dortigen `.venv`
installiert. `RESOURCES` in der folgenden Tabelle steht für
`/opt/app/.venv/lib/python3.15/site-packages/student/config/resources`.
Quellpfade gelten relativ zu diesem Verzeichnis.

| Quelle | Ziel im App-Container | Zugriff |
| --- | --- | --- |
| `./app.toml` | `RESOURCES/app.toml` | nur lesen |
| `../../../src/student/config/resources/tls/key.pem` | `RESOURCES/tls/key.pem` | nur lesen |
| `../postgres/init/student/csv/student.csv` | `/csv/student.csv` | nur lesen |
| `../../../log` | `/opt/app/log` | schreiben |

Das HTTPS-Zertifikat `tls/certificate.crt`, das PostgreSQL-Vertrauenszertifikat
`postgresql/server.crt`, das Keycloak-Vertrauenszertifikat
`keycloak/certificate.crt` sowie die SQL-Dateien unter `postgresql` müssen als
Paketressourcen im Image enthalten sein. Der private HTTPS-Schlüssel wird wie
im Beispiel zur Laufzeit gemountet. TLS-Prüfung bleibt aktiv; im abgeschlossenen
Smoke-Test wurden die TLS-Verbindungen zu den internen Backend-Hostnamen geprüft.
Das Logverzeichnis muss für den Nonroot-Benutzer des Images schreibbar sein.

Für das Keycloak-Neuladen liest die Anwendung `/csv/student.csv`. PostgreSQL
liest seine drei CSV-Dateien dagegen selbst aus `/init/student/csv` im bereits
eingebundenen Volume `pg_init`. Dieses Volume benötigt der App-Container nicht.

## CLIENT_SECRET aus der lokalen Umgebung

Das Secret bleibt in der vorhandenen, ignorierten `.env` im Projektverzeichnis.
Es wird weder in `app.toml` noch in das Image kopiert. Der
Compose-Service übergibt es explizit:

```yaml
environment:
  CLIENT_SECRET: ${CLIENT_SECRET:?CLIENT_SECRET muss gesetzt sein}
```

Die Compose-Datei wird aus diesem Verzeichnis mit
`docker compose --env-file ../../../.env up` gestartet. `--env-file` stellt die
Werte für die Compose-Interpolation bereit; erst `environment` übergibt das
Secret an den Container. Andere Werte der Root-`.env`, etwa `NVD_API_KEY`, werden
dadurch nicht an die Anwendung weitergereicht. Eine bereits gesetzte
Shell-Umgebungsvariable hat bei der Interpolation Vorrang.

## Geprüfter Containerbetrieb

Ein Container-Smoke-Test mit `student:local` und den laufenden Backend-Diensten
im Netzwerk `acme-network` war erfolgreich: Paketressourcen, Nonroot- und
Mount-Berechtigungen, App-Start mit Secret-Übergabe, Keycloak-Discovery mit TLS
sowie HTTPS-Liveness (`status: up`) und DB-Readiness (`db: up`).
Für die Prüfung waren beide Populate-Schalter in einer temporären
Konfigurationskopie deaktiviert. Der Prüfcontainer wurde anschließend entfernt;
die ursprüngliche `app.toml` blieb unverändert.

Bereits der App-Import initialisiert den `UserService` mit Keycloak-Admin-Anmeldung
und liest Client-/Rolleninformationen. Daher benötigt auch ein Start ohne
Daten-Neuladen das `CLIENT_SECRET`.
Der Start mit Daten-Neuladen und fachliche REST-/GraphQL-Aufrufe waren nicht
Teil dieser Prüfung.

## Gemeinsamer Start und Stopp

Voraussetzungen: Docker Desktop mit Linux-Containern, eingerichtete Backend-Volumes
und Student-Realm, gültiges `CLIENT_SECRET` in der Root-`.env`, vorhandener
TLS-Schlüssel sowie ein für UID/GID 10000 schreibbares Logverzeichnis.
Die Bind-Mounts für Dateien brechen bei fehlenden Quelldateien ab.
Port 8000 muss frei sein: eine lokale Student-App oder MkDocs vorher beenden.
Das Beispiel darf wegen der gemeinsam genutzten Container und Volumes nicht
parallel laufen. Bereits laufende Backend-Dienste im Projekt `student` werden
über denselben Compose-Einstieg verwaltet.

Vom Projektverzeichnis aus nur die Konfiguration prüfen (keine Secret-Ausgabe):

```powershell
docker compose --env-file .env -f extras/compose/student/compose.yml config --quiet
docker compose --env-file .env -f extras/compose/student/compose.yml config --services
```

Die Dienstliste enthält `postgres`, `keycloak` und `student`. Ein ungekürztes
`config` gibt auch das interpolierte Secret aus; für Prüfungen `--quiet` verwenden.

Start aus dem Projektverzeichnis:

```powershell
cd extras\compose\student
docker compose --env-file ../../../.env up --build -d
docker compose --env-file ../../../.env ps
```

**Beim Start werden gemäß `app.toml` DB-Tabellen/Testdaten und Keycloak-Benutzer
außer `admin` neu geladen.** Für einen Betrieb ohne Neuladen vorher beide
Populate-Schalter unter `[dev]` auf `false` setzen. Der App-Import benötigt
weiterhin die Keycloak-Anmeldung.

Die Anwendung wartet auf die vorhandenen Healthchecks von PostgreSQL und Keycloak.
Der bestehende Keycloak-Check prüft das Absenden der HTTP-Anfrage, wertet aber
keinen HTTP-Status aus; er garantiert daher noch keine erfolgreiche Anmeldung.
Der App-Healthcheck ruft alle 30 Sekunden `/health/readiness` über geprüftes HTTPS
auf und verlangt `db: up`; HTTP 200 allein genügt nicht. Er verwendet Python aus
dem Image und benötigt kein zusätzliches curl. Während der ersten 60 Sekunden
gilt eine Startfrist, danach führen drei Fehlversuche zu `unhealthy`.
Die App ist unter `https://localhost:8000` erreichbar.
Der feste Containername ist `student`. Nach einer Änderung des Containernamens
erstellt das nächste `up` den App-Container neu; dabei gelten erneut die
Populate-Schalter aus `app.toml`.

Im selben Ordner alle drei Dienste stoppen, Container behalten:

```powershell
docker compose --env-file ../../../.env stop
```

Container und Netzwerk entfernen, externe Backend-Volumes behalten:

```powershell
docker compose --env-file ../../../.env down
```

Für den vollständigen Stack diesen App-Einstieg verwenden. Der Backend-Einstieg
bleibt für den Betrieb mit einer lokal gestarteten App bestehen.

## Prüfstand

Die aufgelöste Compose-Konfiguration einschließlich der drei Dienste, relativen
Mount-/Build-Pfade, Secret-Übergabe und Startabhängigkeiten ist statisch geprüft.
Compose-Build und gemeinsamer Containerbetrieb sind erfolgreich geprüft.
PostgreSQL, Keycloak und die Anwendung mit festem Containernamen `student` zeigen
`healthy`. Der App-Healthcheck bestätigt HTTPS mit Zertifikatsprüfung und
DB-Readiness (`db: up`). Fachliche REST-/GraphQL-Tests im Compose-Betrieb und
eine separate Prüfung der neu geladenen Daten waren nicht Teil dieses Laufs.
Der oben beschriebene erfolgreiche separate Container-Smoke-Test bleibt gültig.
