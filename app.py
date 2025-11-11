
import os
from datetime import date
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from db import query
from auth import User

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.by_id(user_id)

# Bootstrap admin account if missing
User.create_admin_if_missing(
    os.getenv("ADMIN_USERNAME", "admin"),
    os.getenv("ADMIN_PASSWORD", "admin123")
)

# ---------- Table metadata for generic CRUD ----------
TABLES = {
    "Court": {"pk": ["Court_ID"], "columns": ["Court_ID", "Court_Name", "Location"]},
    "Case_": {"pk": ["Case_ID"], "columns": ["Case_ID", "Title", "Description"]},
    "Investigator": {"pk": ["Investigator_ID"], "columns": ["Investigator_ID","Name","INVESTIGATION_Rank","Contact"]},
    "Lab": {"pk": ["Lab_ID"], "columns": ["Lab_ID","Lab_Name","Location"]},
    "Evidence": {"pk": ["Evidence_ID"], "columns": ["Evidence_ID","Evidence_Type","Description","Investigator_ID","Lab_ID"]},
    "Evidence_Item": {"pk": ["Item_ID"], "columns": ["Item_ID","Evidence_ID","Quantity","Description"]},
    "Report": {"pk": ["Report_ID"], "columns": ["Report_ID","Content","Date","Case_ID"]},
    "Suspect": {"pk": ["Suspect_ID"], "columns": ["Suspect_ID","Name","DOB","Street","City","State","Zip","Case_ID","Accomplice_ID"]},
    "Suspect_Alias": {"pk": ["Suspect_ID","Alias"], "columns": ["Suspect_ID","Alias"]},
    "Test_Result": {"pk": ["Result_ID"], "columns": ["Result_ID","Evidence_ID","Lab_ID","Result"]},
    "Trial": {"pk": ["Case_ID","Court_ID","Suspect_ID","Evidence_ID"], "columns": ["Case_ID","Court_ID","Suspect_ID","Evidence_ID"]},
    "Witness": {"pk": ["Witness_ID"], "columns": ["Witness_ID","Name","Statement"]},
    "Witnessed": {"pk": ["Case_ID","Witness_ID"], "columns": ["Case_ID","Witness_ID"]},
}

# ---------- Auth ----------
@app.get("/login")
def login():
    return render_template("login.html")

@app.post("/login")
def login_post():
    username = request.form.get("username")
    password = request.form.get("password")
    user = User.by_username(username)
    if not user or not user.check_password(password):
        flash("Invalid credentials", "error")
        return redirect(url_for("login"))
    login_user(user)
    return redirect(url_for("dashboard"))

@app.get("/signup")
def signup():
    return render_template("signup.html")

@app.post("/signup")
def signup_post():
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role") or 'readonly'
    if User.by_username(username):
        flash("Username already exists", "error")
        return redirect(url_for("signup"))
    ph = generate_password_hash(password)
    query("INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s)", (username, ph, role), fetch=None)
    flash("User registered. Please login.", "ok")
    return redirect(url_for("login"))

@app.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------- Dashboard (aggregates/joins) ----------
@app.get("/")
@login_required
def dashboard():
    cases_count = query("SELECT COUNT(*) AS cnt FROM Case_", fetch="one")["cnt"]
    evidence_by_type = query("SELECT Evidence_Type, COUNT(*) cnt FROM Evidence GROUP BY Evidence_Type ORDER BY cnt DESC")
    investigator_load = query("""
        SELECT i.Name, COUNT(a.Case_ID) cnt
        FROM Investigator i
        LEFT JOIN Assigned a ON a.Investigator_ID = i.Investigator_ID
        GROUP BY i.Investigator_ID
        ORDER BY cnt DESC, i.Name
        LIMIT 5
    """)
    lab_usage = query("""
        SELECT l.Lab_Name, COUNT(e.Evidence_ID) cnt
        FROM Lab l
        LEFT JOIN Evidence e ON e.Lab_ID = l.Lab_ID
        GROUP BY l.Lab_ID
        ORDER BY cnt DESC, l.Lab_Name
    """)
    # EXISTS: cases having ANY evidence (no type filter)
    cases_with_any_evidence = query("""
        SELECT c.Case_ID, c.Title
        FROM Case_ c
        WHERE EXISTS (
          SELECT 1
          FROM Trial t JOIN Evidence e ON e.Evidence_ID = t.Evidence_ID
          WHERE t.Case_ID = c.Case_ID
        )
        ORDER BY c.Case_ID
    """)
    return render_template(
        "dashboard.html",
        cases_count=cases_count,
        evidence_by_type=evidence_by_type,
        investigator_load=investigator_load,
        lab_usage=lab_usage,
        cases_with_any_evidence=cases_with_any_evidence,
    )

# ---------- Generic CRUD with role checks ----------
def is_readonly():
    return current_user.role == 'readonly'

@app.get("/table/<name>")
@login_required
def list_table(name):
    if name not in TABLES:
        flash("Unknown table", "error")
        return redirect(url_for("dashboard"))
    rows = query(f"SELECT * FROM `{name}` ORDER BY 1")
    return render_template("table_list.html", name=name, spec=TABLES[name], rows=rows, readonly=is_readonly())

@app.get("/table/<name>/new")
@login_required
def new_row(name):
    if is_readonly():
        flash("Read-only users cannot add data", "error")
        return redirect(url_for("list_table", name=name))
    return render_template("form.html", name=name, spec=TABLES[name], values={})

@app.post("/table/<name>/create")
@login_required
def create_row(name):
    if is_readonly():
        flash("Permission denied", "error")
        return redirect(url_for("list_table", name=name))
    cols = TABLES[name]["columns"]
    vals = [request.form.get(c) or None for c in cols]
    placeholders = ",".join(["%s"] * len(cols))
    sql = f"INSERT INTO `{name}` ({','.join('`'+c+'`' for c in cols)}) VALUES ({placeholders})"
    try:
        query(sql, tuple(vals), fetch=None)
        flash("Created", "ok")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("list_table", name=name))

@app.get("/table/<name>/edit")
@login_required
def edit_row(name):
    if is_readonly():
        flash("Read-only users cannot edit data", "error")
        return redirect(url_for("list_table", name=name))
    pk = TABLES[name]["pk"]
    where = " AND ".join(f"`{k}`=%s" for k in pk)
    params = tuple(request.args.get(k) for k in pk)
    row = query(f"SELECT * FROM `{name}` WHERE {where} LIMIT 1", params, fetch="one")
    return render_template("form.html", name=name, spec=TABLES[name], values=row)

@app.post("/table/<name>/update")
@login_required
def update_row(name):
    if is_readonly():
        flash("Permission denied", "error")
        return redirect(url_for("list_table", name=name))
    cols = TABLES[name]["columns"]
    pk = TABLES[name]["pk"]
    set_cols = [c for c in cols if c not in pk]
    set_expr = ", ".join(f"`{c}`=%s" for c in set_cols)
    where = " AND ".join(f"`{k}`=%s" for k in pk)
    set_vals = [request.form.get(c) or None for c in set_cols]
    pk_vals = [request.form.get(k) for k in pk]
    sql = f"UPDATE `{name}` SET {set_expr} WHERE {where}"
    try:
        query(sql, tuple(set_vals + pk_vals), fetch=None)
        flash("Updated", "ok")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("list_table", name=name))

@app.post("/table/<name>/delete")
@login_required
def delete_row(name):
    if is_readonly():
        flash("Permission denied", "error")
        return redirect(url_for("list_table", name=name))
    pk = TABLES[name]["pk"]
    where = " AND ".join(f"`{k}`=%s" for k in pk)
    params = tuple(request.form.get(k) for k in pk)
    try:
        query(f"DELETE FROM `{name}` WHERE {where}", params, fetch=None)
        flash("Deleted", "ok")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("list_table", name=name))

# ---------- Tools: procedures, functions, trigger log ----------
@app.get("/tools")
@login_required
def tools():
    return render_template("tools.html")

@app.post("/tools/add_case_with_report")
@login_required
def tool_add_case_with_report():
    caseTitle = request.form.get("caseTitle")
    caseDesc = request.form.get("caseDesc")
    reportContent = request.form.get("reportContent")
    reportDate = request.form.get("reportDate") or date.today().isoformat()

    try:
        # Call stored procedure and fetch the Case_ID + Report_ID
        result = query("CALL Add_Case_With_Report(%s,%s,%s,%s)",
                       (caseTitle, caseDesc, reportContent, reportDate),
                       fetch="all")

        # Extract IDs (from SELECT inside the procedure)
        if result and len(result) > 0:
            case_id = result[0]["Case_ID"]
            report_id = result[0]["Report_ID"]
            flash(f"✅ Case added successfully! Case_ID: {case_id}, Report_ID: {report_id}", "ok")
        else:
            flash("Procedure executed, but no IDs returned.", "warning")

    except Exception as e:
        flash(f"Error executing procedure: {e}", "error")

    return redirect(url_for("tools"))


@app.post("/tools/get_age")
@login_required
def tool_get_age():
    dob = request.form.get("dob")
    row = query("SELECT get_age(%s) AS age", (dob,), fetch="one")
    flash(f"Age = {row['age']}", "ok")
    return redirect(url_for("tools"))

@app.post("/tools/total_evidence")
@login_required
def tool_total_evidence():
    case_id = request.form.get("case_id")
    row = query("SELECT total_evidence(%s) AS total", (case_id,), fetch="one")
    flash(f"Total evidence for Case {case_id} = {row['total']}", "ok")
    return redirect(url_for("tools"))

@app.get("/evidence-log")
@login_required
def evidence_log():
    rows = query("""
        SELECT el.Log_ID, el.Evidence_ID, el.Action, el.Log_Time,
               e.Evidence_Type, e.Description
        FROM Evidence_Log el
        LEFT JOIN Evidence e ON e.Evidence_ID = el.Evidence_ID
        ORDER BY el.Log_Time DESC
        LIMIT 100
    """)
    return render_template("evidence_log.html", rows=rows)

@app.get("/tools/suspect_aliases")
@login_required
def tool_suspect_aliases():
    try:
        rows = query("CALL Get_Suspect_Aliases();")
        flash(f"✅ Retrieved {len(rows)} suspect alias records", "ok")
    except Exception as e:
        flash(f"Error executing Get_Suspect_Aliases: {e}", "error")
        rows = []

    return render_template(
        "table_list.html",
        name="Suspect Aliases (Proc)",
        spec={"columns": ["Suspect_ID", "Name", "Alias"], "pk": []},
        rows=rows,
        readonly=True
    )


# ---------- Analytics (joins / aggregates / nested) ----------
@app.get("/analytics/cases-with-evidence")
@login_required
def cases_with_evidence():
    rows = query("""
        SELECT c.Case_ID, c.Title
        FROM Case_ c
        WHERE EXISTS (
          SELECT 1
          FROM Trial t JOIN Evidence e ON e.Evidence_ID = t.Evidence_ID
          WHERE t.Case_ID = c.Case_ID
        )
        ORDER BY c.Case_ID
    """)
    return render_template("table_list.html",
                           name="Cases With Any Evidence (EXISTS)",
                           spec={"columns":["Case_ID","Title"], "pk":[]},
                           rows=rows, readonly=True)

@app.get("/analytics/evidence-by-case")
@login_required
def evidence_by_case():
    rows = query("""
        SELECT c.Case_ID, c.Title, COUNT(t.Evidence_ID) AS Evidence_Count
        FROM Case_ c
        LEFT JOIN Trial t ON t.Case_ID = c.Case_ID
        GROUP BY c.Case_ID, c.Title
        ORDER BY Evidence_Count DESC, c.Case_ID
    """)
    return render_template("table_list.html",
                           name="Evidence Count By Case (Aggregate)",
                           spec={"columns":["Case_ID","Title","Evidence_Count"], "pk":[]},
                           rows=rows, readonly=True)

@app.get("/analytics/investigator-workload")
@login_required
def investigator_workload():
    rows = query("""
        SELECT i.Investigator_ID, i.Name, COUNT(a.Case_ID) AS Case_Count
        FROM Investigator i
        LEFT JOIN Assigned a ON a.Investigator_ID = i.Investigator_ID
        GROUP BY i.Investigator_ID, i.Name
        ORDER BY Case_Count DESC, i.Name
    """)
    return render_template("table_list.html",
                           name="Investigator Workload (Aggregate)",
                           spec={"columns":["Investigator_ID","Name","Case_Count"], "pk":[]},
                           rows=rows, readonly=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
