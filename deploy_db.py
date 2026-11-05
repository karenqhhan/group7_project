import os
import csv
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def deploy():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL missing from .env")
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # 1. Execute SQL schema
    with open("schema.sql", "r") as f:
        cur.execute(f.read())
    conn.commit()

    # 2. Locate Survey Data CSV
    csv_file = "Survey Data (1).csv"
    if not os.path.exists(csv_file):
        csv_file = "Survey Data.csv"
    if not os.path.exists(csv_file):
        print("Error: CSV dataset file not found in root directory.")
        return

    sourcing_cols = [
        'Tisch Database', 'Instagram ISOs', 'Facebook Groups', 'Other Social Media',
        'Backstage', 'Apps', 'Cold Email / Pitching', 'WOM / Peer Recommendations',
        'Classmates', 'Already Know', 'Already Worked With'
    ]

    with open(csv_file, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            respondent = row.get("Respondent #", "Unknown")
            production_name = row.get("Production Name", "Untitled")
            respondent_role = row.get("Respondent Role", "")
            production_type = row.get("Production Type", "")

            try:
                shoot_days = int(row.get("Shoot Days", 0))
            except ValueError:
                shoot_days = 0

            try:
                hours_per_day = int(row.get("Hours Per Day", 0))
            except ValueError:
                hours_per_day = 0

            try:
                total_hours = int(row.get("Total Shoot Hours", 0))
            except ValueError:
                total_hours = shoot_days * hours_per_day

            # Insert into productions
            cur.execute(
                """INSERT INTO productions 
                   (respondent_id, production_name, respondent_role, production_type, shoot_days, hours_per_day, total_shoot_hours)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   RETURNING production_id;""",
                (respondent, production_name, respondent_role, production_type, shoot_days, hours_per_day, total_hours)
            )
            production_id = cur.fetchone()[0]

            # Insert into role_hires
            role_hired = row.get("Role Hired", "General Crew")
            try:
                ease = int(row.get("Ease of finding (1-10)", 0))
            except ValueError:
                ease = None
            try:
                perf = int(row.get("Performance (1-10)", 0))
            except ValueError:
                perf = None
            would_hire = row.get("Would hire again", "")
            flaked = row.get("Cancelled/flaked 24-48h (for anyone hired in this position)", "")

            cur.execute(
                """INSERT INTO role_hires 
                   (production_id, role_hired, ease_of_finding, performance_rating, would_hire_again, flaked_last_minute)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   RETURNING hire_id;""",
                (production_id, role_hired, ease, perf, would_hire, flaked)
            )
            hire_id = cur.fetchone()[0]

            # Populate bridge table
            for col in sourcing_cols:
                val = row.get(col, "0")
                if str(val).strip() in ["1", "1.0", "Y", "Yes", "true", "True"]:
                    cur.execute(
                        "INSERT INTO sourcing_methods (method_name) VALUES (%s) ON CONFLICT (method_name) DO NOTHING;",
                        (col,)
                    )
                    cur.execute(
                        """INSERT INTO hire_sourcing_methods (hire_id, method_id)
                           VALUES (%s, (SELECT method_id FROM sourcing_methods WHERE method_name = %s))
                           ON CONFLICT DO NOTHING;""",
                        (hire_id, col)
                    )

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM productions;")
    p_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM role_hires;")
    h_count = cur.fetchone()[0]

    print(f"Database Seeded Successfully! Loaded {p_count} productions and {h_count} role hires into Postgres.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    deploy()