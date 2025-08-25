import sqlite3, os

db_path = "pfs.sqlite"
schema_path = "pfs_schema.sql"

ddl = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS person (
  id              INTEGER PRIMARY KEY,
  last            TEXT NOT NULL,
  first           TEXT,
  middle          TEXT,
  other_names     TEXT,
  prefix          TEXT,
  suffix          TEXT,
  birth_year      INTEGER,
  death_year      INTEGER,
  notes           TEXT
);

CREATE TABLE IF NOT EXISTS location (
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

CREATE TABLE IF NOT EXISTS person_hometown (
  id           INTEGER PRIMARY KEY,
  person_id    INTEGER NOT NULL,
  location_id  INTEGER NOT NULL,
  start_year   INTEGER,
  end_year     INTEGER,
  source_id    INTEGER,
  notes        TEXT,
  FOREIGN KEY (person_id)   REFERENCES person(id)   ON DELETE CASCADE,
  FOREIGN KEY (location_id) REFERENCES location(id) ON DELETE RESTRICT,
  FOREIGN KEY (source_id)   REFERENCES source(id)   ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS organization (
  id            INTEGER PRIMARY KEY,
  name          TEXT NOT NULL UNIQUE,
  org_type      TEXT NOT NULL CHECK (org_type IN ('society','religious','social','political','other')),
  founded_year  INTEGER,
  dissolved_year INTEGER,
  notes         TEXT
);

CREATE TABLE IF NOT EXISTS induction_method (
  id          INTEGER PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE,
  description TEXT
);

CREATE TABLE IF NOT EXISTS leaving_reason (
  id          INTEGER PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE,
  description TEXT
);

CREATE TABLE IF NOT EXISTS membership (
  id                 INTEGER PRIMARY KEY,
  person_id          INTEGER NOT NULL,
  organization_id    INTEGER NOT NULL,
  role               TEXT,
  start_year         INTEGER,
  end_year           INTEGER,
  induction_method_id INTEGER,
  leaving_reason_id   INTEGER,
  source_id          INTEGER,
  notes              TEXT,
  FOREIGN KEY (person_id)        REFERENCES person(id)        ON DELETE CASCADE,
  FOREIGN KEY (organization_id)  REFERENCES organization(id)  ON DELETE CASCADE,
  FOREIGN KEY (induction_method_id) REFERENCES induction_method(id) ON DELETE SET NULL,
  FOREIGN KEY (leaving_reason_id)   REFERENCES leaving_reason(id)   ON DELETE SET NULL,
  FOREIGN KEY (source_id)        REFERENCES source(id)        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS family_relationship (
  id                 INTEGER PRIMARY KEY,
  person_id          INTEGER NOT NULL,
  related_person_id  INTEGER NOT NULL,
  relation_type      TEXT NOT NULL,
  start_year         INTEGER,
  end_year           INTEGER,
  source_id          INTEGER,
  notes              TEXT,
  FOREIGN KEY (person_id)         REFERENCES person(id) ON DELETE CASCADE,
  FOREIGN KEY (related_person_id) REFERENCES person(id) ON DELETE CASCADE,
  FOREIGN KEY (source_id)         REFERENCES source(id) ON DELETE SET NULL,
  CHECK (person_id != related_person_id)
);

CREATE TABLE IF NOT EXISTS profession (
  id        INTEGER PRIMARY KEY,
  name      TEXT NOT NULL UNIQUE,
  category  TEXT
);

CREATE TABLE IF NOT EXISTS person_profession (
  id            INTEGER PRIMARY KEY,
  person_id     INTEGER NOT NULL,
  profession_id INTEGER NOT NULL,
  start_year    INTEGER,
  end_year      INTEGER,
  source_id     INTEGER,
  notes         TEXT,
  FOREIGN KEY (person_id)     REFERENCES person(id)     ON DELETE CASCADE,
  FOREIGN KEY (profession_id) REFERENCES profession(id) ON DELETE RESTRICT,
  FOREIGN KEY (source_id)     REFERENCES source(id)     ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS political_office (
  id                INTEGER PRIMARY KEY,
  title             TEXT NOT NULL,
  jurisdiction_lvl  TEXT NOT NULL CHECK (jurisdiction_lvl IN ('local','regional','state','national')),
  jurisdiction_name TEXT,
  UNIQUE (title, jurisdiction_lvl, jurisdiction_name)
);

CREATE TABLE IF NOT EXISTS person_office (
  id           INTEGER PRIMARY KEY,
  person_id    INTEGER NOT NULL,
  office_id    INTEGER NOT NULL,
  start_year   INTEGER,
  end_year     INTEGER,
  source_id    INTEGER,
  notes        TEXT,
  FOREIGN KEY (person_id) REFERENCES person(id) ON DELETE CASCADE,
  FOREIGN KEY (office_id) REFERENCES political_office(id) ON DELETE RESTRICT,
  FOREIGN KEY (source_id) REFERENCES source(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS source (
  id        INTEGER PRIMARY KEY,
  citation  TEXT NOT NULL,
  url       TEXT,
  source_type TEXT,
  year      INTEGER
);

CREATE VIEW IF NOT EXISTS v_pfs_membership AS
SELECT
  m.id AS membership_id,
  p.id AS person_id,
  p.last, p.first, p.middle, p.suffix,
  m.start_year,
  m.end_year,
  CASE
    WHEN m.start_year IS NOT NULL AND m.end_year IS NOT NULL THEN (m.end_year - m.start_year + 1)
    ELSE NULL
  END AS duration_years,
  m.role,
  im.name AS induction_method,
  lr.name AS leaving_reason
FROM membership m
JOIN organization o ON o.id = m.organization_id
JOIN person p       ON p.id = m.person_id
LEFT JOIN induction_method im ON im.id = m.induction_method_id
LEFT JOIN leaving_reason  lr ON lr.id = m.leaving_reason_id
WHERE o.name = 'Piedmont Farmers’ Society';

CREATE INDEX IF NOT EXISTS idx_membership_person ON membership(person_id);
CREATE INDEX IF NOT EXISTS idx_membership_org ON membership(organization_id);
CREATE INDEX IF NOT EXISTS idx_membership_years ON membership(start_year, end_year);
CREATE INDEX IF NOT EXISTS idx_person_hometown_person ON person_hometown(person_id);
CREATE INDEX IF NOT EXISTS idx_person_hometown_location ON person_hometown(location_id);
CREATE INDEX IF NOT EXISTS idx_person_profession_pid ON person_profession(person_id);
CREATE INDEX IF NOT EXISTS idx_person_office_pid ON person_office(person_id);
CREATE INDEX IF NOT EXISTS idx_family_rel_person ON family_relationship(person_id, related_person_id);
"""

# Create the DB and apply schema
if os.path.exists(db_path):
    os.remove(db_path)
con = sqlite3.connect(db_path)
cur = con.cursor()
cur.executescript(ddl)

# Seed vocab & the PFS organization
cur.execute("INSERT INTO organization (name, org_type, notes) VALUES (?,?,?)",
            ("Piedmont Farmers’ Society", "society", "Primary society of interest"))
cur.executemany("INSERT INTO induction_method (name, description) VALUES (?,?)",
                [("Invitation","Invited by existing member(s)"),
                 ("Election","Elected by vote"),
                 ("Petition","Applied/petitioned and accepted"),
                 ("Automatic","Automatic by office/role")])
cur.executemany("INSERT INTO leaving_reason (name, description) VALUES (?,?)",
                [("Resigned","Voluntary resignation"),
                 ("Removed","Removed for cause"),
                 ("Non-payment","Lapsed membership due to dues"),
                 ("Deceased","Death"),
                 ("Relocated","Moved away")])
cur.executemany("INSERT INTO profession (name, category) VALUES (?,?)",
                [("Planter","agriculture"),
                 ("Farmer","agriculture"),
                 ("Merchant","mercantile"),
                 ("Attorney","legal"),
                 ("Physician","medical"),
                 ("Clergy","religious"),
                 ("Surveyor","technical"),
                 ("Blacksmith","trade"),
                 ("Teacher","education")])
con.commit()

# Save DDL to file for reference
with open(schema_path, "w") as f:
    f.write(ddl)

(db_path, schema_path)
