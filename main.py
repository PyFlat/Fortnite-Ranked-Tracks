import json
import os
from datetime import date, datetime
from pathlib import Path
from subprocess import CalledProcessError, run

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# ---------------- Configuration ----------------
DB_CONFIG = {
    "user": os.getenv("PG_USER"),
    "host": os.getenv("PG_HOST"),
    "database": os.getenv("PG_DATABASE"),
    "password": os.getenv("PG_PASSWORD"),
    "port": int(os.getenv("PG_PORT", 5432)),
}

REPO_DIR = Path(__file__).parent  # Git repo directory
FILE_PATH = REPO_DIR / "data.json"
GIT_COMMIT_MSG = "Update JSON data"
QUERY = "SELECT * FROM ranked.seasons"


# ---------------- JSON serializer ----------------
def json_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


# ---------------- Main function ----------------
def fetch_data_and_update_file():
    os.chdir(REPO_DIR)  # Ensure Git commands run in the repo
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(QUERY)
        data = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]

        data_dicts = [dict(zip(colnames, row)) for row in data]

        # Write JSON file
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data_dicts, f, indent=2, default=json_serializer)

        print("✔ Data written to JSON file.")

        # Git commands: only commit if there are changes
        try:
            run(["git", "add", str(FILE_PATH)], check=True)
            status = run(
                ["git", "status", "--porcelain"], capture_output=True, text=True
            )
            if status.stdout.strip():  # Non-empty = changes exist
                run(["git", "commit", "-m", GIT_COMMIT_MSG], check=True)
                run(["git", "push"], check=True)
                print("🚀 Changes committed and pushed.")
            else:
                print("ℹ No changes detected. Skipping Git commit.")
        except CalledProcessError as git_err:
            print(f"❌ Git error: {git_err}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if "cur" in locals():
            cur.close()
        if "conn" in locals():
            conn.close()


# ---------------- Run ----------------
if __name__ == "__main__":
    fetch_data_and_update_file()
