-- Datenbank "student" mit dem DB-User "student" anlegen
-- Aufruf im Container:
--   psql --dbname=postgres --username=postgres --file=/init/student/sql/create-db.sql

CREATE USER student PASSWORD 'p';
CREATE DATABASE student;
GRANT ALL ON DATABASE student TO student;
CREATE TABLESPACE studentspace OWNER student LOCATION '/tablespace/student';
