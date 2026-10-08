# PostgreSQL für das Projekt `student`

Der PostgreSQL-Server läuft als Docker-Container mit TLS. Das Vorgehen entspricht
`extras/compose/postgres/ReadMe.md` aus dem FastAPI-Beispiel, angepasst auf die
Datenbank `student`.

Die **Ersteinrichtung** (Schritte 1 bis 7) ist nur **einmal pro Rechner** nötig.
Danach reicht für die tägliche Arbeit der Abschnitt [Täglicher Betrieb](#täglicher-betrieb).

Zugangsdaten (nur für die lokale Entwicklung):

| Was | Wert |
|---|---|
| Superuser | `postgres`, Passwort `p` (aus `password.txt`) |
| Datenbank | `student` |
| DB-User | `student`, Passwort `p` |
| Schema | `student` |
| Port | `5432` |

## Voraussetzungen

- Docker Desktop läuft.
- Port 5432 ist frei, d.h. es läuft kein lokal installiertes PostgreSQL und kein
  anderer Container namens `postgres`:

  ```powershell
  docker ps -a --filter name=postgres
  ```

  Die Ausgabe darf außer der Kopfzeile nichts enthalten.

- Alle Befehle werden in **PowerShell im Verzeichnis `extras\compose\postgres`**
  ausgeführt:

  ```powershell
  cd extras\compose\postgres
  ```

## Ersteinrichtung

### Schritt 1: Named Volumes anlegen

```powershell
docker volume create pg_data
docker volume create pg_tablespace
docker volume create pg_init
```

- `pg_data`: die eigentlichen Datenbankdateien
- `pg_tablespace`: Speicherort für den Tablespace `studentspace`
- `pg_init`: SQL-Skripte sowie Zertifikat und Schlüssel für TLS

### Schritt 2: Volumes befüllen

Ein temporärer Container mit einer Bash als Linux-Superuser (`-u 0`) kopiert die
Dateien aus `.\init` in das Volume `pg_init`:

Der Befehl ist bewusst **eine** lange Zeile, also vollständig kopieren:

```powershell
docker run -v pg_init:/init -v pg_tablespace:/tablespace -v ./init:/tmp/init:ro --rm -it -u 0 --entrypoint '' postgres:19beta4-trixie /bin/bash
```

In der Bash des Containers (Prompt `root@...:/#`):

```bash
cp -r /tmp/init/* /init
mkdir /tablespace/student
chown -R postgres:postgres /init /tablespace
chmod 400 /init/*/sql/* /init/tls/*
ls -lR /init
ls -l /tablespace
exit
```

`ls -lR /init` muss `student/sql/create-db.sql`, `student/sql/create-schema.sql`
sowie `tls/server.crt` und `tls/server.key` zeigen, jeweils mit Owner `postgres`
und Rechten `-r--------`.

### Schritt 3: `compose.yml` für den ersten Start ohne TLS anpassen

**Wichtig:** `docker compose up` erst nach dieser Anpassung aufrufen. Sonst bricht der
Container mit `initdb: error: could not change permissions of directory` ab und
startet in einer Schleife neu (mit `Strg+C` beenden, dann Schritt 3 nachholen).

PostgreSQL erwartet Zertifikat und Schlüssel im Datenverzeichnis. Das muss beim
allerersten Start aber leer sein. Deshalb wird der Server zuerst **ohne TLS**
gestartet. Dazu in `compose.yml` **vorübergehend** drei Stellen ändern:

1. Den Block `command:` mit den vier folgenden Zeilen auskommentieren:

   ```yaml
       #command:
       #  [
       #    "--ssl=on",
       #    "--ssl-cert-file=/var/lib/postgresql/19/docker/server.crt",
       #    "--ssl-key-file=/var/lib/postgresql/19/docker/server.key",
       #  ]
   ```

2. Die Zeile `user:` auskommentieren:

   ```yaml
       #user: "postgres:postgres"
   ```

3. Bei der Zeile `cap_add:` den Kommentar entfernen:

   ```yaml
       cap_add: [CHOWN, DAC_OVERRIDE, FOWNER, SETGID, SETUID]
   ```

Warum 2. und 3.: Beim ersten Start legt das Image das Datenverzeichnis an und setzt
dafür als `root` Owner und Rechte. Dafür braucht es kurzzeitig diese Linux-Rechte
(*Capabilities*), die sonst mit `cap_drop: [ALL]` entzogen sind.

### Schritt 4: Server ohne TLS starten und Zertifikat kopieren

In der **1. PowerShell**:

```powershell
docker compose up
```

Warten, bis im Log `database system is ready to accept connections` erscheint.

In einer **2. PowerShell**. Auch dort zuerst in das Verzeichnis wechseln, sonst meldet
Docker `no configuration file provided: not found`:

```powershell
cd <Projektverzeichnis>\extras\compose\postgres
```

```powershell
docker compose exec postgres bash
```

In der Bash des Containers:

```bash
cd /var/lib/postgresql/19/docker
cp /init/tls/* .
chown postgres:postgres server.*
chmod 400 server.*
ls -l server.*
exit
```

Danach, weiterhin in der 2. PowerShell:

```powershell
docker compose down
```

### Schritt 5: `compose.yml` zurücksetzen

Die Änderungen aus Schritt 3 wieder rückgängig machen. Am einfachsten mit Git, da
`compose.yml` im Repository den richtigen Endzustand hat:

```powershell
git restore compose.yml
git status
```

`git status` darf `compose.yml` danach nicht mehr als geändert anzeigen. Alternativ
die drei Stellen von Hand zurückändern: `command` und `user` wieder aktiv,
`cap_add` wieder auskommentiert.

### Schritt 6: Server mit TLS starten, Datenbank und Schema anlegen

In der **1. PowerShell**:

```powershell
docker compose up
```

In der **2. PowerShell**:

```powershell
docker compose exec postgres bash
```

In der Bash des Containers die beiden SQL-Skripte ausführen. Das erste fragt nach dem
Passwort von `postgres`, das zweite nach dem von `student`, beide Male `p`:

```bash
psql --dbname=postgres --username=postgres --file=/init/student/sql/create-db.sql
psql --dbname=student --username=student --file=/init/student/sql/create-schema.sql
exit
```

Erwartete Ausgaben: `CREATE ROLE`, `CREATE DATABASE`, `GRANT`, `CREATE TABLESPACE`
bzw. `CREATE SCHEMA`, `ALTER ROLE`.

### Schritt 7: Prüfen

```powershell
docker compose exec postgres bash -c "psql --dbname=student --username=student --command='SHOW ssl;' --command='SELECT current_schema();'"
```

Nach Eingabe des Passworts `p` muss `ssl` den Wert `on` haben und das aktuelle Schema
`student` sein. Damit ist die Ersteinrichtung abgeschlossen:

```powershell
docker compose down
```

## Täglicher Betrieb

```powershell
cd extras\compose\postgres
docker compose up      # starten, Fenster offen lassen
docker compose down    # in einer 2. PowerShell: herunterfahren
```

Die Daten bleiben in den Volumes erhalten.

## Häufige Probleme

- **`port is already allocated`**: Auf Port 5432 läuft bereits etwas, z.B. ein lokal
  installiertes PostgreSQL. Den Dienst beenden oder in `compose.yml` bei
  `published` einen anderen Port eintragen.
- **`Conflict. The container name "/postgres" is already in use`**: Es existiert schon
  ein Container `postgres`, z.B. aus dem FastAPI-Beispiel. Dessen `compose.yml`
  verwendet dieselben Volume-Namen. Vorher klären, ob dieser Container noch
  gebraucht wird.
- **Server startet in Schritt 6 nicht, Meldung zu `server.key`**: Schritt 4 wurde
  nicht vollständig ausgeführt, d.h. Zertifikat und Schlüssel liegen nicht im
  Datenverzeichnis.
