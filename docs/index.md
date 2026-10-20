# student

## Überblick

Dokumentation zum Projekt _student_ im Modul _Softwareengineering_ an der
Hochschule Karlsruhe: ein Appserver mit FastAPI zur Verwaltung von
Studierendendaten mit Adresse und Prüfungsleistungen.

| Schnittstelle | Beschreibung |
| ------------- | ------------ |
| REST | Lesen, Suchen (mit Pagination), Anlegen, Ändern (mit `If-Match`) und Löschen unter `/rest` |
| GraphQL | Queries `student` und `studenten`, Mutationen `create` und `login` unter `/graphql` |
| Login | Token von Keycloak über `QUERY /auth/token` |

Technik: FastAPI, Pydantic, SQLAlchemy mit PostgreSQL, Strawberry für GraphQL und
Keycloak für OIDC und OAuth 2. Installation, Start und Tests sind in der `README.md`
des Repositorys beschrieben.

## Weiterführende Links

| Link | Erläuterung |
| ---- | ----------- |
| <https://www.h-ka.de> | Homepage der Hochschule Karlsruhe |
| <https://fastapi.tiangolo.com> | FastAPI |
| <https://strawberry.rocks> | Strawberry (GraphQL) |
| <https://www.keycloak.org> | Keycloak |
