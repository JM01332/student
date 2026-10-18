# Gemeinsamer Backend-Betrieb

Dieser Einstieg startet PostgreSQL und Keycloak im Compose-Projekt `student`.
Die vorhandenen Container-, Netzwerk- und Volume-Namen bleiben erhalten.
Die Datenbanken und der Keycloak-Realm müssen bereits eingerichtet sein;
siehe die Anleitungen unter `../postgres` und `../keycloak`.

Vom Projektverzeichnis aus:

```powershell
cd extras\compose\backend
docker compose up
```

Alternativ im Hintergrund starten und den Status prüfen:

```powershell
docker compose up -d
docker compose ps
```

Keycloak wartet auf den PostgreSQL-Healthcheck. Die Admin-Konsole ist unter
`https://localhost:8843` erreichbar.

Im selben Ordner beide Dienste stoppen, Container behalten:

```powershell
docker compose stop
```

Oder beide Dienste stoppen und Container sowie Netzwerk entfernen:

```powershell
docker compose down
```

Die externen Volumes `pg_data`, `pg_init`, `pg_tablespace`, `kc_data` und `kc_tls`
bleiben erhalten. Vor dem Stoppen die Anwendung beenden. Das Beispiel nutzt
dieselben Containernamen und Volumes und darf nicht parallel gestartet werden.

Die bisherigen Einstiegspunkte bleiben nutzbar: Im Ordner `postgres` startet
`docker compose up` nur PostgreSQL, im Ordner `keycloak` beide Dienste.
Für den gemeinsamen Betrieb vorzugsweise diesen Backend-Ordner verwenden.
Alle drei Einstiegspunkte verwenden denselben Projektnamen `student`.
