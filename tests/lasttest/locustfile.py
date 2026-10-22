# Aufruf:   uvx locust -f .\tests\lasttest\locustfile.py
#           http://localhost:8089
#           Number of users: 50
#           Ramp Up (users started/second): 5
#           Host: https://localhost:8000

"""Lasttest mit Locust."""

from typing import Final, Literal

import urllib3
from locust import HttpUser, constant_throughput, task

# selbstsigniertes Zertifikat: Warnung bei jedem Request unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GetUser(HttpUser):
    """Lasttest für GET-Requests."""

    # jeder simulierte Benutzer führt höchstens 0,1 Tasks pro Sekunde aus
    wait_time = constant_throughput(0.1)

    def on_start(self) -> None:
        """Einmal pro Benutzer einloggen und den Token im Header speichern."""
        self.client.verify = False

        # Login ist bei uns ein QUERY-Request, nicht POST wie im Beispiel
        response: Final = self.client.request(
            method="QUERY",
            url="/auth/token",
            json={"username": "admin", "password": "p"},
        )
        body: Final[dict[Literal["token"], str]] = response.json()
        token: Final = body["token"]
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(100)
    def get_id(self) -> None:
        """GET-Requests mit einer ID als Pfadparameter."""
        for student_id in [1, 20, 30, 40, 50]:
            self.client.get(f"/rest/{student_id}")

    @task(200)
    def get_nachname(self) -> None:
        """GET-Requests mit einem Teil des Nachnamens als Query-Parameter."""
        for teil in ["a", "er", "mu", "sch", "w"]:
            self.client.get("/rest", params={"nachname": teil})

    @task(150)
    def get_email(self) -> None:
        """GET-Requests mit der Emailadresse als Query-Parameter."""
        for email in [
            "max.mustermann@h-ka.de",
            "erika.musterfrau@h-ka.de",
            "lena.schmidt@h-ka.de",
            "jonas.becker@h-ka.de",
            "sophie.wagner@h-ka.de",
        ]:
            self.client.get("/rest", params={"email": email})
