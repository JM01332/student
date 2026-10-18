# Keycloak für die lokale Entwicklung

Die Compose-Konfiguration und TLS-Dateien entsprechen dem FastAPI-Beispiel:
`dhi.io/keycloak:26.7.4-debian13`, PostgreSQL als Datenbank sowie die externen
Volumes `kc_data` und `kc_tls`. Zertifikat, privater Schlüssel und die Passwörter
`p` sind ausschließlich für die lokale Entwicklung vorgesehen.

Die Infrastruktur und die Einrichtung des Student-Realms sind hier beschrieben.
Die OIDC-Anbindung der Anwendung folgt in einem separaten Paket.

## Vorhandene Einrichtung zuerst prüfen

Im Projektverzeichnis:

```powershell
docker ps -a
docker volume inspect kc_data kc_tls
docker image ls dhi.io/keycloak
docker inspect postgres --format '{{ index .Config.Labels "com.docker.compose.project" }}'
```

Vorhandene Volumes nicht neu befüllen. Die Realms, Clients und Benutzer liegen
in der PostgreSQL-Datenbank `keycloak`, nicht allein in `kc_data`.
In einer vorhandenen Datenbank vor dem Start die Herkunft und Version prüfen:

```powershell
docker exec -it postgres psql --username=postgres --dbname=keycloak
```

In psql nach Eingabe des PostgreSQL-Passworts:

```sql
SELECT name FROM keycloak.realm;
SELECT r.name AS realm, c.client_id
FROM keycloak.client c JOIN keycloak.realm r ON r.id = c.realm_id
ORDER BY 1, 2;
SELECT version FROM keycloak.migration_model;
\q
```

`python` / `python-client` und die Client-Rolle `patient` kennzeichnen die
Konfiguration des Beispiels. Diese nicht für Student umbenennen oder löschen.
Eine abweichende Datenbankversion vor einem Start gesondert klären.
Bei einer bestehenden Installation nicht davon ausgehen, dass der
Bootstrap-Zugang `tmp` / `p` erneut angelegt wird.

## Ersteinrichtung auf einem Rechner ohne Keycloak

Nur ausführen, wenn Benutzer, Datenbank, Schema und Volumes noch nicht existieren.
PostgreSQL zuerst nach `../postgres/ReadMe.md` einrichten und starten.
Die vorhandenen PostgreSQL-Volumes `pg_data`, `pg_init` und `pg_tablespace`
werden weiterverwendet.

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

TLS-Volumes wie im Beispiel vorbereiten, ausgehend vom Projektverzeichnis:

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

## Start mit bereits laufendem PostgreSQL

Die Compose-Datei bindet wie im Beispiel `../postgres/compose.yml` ein.
Für den bereits unter dem Compose-Projektnamen `postgres` gestarteten
Datenbankcontainer im Projektverzeichnis ausführen:

```powershell
docker compose -p postgres -f extras/compose/keycloak/compose.yml config --quiet
docker compose -p postgres -f extras/compose/keycloak/compose.yml up -d --no-deps keycloak
docker compose -p postgres -f extras/compose/keycloak/compose.yml logs --tail 50 keycloak
```

Der Projektname muss dem oben ausgelesenen Label entsprechen. `--no-deps`
setzt voraus, dass PostgreSQL bereits gesund im Netzwerk `acme-network` läuft.
Damit wird der bestehende Datenbankcontainer beim Keycloak-Start nicht neu erstellt.
Bei einem fehlgeschlagenen Einrichtungsschritt stoppen und die Ursache klären.

Admin-Konsole: <https://localhost:8843> (selbstsigniertes Zertifikat), alternativ
<http://localhost:8880>. Der Management-Port ist `9990`.
Der übernommene Container-Healthcheck prüft nicht den HTTP-Antwortstatus;
für die Bereitschaft zusätzlich `https://localhost:9990/health/ready` prüfen.

Nur Keycloak stoppen, ohne PostgreSQL herunterzufahren:

```powershell
docker compose -p postgres -f extras/compose/keycloak/compose.yml stop keycloak
```

Kein `docker compose down` für die gemeinsam verwendete Infrastruktur ausführen,
während die Student-Anwendung oder das Beispiel PostgreSQL benötigen.

## Student-Realm einrichten

Referenz ist `extras/compose/keycloak/ReadMe.md` des FastAPI-Beispiels,
Abschnitt „Konfiguration“. Die Schritte werden in der Admin-Konsole ausgeführt.
Die folgenden Namen ersetzen `python`, `python-client` und `patient` aus dem
Beispiel. Vorhandene Realms und Benutzer nicht erneut anlegen oder zurücksetzen.

1. Mit dem vorhandenen Administrator im Realm `master` anmelden.
   Bei abgeschlossener Beispiel-Einrichtung ist dies `admin` mit dem lokalen
   Entwicklungspasswort `p`.
2. **Manage realms → Create realm**: Realm name `student`, Enabled eingeschaltet.
3. Im Realm `student` unter **Clients → Create client**:
   - Client type `OpenID Connect`, Client ID `student-client`, Name `Student Client`.
   - Client authentication **On**, Authorization **Off**.
   - **Standard flow**, **Direct access grants** und **Service account roles** aktivieren.
   - Root URL `https://localhost:8000`, Valid redirect URIs `*`, Web origins `+`.
   - Speichern. Die Beispielanleitung macht keine Vorgabe zur Admin URL;
     einen automatisch ausgefüllten Wert beibehalten.
4. Unter **student-client → Roles** die Client-Rollen `admin` und `student`
   anlegen, jeweils kleingeschrieben.
5. Unter **Users → Add user** den Administrator anlegen:
   Username `admin`, Email `admin@acme.com`, First name `Student`, Last name `Admin`.
   **Required user actions** leer lassen.
6. Unter **Credentials → Set password** das lokale Entwicklungspasswort `p`
   eintragen und bestätigen; **Temporary Off**, speichern und bestätigen.
7. Unter **Role mapping → Assign role → Client roles** zuweisen:

   | Client | Rollen |
   |---|---|
   | `student-client` | `admin` |
   | `realm-management` | `manage-users`, `query-users`, `realm-admin`, `view-users` |

   Die vorhandene Rolle `default-roles-student` beibehalten. Unter **Details**
   erneut prüfen, dass **Required user actions** leer ist.
8. Unter **Realm settings → Sessions**: **SSO Session Idle 1 Hours**, speichern.
9. Unter **Realm settings → Tokens**: **Access Token Lifespan 30 Minutes** und
   **Access Token Lifespan For Implicit Flow 30 Minutes**, speichern.

Für die separat prüfbare Realm-Einrichtung wird zusätzlich ein normaler
Testbenutzer manuell angelegt. Das Beispiel erzeugt normale Benutzer später
über `KeycloakPopulateService` aus den CSV-Daten; diese Funktion ist hier noch
nicht angebunden.

- **Users → Add user**: Username `student`, Email `student@acme.com`,
  First name `Test`, Last name `Student`, **Required user actions** leer.
- Unter **Credentials** Passwort `p` mit **Temporary Off** setzen.
- Unter **Role mapping** nur die Client-Rolle `student-client → student` ergänzen;
  `default-roles-student` beibehalten. Keine Verwaltungsrollen zuweisen.

## Client Secret und Prüfung

Unter **Clients → student-client → Credentials** das **Client Secret** kopieren.
Wenn im Projektverzeichnis noch keine `.env` vorhanden ist, einmalig anlegen:

```powershell
Copy-Item .env.example .env
```

In der lokalen `.env` den Eintrag `CLIENT_SECRET` mit dem kopierten Wert befüllen.
Vorhandene Einträge erhalten. Die Datei wird von Git ignoriert; Secrets und Tokens
nicht in Screenshots oder Commits aufnehmen. Die TOML-Konfiguration für die
Anwendung aus dem Beispiel folgt erst mit deren OIDC-Anbindung.

Bei laufendem Keycloak und PostgreSQL im Projektverzeichnis ausführen:

```powershell
uv run python extras/compose/keycloak/check_realm.py
```

Das Skript nutzt die bereits vorhandenen Entwicklungsabhängigkeiten `httpx` und
`python-dotenv`. Es prüft das TLS-Zertifikat aus `tls/certificate.crt`, Discovery,
die Ausgabe von Access und Refresh Tokens für beide Testbenutzer sowie Issuer,
Client, Benutzername, Email, Client-Rollen und 30 Minuten Access-Token-Laufzeit.
Der normale Benutzer darf keine `realm-management`-Rollen haben. Das Skript
verändert keine Benutzer oder Konfiguration, erzeugt aber Login-Sessions.
Secrets und Tokens werden nicht ausgegeben. Bei einem Fehler bricht es ab.

Die Claims werden ausschließlich aus der direkt über geprüftes HTTPS bezogenen
Tokenantwort gelesen. Dies ist **keine kryptografische JWT-Prüfung** und kein
Code zur Authentifizierung von API-Requests. Die Anwendung des Beispiels verwendet
hierfür `KeycloakOpenID.decode_token` in `src/patient/security/token_service.py`;
diese Anbindung folgt separat.

Eine zusätzliche Introspection gehört nicht zur Beispielprüfung. Beim lokalen
Client wurde sie mit `active: false` abgelehnt; das Keycloak-Log nennt als Grund,
dass `student-client` nicht in der Token-Audience enthalten ist. Dafür werden
keine zusätzlichen Audience-Mapper eingerichtet. Das Prüfskript verwendet keine
Introspection.
