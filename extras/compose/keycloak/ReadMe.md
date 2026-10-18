# Keycloak für die lokale Entwicklung

Die Compose-Konfiguration und TLS-Dateien entsprechen dem FastAPI-Beispiel:
`dhi.io/keycloak:26.7.4-debian13`, PostgreSQL als Datenbank sowie die externen
Volumes `kc_data` und `kc_tls`. Zertifikat, privater Schlüssel und die Passwörter
`p` sind ausschließlich für die lokale Entwicklung vorgesehen.

Die Infrastruktur ist vorbereitet. Ein eigener Student-Realm, Client, Rollen
und die OIDC-Anbindung der Anwendung folgen in separaten Paketen.

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
