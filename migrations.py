"""
Safe, idempotent schema upgrade for existing databases.

`Base.metadata.create_all()` creates NEW tables but never alters existing ones.
This module adds the new columns introduced by the upgrade to tables that
already exist (SQLite and PostgreSQL both support `ALTER TABLE ... ADD COLUMN`).
Existing rows and data are never modified or removed.
"""
from sqlalchemy import inspect, text

# table -> [(column, DDL type + default)]
NEW_COLUMNS = {
    "users": [
        ("role", "VARCHAR(20) DEFAULT 'student'"),
        ("xp", "INTEGER DEFAULT 0"),
        ("bio", "TEXT DEFAULT ''"),
        ("last_active_at", "DATETIME"),
    ],
    "problems": [
        ("points", "INTEGER DEFAULT 100"),
        ("is_published", "BOOLEAN DEFAULT 1"),
        ("tags", "VARCHAR(200) DEFAULT ''"),
    ],
    "test_cases": [
        ("weight", "INTEGER DEFAULT 1"),
    ],
    "submissions": [
        ("score", "FLOAT DEFAULT 0"),
        ("contest_id", "INTEGER"),
        ("max_memory_kb", "INTEGER DEFAULT 0"),
        ("similarity_score", "FLOAT DEFAULT 0"),
    ],
}


def run_migrations(engine):
    from app.database import Base
    from app import models  # noqa: F401  (register all tables)

    Base.metadata.create_all(bind=engine)  # new tables
    insp = inspect(engine)
    applied = []
    with engine.begin() as conn:
        for table, cols in NEW_COLUMNS.items():
            if not insp.has_table(table):
                continue
            existing = {c["name"] for c in insp.get_columns(table)}
            for name, ddl in cols:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                    applied.append(f"{table}.{name}")
                    existing.add(name)
        # Generic pass: any column declared in models.py but missing from an existing
        # table (e.g. from an older database) is added too, so no query can hit
        # "no such column".
        for table_name, table in Base.metadata.tables.items():
            if not insp.has_table(table_name):
                continue
            existing = {c["name"] for c in insp.get_columns(table_name)}
            existing |= {n.split(".", 1)[1] for n in applied if n.startswith(table_name + ".")}
            for col in table.columns:
                if col.name in existing or col.primary_key:
                    continue
                ddl = col.type.compile(dialect=engine.dialect)
                conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {col.name} {ddl}'))
                applied.append(f"{table_name}.{col.name}")
        # Backfill roles from the legacy is_admin flag (never downgrades anyone).
        conn.execute(text("UPDATE users SET role='admin' WHERE is_admin = 1 AND (role IS NULL OR role='student')"))
        conn.execute(text("UPDATE users SET role='student' WHERE role IS NULL"))
        conn.execute(text("UPDATE users SET xp=0 WHERE xp IS NULL"))
        conn.execute(text("UPDATE problems SET points=100 WHERE points IS NULL"))
        conn.execute(text("UPDATE problems SET is_published=1 WHERE is_published IS NULL"))
        conn.execute(text("UPDATE test_cases SET weight=1 WHERE weight IS NULL"))
        conn.execute(text("UPDATE submissions SET score=0 WHERE score IS NULL"))
    return applied
