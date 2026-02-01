from flask import Flask, render_template, request, redirect, session
import sqlite3, os

app = Flask(__name__)
app.secret_key = "internalchat123"

# ---------------- DB ----------------
def get_db():
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id TEXT UNIQUE,
        name TEXT,
        password TEXT,
        role TEXT
    )
    """)

    con.commit()
    con.close()

init_db()

# -------- CREATE FIRST ADMIN IF NOT EXIST --------
def create_admin():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE role='admin'")
    if not cur.fetchone():
        cur.execute("""
        INSERT INTO users(emp_id,name,password,role)
        VALUES('admin','System Admin','1234','admin')
        """)
        con.commit()
    con.close()

create_admin()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    error=""

    if request.method=="POST":
        emp=request.form["emp"]
        pwd=request.form["pwd"]
        role=request.form["role"]

        con=get_db()
        cur=con.cursor()
        cur.execute("""
        SELECT * FROM users
        WHERE emp_id=? AND password=? AND role=?
        """,(emp,pwd,role))
        user=cur.fetchone()
        con.close()

        if user:
            session["emp_id"]=user["emp_id"]
            session["name"]=user["name"]
            session["role"]=user["role"]
            return redirect("/dashboard")
        else:
            error="Invalid ID / Password / Role"

    return render_template("login.html",error=error)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ---------------- MANAGE USERS (ADMIN) ----------------
@app.route("/manage_users",methods=["GET","POST"])
def manage_users():

    if session.get("role")!="admin":
        return "Unauthorized"

    con=get_db()
    cur=con.cursor()

    if request.method=="POST":
        emp=request.form["emp"]
        name=request.form["name"]
        pwd=request.form["pwd"]
        role=request.form["role"]

        cur.execute("""
        INSERT INTO users(emp_id,name,password,role)
        VALUES(?,?,?,?)
        """,(emp,name,pwd,role))
        con.commit()

    cur.execute("SELECT * FROM users")
    users=cur.fetchall()
    con.close()

    return render_template("manage_users.html",users=users)

# ---------------- CHANGE ROLE ----------------
@app.route("/change_role/<uid>/<role>")
def change_role(uid,role):
    con=get_db()
    cur=con.cursor()
    cur.execute("UPDATE users SET role=? WHERE emp_id=?",(role,uid))
    con.commit()
    con.close()
    return redirect("/manage_users")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
