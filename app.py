from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "internalchat123"

# ---------------- DATABASE ----------------
def get_db():
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_db()
    cur = con.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id TEXT UNIQUE,
        name TEXT,
        password TEXT,
        role TEXT
    )
    """)

    # GROUPS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS groups(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT UNIQUE
    )
    """)

    # GROUP MEMBERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS group_members(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        emp_id TEXT
    )
    """)

    # GROUP MESSAGES
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

# ---------------- CREATE DEFAULT ADMIN ----------------
def create_admin():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE emp_id='admin'")
    if not cur.fetchone():
        cur.execute("""
        INSERT INTO users(emp_id,name,password,role)
        VALUES('admin','System Admin','1234','admin')
        """)
        con.commit()
    con.close()

create_admin()

# ---------------- ROOT ----------------
@app.route("/")
def home():
    return redirect("/login")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    error=""

    if request.method=="POST":
        emp = request.form["emp"]
        pwd = request.form["pwd"]
        role = request.form["role"]

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

# ---------------- GROUP CHAT ----------------
@app.route("/group_chat/<gid>",methods=["GET","POST"])
def group_chat(gid):
    con=get_db()
    cur=con.cursor()

    if request.method=="POST":
        msg=request.form["message"]
        cur.execute("""
        INSERT INTO group_messages(group_id,sender,message,time)
        VALUES(?,?,?,?)
        """,(gid,session["name"],msg,str(datetime.now())))
        con.commit()

    cur.execute("""
    SELECT * FROM group_messages
    WHERE group_id=?
    ORDER BY id ASC
    """,(gid,))
    chats=cur.fetchall()
    con.close()

    return render_template("group_chat.html",chats=chats)

# ---------------- MANAGE GROUPS (ADMIN) ----------------
@app.route("/groups",methods=["GET","POST"])
def groups():
    if session.get("role")!="admin":
        return "Unauthorized"

    con=get_db()
    cur=con.cursor()

    if request.method=="POST":
        gname=request.form["gname"]
        cur.execute("INSERT INTO groups(group_name) VALUES(?)",(gname,))
        con.commit()

    cur.execute("SELECT * FROM groups")
    groups=cur.fetchall()
    con.close()
    return render_template("groups.html",groups=groups)

# ---------------- ADD MEMBER ----------------
@app.route("/add_member/<gid>",methods=["POST"])
def add_member(gid):
    emp=request.form["emp"]
    con=get_db()
    cur=con.cursor()
    cur.execute("""
    INSERT INTO group_members(group_id,emp_id)
    VALUES(?,?)
    """,(gid,emp))
    con.commit()
    con.close()
    return redirect("/groups")

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

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
