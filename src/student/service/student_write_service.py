"""Geschäftslogik zum Schreiben von Studierendendaten."""

from typing import Final

from loguru import logger

from student.repository import Session
from student.security import Role, User
from student.service.exceptions import (
    EmailExistsError,
    EmptyUsernameError,
    MatrikelnummerExistsError,
    NotFoundError,
    UsernameExistsError,
    VersionOutdatedError,
)
from student.service.student_dto import StudentDTO
lazy from student.entity import Student
lazy from student.repository import StudentRepository
lazy from student.security import UserService

__all__ = ["StudentWriteService"]

_PASSWORD: Final = "p"  # ruff: ignore[hardcoded-password-string]  # NOSONAR
"""Startpasswort neuer Benutzer in Keycloak wie im Beispielprojekt."""


class StudentWriteService:
    """Service-Klasse mit Geschäftslogik zum Schreiben von Studierendendaten."""

    def __init__(self, repo: StudentRepository, user_service: UserService) -> None:
        """Konstruktor mit abhängigem StudentRepository und UserService."""
        self.repo: StudentRepository = repo
        self.user_service: UserService = user_service

    def create(self, student: Student) -> StudentDTO:
        """Einen neuen Studierenden in der DB und als Benutzer in Keycloak anlegen.

        Abweichend vom Beispiel wird zuerst die DB geprüft und erst dann der
        Keycloak-Benutzer angelegt, damit z.B. eine doppelte Matrikelnummer keinen
        verwaisten Keycloak-Benutzer hinterlässt. Scheitert danach das Speichern in
        der DB, bleibt der Keycloak-Benutzer wie im Beispiel bestehen (bekannte
        Einschränkung).

        :param student: Der neue Studierende ohne ID
        :return: Der neu angelegte Studierende mit generierter ID
        :rtype: StudentDTO
        :raises EmptyUsernameError: Falls der Benutzername fehlt
        :raises EmailExistsError: Falls die Emailadresse bereits existiert
        :raises MatrikelnummerExistsError: Falls die Matrikelnummer bereits existiert
        :raises UsernameExistsError: Falls der Benutzername in Keycloak existiert
        """
        logger.debug(
            "student={}, adresse={}, pruefungsleistungen={}",
            student,
            student.adresse,
            student.pruefungsleistungen,
        )
        username: Final = student.username
        if not username:
            raise EmptyUsernameError

        with Session() as session:
            # 1. Prüfungen in der DB
            if self.repo.exists_email(email=student.email, session=session):
                raise EmailExistsError(email=student.email)
            if self.repo.exists_matrikelnummer(
                matrikelnummer=student.matrikelnummer,
                session=session,
            ):
                raise MatrikelnummerExistsError(matrikelnummer=student.matrikelnummer)

            # 2. Prüfungen in Keycloak
            if self.user_service.username_exists(username):
                raise UsernameExistsError(username)
            if self.user_service.email_exists(student.email):
                raise EmailExistsError(email=student.email)

            # 3. Benutzer in Keycloak, 4. Datensatz in der DB
            self.user_service.create_user(
                User(
                    username=username,
                    email=student.email,
                    nachname=student.nachname,
                    vorname=student.vorname,
                    roles=[Role.STUDENT],
                    password=_PASSWORD,
                )
            )
            student_db: Final = self.repo.create(student=student, session=session)
            student_dto: Final = StudentDTO.from_student(student_db)
            session.commit()

        logger.debug("student_dto={}", student_dto)
        return student_dto

    def update(self, student: Student, student_id: int, version: int) -> StudentDTO:
        """Daten eines Studierenden ändern.

        :param student: Die neuen Daten
        :param student_id: ID des zu aktualisierenden Studierenden
        :param version: Version für optimistische Synchronisation
        :return: Der aktualisierte Studierende
        :rtype: StudentDTO
        :raises NotFoundError: Falls der zu aktualisierende Studierende nicht existiert
        :raises VersionOutdatedError: Falls die Versionsnummer nicht aktuell ist
        :raises EmailExistsError: Falls die Emailadresse bereits existiert
        :raises MatrikelnummerExistsError: Falls die Matrikelnummer bereits existiert
        """
        logger.debug("student_id={}, version={}, {}", student_id, version, student)

        with Session() as session:
            if (
                student_db := self.repo.find_by_id(
                    student_id=student_id,
                    session=session,
                )
            ) is None:
                raise NotFoundError(student_id)
            if student_db.version > version:
                raise VersionOutdatedError(version)

            email: Final = student.email
            if email != student_db.email and self.repo.exists_email_other_id(
                email=email,
                student_id=student_id,
                session=session,
            ):
                raise EmailExistsError(email)

            matrikelnummer: Final = student.matrikelnummer
            if (
                matrikelnummer != student_db.matrikelnummer
                and self.repo.exists_matrikelnummer_other_id(
                    matrikelnummer=matrikelnummer,
                    student_id=student_id,
                    session=session,
                )
            ):
                raise MatrikelnummerExistsError(matrikelnummer)

            student_db.set(student)
            if (
                student_updated := self.repo.update(student=student_db, session=session)
            ) is None:
                raise NotFoundError(student_id)
            student_dto: Final = StudentDTO.from_student(student_updated)
            logger.debug("{}", student_dto)

            session.commit()
            # Die erhöhte Versionsnummer ist erst nach dem COMMIT sichtbar
            student_dto.version += 1
            return student_dto

    def delete_by_id(self, student_id: int) -> None:
        """Einen Studierenden anhand seiner ID löschen.

        Eine nicht vorhandene ID ist kein Fehler: Danach gibt es den Studierenden
        so oder so nicht (idempotentes DELETE).

        :param student_id: ID des zu löschenden Studierenden
        """
        logger.debug("student_id={}", student_id)
        with Session() as session:
            self.repo.delete_by_id(student_id=student_id, session=session)
            session.commit()
