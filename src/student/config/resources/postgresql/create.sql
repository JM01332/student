-- Tabellen fuer Studierende, Adressen und Pruefungsleistungen im Schema "student"
-- Wird im Dev-Modus beim Start der Anwendung ausgefuehrt (siehe drop.sql).
-- https://www.postgresql.org/docs/current/sql-createtable.html

SET default_tablespace = studentspace;

CREATE TABLE IF NOT EXISTS student (
    id             INTEGER GENERATED ALWAYS AS IDENTITY(START WITH 1000) PRIMARY KEY,
                   -- Versionsnummer fuer ETag und optimistische Synchronisation
    version        INTEGER NOT NULL DEFAULT 0,
                   -- impliziter Index als B-Baum durch UNIQUE
    matrikelnummer TEXT NOT NULL UNIQUE CHECK (matrikelnummer ~ '^\d{6}$'),
    nachname       TEXT NOT NULL,
    vorname        TEXT NOT NULL,
    email          TEXT NOT NULL UNIQUE,
                   -- Benutzername in Keycloak
    username       TEXT NOT NULL,
    erzeugt        TIMESTAMP NOT NULL,
    aktualisiert   TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS student_nachname_idx ON student(nachname);

-- 1:1-Beziehung: genau eine Adresse pro Student
CREATE TABLE IF NOT EXISTS adresse (
    id          INTEGER GENERATED ALWAYS AS IDENTITY(START WITH 1000) PRIMARY KEY,
    plz         TEXT NOT NULL CHECK (plz ~ '^\d{5}$'),
    ort         TEXT NOT NULL,
    student_id  INTEGER NOT NULL UNIQUE REFERENCES student ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS adresse_plz_idx ON adresse(plz);

-- 1:N-Beziehung: beliebig viele Pruefungsleistungen pro Student
CREATE TABLE IF NOT EXISTS pruefungsleistung (
    id          INTEGER GENERATED ALWAYS AS IDENTITY(START WITH 1000) PRIMARY KEY,
    modul       TEXT NOT NULL,
                -- 2 Stellen, davon 1 Nachkommastelle; nur zulaessige Noten
    note        NUMERIC(2,1) NOT NULL
                CHECK (note IN (1.0, 1.3, 1.7, 2.0, 2.3, 2.7, 3.0, 3.3, 3.7, 4.0, 5.0)),
    semester    TEXT NOT NULL,
    student_id  INTEGER NOT NULL REFERENCES student ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS pruefungsleistung_student_id_idx ON pruefungsleistung(student_id);
