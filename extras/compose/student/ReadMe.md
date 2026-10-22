# Vorbereitung der Anwendung für Docker Compose

`app.toml` enthält die Konfiguration für die Student-Anwendung im gemeinsamen
Docker-Netz `acme-network`. Die Datei wird beim lokalen Start mit `uv run student`
nicht verwendet. Sie ist für den späteren App-Service aus Issue #43 vorbereitet;
ein Dockerfile (#42) und eine ausführbare Compose-Datei für diesen Service fehlen
noch. Image und Python-Version müssen zuerst feststehen.

Die Anwendung bindet im Container an `0.0.0.0:8000`. PostgreSQL ist dort unter
`postgres:5432`, Keycloak unter `https://keycloak:8443` erreichbar. `student` ist
der Compose-Projektname sowie der Datenbank-, Benutzer- und Realmname; der
Datenbank-Hostname bleibt `postgres`.

Die Dev-Einstellungen entsprechen dem lokalen Betrieb: Bei jedem App-Start
werden Datenbanktabellen und Testdaten sowie Keycloak-Benutzer außer `admin`
neu geladen. Die Konfiguration ist für die lokale Entwicklungsumgebung gedacht.

## Mounts für den späteren App-Service

Wie im Beispiel soll die Anwendung unter `/opt/app` mit einer dortigen `.venv`
installiert werden. `RESOURCES` in der folgenden Tabelle steht für
`/opt/app/.venv/lib/pythonX.Y/site-packages/student/config/resources`.
`X.Y` muss beim Erstellen der Compose-Datei durch die tatsächliche Python-Version
des Images ersetzt werden; es ist keine konfigurierte Umgebungsvariable.
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
im Beispiel zur Laufzeit gemountet. TLS-Prüfung bleibt aktiv; beim späteren
Containerlauf sind die Zertifikate für die internen Hostnamen zu prüfen.
Das Logverzeichnis muss für den Nonroot-Benutzer des Images schreibbar sein.

Für das Keycloak-Neuladen liest die Anwendung `/csv/student.csv`. PostgreSQL
liest seine drei CSV-Dateien dagegen selbst aus `/init/student/csv` im bereits
eingebundenen Volume `pg_init`. Dieses Volume benötigt der App-Container nicht.

## CLIENT_SECRET aus der lokalen Umgebung

Das Secret bleibt in der vorhandenen, ignorierten `.env` im Projektverzeichnis.
Es wird weder in `app.toml` noch in das Image kopiert. Für den späteren
Compose-Service ist folgende Übergabe vorgesehen:

```yaml
environment:
  CLIENT_SECRET: ${CLIENT_SECRET:?CLIENT_SECRET muss gesetzt sein}
```

Nach Fertigstellung der Compose-Datei wird sie aus diesem Verzeichnis mit
`docker compose --env-file ../../../.env up` gestartet. `--env-file` stellt die
Werte für die Compose-Interpolation bereit; erst `environment` übergibt das
Secret an den Container. Andere Werte der Root-`.env`, etwa `NVD_API_KEY`, werden
dadurch nicht an die Anwendung weitergereicht. Eine bereits gesetzte
Shell-Umgebungsvariable hat bei der Interpolation Vorrang.

## Noch zu prüfen, sobald das Image vorhanden ist

Der App-Service soll `../backend/compose.yml` einbinden, im gleichen Netzwerk
laufen, Port 8000 veröffentlichen und auf die Bereitschaft von PostgreSQL und
Keycloak warten. Die derzeitige Vorbereitung startet keine Dienste.
Danach sind Paketpfade, Mount-Berechtigungen, TLS-Verbindungen, Secret-Übergabe,
HTTPS-Erreichbarkeit und der gemeinsame Start im echten Container zu prüfen.
