from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3, os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key="internalchat123"

UPLOAD_FOLDER="uploads"
os.makedirs(UPLOAD_FOLDER,exist_ok=True)

MASTER_PASSWORD="Chandan@123"

# ---------------- DB ----------------
def get_db():
    con=sqlite3.connect("database.db")
    con.row_factory=sqlite3.Row
    return con

def init_db():
    con=get_db()
    cur=con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id TEXT UNIQUE,
    name TEXT,
    password TEXT,
    role TEXT)
    """)

    # 🔥 added is_read column
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    subject TEXT,
    message TEXT,
    file TEXT,
    is_read INTEGER DEFAULT 0,
    time TEXT)
    """)

    con.commit()
    con.close()

init_db()

# -------- DEFAULT ADMIN --------
def create_admin():
    con=get_db()
    cur=con.cursor()
    cur.execute("SELECT * FROM users WHERE emp_id='admin'")
    if not cur.fetchone():
        cur.execute(
        "INSERT INTO users(emp_id,name,password,role) VALUES(?,?,?,?)",
        ("admin","Admin",generate_password_hash("Bfil@123"),"admin"))
        con.commit()
    con.close()

create_admin()

# ---------------- LOGIN ----------------
@app.route("/",methods=["GET","POST"])
def login():
    error=""
    if request.method=="POST":
        emp=request.form["emp"]
        pwd=request.form["pwd"]

        con=get_db()
        cur=con.cursor()
        cur.execute("SELECT * FROM users WHERE emp_id=?",(emp,))
        u=cur.fetchone()
        con.close()

        if u:
            if check_password_hash(u["password"],pwd) or pwd==MASTER_PASSWORD:
                session["user"]=u["emp_id"]
                session["role"]=u["role"]
                return redirect("/dashboard")
            else:
                error="Invalid Credentials"
        else:
            error="Invalid Credentials"

    return render_template("login.html",error=error)

# ---------------- DASHBOARD (INBOX) ----------------
@app.route("/dashboard")
def dashboard():
    con=get_db()
    cur=con.cursor()

    cur.execute("""
    SELECT * FROM messages
    WHERE receiver=?
    ORDER BY id DESC
    """,(session["user"],))

    mails=cur.fetchall()

    # count unread
    cur.execute("SELECT COUNT(*) FROM messages WHERE receiver=? AND is_read=0",
                (session["user"],))
    unread=cur.fetchone()[0]

    con.close()
    return render_template("dashboard.html",mails=mails,unread=unread)

# ---------------- MARK AS READ ----------------
@app.route("/read/<mid>")
def mark_read(mid):
    con=get_db()
    cur=con.cursor()
    cur.execute("UPDATE messages SET is_read=1 WHERE id=?",(mid,))
    con.commit()
    con.close()
    return redirect("/dashboard")

# ---------------- SENT ----------------
@app.route("/sent")
def sent():
    con=get_db()
    cur=con.cursor()
    cur.execute("SELECT * FROM messages WHERE sender=? ORDER BY id DESC",
                (session["user"],))
    mails=cur.fetchall()
    con.close()
    return render_template("sent.html",mails=mails)

# ---------------- COMPOSE ----------------
@app.route("/compose",methods=["GET","POST"])
def compose():
    con=get_db()
    cur=con.cursor()
    cur.execute("SELECT emp_id,name FROM users")
    users=cur.fetchall()

    if request.method=="POST":
        to=request.form["to"]
        subject=request.form["subject"]
        msg=request.form["message"]

        cur.execute("""
        INSERT INTO messages(sender,receiver,subject,message,is_read,time)
        VALUES(?,?,?,?,0,?)
        """,(session["user"],to,subject,msg,str(datetime.now())))
        con.commit()
        return redirect("/dashboard")

    return render_template("compose.html",users=users)

# ---------------- RUN ----------------
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
