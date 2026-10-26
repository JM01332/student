# Keycloak für die lokale Entwicklung

Compose-Konfiguration und TLS-Dateien entsprechen dem FastAPI-Beispiel:
`dhi.io/keycloak:26.7.4-debian13`, PostgreSQL als Datenbank sowie die externen
Volumes `kc_data` und `kc_tls`. Zertifikat, privater Schlüssel und die Passwörter
`p` sind ausschließlich für die lokale Entwicklung vorgesehen.

Hier stehen Einrichtung und Betrieb von Keycloak. Wie die Anwendung Keycloak nutzt
(Login, Rollen, Benutzer aus den Testdaten), beschreibt die
[README](../../../README.md#keycloak).

## Vorhandene Einrichtung zuerst prüfen

Das Beispielprojekt verwendet **dieselben Containernamen und Volumes**
(`postgres`, `keycloak`, `pg_data`, `kc_data` …). Beide Projekte daher nie
parallel starten und eine vorhandene Einrichtung weiterverwenden, nicht neu
befüllen:

```powershell
docker ps -a
docker volume inspect kc_data kc_tls
docker exec -it postgres psql --username=postgres --dbname=keycloak
```

In psql:

```sql
SELECT name FROM keycloak.realm;
SELECT version FROM keycloak.migration_model;
\q
```

Realms, Clients und Benutzer liegen in der PostgreSQL-Datenbank `keycloak`.
Der Realm `python` mit `python-client` gehört zum Beispiel und bleibt unverändert.

## Ersteinrichtung auf einem Rechner ohne Keycloak

Nur ausführen, wenn Benutzer, Datenbank und Volumes noch nicht existieren.
PostgreSQL vorher nach [../postgres/ReadMe.md](../postgres/ReadMe.md) einrichten
und starten.

```powershell
docker exec -it postgres psql --username=postgres --dbname=postgres
```

```sql
CREATE USER keycloak PASSWORD 'p';
CREATE DATABASE keycloak;
GRANT ALL ON DATABASE keycloak TO keycloak;
\q
```

```powershell
docker exec -it postgres psql --username=keycloak --dbname=keycloak
```

```sql
CREATE SCHEMA IF NOT EXISTS AUTHORIZATION keycloak;
ALTER ROLE keycloak SET search_path = 'keycloak';
\q
```

TLS-Volumes vorbereiten (vom Projektverzeichnis aus):

```powershell
docker volume create kc_data
docker volume create kc_tls
cd extras\compose\keycloak
docker run -v kc_tls:/opt/keycloak/tls -v ./tls:/tmp/tls:ro `
  --rm -it -u 0:0 --entrypoint '' dhi.io/keycloak:26.7.4-debian13 bash
```

In der Container-Bash:

```bash
cp /tmp/tls/certificate.crt /opt/keycloak/tls/kc_cert
cp /tmp/tls/key.pem /opt/keycloak/tls/kc_key
chown -R nonroot:nonroot /opt/keycloak/tls
chmod 400 /opt/keycloak/tls/*
chmod 500 /opt/keycloak/tls
exit
```

Beim ersten Start legt Keycloak im Realm `master` den temporären Administrator
`tmp` / `p` an (siehe `compose.yml`). Wie im Beispiel damit anmelden und unter
**Users → Add user** den dauerhaften Administrator anlegen: Username `admin`,
Email `admin@acme.com`, unter **Credentials** Passwort `p` mit **Temporary Off**,
unter **Role mapping → Assign role → Realm roles** die Rolle `admin`.

## Starten und stoppen

Für den täglichen Betrieb mit lokal gestarteter Anwendung den
[Backend-Einstieg](../backend/ReadMe.md) verwenden (PostgreSQL und Keycloak), für
die Anwendung im Container den [App-Einstieg](../student/ReadMe.md). Nur mit
dieser Compose-Datei, vom Projektverzeichnis aus:

```powershell
docker compose -f extras/compose/keycloak/compose.yml up -d
docker compose -f extras/compose/keycloak/compose.yml ps
docker compose -f extras/compose/keycloak/compose.yml down
```

Diese Datei bindet `../postgres/compose.yml` ein und verwaltet damit beide Dienste
im Compose-Projekt `student`. Keycloak wartet auf den Healthcheck von PostgreSQL.
`down` entfernt Container und Netzwerk, die externen Volumes bleiben erhalten.

Admin-Konsole: <https://localhost:8843> (selbstsigniertes Zertifikat), alternativ
<http://localhost:8880>. Der Healthcheck des Containers wertet den HTTP-Status
nicht aus; die Bereitschaft zeigt zuverlässig `https://localhost:9990/health/ready`.

## Student-Realm einrichten

Wie im Abschnitt „Konfiguration“ der Keycloak-ReadMe des Beispiels, mit
`student` / `student-client` / `student` statt `python` / `python-client` /
`patient`. Alle Schritte in der Admin-Konsole:

1. Als `admin` im Realm `master` anmelden.
2. **Manage realms → Create realm**: Realm name `student`, Enabled an.
3. Im Realm `student` **Clients → Create client**:
   - Client type `OpenID Connect`, Client ID `student-client`, Name `Student Client`.
   - Client authentication **On**, Authorization **Off**.
   - **Standard flow**, **Direct access grants** und **Service account roles** an.
   - Root URL `https://localhost:8000`, Valid redirect URIs `*`, Web origins `+`.
4. **student-client → Roles**: Client-Rollen `admin` und `student` anlegen
   (kleingeschrieben).
5. **Users → Add user**: Username `admin`, Email `admin@acme.com`, First name
   `Student`, Last name `Admin`, **Required user actions** leer.
6. **Credentials → Set password**: `p`, **Temporary Off**.
7. **Role mapping → Assign role → Client roles**:

   | Client | Rollen |
   |---|---|
   | `student-client` | `admin` |
   | `realm-management` | `manage-users`, `query-users`, `realm-admin`, `view-users` |

   Die Rollen von `realm-management` braucht die Anwendung, um Benutzer anzulegen
   und zu löschen.
8. **Realm settings → Sessions**: SSO Session Idle **1 Hours**.
9. **Realm settings → Tokens**: Access Token Lifespan und Access Token Lifespan
   For Implicit Flow jeweils **30 Minutes**.

Studierende werden **nicht** von Hand angelegt: Im Dev-Modus löscht die Anwendung
beim Start und per `QUERY /dev/keycloak_populate` alle Benutzer außer `admin` und
legt die Studierenden aus `student.csv` mit der Client-Rolle `student` und dem
Passwort `p` neu an (z.B. `erika`).

## Client Secret und Prüfung

Unter **Clients → student-client → Credentials** das **Client Secret** kopieren
und in die lokale `.env` im Projektverzeichnis eintragen (`CLIENT_SECRET=...`;
Vorlage: `Copy-Item .env.example .env`). Die `.env` wird von Git ignoriert.
Warum das Secret nicht wie im Beispiel in `app.toml` steht, erklärt die
[README](../../../README.md#keycloak).

Prüfskript, bei laufendem Keycloak und PostgreSQL im Projektverzeichnis:

```powershell
uv run python extras/compose/keycloak/check_realm.py
```

Es prüft TLS-Zertifikat, Discovery, Token-Ausgabe für `admin` und `erika` (nach dem
ersten Start der Anwendung vorhanden), Issuer, Client-Rollen und die Token-Laufzeit
von 30 Minuten. Es ändert nichts und gibt keine Secrets oder Tokens aus. Die
kryptografische Prüfung der Tokens übernimmt in der Anwendung
`KeycloakOpenID.decode_token` (`src/student/security/token_service.py`).
