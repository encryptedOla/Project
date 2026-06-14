-- ============================================================
--  ExamSync — MySQL Database Setup
--  Run this file once to create all tables:
--  mysql -u root -p examsynced < database_setup.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS examsynced;
USE examsynced;

-- ── Users (login & register) ─────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    first_name     VARCHAR(80)  NOT NULL,
    last_name      VARCHAR(80)  NOT NULL,
    email          VARCHAR(120) NOT NULL UNIQUE,
    institution    VARCHAR(120) NOT NULL,
    department     VARCHAR(120),
    role           ENUM('registry', 'admin', 'tutor', 'viewer') NOT NULL DEFAULT 'viewer',
    password_hash  VARCHAR(256) NOT NULL,
    terms_accepted BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at     DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- ── Tutors ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tutors (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(120) NOT NULL,
    staff_id   VARCHAR(40)  NOT NULL UNIQUE,
    department VARCHAR(120),
    email      VARCHAR(120) UNIQUE,
    phone      VARCHAR(30),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Courses ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS courses (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    code          VARCHAR(20)  NOT NULL UNIQUE,
    name          VARCHAR(150) NOT NULL,
    units         INT          NOT NULL DEFAULT 3,
    department    VARCHAR(120),
    level         ENUM('L100','L200','L300','L400') NOT NULL DEFAULT 'L100',
    student_count INT          NOT NULL DEFAULT 0,
    tutor_id      INT,
    duration      VARCHAR(20)  DEFAULT '3 hrs',
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tutor_id) REFERENCES tutors(id) ON DELETE SET NULL
);

-- ── Exam Halls ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS halls (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(120) NOT NULL,
    location   VARCHAR(120),
    capacity   INT          NOT NULL DEFAULT 0,
    facilities TEXT,
    status     ENUM('available', 'unavailable') NOT NULL DEFAULT 'available',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Schedule Sessions ────────────────────────────────────
CREATE TABLE IF NOT EXISTS schedule_sessions (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    date         DATE        NOT NULL,
    session_type ENUM('morning', 'afternoon', 'evening') NOT NULL,
    start_time   TIME        NOT NULL,
    end_time     TIME        NOT NULL,
    created_at   DATETIME    DEFAULT CURRENT_TIMESTAMP
);

-- ── Timetable Entries (generated output) ─────────────────
CREATE TABLE IF NOT EXISTS timetable_entries (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    session_id   INT NOT NULL,
    course_id    INT NOT NULL,
    hall_id      INT NOT NULL,
    tutor_id     INT,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES schedule_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses(id)           ON DELETE CASCADE,
    FOREIGN KEY (hall_id)    REFERENCES halls(id)             ON DELETE CASCADE,
    FOREIGN KEY (tutor_id)   REFERENCES tutors(id)            ON DELETE SET NULL
);
