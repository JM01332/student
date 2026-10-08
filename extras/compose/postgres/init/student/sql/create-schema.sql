-- Schema "student" mit dem DB-User "student" als Owner anlegen
-- Aufruf im Container:
--   psql --dbname=student --username=student --file=/init/student/sql/create-schema.sql

CREATE SCHEMA IF NOT EXISTS AUTHORIZATION student;
ALTER ROLE student SET search_path = 'student';
