import os
import mysql.connector
from mysql.connector import pooling, Error
from dotenv import load_dotenv

load_dotenv()

# ------------------- DATABASE CONNECTION POOL -------------------
POOL = pooling.MySQLConnectionPool(
    pool_name="fe_pool",
    pool_size=10,
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "fe_db"),
    charset='utf8mb4'
)

# ------------------- UNIVERSAL QUERY FUNCTION -------------------
def query(sql, params=None, fetch="all"):
    """
    Helper function to execute SELECT / CALL / INSERT / UPDATE / DELETE safely.
    Handles stored procedures and clears all result sets properly.
    """
    conn = POOL.get_connection()
    try:
        cur = conn.cursor(dictionary=True)

        # If this is a stored procedure (CALL ...)
        if sql.strip().lower().startswith("call"):
            rows = []
            # Enable multi=True for stored procedures
            for result in cur.execute(sql, params or (), multi=True):
                if result.with_rows:
                    rows.extend(result.fetchall())
            # Consume all remaining result sets
            while cur.nextset():
                cur.fetchall()
            return rows if fetch != "one" else (rows[0] if rows else None)

        # If this is a normal SELECT
        elif sql.strip().lower().startswith("select"):
            cur.execute(sql, params or ())
            if fetch == "one":
                return cur.fetchone()
            return cur.fetchall()

        # For INSERT/UPDATE/DELETE
        else:
            cur.execute(sql, params or ())
            conn.commit()
            return cur.rowcount

    except Error as e:
        print(f"❌ DB Error in query(): {e}")
        raise

    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass


# ------------------- BATCH EXECUTION FUNCTION -------------------
def execute_many(sql, seq_of_params):
    conn = POOL.get_connection()
    try:
        cur = conn.cursor()
        cur.executemany(sql, seq_of_params)
        conn.commit()
        return cur.rowcount
    finally:
        cur.close()
        conn.close()
