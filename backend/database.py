
import sqlite3
from pathlib import Path
import numpy as np

# ==========================================
# Database Configuration
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "pawprint.db"

EMBEDDING_DIMENSION = 768

VALID_STATUSES = {"lost", "found"}

# ==========================================
# Database Connection
# ==========================================

def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


# ==========================================
# Create New Database Tables
# ==========================================

def init_db():

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Lost dogs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lost_dogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dog_name TEXT,
                image_path TEXT NOT NULL,
                district TEXT NOT NULL,
                date TEXT NOT NULL,
                size TEXT,
                color TEXT,
                reporter_name TEXT NOT NULL,
                contact TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Found dogs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS found_dogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dog_name TEXT,
                image_path TEXT NOT NULL,
                district TEXT NOT NULL,
                date TEXT NOT NULL,
                size TEXT,
                color TEXT,
                reporter_name TEXT NOT NULL,
                contact TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Potential matches between lost and found reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                lost_dog_id INTEGER NOT NULL,
                found_dog_id INTEGER NOT NULL,

                similarity REAL NOT NULL,

                status TEXT DEFAULT 'pending'
                    CHECK (
                        status IN (
                            'pending',
                            'confirmed',
                            'rejected'
                        )
                    ),

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(lost_dog_id, found_dog_id),

                FOREIGN KEY(lost_dog_id)
                    REFERENCES lost_dogs(id),

                FOREIGN KEY(found_dog_id)
                    REFERENCES found_dogs(id)
            )
        """)

        # Useful indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lost_dogs_district
            ON lost_dogs(district)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_found_dogs_district
            ON found_dogs(district)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lost_dogs_date
            ON lost_dogs(date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_found_dogs_date
            ON found_dogs(date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_matches_lost
            ON matches(lost_dog_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_matches_found
            ON matches(found_dog_id)
        """)

        # Migrate reports from the previous database design.
        migrate_legacy_reports(connection)

        connection.commit()

        print("Pawprint database initialized successfully!")
        print(f"Database location: {DATABASE_PATH}")

    finally:
        connection.close()


# ==========================================
# Migrate Previous Reports Table
# ==========================================

def migrate_legacy_reports(connection):

    cursor = connection.cursor()

    tables = {
        row["name"]
        for row in cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
        """).fetchall()
    }

    if "reports" not in tables:
        print("No previous reports table found.")
        return

    reports = cursor.execute("""
        SELECT *
        FROM reports
        ORDER BY id
    """).fetchall()

    migrated = 0

    for report in reports:

        status = report["status"]

        if status not in VALID_STATUSES:
            continue

        embedding_blob = report["embedding"]

        # Reports without embeddings cannot participate
        # in the new AI matching pipeline.
        if embedding_blob is None:
            print(
                f"Skipping legacy report {report['id']}: "
                "embedding is missing."
            )
            continue

        embedding = np.frombuffer(
            embedding_blob,
            dtype=np.float32
        )

        if embedding.shape != (EMBEDDING_DIMENSION,):
            print(
                f"Skipping legacy report {report['id']}: "
                "invalid embedding dimension."
            )
            continue

        table_name = (
            "lost_dogs" if status == "lost"
            else "found_dogs"
        )

        cursor.execute(f"""
            INSERT OR IGNORE INTO {table_name} (
                id,
                dog_name,
                image_path,
                district,
                date,
                size,
                color,
                reporter_name,
                contact,
                embedding,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report["id"],
            report["dog_name"],
            report["image_path"],
            "Unknown",
            report["date"],
            report["size"],
            report["color"],
            report["reporter_name"],
            report["contact"],
            embedding_blob,
            report["created_at"]
        ))

        if cursor.rowcount > 0:
            migrated += 1

    print(f"Legacy reports migrated: {migrated}")


# ==========================================
# Save New Lost or Found Report
# ==========================================

def save_dog_report(
    dog_name,
    status,
    image_path,
    district,
    date,
    size,
    color,
    reporter_name,
    contact,
    embedding
):

    status = status.strip().lower()
    district = district.strip()

    if status not in VALID_STATUSES:
        raise ValueError("Status must be lost or found.")

    if not district:
        raise ValueError("District is required.")

    embedding = np.asarray(
        embedding,
        dtype=np.float32
    )

    if embedding.shape != (EMBEDDING_DIMENSION,):
        raise ValueError(
            "Embedding must contain exactly 768 values."
        )

    if not np.isfinite(embedding).all():
        raise ValueError("Embedding contains invalid values.")

    table_name = (
        "lost_dogs" if status == "lost"
        else "found_dogs"
    )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(f"""
            INSERT INTO {table_name} (
                dog_name,
                image_path,
                district,
                date,
                size,
                color,
                reporter_name,
                contact,
                embedding
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dog_name.strip() if dog_name and dog_name.strip() else None,
            image_path,
            district,
            date,
            size,
            color,
            reporter_name.strip(),
            contact.strip(),
            embedding.tobytes()
        ))

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# ==========================================
# Retrieve Embeddings by Report Category
# ==========================================

def get_dog_embeddings(status):

    status = status.strip().lower()

    if status not in VALID_STATUSES:
        raise ValueError("Status must be lost or found.")

    table_name = (
        "lost_dogs" if status == "lost"
        else "found_dogs"
    )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(f"""
            SELECT *
            FROM {table_name}
            WHERE embedding IS NOT NULL
            ORDER BY id
        """)

        reports = cursor.fetchall()

        saved_reports = []

        for report in reports:

            embedding = np.frombuffer(
                report["embedding"],
                dtype=np.float32
            ).copy()

            if embedding.shape != (EMBEDDING_DIMENSION,):
                continue

            metadata = dict(report)

            metadata["status"] = status

            saved_reports.append({
                "report_id": report["id"],
                "embedding": embedding,
                "metadata": metadata
            })

        return saved_reports

    finally:
        connection.close()


# ==========================================
# Retrieve All Reports
# ==========================================

def get_reports(status=None):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if status is None:

            lost = cursor.execute("""
                SELECT *, 'lost' AS status
                FROM lost_dogs
                ORDER BY created_at DESC
            """).fetchall()

            found = cursor.execute("""
                SELECT *, 'found' AS status
                FROM found_dogs
                ORDER BY created_at DESC
            """).fetchall()

            return (
                [dict(row) for row in lost]
                + [dict(row) for row in found]
            )

        status = status.strip().lower()

        if status not in VALID_STATUSES:
            raise ValueError("Invalid report status.")

        table_name = (
            "lost_dogs" if status == "lost"
            else "found_dogs"
        )

        rows = cursor.execute(f"""
            SELECT *, ? AS status
            FROM {table_name}
            ORDER BY created_at DESC
        """, (status,)).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


# ==========================================
# Save Potential Match
# ==========================================

def save_match(
    lost_dog_id,
    found_dog_id,
    similarity
):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO matches (
                lost_dog_id,
                found_dog_id,
                similarity
            )
            VALUES (?, ?, ?)

            ON CONFLICT(lost_dog_id, found_dog_id)
            DO UPDATE SET
                similarity = excluded.similarity
        """, (
            lost_dog_id,
            found_dog_id,
            float(similarity)
        ))

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# ==========================================
# Retrieve Matches
# ==========================================

def get_matches(lost_dog_id=None, found_dog_id=None):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
            SELECT
                m.*,
                l.dog_name AS lost_dog_name,
                l.image_path AS lost_image_path,
                l.district AS lost_district,
                l.reporter_name AS lost_reporter_name,
                l.contact AS lost_contact,

                f.dog_name AS found_dog_name,
                f.image_path AS found_image_path,
                f.district AS found_district,
                f.reporter_name AS found_reporter_name,
                f.contact AS found_contact

            FROM matches m

            JOIN lost_dogs l
                ON l.id = m.lost_dog_id

            JOIN found_dogs f
                ON f.id = m.found_dog_id

            WHERE 1 = 1
        """

        parameters = []

        if lost_dog_id is not None:
            query += " AND m.lost_dog_id = ?"
            parameters.append(lost_dog_id)

        if found_dog_id is not None:
            query += " AND m.found_dog_id = ?"
            parameters.append(found_dog_id)

        query += " ORDER BY m.similarity DESC"

        rows = cursor.execute(
            query,
            parameters
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


if __name__ == "__main__":
    init_db()
