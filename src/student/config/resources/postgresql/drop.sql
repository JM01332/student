-- Tabellen und Indexe im Schema "student" loeschen (Dev-Modus, vor create.sql)

DROP INDEX IF EXISTS
    adresse_plz_idx,
    pruefungsleistung_student_id_idx,
    student_nachname_idx;

DROP TABLE IF EXISTS
    adresse,
    pruefungsleistung,
    student;
