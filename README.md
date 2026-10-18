# Student

FastAPI-Appserver zur Verwaltung von Studierendendaten.

## Stand und Technik

Die FastAPI-Anwendung unter `src/student/` liest Studierende mit Adresse (1:1) und
Prüfungsleistungen (1:N) über SQLAlchemy aus PostgreSQL:

- `GET /rest/{id}`: ein Studierender anhand der ID
  mit ETag; passendes `If-None-Match` liefert HTTP 304 ohne Body
- `GET /rest?nachname=...&email=...`: Suche (Teil des Nachnamens bzw. Emailadresse,
  jeweils ohne Groß-/Kleinschreibung), mit Seiteninhalt und Metadaten;
  ohne Parameter die erste Seite mit bis zu fünf Studierenden
- `POST /rest`: neuen Studierenden mit Adresse und Prüfungsleistungen anlegen,
  Antwort 201 mit `Location`-Header
- `PUT /rest/{id}`: Studierenden ändern, nur mit passendem `If-Match`-Header;
  Antwort 204 mit neuem ETag
- `DELETE /rest/{id}`: Studierenden mit Adresse und Prüfungsleistungen löschen,
  Antwort 204
- `GET /health/liveness` und `GET /health/readiness`: Server bzw. Server und
  Datenbank bereit
- `QUERY /dev/db_populate`: Datenbank mit den Testdaten neu laden (nur im Dev-Modus)
- `GET /hello/`: Demo-Endpunkt
- `QUERY /auth/token`: Login mit JSON-Feldern `username` und `password`;
  Antwort mit `token`, `expires_in` und `rollen`

Wird nichts gefunden, antwortet der Server mit 404 im Format ProblemDetails
(`application/problem+json`, z.B. `{"title": "Not Found", "status_code": 404, ...}`).
Die Suchparameter werden in einem Pydantic-Modell gebündelt. Unbekannte
Query-Parameter bei `GET /rest` werden mit HTTP 422 abgewiesen.

Aufbau: Router → Service → Repository mit Dependency Injection, Entities für
SQLAlchemy, DTOs als Rückgabe des Service und Pydantic-Response-Models im Router.
Fehler wie `NotFoundError` wirft der Service, ein Exception-Handler in
`fastapi_app.py` macht daraus die HTTP-Antwort. Der Server läuft über HTTPS mit einem
selbstsignierten Zertifikat, die Datenbankverbindung ebenfalls über TLS.
Die Keycloak-Anbindung einschließlich Login und Rollenschutz für lesende REST-Endpunkte
sowie POST und PUT ist vorhanden; Rollenschutz für DELETE, GraphQL und ein Docker-Image
der Anwendung sind noch geplant.
Python und Abhängigkeiten werden mit uv verwaltet; Qualitätssicherung erfolgt
mit pytest, Ruff und ty, ergänzt um SonarQube und OWASP Dependency Check.

## Einrichtung

Voraussetzungen: Python >=3.15 und uv >=0.12.20, entsprechend dem FastAPI-Beispiel.
Die installierten Versionen vor der Einrichtung prüfen:

```powershell
python --version
uv --version
```

Python 3.15 unter Windows von <https://www.python.org/downloads/windows/> mit dem
**„Windows installer (64-bit)“** installieren, wie im FastAPI-Beispiel empfohlen.
Diese Builds sind digital signiert. Ist **Smart App Control** aktiv, blockiert Windows
dagegen das unsignierte Python, das `uv python install` herunterlädt („Eine
Anwendungssteuerungsrichtlinie hat diese Datei blockiert“).

Im Projektverzeichnis die virtuelle Umgebung mit diesem Python anlegen und alle
Abhängigkeiten einrichten:

```powershell
uv venv --python "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe"
uv sync --all-groups
```

Das Paket wird dabei aus `src/student/` installiert. Zur Laufzeit werden FastAPI,
Uvicorn, loguru, SQLAlchemy, psycopg, python-dotenv und python-keycloak benötigt,
für Tests und Hilfsskripte pytest, pytest-mock und httpx sowie Ruff und ty für die Codeprüfung.
`uv.lock` hält die aufgelösten Versionen fest.

Für OWASP Dependency Check wird eine lokale `.env` benötigt (siehe
[Sicherheits- und Codeanalyse](#sicherheits--und-codeanalyse)):

```powershell
Copy-Item .env.example .env
```

## Server starten

Vorher muss PostgreSQL laufen (siehe [PostgreSQL](#postgresql)). Gestartet wird
Uvicorn über `src/student/__main__.py`:

```powershell
uv run python -m student
```

Alternativ startet `uv run student` (Eintrag `student = "student:main"` in
`pyproject.toml`) dasselbe. Unter Windows mit Smart App Control wird die dafür von uv
erzeugte `student.exe` allerdings blockiert.

Im Dev-Modus (`[dev] db-populate = true` in `app.toml`) wird die Datenbank bei jedem
Start mit `drop.sql`, `create.sql` und den CSV-Testdaten neu geladen; im Log
erscheint dann `>>> Die DB wurde neu geladen <<<`. Nach Code-Änderungen den Server
neu starten, da Uvicorn geänderten Code nicht automatisch lädt.

Endpunkte: <https://127.0.0.1:8000/rest/1>, <https://127.0.0.1:8000/rest> und
<https://127.0.0.1:8000/rest?nachname=muster>. Da das Zertifikat
selbstsigniert ist, zeigt der Browser beim ersten Aufruf eine Warnung, die man für
die Entwicklung bestätigt. REST-Lesezugriffe, POST und PUT benötigen zusätzlich einen
Bearer-Token; ein direkter Browseraufruf ohne Authorization-Header ergibt 401.

Jede Response enthält Security-Header (HSTS, `nosniff`, `X-Frame-Options`,
Content-Security-Policy). Die Content-Security-Policy erlaubt nur Inhalte vom
eigenen Server; die Swagger-Oberfläche unter `/docs` lädt ihre Skripte aber von
einem CDN und bleibt deshalb im Browser leer. Die API-Beschreibung ist weiterhin
unter <https://127.0.0.1:8000/openapi.json> abrufbar; zum manuellen Testen dient
Bruno (siehe unten).

Beenden mit `Strg+C`. Solange der Browser noch eine Verbindung offen hält, wartet
Uvicorn bei „Shutting down“; dann den Tab schließen oder ein zweites Mal `Strg+C`
drücken.

## Konfiguration

Die Konfiguration liegt in `src/student/config/resources/app.toml` und wird beim
Start mit `tomllib` eingelesen:

- `[server]`: `host-binding` (Standard `127.0.0.1`) und `port` (Standard `8000`)
- `[tls]`: Dateinamen von `key` (Standard `key.pem`) und `certificate`
  (Standard `certificate.crt`) im Verzeichnis `resources/tls/`
- `[logger]`: `debug-level` für DEBUG-Ausgaben in Konsole und `log/app.log`
- `[db]`: Zugangsdaten für PostgreSQL (`host = "localhost"` für die App auf dem
  Host-Rechner), `password-admin` für den Superuser beim Neuladen,
  `log-statements` zum Protokollieren der SQL-Anweisungen, `connect-timeout`
  (Standard 2 Sekunden) als maximale Wartezeit beim Verbindungsaufbau
- `[dev]`: `db-populate` lädt die Datenbank beim Start neu
- `[keycloak]`: `schema`, `host` und `port` (Standard `https`, `localhost`, `8843`),
  `realm` (`student`), `client-id` (`student-client`) und `certificate`
  (`certificate.crt` unter `resources/keycloak/`) für die TLS-Prüfung

Auskommentierte Einträge verwenden den Standardwert. Das Paket `student.config`
stellt die Werte für die Anwendung bereit. Der private Schlüssel ist bewusst im
Repository, da er nur für die lokale Entwicklung dient.

## PostgreSQL

Der Datenbankserver läuft als Docker-Container mit TLS (Datenbank, DB-User und Schema
jeweils `student`). Die einmalige Einrichtung pro Rechner und der tägliche Start sind
in [extras/compose/postgres/ReadMe.md](extras/compose/postgres/ReadMe.md) beschrieben.
Täglicher Start:

```powershell
cd extras\compose\postgres
docker compose up
```

Tabellen: `src/student/config/resources/postgresql/create.sql` (und `drop.sql`),
Testdaten: `extras/compose/postgres/init/student/csv` (5 Studierende mit den IDs 1,
20, 30, 40 und 50). Die Anwendung verbindet sich mit `sslmode=verify-full` und
vertraut dem DB-Zertifikat über `src/student/config/resources/postgresql/server.crt`.

## Keycloak

Compose-Konfiguration, TLS-Dateien und die Anleitung für vorhandene oder neue
lokale Installationen liegen unter
[extras/compose/keycloak](extras/compose/keycloak/ReadMe.md).
Die Infrastruktur verwendet wie das Beispiel PostgreSQL und die externen Volumes
`kc_data` und `kc_tls`. Vorhandene Beispiel-Realms werden nicht verändert.
Der lokale Realm `student` mit Client `student-client`, den Client-Rollen
`admin` und `student` sowie zwei Testzugängen ist eingerichtet. Die Anleitung
enthält die Einrichtungsschritte und einen Prüfaufruf für Discovery,
Token-Ausstellung und Rollen. Das Client Secret liegt ausschließlich in der
lokalen `.env` (Vorlage: `.env.example`). Die OIDC-Anbindung der Anwendung ist
vorhanden; lesende REST-Endpunkte, POST und PUT prüfen bereits Bearer-Token und Rollen.

Die Anwendung stellt bereits `keycloak_config` mit diesen Verbindungsdaten bereit.
`CLIENT_SECRET` wird aus der Prozessumgebung gelesen, ersatzweise aus `.env` im
aktuellen Arbeitsverzeichnis; die Anwendung daher aus dem Projektverzeichnis starten.
Das Secret wird nicht in der Konfigurationsdarstellung ausgegeben. Ohne Secret
bleibt das Feld vorerst leer, damit Unit-Tests und der bisherige App-Betrieb ohne
Keycloak-Zugang möglich bleiben. Die Konfiguration allein baut keine Verbindung auf.
Das öffentliche Zertifikat unter `src/student/config/resources/keycloak/` entspricht
dem Compose-Zertifikat. `TokenService` verwendet die Konfiguration einschließlich
dieses Zertifikats für die TLS-Prüfung. `token(username, password)` fordert Access
und Refresh Token an und gibt die Keycloak-Antwort einschließlich Ablaufangaben
unverändert zurück. Fehlende Zugangsdaten (`None`) und die Keycloak-Fehler
`KeycloakAuthenticationError` bzw. `KeycloakOperationError` ergeben `LoginError`.
Leere Zeichenketten und ein fehlendes Client Secret werden beim Token-Aufruf
durch Keycloak geprüft. Passwörter und Tokens werden nicht protokolliert.
Die Unit-Tests ersetzen den OIDC-Client durch Mocks und benötigen keinen Server.
Die Security-Modelle `User` und `Role` sind als Grundlage für die Token-Auswertung
vorhanden. `User` enthält Benutzername, Email, Vorname, Nachname und Rollen;
das optionale Passwort ist von der Objektdarstellung ausgeschlossen. `Role`
definiert `ADMIN` und `STUDENT`, passend zu den Keycloak-Client-Rollen.
`TokenService.get_user_from_token()` verwendet `decode_token` mit dessen
standardmäßig aktivierter Validierung und übernimmt die Benutzer-Claims sowie
die Rollen des konfigurierten Clients in `User`. JWT-Fehler (`JWException`) und
Auswertungsfehler (`KeyError`, `TypeError`, `ValueError`) ergeben `AuthorizationError`.
Unbekannte Rollen werden wie im Beispiel abgelehnt; eine leere Rollenliste ist
zulässig. Tokens und decodierte Benutzerdaten werden nicht protokolliert.
`TokenService.get_user_from_request()` liest den `Authorization`-Header und
übergibt den enthaltenen Bearer-Token an die bestehende Token-Auswertung.
Das Schema wird unabhängig von Groß-/Kleinschreibung erkannt; Whitespace wird
wie im Beispiel mit `split()` behandelt. Fehlende Header, ein anderes Schema
oder eine von zwei abweichende Anzahl Bestandteile ergeben `AuthorizationError`.
Auch Authorization-Header werden nicht protokolliert.
`QUERY /auth/token` nimmt `username` und `password` als JSON-Objekt entgegen.
Der Login-Router fordert ein Token an und wertet es mit `get_user_from_token`
aus. Die Antwort enthält ausschließlich `token` (Access Token), `expires_in`
und `rollen`; das Refresh Token wird nicht ausgegeben. Fehlender oder ungültiger
JSON-Body sowie fehlende/zusätzliche Felder ergeben 401 ohne Body statt 422.
Wie im Beispiel erfolgt keine zusätzliche Typvalidierung der Dataclass-Felder.
`LoginError` und `AuthorizationError` werden als 401 mit ProblemDetails beantwortet.
Der TokenService wird bei Bedarf erzeugt und wiederverwendet. Für echte Logins
muss Keycloak mit dem Student-Realm laufen und `CLIENT_SECRET` gesetzt sein.
Die Router-Tests ersetzen den Service und benötigen keine laufenden Dienste.
`RolesRequired` steht als FastAPI-Dependency für die Rollenprüfung bereit.
Bei einer einzelnen Rolle muss diese vorhanden sein; bei einer Rollenliste
genügt eine Übereinstimmung. Eine leere Anforderungsliste erlaubt keinen Zugriff.
Fehlende Rollen ergeben HTTP 403, ungültige Authentifizierung über den bestehenden
Handler HTTP 401. Nur bei erfolgreicher Prüfung wird der Benutzer unter
`request.state.current_user` abgelegt. Benutzerdaten werden nicht protokolliert.
Folgende REST-Endpunkte verlangen einen gültigen Bearer-Token:

- `GET /rest/{id}`: Rolle `admin` oder `student`
- `GET /rest`: Rolle `admin`
- `PUT /rest/{id}`: Rolle `admin` oder `student`
- `POST /rest`: Rolle `admin` (abweichend vom ungeschützten POST im Beispiel)

Fehlende oder ungültige Authentifizierung ergibt 401, eine fehlende Rolle 403.
Auch eine Antwort mit 304 setzt erfolgreichen Datensatzzugriff voraus.
`StudentService.find_by_id` prüft den Benutzer aus dem Token: `admin` darf jeden
Datensatz lesen, `student` nur bei exakt übereinstimmendem `username`. Fremde
und nicht vorhandene IDs ergeben für `student` gleichermaßen 403 mit
ProblemDetails; für `admin` bleibt eine unbekannte ID bei 404.
PUT prüft wie im Beispiel ausschließlich die Rolle, nicht den Datensatzbesitz:
Auch `student` kann fremde Datensätze ändern.
Als nächstes kleines Paket ist der REST-Rollenschutz für DELETE vorgesehen.
DELETE und der Dev-Endpunkt sind weiterhin ungeschützt.

## Manuelle Tests mit Bruno

Die Bruno-Collection liegt in `extras/bruno/student` (OpenCollection-Format wie im
FastAPI-Beispiel). In Bruno (`C:\Zimmermann\Bruno\Bruno.exe`) über
*Open Collection* den Ordner `extras\bruno\student` öffnen. Da das Zertifikat
selbstsigniert ist, unter *Preferences > General* die Option
*SSL/TLS Certificate Verification* deaktivieren.

Die Collection hat die Ordner *Dev*, *Hello*, *Health* und *REST* (mit *Token*,
*Suche mit ID*, *Suche mit Suchparameter*, *Neu anlegen*, *Aendern* und *Loeschen*).
Für den Login müssen PostgreSQL, Keycloak mit Student-Realm und die Anwendung
laufen; `CLIENT_SECRET` muss für die Anwendung gesetzt sein.

1. In Bruno das Environment *student* auswählen. Es enthält `username = admin`
   und die Secret-Variable `password` ohne gespeicherten Wert.
2. Im Environment das Passwort des lokalen Keycloak-Benutzers `admin` bei
   `password` eintragen, die Markierung *Secret* beibehalten und *Save* wählen.
   Bruno speichert Secret-Werte lokal außerhalb der Collection.
3. Unter *REST > Token* den Request *Token als admin* ausführen. Er ruft
   `QUERY /auth/token` auf und übernimmt bei Erfolg `token` als Laufzeitvariable
   `accessToken`. Die vorhandenen REST-GET-, POST- und PUT-Requests verwenden diese
   automatisch im Bearer-Header. Vor jedem Login wird der bisherige Laufzeitwert geleert,
   damit ein fehlgeschlagener Login keinen alten Token weiterverwendet.
4. Danach einzelne REST-Requests ausführen. Nach Ablauf des Tokens (30 Minuten)
   oder nach einem Bruno-Neustart erneut einloggen. Tokens nicht als feste
   Collection- oder Environment-Werte speichern.

Bei *Run* auf der ganzen Collection zuerst das Environment *student* auswählen.
Die Requests müssen nacheinander in der gespeicherten Reihenfolge laufen, nicht
parallel. Beim Lauf nur des REST-Ordners vorher unter *Dev* die Datenbank neu laden.
Alle HTTP-Requests haben collectionweit eindeutige Sequenznummern (1–33).
Damit ergibt sowohl die Sortierung innerhalb der Ordner als auch die Sortierung
einer flachen Request-Liste dieselbe Reihenfolge. Neue Requests entsprechend
einsortieren und die nachfolgenden Sequenznummern anpassen.
Der Lauf der ganzen Collection lädt zunächst die Datenbank neu und führt innerhalb von *REST* den Login
vor den Lese- und Schreibtests aus. Die Variable `baseUrl` steht weiterhin in
`opencollection.yml`. Für den Login über die Anwendung wird kein Client Secret
in Bruno benötigt.

Schreibende Requests verändern die Testdaten: „Neuer Student“, „Vorhandenen Student
aendern“ und „Vorhandene ID 50 loeschen“ klappen jeweils nur einmal. Beim Ausführen
einzelner Requests deshalb vorher im Ordner *Dev* „DB neu laden“ ausführen; sonst
folgt z.B. 422 mit „Existierende Email“. Ein Lauf der ganzen Collection beginnt
automatisch mit diesem Request.

## Tests und Codeprüfung

Es gibt zwei Arten von Tests, wie im FastAPI-Beispiel:

- **Unit-Tests** (`tests/unit`) brauchen weder Server noch Datenbank und laufen auch
  in der CI.
- **Integrationstests** (`tests/integration`) schicken mit httpx echte
  HTTPS-Requests an den laufenden Server. Vorher Keycloak, PostgreSQL und den Server
  (`uv run python -m student`) starten; sonst bricht der Testlauf mit einem Hinweis ab. Sie
  laufen nur lokal. Zusätzlich `STUDENT_TEST_TOKEN` in der Prozessumgebung mit
  einem aktuellen Admin-Access-Token aus `QUERY /auth/token` setzen. Die Fixture
  prüft den Zugriff vor dem automatischen Neuladen der Datenbank und bricht bei
  fehlendem oder abgelehntem Token ab. Token weder speichern noch committen.

```powershell
uv run pytest tests/unit          # nur Unit-Tests
uv run pytest                     # alle Tests, Server muss laufen
uv run ruff check --preview src tests
uv run ruff format --preview --check src tests
uv run ty check src tests
```

Meldet Windows bei `uv run pytest` „Eine Anwendungssteuerungsrichtlinie hat diese
Datei blockiert“, blockiert die Anwendungssteuerung (z.B. Smart App Control) die
lokal erzeugte, unsignierte `pytest.exe`. Gleichwertig ist dann der Aufruf über den
Python-Interpreter, z.B. `uv run python -m pytest tests/unit`. Wird auch `python`
selbst blockiert, wurde die `.venv` mit einem unsignierten Python angelegt; dann wie
unter [Einrichtung](#einrichtung) beschrieben mit Python von python.org neu anlegen.

Ruff verwendet das Regelset aus dem FastAPI-Beispiel (`[tool.ruff.lint]` in
`pyproject.toml`), unter anderem mit Regeln für Sicherheit, Docstrings und
Import-Sortierung. Die Prüfungen vor jedem Push lokal ausführen, da die CI sonst
fehlschlägt.

Unit-Tests in `tests/unit` testen einzelne Klassen wie den Service mit Mocks
(`pytest-mock`) statt echter Abhängigkeiten.

## Continuous Integration

Der Workflow [CI](.github/workflows/ci.yml) führt bei Push und Pull Request auf
GitHub die Unit-Tests, Ruff, die Formatprüfung und ty aus. Die Integrationstests
brauchen Server und Datenbank und laufen deshalb nur lokal. Er läuft auf Ubuntu
mit uv 0.12.23 und Python `"3.15"` mit `allow-prereleases: true`. Solange es
kein finales Python 3.15 gibt, wird der neueste Release Candidate verwendet,
danach automatisch die finale Version.

`uv sync --locked --all-groups` installiert die Abhängigkeiten aus `uv.lock`
und bricht ab, falls die Lockdatei nicht zur Projektkonfiguration passt.
Auch die Prüfungen verwenden `uv run --locked`. Externe Dienste und Secrets
sind für die Unit-Tests nicht erforderlich.

Die Einrichtung orientiert sich an der
[offiziellen uv-Anleitung für GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/).
Die verwendeten Actions sind auf Commit-SHAs festgelegt. Ergebnisse erscheinen
nach dem Push im GitHub-Reiter **Actions** und beim Pull Request unter den Checks.

## Sicherheits- und Codeanalyse

### Abhängigkeiten prüfen

```powershell
uv tree --outdated --all-groups --depth=1
uv audit
```

`uv tree --outdated` zeigt direkte Abhängigkeiten mit neueren Versionen,
`uv audit` gleicht alle Pakete aus `uv.lock` mit bekannten Sicherheitslücken ab.

### SonarQube

Der SonarQube-Server läuft als Docker-Container
([compose.yml](extras/compose/sonarqube/compose.yml)); die Daten liegen unter
`C:/Zimmermann/volumes/sonarqube`:

```powershell
cd extras\compose\sonarqube
docker compose up
```

Beim ersten Start unter <http://localhost:9000> mit `admin`/`admin` anmelden, das
Passwort ändern und unter *My Account > Security*
(<http://localhost:9000/account/security>) einen *Global Analysis Token* erzeugen.
Jeder nutzt seinen eigenen lokalen Server und Token. Der Token steht deshalb nicht
in `sonar-project.properties`, sondern als Windows-Umgebungsvariable:

```powershell
[Environment]::SetEnvironmentVariable("SONAR_TOKEN", "<Token>", "User")
```

Danach VS Code bzw. das Terminal neu starten. Die Analyse startet man in einem
zweiten Terminal im Projektverzeichnis; das Ergebnis erscheint unter
<http://localhost:9000> im Projekt `student`:

```powershell
uv run python sonar-scanner.py
```

Herunterfahren mit `docker compose down` im Verzeichnis `extras\compose\sonarqube`.

### OWASP Dependency Check

OWASP Dependency Check gleicht die installierten Pakete mit der NVD-Datenbank ab.
Dafür wird ein eigener API-Key benötigt
(<https://nvd.nist.gov/developers/request-an-api-key>), der in der lokalen `.env`
als `NVD_API_KEY` eingetragen wird. `.env` ist in `.gitignore`; `.env.example`
dient als Vorlage.

```powershell
uv run extras/dependency-check.py
```

Der Report wird als `dependency-check-report.html` im Projektverzeichnis abgelegt.
Die Python-Analyzer sind bei Dependency Check experimentell und werden im Skript
mit `--enableExperimental` aktiviert; ohne diese Option werden keine Python-Pakete
geprüft. Bekannte Fehlalarme stehen mit Begründung in
[extras/suppression.xml](extras/suppression.xml).

## Zusammenarbeit

Die Aufgaben werden als Issues im
[GitHub Project](https://github.com/users/JM01332/projects/1) geplant und verteilt.

Gearbeitet wird nach der `VORGEHENSWEISE.md` aus dem FastAPI-Beispiel.
Abgeschlossen sind die Abschnitte „Elementare Infrastruktur und einfacher Server“
(Endpunkt, HTTPS, Konfiguration mit TOML) und „Codeanalyse, Formatierung,
Typprüfung und Sicherheit“ (Ruff, ty, CI, uv audit, SonarQube, OWASP Dependency
Check) sowie „Infrastruktur“ (Schichten Router → Service → Repository mit
Dependency Injection, gebündelte Router, gzip, Security-Header).

Im Abschnitt „REST-Schnittstelle, DB-Zugriff, Validierung, Bruno und Testen“ sind
erledigt: Logging mit loguru, Pfad- und Query-Parameter, OR-Mapping mit SQLAlchemy
und PostgreSQL einschließlich Fetch-Join, Neuladen der DB im Dev-Modus, Bruno,
Unit-Tests mit Mocks, Integrationstests mit pytest und httpx sowie CI, Health-Router
und Fehlerbehandlung mit `NotFoundError` und ProblemDetails, Pydantic-Response-Models
sowie ETag und `If-None-Match` für GET nach ID und ein Pydantic-Modell für
die Suchparameter `nachname` und `email` sowie REST-Pagination mit `page` und `size`,
POST mit Validierung. Aus „Weitere Funktionalitäten“ sind PUT mit `If-Match`
(Vermeidung von „Lost Updates“) und DELETE umgesetzt.

`GET /rest/{id}` liefert die Version als ETag (z.B. `"0"`). Bei einem passenden
`If-None-Match: "0"` antwortet der Server mit 304 ohne Body und mit ETag.
Bei anderer Version oder ungültigem Header folgt 200 mit JSON und aktuellem ETag.
Die Header-Auswertung entspricht dem Beispiel: ein einzelner ganzzahliger
Versionswert in doppelten Anführungszeichen. ETag-Listen, `*` und schwache ETags
(`W/"0"`) werden in diesem Paket nicht ausgewertet.

`POST /rest` legt mit der Rolle `admin` neue Studierende an. Der Request-Body wird
mit Pydantic validiert (`router/student_model.py`, `student_update_model.py`, `adresse_model.py`,
`pruefungsleistung_model.py`): Matrikelnummer mit 6 Ziffern, Vor- und Nachname mit
großem Anfangsbuchstaben (auch Doppelnamen wie „Müller-Lüdenscheidt“), gültige Email,
PLZ mit 5 Ziffern, nur zulässige Notenstufen und Semester wie `WS 2026/27` oder
`SS 2026`. Ungültige Daten liefern HTTP 422 mit den betroffenen Feldern, eine bereits
vorhandene Email oder Matrikelnummer HTTP 422 mit ProblemDetails. Bei Erfolg antwortet
der Server mit 201 ohne Body und dem `Location`-Header zum neuen Datensatz.

`PUT /rest/{id}` ändert mit der Rolle `admin` oder `student` Matrikelnummer,
Nachname, Vorname und Email
(`router/student_update_model.py`); Adresse und Prüfungsleistungen bleiben
unverändert. Der Client schickt die gelesene Version als `If-Match: "0"` mit
(optimistische Synchronisation):

- ohne `If-Match`: 428 Precondition Required
- `If-Match` ohne Anführungszeichen oder ohne Zahl: 412 Precondition Failed
- veraltete Version, weil inzwischen jemand anderes geändert hat: 412 mit
  „Veraltete Version: …“
- nicht vorhandene ID: 404; Email oder Matrikelnummer eines anderen
  Studierenden bzw. ungültige Daten: 422
- Erfolg: 204 ohne Body mit dem neuen ETag, z.B. `"1"`

Alle Fehler kommen als ProblemDetails (bis auf die Validierungsfehler von
Pydantic). Bekannte Einschränkung wie im Beispiel: Schickt ein PUT genau die
gespeicherten Daten, führt SQLAlchemy kein UPDATE aus und die Version in der DB
bleibt gleich. Die Antwort meldet trotzdem die um 1 erhöhte Version, da der Service
sie nach dem COMMIT selbst hochzählt. Ein folgendes PUT mit diesem ETag
funktioniert, ein GET mit `If-None-Match` liefert dann aber 200 statt 304.

`DELETE /rest/{id}` löscht den Studierenden; Adresse und Prüfungsleistungen werden
über `cascade="save-update, delete"` in der Entity mitgelöscht. Der Server antwortet
wie im Beispiel immer mit 204, auch wenn es die ID nicht gibt: DELETE ist
idempotent, danach existiert der Datensatz in jedem Fall nicht.
DELETE wird später mit Keycloak auf bestimmte Rollen beschränkt.

Im Dev-Modus lädt `QUERY /dev/db_populate` die Datenbank neu. Die Integrationstests
rufen den Endpunkt vor jedem Testlauf auf, damit sie immer mit denselben Testdaten
beginnen; in Bruno steht er als erster Request im Ordner *Dev*. Wie im Beispiel wird
der Endpunkt später mit Keycloak auf die Rolle Admin beschränkt.

**Offen, in dieser Reihenfolge:** Keycloak, GraphQL,
Docker sowie Dokumentation und Lasttests (siehe GitHub Project).

Datenmodell: Student mit einer 1:1-Beziehung zu Adresse und einer 1:N-Beziehung zu
Prüfungsleistungen (siehe `src/student/entity`).

Das Repository unterstützt bereits optionale Pagination, z.B. mit
`Pageable(number=0, size=2)`: Seiten beginnen bei 0; `size=0` oder kein `Pageable` liefert
alle Treffer. Die Abfrage sortiert nach ID und begrenzt die Treffer mit SQL-`LIMIT`
und `OFFSET`. `StudentService.find` nimmt ebenfalls optional `Pageable` entgegen
und gibt es an das Repository weiter. Der Service liefert weiterhin eine Liste
von DTOs und wirft bei einem leeren Ergebnis `NotFoundError`, auch bei einer
leeren Seite.

`GET /rest?page=1&size=2` liefert die zweite Seite mit höchstens zwei Treffern
im Feld `content` der JSON-Seitenantwort. Ohne Seitenparameter gelten `page=0`
und `size=5` wie im Beispiel.
Erlaubt sind `page >= 0` und `0 <= size <= 100`; `size=0` liefert unabhängig
von `page` alle Treffer. Beide Suchfilter lassen sich mit Pagination kombinieren.
Ungültige Werte führen zu HTTP 422, eine leere Seite zu HTTP 404 mit ProblemDetails.
Das Feld `page` enthält `size`, `number`, `total_elements` und `total_pages`.

`StudentRepository.count` ermittelt bereits die Gesamtanzahl mit denselben
optionalen Suchfiltern wie `find`, einschließlich kombinierter Filter. Die
SQL-Zählabfrage zählt Studierende ohne Joins und unabhängig von der Pagination;
ohne Treffer liefert sie 0. `StudentService.count(nachname, email)` stellt diese
Zählung mit eigener Session-Verwaltung bereit und liefert ebenfalls 0 ohne
`NotFoundError`. Der Router nutzt diese Zählung für die Gesamtanzahl der
gefilterten Treffer.

Die REST-Suche verwendet folgende Pydantic-Antwortmodelle:
`StudentPageModel` enthält `content` mit den Studierendendaten und `page` mit
`size`, `number` (nullbasiert), `total_elements` und `total_pages`.
Die Struktur entspricht dem FastAPI-Beispiel. `PageMetaModel.from_pageable`
berechnet die Seitenanzahl aus Pagination und Gesamtanzahl mit Aufrundung.
Ohne Treffer ergeben sich bei positiver Seitengröße 0 Seiten; `size=0` ergibt
wie im Beispiel stets eine unbegrenzte Seite. Größe und angefragte Seitennummer
werden unverändert übernommen. Suchparameter und Pagination einschließlich
Seitenmetadaten sind damit abgeschlossen. Clients lesen die Treffer nun aus
`content` statt aus einer JSON-Liste auf oberster Ebene.
