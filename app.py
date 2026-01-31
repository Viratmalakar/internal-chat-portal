from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key="internalchat123"

AGENT_PASS="1962"
SUPPORT_PASS="1122"

# ---------------- DB ----------------
def get_db():
    con=sqlite3.connect("database.db")
    con.row_factory=sqlite3.Row
    return con

def init_db():
    con=get_db()
    cur=con.cursor()

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

# ---------------- LOGIN ----------------
@app.route("/",methods=["GET","POST"])
def login():
    error=""
    if request.method=="POST":
        campaign=request.form["campaign"]
        uid=request.form["loginid"]
        pwd=request.form["password"]

        if campaign in ["Inbound","Outbound"] and pwd==AGENT_PASS:
            session["user"]=uid
            session["role"]="agent"
            session["campaign"]=campaign
            return redirect("/dashboard")

        elif campaign=="Support Staff" and pwd==SUPPORT_PASS:
            session["user"]="Support"
            session["role"]="support"
            session["campaign"]="Support"
            return redirect("/dashboard")

        else:
            error="Invalid Credentials"

    return render_template("login.html",error=error)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    con=get_db()
    cur=con.cursor()
    cur.execute("SELECT * FROM messages WHERE receiver=? ORDER BY id DESC",
                (session["user"],))
    mails=cur.fetchall()
    con.close()
    return render_template("dashboard.html",mails=mails)

# ---------------- COMPOSE ----------------
@app.route("/compose",methods=["GET","POST"])
def compose():

    if request.method=="POST":
        to_campaign=request.form["to_campaign"]
        subject=request.form["subject"]
        msg=request.form["message"]

        con=get_db()
        cur=con.cursor()

        # ===== SUPPORT SENDING =====
        if session["role"]=="support":

            if to_campaign=="Inbound":
                targets=["Inbound","Support"]

            elif to_campaign=="Outbound":
                targets=["Outbound","Support"]

            for r in targets:
                cur.execute("""
                INSERT INTO messages(sender,receiver,subject,message,time)
                VALUES(?,?,?,?,?)
                """,(session["user"],r,subject,msg,str(datetime.now())))

        # ===== AGENT SENDING =====
        else:
            # goes to support AND agent's own campaign
            targets=["Support",session["campaign"]]

            for r in targets:
                cur.execute("""
                INSERT INTO messages(sender,receiver,subject,message,time)
                VALUES(?,?,?,?,?)
                """,(session["user"],r,subject,msg,str(datetime.now())))

        con.commit()
        con.close()
        return redirect("/dashboard")

    return render_template("compose.html")

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

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
