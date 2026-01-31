from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3, os
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key="internalchat123"

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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    subject TEXT,
    message TEXT,
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
        cur.execute("INSERT INTO users(emp_id,name,password,role) VALUES('admin','Admin','Bfil@123','admin')")
        con.commit()
    con.close()

create_admin()

# ---------------- LOGIN ----------------
@app.route("/",methods=["GET","POST"])
def login():
    if request.method=="POST":
        emp=request.form["emp"]
        pwd=request.form["pwd"]
        con=get_db()
        cur=con.cursor()
        cur.execute("SELECT * FROM users WHERE emp_id=? AND password=?",(emp,pwd))
        u=cur.fetchone()
        con.close()
        if u:
            session["user"]=u["emp_id"]
            session["role"]=u["role"]
            return redirect("/dashboard")
    return render_template("login.html")

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
    con.close()
    return render_template("dashboard.html",mails=mails)

# ---------------- SENT ----------------
@app.route("/sent")
def sent():
    con=get_db()
    cur=con.cursor()
    cur.execute("""
    SELECT * FROM messages
    WHERE sender=?
    ORDER BY id DESC
    """,(session["user"],))
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
        INSERT INTO messages(sender,receiver,subject,message,time)
        VALUES(?,?,?,?,?)
        """,(session["user"],to,subject,msg,str(datetime.now())))
        con.commit()
        return redirect("/dashboard")

    return render_template("compose.html",users=users)

# ---------------- ADD USER ----------------
@app.route("/add_user",methods=["GET","POST"])
def add_user():
    if request.method=="POST":
        emp=request.form["emp"]
        name=request.form["name"]
        pwd=request.form["pwd"]
        role=request.form["role"]

        con=get_db()
        cur=con.cursor()
        cur.execute("INSERT INTO users(emp_id,name,password,role) VALUES(?,?,?,?)",
                    (emp,name,pwd,role))
        con.commit()
    return render_template("add_user.html")

# ---------------- MANAGE AGENTS ----------------
@app.route("/manage_agents")
def manage_agents():
    con=get_db()
    cur=con.cursor()
    cur.execute("SELECT * FROM users WHERE role='agent'")
    agents=cur.fetchall()
    con.close()
    return render_template("manage_agents.html",agents=agents)

@app.route("/delete_agent/<emp>")
def delete_agent(emp):
    con=get_db()
    cur=con.cursor()
    cur.execute("DELETE FROM users WHERE emp_id=?",(emp,))
    con.commit()
    con.close()
    return redirect("/manage_agents")

# ---------------- DOWNLOAD REPORT ----------------
@app.route("/download")
def download():
    con=get_db()
    df=pd.read_sql("SELECT * FROM messages",con)
    df.to_excel("chat_report.xlsx",index=False)
    return send_file("chat_report.xlsx",as_attachment=True)

# ---------------- RUN ----------------
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
