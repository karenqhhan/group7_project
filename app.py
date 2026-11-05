import os
import psycopg2
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    return psycopg2.connect(db_url)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def get_data():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            p.production_id,
            p.respondent_id,
            p.production_name,
            p.respondent_role,
            p.production_type,
            p.shoot_days,
            p.hours_per_day,
            p.total_shoot_hours,
            rh.role_hired,
            rh.ease_of_finding,
            rh.performance_rating,
            rh.would_hire_again,
            rh.flaked_last_minute,
            COALESCE(STRING_AGG(sm.method_name, ', '), 'None Specified') AS sourcing_channels
        FROM productions p
        JOIN role_hires rh ON p.production_id = rh.production_id
        LEFT JOIN hire_sourcing_methods hsm ON rh.hire_id = hsm.hire_id
        LEFT JOIN sourcing_methods sm ON hsm.method_id = sm.method_id
        GROUP BY p.production_id, rh.hire_id
        ORDER BY p.production_id ASC;
    """)
    
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "production_id": r[0],
            "respondent_id": r[1],
            "production_name": r[2],
            "respondent_role": r[3],
            "production_type": r[4],
            "shoot_days": r[5],
            "hours_per_day": r[6],
            "total_shoot_hours": r[7],
            "role_hired": r[8],
            "ease_of_finding": r[9],
            "performance_rating": r[10],
            "would_hire_again": r[11],
            "flaked_last_minute": r[12],
            "sourcing_channels": r[13]
        })

    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)