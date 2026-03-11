import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Execute SQL directly
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

with open("apply_semantic_metadata.sql", "r", encoding="utf-8") as f:
    sql = f.read()

try:
    cur.execute(sql)
    # Also notify pgrst to reload the schema cache
    cur.execute("NOTIFY pgrst, 'reload schema';")
    conn.commit()
    print("Migration applied successfully!")
except Exception as e:
    conn.rollback()
    print(f"Error applying migration: {e}")
finally:
    cur.close()
    conn.close()
