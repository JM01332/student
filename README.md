# Student

FastAPI-Appserver zur Verwaltung von Studierendendaten.

## Stand und Technik

Editor- und Git-Konfiguration sind vorhanden; die Anwendung ist noch nicht startbar.
Geplant: REST und GraphQL, Pydantic, SQLAlchemy/PostgreSQL, Keycloak und Docker.
Python und Abhängigkeiten werden mit uv verwaltet; Qualitätssicherung erfolgt
mit pytest, Ruff und ty oder Pyrefly.

## Zusammenarbeit

Vorläufige Aufteilung für zwei Personen; die Zuordnung ist noch offen:

- Person A: Datenmodell, Repository, Services und Unit-Tests.
- Person B: REST, GraphQL, Security und Integrationstests.
- Gemeinsam: Schnittstellen, Konfiguration, CI und Dokumentation.

Nächster Schritt: minimale `pyproject.toml` und Source-Layout.
