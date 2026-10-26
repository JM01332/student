# Student

FastAPI-Appserver zur Verwaltung von Studierendendaten (Aufgabe 1 im Modul
Softwareengineering, Hochschule Karlsruhe). Vorbild ist das FastAPI-Beispielprojekt
„Patient“; Abweichungen davon sind [unten gesammelt](#abweichungen-vom-beispielprojekt).

## Überblick

| Bereich | Technik |
|---|---|
| Sprache, Projekt | Python 3.15, uv |
| Web | FastAPI mit REST und GraphQL (Strawberry), Validierung mit Pydantic |
| Datenbank | PostgreSQL mit TLS, OR-Mapping mit SQLAlchemy |
| Security | Keycloak (OIDC/OAuth 2) über python-keycloak, HTTPS, Security-Header |
| Tests | pytest (Unit und Integration), Bruno, Locust |
| Qualität | Ruff, ty, GitHub Actions, uv audit, SonarQube, OWASP Dependency Check |
| Betrieb, Doku | Docker und Docker Compose, MkDocs |

**Aufbau** (`src/student/`): `router` → `service` → `repository` mit Dependency
Injection, `entity` für SQLAlchemy, `graphql_api`, `security`, `config`. Der Service
gibt DTOs zurück, der Router Pydantic-Response-Models. Fehler wie `NotFoundError`
wirft der Service; Exception-Handler in `fastapi_app.py` machen daraus
ProblemDetails (`application/problem+json`).

**Datenmodell:** Student mit Adresse (1:1) und Prüfungsleistungen (1:N).
Tabellen in `src/student/config/resources/postgresql/create.sql`, Testdaten in
`extras/compose/postgres/init/student/csv` (5 Studierende mit den IDs 1, 20, 30,
40 und 50).

**Stand:** Alle Funktionen sind umgesetzt

## Schnellstart

Voraussetzungen: Python ≥ 3.15 und uv ≥ 0.12.20, Docker Desktop.
Python unter Windows mit dem **„Windows installer (64-bit)“** von
<https://www.python.org/downloads/windows/> installieren (signiert; ein mit
`uv python install` geholtes Python blockiert Smart App Control).

```powershell
uv venv --python "$env:LOCALAPPDATA\Programs\Python\Python315\python.exe"
uv sync --all-groups
Copy-Item .env.example .env      # CLIENT_SECRET und NVD_API_KEY eintragen
```

Einmalige Einrichtung von PostgreSQL und Keycloak:
[extras/compose/postgres](extras/compose/postgres/ReadMe.md) und
[extras/compose/keycloak](extras/compose/keycloak/ReadMe.md).
Das Beispielprojekt "patient" nutzt dieselben Container- und Volume-Namen, deshalb nie
beide gleichzeitig starten.

Täglicher Start, PostgreSQL und Keycloak im Compose-Projekt `student`:

```powershell
cd extras\compose\backend
docker compose up -d          # stoppen: docker compose stop bzw. down
cd ..\..\..
uv run python -m student      # Server unter https://127.0.0.1:8000
```

Der Server lädt im Dev-Modus beim Start die DB und die Keycloak-Benutzer neu
(`>>> Die DB wurde neu geladen <<<` im Log). Geänderten Code lädt Uvicorn nicht
automatisch: Server neu starten. Beenden mit `Strg+C`; hält ein Browser-Tab die
Verbindung offen, den Tab schließen oder ein zweites Mal `Strg+C` drücken.

Das Zertifikat ist selbstsigniert (Browser-Warnung für die Entwicklung bestätigen),
der private Schlüssel liegt bewusst im Repository. Wegen der
Content-Security-Policy bleiben `/docs` (Swagger) und GraphiQL leer; die
API-Beschreibung liefert `/openapi.json`, getestet wird mit Bruno.

## REST-Schnittstelle

| Methode und Pfad | Rolle | Beschreibung |
|---|---|---|
| `GET /rest/{id}` | admin, student | ein Studierender mit ETag; `student` nur der eigene Datensatz |
| `GET /rest?nachname=&email=&page=&size=` | admin | Suche mit Pagination |
| `POST /rest` | admin | neu anlegen, auch als Keycloak-Benutzer |
| `PUT /rest/{id}` | admin, student | ändern, nur mit `If-Match` |
| `DELETE /rest/{id}` | admin, student | löschen mit Adresse und Prüfungsleistungen |
| `QUERY /auth/token` | – | Login mit `username` und `password` |
| `QUERY /dev/db_populate` | admin | DB neu laden (nur Dev-Modus) |
| `QUERY /dev/keycloak_populate` | admin | Keycloak-Benutzer neu laden (nur Dev-Modus) |
| `GET /health/liveness`, `/health/readiness` | – | Server bzw. Server und DB bereit |
| `GET /hello/` | – | Demo |

Fehlende oder ungültige Tokens ergeben 401, eine fehlende Rolle 403.

- **GET nach ID:** Die Version kommt als ETag (z.B. `"0"`); passt `If-None-Match`,
  folgt 304 ohne Body. Für `student` ergeben fremde und nicht vorhandene IDs
  gleichermaßen 403, für `admin` eine unbekannte ID 404.
- **Suche:** `nachname` (Teil, ohne Groß-/Kleinschreibung) und `email`, kombinierbar.
  Standard `page=0`, `size=5`; erlaubt `page ≥ 0` und `0 ≤ size ≤ 100`, `size=0`
  liefert alle Treffer. Antwort `{content: [...], page: {size, number,
  total_elements, total_pages}}`. Unbekannte Parameter oder ungültige Werte
  ergeben 422, keine Treffer bzw. eine leere Seite 404.
- **POST:** Pydantic prüft Matrikelnummer (6 Ziffern), Namen mit großem
  Anfangsbuchstaben (auch Doppelnamen wie „Müller-Lüdenscheidt“), Email, PLZ
  (5 Ziffern), zulässige Notenstufen und Semester wie `WS 2026/27` oder `SS 2026`.
  Ungültige Daten ergeben 422 mit den Feldern, eine vorhandene Email,
  Matrikelnummer oder ein vorhandener Benutzername 422 mit ProblemDetails, Erfolg
  201 mit `Location`-Header.
- **PUT** ändert Matrikelnummer, Name, Vorname und Email. Ohne `If-Match` folgt 428,
  bei ungültigem Format oder veralteter Version 412, bei unbekannter ID 404, Erfolg
  204 mit neuem ETag.
- **DELETE** antwortet immer mit 204, auch für unbekannte IDs (idempotent).

## GraphQL

Endpunkt `POST /graphql` mit Strawberry („Code-first“), z.B.
`{ student(studentId: "20") { nachname email adresse { ort } } }`:

- Queries `student(studentId)` und `studenten(suchparameter)`: unbekannte ID ergibt
  `null`, die Suche ohne Rolle `admin` eine leere Liste. Fehler wie ein fehlendes
  Token erscheinen unter `errors` (HTTP 200).
- Mutation `create(studentInput)` (nur admin) mit denselben Pydantic-Regeln wie
  POST, Ergebnis die neue `id`.
- Mutation `login(username, password)` mit `token`, `expiresIn` und `roles`.

Das Token kommt wie bei REST aus dem `Authorization`-Header. Wie im Beispiel
werden Services und `UserService` beim Laden von `graphql_api/schema.py` erzeugt;
der `UserService` verbindet sich dabei mit Keycloak (ohne Keycloak, z.B. in der CI,
wird nur ein Fehler geloggt).

## Konfiguration

`src/student/config/resources/app.toml`; auskommentierte Einträge verwenden den
Standardwert:

| Abschnitt | Inhalt |
|---|---|
| `[server]` | `host-binding` (`127.0.0.1`), `port` (`8000`) |
| `[tls]` | Schlüssel und Zertifikat unter `resources/tls/` |
| `[logger]` | `debug-level`: DEBUG-Ausgaben in Konsole und `log/app.log` |
| `[db]` | Zugangsdaten, `host` (`localhost`), `password-admin` für das Neuladen, `log-statements`, `connect-timeout` (2 s) |
| `[keycloak]` | `host`/`port` (`localhost:8843`), `realm`, `client-id`, Zertifikat, `admin`/`admin-password` für die Admin-API, `csv` mit den Testbenutzern |
| `[graphql]` | `graphiql-enabled` |
| `[dev]` | `db-populate`, `keycloak-populate`: beim Start neu laden |

## Keycloak

Realm `student`, Client `student-client` mit den Client-Rollen `admin` und
`student`; Einrichtung siehe [Keycloak-Anleitung](extras/compose/keycloak/ReadMe.md).
Den Benutzer `admin` legt man einmal von Hand an. Die Studierenden aus
`student.csv` lädt die Anwendung im Dev-Modus beim Start und per
`QUERY /dev/keycloak_populate` (alle Benutzer außer `admin` werden gelöscht und
mit Rolle `student` und Passwort `p` neu angelegt, z.B. `erika`). POST legt den
Keycloak-Benutzer mit an.

Das **Client Secret** steht in der `.env` (`CLIENT_SECRET`), nicht in `app.toml`:
Jeder von uns hat einen eigenen lokalen Keycloak und damit ein eigenes Secret.
Die Anwendung liest es aus der Umgebung oder ersatzweise aus `.env` im
Arbeitsverzeichnis, deshalb aus dem Projektverzeichnis starten.

Tokens prüft `TokenService` mit `decode_token` (Signatur und Ablauf); die Rollen
kommen aus den Client-Rollen von `student-client`. Passwörter, Tokens und
Authorization-Header werden nicht protokolliert.

## Docker

`Dockerfile` (zweistufig: uv installiert nur die Laufzeitabhängigkeiten, das
Laufzeit-Image übernimmt die fertige `.venv` und läuft als Benutzer `app`) und
[extras/compose/student](extras/compose/student/ReadMe.md) für Anwendung,
PostgreSQL und Keycloak zusammen:

```powershell
cd extras\compose\student
docker compose --env-file ../../../.env up --build -d
```

Die Container-Konfiguration steht in `extras/compose/student/app.toml`, das Secret
wird aus der `.env` übergeben und nicht ins Image kopiert. Lokaler Server und
Container nutzen beide Port 8000, also nur eines von beiden starten.

## Tests

| Art | Ort | Ausführen |
|---|---|---|
| Unit-Tests mit Mocks, ohne Server | `tests/unit` | `uv run python -m pytest tests/unit` |
| Integrationstests mit httpx gegen den laufenden Server | `tests/integration` | `uv run python -m pytest` |
| Manuelle Tests | `extras/bruno/student` | Bruno, siehe unten |
| Lasttest | `tests/lasttest/locustfile.py` | `uvx locust -f .\tests\lasttest\locustfile.py` |

**Integrationstests** brauchen PostgreSQL, Keycloak und den Server, sonst bricht
der Lauf mit einem Hinweis ab. Sie holen sich das Token wie im Beispiel selbst
(Fixtures `client` für `admin` und `login` für andere Benutzer) und laden DB und
Keycloak einmal pro Testlauf neu. Tests, die Studierende anlegen oder löschen,
erzeugen ihre Daten selbst, damit die übrigen Tests die 5 Testdatensätze behalten.

**Bruno** (`C:\Zimmermann\Bruno\Bruno.exe`): *Open Collection* auf
`extras\bruno\student`, unter *Preferences > General* die
*SSL/TLS Certificate Verification* ausschalten, das Environment *student* wählen
und dort das Secret `password` = `p` eintragen. Danach die ganze Collection mit
dem Runner ausführen: Sie loggt sich zuerst ein (*Token*, das Token landet in
`accessToken`), lädt DB und Keycloak neu (*Dev*) und testet dann Hello, Health,
REST (zuletzt *Als Studierende* mit `erika`) und GraphQL. Die Requests haben
collectionweit eindeutige Sequenznummern (1–50); neue Requests entsprechend
einsortieren. Einzeln ausgeführte schreibende Requests klappen nur einmal pro
Neuladen (sonst z.B. 422 „Existierende Email“); vorher *Token* und *Dev* ausführen.

**Locust:** Jeder simulierte Benutzer loggt sich als `admin` ein und sucht nach
ID, Nachname und Email (Gewichte 100 : 200 : 150). Im Browser
`http://localhost:8089` öffnen, z.B. 50 Users, Ramp Up 5, Host
`https://localhost:8000`. Server, DB, Keycloak und Locust laufen auf demselben
Notebook; für aussagekräftigere Werte `debug-level` und `log-statements` in
`app.toml` auf `false` setzen.

## Codeprüfung und Sicherheit

```powershell
uv run ruff check --preview src tests
uv run ruff format --preview --check src tests
uv run ty check src tests
uv tree --outdated --all-groups --depth=1   # neuere Versionen
uv audit                                    # bekannte Sicherheitslücken
```

Ruff verwendet das Regelset des Beispiels (`[tool.ruff.lint]` in `pyproject.toml`).
Die [CI](.github/workflows/ci.yml) führt bei jedem Push Unit-Tests, Ruff und ty mit
`uv sync --locked` aus; die Actions sind auf Commit-SHAs festgelegt. Die
Integrationstests brauchen Server und DB und laufen nur lokal.

**SonarQube:** `docker compose up` in `extras\compose\sonarqube`, unter
<http://localhost:9000> (beim ersten Mal `admin`/`admin`, Passwort ändern) unter
*My Account > Security* einen *Global Analysis Token* erzeugen und als
Umgebungsvariable speichern:

```powershell
[Environment]::SetEnvironmentVariable("SONAR_TOKEN", "<Token>", "User")
uv run python sonar-scanner.py   # nach Neustart von Terminal bzw. VS Code
```

**OWASP Dependency Check** braucht einen NVD-API-Key
(<https://nvd.nist.gov/developers/request-an-api-key>) als `NVD_API_KEY` in der
`.env`. `uv run extras/dependency-check.py` schreibt
`dependency-check-report.html`; die Python-Analyzer sind experimentell und werden
im Skript eingeschaltet. Begründete Fehlalarme stehen in
[extras/suppression.xml](extras/suppression.xml).

## Dokumentation und Library Skills

**MkDocs** mit Material und mkdocstrings (`mkdocs.yml`, Seiten unter `docs/`):

```powershell
uv run mkdocs serve   # http://localhost:8001 (nicht 127.0.0.1, siehe unten)
uv run mkdocs build   # HTML im Ordner site/
```

Die Seiten unter `docs/modules/` erzeugen die API-Dokumentation aus den Docstrings
(Stil Sphinx) der in `__all__` exportierten Elemente; `strict: true` bricht bei
Warnungen ab. Im Browser `localhost` statt `127.0.0.1` verwenden: Der HSTS-Header
der Anwendung legt den Browser für `127.0.0.1` auf HTTPS fest, MkDocs spricht nur
HTTP.

**Library Skills:** Anleitungen für KI-Coding-Agenten, die FastAPI im Paket
mitliefert, kopiert `uvx library-skills install --all --copy` nach
`.agents/skills/` (`--copy` statt Symlinks, damit sie im Repository landen). Die
Dateien nicht von Hand ändern, nach einem FastAPI-Update den Befehl erneut
ausführen.

## Abweichungen vom Beispielprojekt "patient"

- **Client Secret** in `.env` statt `app.toml` (eigener Keycloak je Entwickler,
  siehe [Keycloak](#keycloak)).
- **Docker-Image** `python:3.15-trixie` statt `dhi.io/python`: Das Projekt setzt
  Python ≥ 3.15 voraus, das Image des Beispiels basiert auf Python 3.14. Da das
  offizielle Image keinen Nonroot-Benutzer mitbringt, legt das Dockerfile den
  Benutzer `app` (UID 10000) selbst an.
- **POST und GraphQL-`create` nur mit Rolle admin** (im Beispiel ungeschützt).
- **POST prüft zuerst die DB, dann Keycloak**, damit z.B. eine doppelte
  Matrikelnummer keinen verwaisten Keycloak-Benutzer hinterlässt.
- **GraphQL-`login`:** `expiresIn` ist die echte Laufzeit in Sekunden (1800) statt
  fest `"1d"`; das Passwort wird nicht protokolliert.
- **Namensmuster** mit `+` im zweiten Teil, damit Doppelnamen wie
  „Müller-Lüdenscheidt“ gültig sind.
- **PUT:** Ein `If-Match` ohne Zahl ergibt 412 mit ProblemDetails statt einer leeren
  Antwort.
- **Kleinere Korrekturen:** Health-Readiness fängt auch Fehler beim
  Verbindungsaufbau ab, `connect-timeout` für die DB, ProblemDetails mit Titel für
  404.
- **MkDocs** auf Port 8001, damit die Anwendung parallel auf 8000 laufen kann.
- **Locust** ohne `print` je Request; Login per `QUERY` wie unsere Schnittstelle.


## Zusammenarbeit

Aufgaben stehen als Issues im
[GitHub Project](https://github.com/users/JM01332/projects/1). 
