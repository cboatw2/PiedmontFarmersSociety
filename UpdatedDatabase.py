import os
import sqlite3

def create_pfsdatabase(db_path="pfs.sqlite"):
    if os.path.exists(db_path):
        os.remove(db_path)
    schema = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE person (
      id               INTEGER PRIMARY KEY,
      last             TEXT NOT NULL,
      first            TEXT,
      middle           TEXT,
      other_names      TEXT,
      prefix           TEXT,
      suffix           TEXT,
      birth_year       INTEGER,
      death_year       INTEGER,
      notes            TEXT
    );

    CREATE TABLE location (
      id                INTEGER PRIMARY KEY,
      name              TEXT NOT NULL,
      county            TEXT,
      state             TEXT,
      country           TEXT DEFAULT 'USA',
      latitude          REAL,
      longitude         REAL,
      geocode_precision TEXT,
      notes             TEXT
    );

    CREATE TABLE source (
      id          INTEGER PRIMARY KEY,
      citation    TEXT NOT NULL,
      url         TEXT,
      source_type TEXT,
      year        INTEGER
    );

    CREATE TABLE person_hometown (
      id          INTEGER PRIMARY KEY,
      person_id   INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
      location_id INTEGER NOT NULL REFERENCES location(id),
      start_year  INTEGER,
      end_year    INTEGER,
      source_id   INTEGER REFERENCES source(id),
      notes       TEXT,
      CHECK (end_year IS NULL OR start_year IS NULL OR end_year >= start_year)
    );

    CREATE TABLE family_relationship (
      id                 INTEGER PRIMARY KEY,
      person_id          INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
      related_person_id  INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
      relation_type      TEXT NOT NULL,
      start_year         INTEGER,
      end_year           INTEGER,
      source_id          INTEGER REFERENCES source(id),
      notes              TEXT
    );

    CREATE TABLE pfs (
      id           INTEGER PRIMARY KEY CHECK (id = 1),
      name         TEXT NOT NULL UNIQUE,
      founded_year INTEGER,
      dissolved_year INTEGER,
      notes        TEXT
    );

    CREATE TABLE induction_method (
      id   INTEGER PRIMARY KEY,
      name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE leaving_reason (
      id   INTEGER PRIMARY KEY,
      name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE pfs_membership (
      id                   INTEGER PRIMARY KEY,
      person_id            INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
      role                 TEXT,
      start_year           INTEGER,
      end_year             INTEGER,
      induction_method_id  INTEGER REFERENCES induction_method(id),
      leaving_reason_id    INTEGER REFERENCES leaving_reason(id),
      source_id            INTEGER REFERENCES source(id),
      notes                TEXT,
      CHECK (end_year IS NULL OR start_year IS NULL OR end_year >= start_year)
    );

    CREATE VIEW v_pfs_membership AS
    SELECT
      pm.id,
      p.last, p.first, p.middle, p.suffix,
      pm.role,
      pm.start_year,
      pm.end_year,
      CASE
        WHEN pm.start_year IS NULL THEN NULL
        WHEN pm.end_year   IS NULL THEN NULL
        ELSE (pm.end_year - pm.start_year + 1)
      END AS duration_years
    FROM pfs_membership pm
    JOIN person p ON p.id = pm.person_id;

    CREATE TABLE landholding (
      id              INTEGER PRIMARY KEY,
      location_id     INTEGER NOT NULL REFERENCES location(id),
      parcel_name     TEXT,
      deed_book       TEXT,
      acreage         REAL,
      notes           TEXT
    );
    CREATE TABLE person_landholding (
      id              INTEGER PRIMARY KEY,
      person_id       INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
      landholding_id  INTEGER NOT NULL REFERENCES landholding(id),
      start_year      INTEGER,
      end_year        INTEGER,
      inferred_from_hometown INTEGER DEFAULT 0 CHECK (inferred_from_hometown IN (0,1)),
      source_id       INTEGER REFERENCES source(id),
      notes           TEXT,
      CHECK (end_year IS NULL OR start_year IS NULL OR end_year >= start_year)
    );

    CREATE TABLE profession (
      id       INTEGER PRIMARY KEY,
      name     TEXT NOT NULL UNIQUE,
      category TEXT
    );
    CREATE TABLE person_profession (
      id             INTEGER PRIMARY KEY,
      person_id      INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
      profession_id  INTEGER NOT NULL REFERENCES profession(id),
      start_year     INTEGER,
      end_year       INTEGER,
      source_id      INTEGER REFERENCES source(id),
      notes          TEXT,
      CHECK (end_year IS NULL OR start_year IS NULL OR end_year >= start_year)
    );

    CREATE TABLE political_office (
      id                 INTEGER PRIMARY KEY,
      title              TEXT NOT NULL,
      jurisdiction_lvl   TEXT NOT NULL,
      jurisdiction_name  TEXT
    );
    CREATE TABLE person_office (
      id          INTEGER PRIMARY KEY,
      person_id   INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
      office_id   INTEGER NOT NULL REFERENCES political_office(id),
      start_year  INTEGER,
      end_year    INTEGER,
      source_id   INTEGER REFERENCES source(id),
      notes       TEXT,
      CHECK (end_year IS NULL OR start_year IS NULL OR end_year >= start_year)
    );

    CREATE TABLE institution (
      id        INTEGER PRIMARY KEY,
      name      TEXT NOT NULL UNIQUE,
      inst_type TEXT,
      location_id INTEGER REFERENCES location(id),
      founded_year INTEGER,
      dissolved_year INTEGER,
      notes     TEXT
    );

    CREATE TABLE institution_membership (
      id            INTEGER PRIMARY KEY,
      person_id     INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
      institution_id INTEGER NOT NULL REFERENCES institution(id),
      role          TEXT,
      start_year    INTEGER,
      end_year      INTEGER,
      source_id     INTEGER REFERENCES source(id),
      notes         TEXT,
      CHECK (end_year IS NULL OR start_year IS NULL OR end_year >= start_year)
    );

    CREATE INDEX idx_person_name ON person(last, first);
    CREATE INDEX idx_pfs_membership_person ON pfs_membership(person_id);
    CREATE INDEX idx_institution_membership_person ON institution_membership(person_id);
    CREATE INDEX idx_person_profession_person ON person_profession(person_id);
    CREATE INDEX idx_person_office_person ON person_office(person_id);
    CREATE INDEX idx_person_hometown_person ON person_hometown(person_id);
    """

    conn = sqlite3.connect(db_path)
    conn.executescript(schema)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_pfsdatabase()