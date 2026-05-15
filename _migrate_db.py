"""
Migrate PostgreSQL data from Render to Neon.
Exports all tables from source DB and imports into target DB.
"""
import psycopg2
import psycopg2.extras
import sys

SOURCE_URL = "postgresql://wealthpilot:O6MhWo4cUQS1BMPPaCnlLhAODuAk96Iw@dpg-d7d9asf41pts739thpj0-a.oregon-postgres.render.com/wealthpilot?sslmode=require"
TARGET_URL = "postgresql://neondb_owner:npg_7cbGixnufMv6@ep-small-flower-aptdl5hz.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require"


def get_tables(conn):
    """Get all user tables in dependency order (respecting FKs)."""
    cur = conn.cursor()
    # Get tables in topological order (dependencies first)
    cur.execute("""
        WITH RECURSIVE fk_tree AS (
            SELECT t.oid, t.relname::text AS table_name, 0 AS depth
            FROM pg_class t
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = 'public' AND t.relkind = 'r'
              AND NOT EXISTS (
                  SELECT 1 FROM pg_constraint c
                  WHERE c.conrelid = t.oid AND c.contype = 'f'
              )
            UNION ALL
            SELECT t.oid, t.relname::text, ft.depth + 1
            FROM pg_class t
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_constraint c ON c.conrelid = t.oid AND c.contype = 'f'
            JOIN fk_tree ft ON ft.oid = c.confrelid
            WHERE n.nspname = 'public' AND t.relkind = 'r'
        )
        SELECT DISTINCT table_name FROM fk_tree
        ORDER BY MAX(depth), table_name;
    """)
    # Fallback: just get all tables if the recursive query has issues
    tables = [row[0] for row in cur.fetchall()]
    if not tables:
        cur.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        tables = [row[0] for row in cur.fetchall()]
    cur.close()
    return tables


def get_columns(conn, table):
    cur = conn.cursor()
    cur.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position;
    """, (table,))
    cols = [row[0] for row in cur.fetchall()]
    cur.close()
    return cols


def get_create_table_ddl(conn):
    """Get full DDL from source using pg_dump style - schema only."""
    cur = conn.cursor()
    # Get all table DDL
    cur.execute("""
        SELECT
            'CREATE TABLE IF NOT EXISTS ' || quote_ident(tablename) || ' ();'
        FROM pg_tables WHERE schemaname = 'public';
    """)
    cur.close()


def migrate():
    print("=" * 60)
    print("MyWealthPilot DB Migration: Render → Neon")
    print("=" * 60)

    # Connect to source
    print("\n[1/5] Connecting to SOURCE (Render)...")
    src = psycopg2.connect(SOURCE_URL)
    src.set_session(readonly=True)
    print("  ✓ Connected to Render DB")

    # Connect to target
    print("\n[2/5] Connecting to TARGET (Neon)...")
    tgt = psycopg2.connect(TARGET_URL)
    tgt.autocommit = False
    print("  ✓ Connected to Neon DB")

    # Get schema DDL from source
    print("\n[3/5] Copying schema...")
    src_cur = src.cursor()

    # Get full schema DDL
    src_cur.execute("""
        SELECT
            'DROP TABLE IF EXISTS ' || string_agg(quote_ident(tablename), ', ' ORDER BY tablename) || ' CASCADE;'
        FROM pg_tables WHERE schemaname = 'public';
    """)
    drop_stmt = src_cur.fetchone()[0]

    # Use information_schema to rebuild CREATE TABLE statements
    src_cur.execute("""
        SELECT table_name, column_name, data_type, is_nullable,
               column_default, character_maximum_length,
               numeric_precision, numeric_scale
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """)
    columns_info = src_cur.fetchall()

    # Get constraints
    src_cur.execute("""
        SELECT conrelid::regclass::text AS table_name,
               pg_get_constraintdef(oid) AS constraint_def,
               conname, contype
        FROM pg_constraint
        WHERE connamespace = 'public'::regnamespace
        ORDER BY contype DESC, conname;
    """)
    constraints = src_cur.fetchall()

    # Get indexes
    src_cur.execute("""
        SELECT indexdef FROM pg_indexes
        WHERE schemaname = 'public'
          AND indexname NOT LIKE '%_pkey'
          AND indexdef NOT LIKE '%UNIQUE%';
    """)
    indexes = [row[0] for row in src_cur.fetchall()]

    # Get sequences
    src_cur.execute("""
        SELECT sequence_name, last_value
        FROM information_schema.sequences s
        JOIN pg_sequences ps ON ps.schemaname = 'public' AND ps.sequencename = s.sequence_name
        WHERE s.sequence_schema = 'public';
    """)
    sequences_info = src_cur.fetchall()
    src_cur.close()

    # Instead of rebuilding DDL manually, let's use a simpler approach:
    # Use Flask-Migrate to create schema, then just copy data
    # But even simpler: dump and restore using psycopg2 COPY

    # Let's take a practical approach: get table list, recreate via
    # the app's SQLAlchemy models, then copy data
    tables = get_tables(src)
    print(f"  Found {len(tables)} tables: {', '.join(tables)}")

    # Drop existing tables in target and let Flask create schema
    tgt_cur = tgt.cursor()

    if drop_stmt and drop_stmt.strip() != 'CASCADE;':
        # First check if target has tables
        tgt_cur.execute("""
            SELECT tablename FROM pg_tables WHERE schemaname = 'public';
        """)
        existing = [r[0] for r in tgt_cur.fetchall()]
        if existing:
            tgt_cur.execute(
                'DROP TABLE IF EXISTS ' +
                ', '.join(f'"{t}"' for t in existing) +
                ' CASCADE;'
            )
            print(f"  Dropped {len(existing)} existing tables in target")

    # Copy schema by dumping DDL from source
    src_cur2 = src.cursor()

    # Get CREATE TABLE statements properly
    for table in tables:
        cols = []
        src_cur2.execute("""
            SELECT column_name, data_type, is_nullable, column_default,
                   character_maximum_length, numeric_precision, numeric_scale,
                   udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """, (table,))

        for col_name, data_type, nullable, default, max_len, num_prec, num_scale, udt_name in src_cur2.fetchall():
            # Map data types
            if udt_name == 'int4':
                col_type = 'INTEGER'
            elif udt_name == 'int8':
                col_type = 'BIGINT'
            elif udt_name == 'float8':
                col_type = 'DOUBLE PRECISION'
            elif udt_name == 'float4':
                col_type = 'REAL'
            elif udt_name == 'bool':
                col_type = 'BOOLEAN'
            elif udt_name == 'text':
                col_type = 'TEXT'
            elif udt_name == 'varchar':
                col_type = f'VARCHAR({max_len})' if max_len else 'VARCHAR'
            elif udt_name == 'numeric':
                if num_prec and num_scale:
                    col_type = f'NUMERIC({num_prec},{num_scale})'
                elif num_prec:
                    col_type = f'NUMERIC({num_prec})'
                else:
                    col_type = 'NUMERIC'
            elif udt_name == 'timestamp':
                col_type = 'TIMESTAMP WITHOUT TIME ZONE'
            elif udt_name == 'timestamptz':
                col_type = 'TIMESTAMP WITH TIME ZONE'
            elif udt_name == 'date':
                col_type = 'DATE'
            elif udt_name == 'json':
                col_type = 'JSON'
            elif udt_name == 'jsonb':
                col_type = 'JSONB'
            elif udt_name == 'uuid':
                col_type = 'UUID'
            else:
                col_type = data_type.upper()

            parts = [f'"{col_name}" {col_type}']
            if default:
                parts.append(f'DEFAULT {default}')
            if nullable == 'NO':
                parts.append('NOT NULL')
            cols.append(' '.join(parts))

        ddl = f'CREATE TABLE "{table}" (\n  ' + ',\n  '.join(cols) + '\n);'
        try:
            tgt_cur.execute(ddl)
        except Exception as e:
            print(f"  ⚠ Error creating {table}: {e}")
            tgt.rollback()
            tgt_cur = tgt.cursor()
            continue

    # Add primary keys
    src_cur2.execute("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY'
          AND tc.table_schema = 'public'
        ORDER BY tc.table_name;
    """)
    pk_map = {}
    for tname, colname in src_cur2.fetchall():
        pk_map.setdefault(tname, []).append(colname)

    for tname, pk_cols in pk_map.items():
        cols_str = ', '.join(f'"{c}"' for c in pk_cols)
        try:
            tgt_cur.execute(f'ALTER TABLE "{tname}" ADD PRIMARY KEY ({cols_str});')
        except Exception as e:
            print(f"  ⚠ PK error on {tname}: {e}")
            tgt.rollback()
            tgt_cur = tgt.cursor()

    # Add foreign keys
    src_cur2.execute("""
        SELECT conrelid::regclass::text, pg_get_constraintdef(oid), conname
        FROM pg_constraint
        WHERE connamespace = 'public'::regnamespace AND contype = 'f';
    """)
    for tname, condef, conname in src_cur2.fetchall():
        try:
            tgt_cur.execute(f'ALTER TABLE {tname} ADD CONSTRAINT "{conname}" {condef};')
        except Exception as e:
            print(f"  ⚠ FK error {conname}: {e}")
            tgt.rollback()
            tgt_cur = tgt.cursor()

    tgt.commit()
    print("  ✓ Schema copied")
    src_cur2.close()

    # Copy data
    print("\n[4/5] Copying data...")
    total_rows = 0
    for table in tables:
        cols = get_columns(src, table)
        if not cols:
            continue

        src_cur3 = src.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cols_quoted = ', '.join(f'"{c}"' for c in cols)
        src_cur3.execute(f'SELECT {cols_quoted} FROM "{table}";')
        rows = src_cur3.fetchall()
        src_cur3.close()

        if rows:
            placeholders = ', '.join(['%s'] * len(cols))
            insert_sql = f'INSERT INTO "{table}" ({cols_quoted}) VALUES ({placeholders});'
            tgt_cur2 = tgt.cursor()
            for row in rows:
                try:
                    tgt_cur2.execute(insert_sql, list(row))
                except Exception as e:
                    tgt.rollback()
                    tgt_cur2 = tgt.cursor()
                    print(f"  ⚠ Row error in {table}: {e}")
                    break
            tgt.commit()
            total_rows += len(rows)
            print(f"  ✓ {table}: {len(rows)} rows")
        else:
            print(f"  - {table}: 0 rows (empty)")

    # Reset sequences
    print("\n[5/5] Resetting sequences...")
    tgt_cur3 = tgt.cursor()
    for table in tables:
        try:
            tgt_cur3.execute(f"""
                SELECT column_name, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                  AND column_default LIKE 'nextval%%';
            """, (table,))
            seq_cols = tgt_cur3.fetchall()
            for col_name, col_default in seq_cols:
                # Extract sequence name from nextval('seq_name'::regclass)
                seq_name = col_default.split("'")[1]
                tgt_cur3.execute(f"""
                    SELECT setval('{seq_name}',
                        COALESCE((SELECT MAX("{col_name}") FROM "{table}"), 1));
                """)
                print(f"  ✓ Reset sequence {seq_name}")
        except Exception as e:
            print(f"  ⚠ Sequence error for {table}: {e}")
            tgt.rollback()
            tgt_cur3 = tgt.cursor()

    tgt.commit()

    # Close connections
    src.close()
    tgt.close()

    print("\n" + "=" * 60)
    print(f"✓ Migration complete! {total_rows} total rows copied.")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Go to Render Dashboard → wealthpilot web service → Environment")
    print("2. Change DATABASE_URL to:")
    print(f"   {TARGET_URL}")
    print("3. Save → auto-redeploy")


if __name__ == '__main__':
    migrate()
