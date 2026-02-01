from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "internalchat123"
DEFAULT_PASSWORD = "1962"

# ---------------- DATABASE ----------------
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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS groups(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT UNIQUE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS group_members(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        emp_id TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS group_messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        sender TEXT,
        message TEXT,
        time TEXT
    )
    """)

    con.commit()
    con.close()

init_db()

# ---------------- CREATE ADMIN ----------------
def create_admin():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE emp_id='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users(emp_id,name,password,role) VALUES(?,?,?,?)",
            ("admin","System Admin",DEFAULT_PASSWORD,"admin")
        )
        con.commit()
    con.close()

create_admin()

# ---------------- BULK AGENT CREATE ----------------
def create_agents():
    agents = [
        ("160251","Rupali Vishwakarma","inbound"),
        ("160312","Poonam Dwivedi","inbound"),
        ("160386","Nafisa","inbound"),
        ("160417","Summer Singh Ghosh","inbound"),
        ("160431","Neha Jat","inbound"),
        ("160432","Baldev Singh","inbound"),
        ("160435","Pankaj Saket","inbound"),
        ("160437","Dinesh Kumar Ahirwar","inbound"),
        ("170010","Sanju Jatav","inbound"),
        ("160366","Golu Yadav","inbound"),
        ("160368","Swati Barman","inbound"),
        ("TDAH1671","Sonu waghde","inbound"),
        ("160299","Savita Uikey","inbound"),
        ("160401","Pooja Sisodiya","inbound"),
        ("160418","Shiva Rai","inbound"),
        ("TDAH2932","Deepika Jhade","inbound"),
        ("160502","Khushi Thakur","inbound"),
        ("160433","Megha Rani Parmar","inbound"),
        ("160458","Harshit Patidar","inbound"),
        ("160459","Umashankar Kumawat","inbound"),
        ("TDAH2899","Sunita Jadhaw","inbound"),
        ("160493","Tosif","inbound"),
        ("160494","Mahendra Pal","inbound"),
        ("160495","Pankaj","inbound"),
        ("TDAH2939","Sabju Pal","inbound"),
        ("160438","Sunil Baghel","inbound"),
        ("160250","Arti Vishwakarma","inbound"),
        ("160272","Sheetal Osari","inbound"),
        ("160300","Anupma Mishra","inbound"),
        ("160304","Varsha Dhakad","inbound"),
        ("160367","Mukesh Sastiya","inbound"),
        ("160427","Ashish Gadhekar","inbound"),
        ("160434","Gourav Mishra","inbound"),
        ("160461","Ritik Kourav","inbound"),
        ("160472","Priyanka Sharma","inbound"),
        ("160473","Nilesh","inbound"),
        ("160478","Vaishali Patle","inbound"),
        ("TDAH1784","Ankit Yadav","inbound"),
        ("TDAH2576","Anjali Yadav","inbound"),
        ("160491","Shireesh Katare","inbound"),
        ("170085","Diksha Shriwastav","inbound"),
        ("160503","Tameshwari Patle","inbound"),
        ("160504","Manish Joshi","inbound"),

        ("160385","Vaishnavi Saner","outbound"),
        ("170049","Shivangi Verma","outbound"),
        ("170111","Ritika Tiwari","outbound"),
        ("TDAH1613","Vaishali Nandeshwar","outbound"),
        ("160261","Pankaj Chidar","outbound"),
        ("170092","Swadesh Singhasiya","outbound"),
        ("170109","Mastram Patel","outbound")
    ]

    con = get_db()
    cur = con.cursor()

    for emp,name,role in agents:
        cur.execute("""
        INSERT OR IGNORE INTO users(emp_id,name,password,role)
        VALUES(?,?,?,?)
        """,(emp,name,DEFAULT_PASSWORD,role))

    con.commit()
    con.close()

create_agents()

# ---------------- ROOT ----------------
@app.route("/")
def home():
    return redirect("/login")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
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
        u=cur.fetchone()
        con.close()

        if u:
            session["emp_id"]=u["emp_id"]
            session["name"]=u["name"]
            session["role"]=u["role"]
            return redirect("/dashboard")
        else:
            error="Invalid Credentials"

    return render_template("login.html",error=error)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    con=get_db()
    cur=con.cursor()
    cur.execute("""
    SELECT g.*
    FROM groups g
    JOIN group_members m ON g.id=m.group_id
    WHERE m.emp_id=?
    """,(session["emp_id"],))
    groups=cur.fetchall()
    con.close()
    return render_template("dashboard.html",groups=groups)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
