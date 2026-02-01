from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "internalchat123"

ADMIN_PASSWORD = "1122"
DEFAULT_PASSWORD = "1962"

# ---------------- DATABASE ----------------
def get_db():
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_db()
    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id TEXT UNIQUE,
        name TEXT,
        password TEXT,
        role TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS groups(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT UNIQUE
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS group_members(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        emp_id TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS group_messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        sender TEXT,
        message TEXT,
        time TEXT
    )""")

    con.commit()
    con.close()

init_db()

# ---------------- CREATE ADMIN ----------------
def create_admin():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE emp_id='admin'")
    if not cur.fetchone():
        cur.execute("""
        INSERT INTO users(emp_id,name,password,role)
        VALUES('admin','System Admin',?, 'admin')
        """,(ADMIN_PASSWORD,))
        con.commit()
    con.close()

create_admin()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/login")

# ---------------- LOGIN ----------------
@app.route("/login",methods=["GET","POST"])
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
    SELECT g.* FROM groups g
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

    cur.execute("SELECT * FROM group_messages WHERE group_id=?",(gid,))
    chats=cur.fetchall()
    con.close()

    return render_template("group_chat.html",chats=chats)

# ---------------- GROUPS (ADMIN) ----------------
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
    cur.execute("INSERT INTO group_members(group_id,emp_id) VALUES(?,?)",(gid,emp))
    con.commit()
    con.close()
    return redirect("/groups")

# ---------------- MANAGE USERS ----------------
@app.route("/manage_users",methods=["GET","POST"])
def manage_users():
    if session.get("role")!="admin":
        return "Unauthorized"

    con=get_db()
    cur=con.cursor()

    if request.method=="POST":
        emp=request.form["emp"]
        name=request.form["name"]
        role=request.form["role"]
        cur.execute("""
        INSERT INTO users(emp_id,name,password,role)
        VALUES(?,?,?,?)
        """,(emp,name,DEFAULT_PASSWORD,role))
        con.commit()

    cur.execute("SELECT * FROM users")
    users=cur.fetchall()
    con.close()
    return render_template("manage_users.html",users=users)

# ---------------- RESET PASSWORD ----------------
@app.route("/reset_password/<emp>")
def reset_password(emp):
    con=get_db()
    cur=con.cursor()
    cur.execute("UPDATE users SET password=? WHERE emp_id=?",(DEFAULT_PASSWORD,emp))
    con.commit()
    con.close()
    return redirect("/manage_users")

# ---------------- COMPOSE MAIL ----------------
@app.route("/compose_mail",methods=["GET","POST"])
def compose_mail():
    msg=""
    if request.method=="POST":
        msg="Mail sent successfully (Demo Mode)"
    return render_template("compose_mail.html",msg=msg)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
