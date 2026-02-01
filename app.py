from flask import Flask, render_template, request, redirect, session
import sqlite3, os, smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key="internalchat123"

SMTP_EMAIL = "yourgmail@gmail.com"
SMTP_PASS  = "your_app_password"

# ---------------- DB ----------------
def get_db():
    con=sqlite3.connect("database.db")
    con.row_factory=sqlite3.Row
    return con

def init_db():
    con=get_db()
    cur=con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        id INTEGER PRIMARY KEY,
        external_email TEXT
    )
    """)

    cur.execute("INSERT OR IGNORE INTO settings(id,external_email) VALUES(1,'')")

    con.commit()
    con.close()

init_db()

# ---------------- SETTINGS ----------------
@app.route("/settings",methods=["GET","POST"])
def settings():
    if session.get("role")!="admin":
        return "Unauthorized"

    con=get_db()
    cur=con.cursor()

    if request.method=="POST":
        email=request.form["email"]
        cur.execute("UPDATE settings SET external_email=? WHERE id=1",(email,))
        con.commit()

    cur.execute("SELECT external_email FROM settings WHERE id=1")
    email=cur.fetchone()["external_email"]
    con.close()

    return render_template("settings.html",email=email)

# ---------------- COMPOSE MAIL ----------------
@app.route("/compose_mail",methods=["GET","POST"])
def compose_mail():
    if request.method=="POST":
        subject=request.form["subject"]
        msg=request.form["message"]

        con=get_db()
        cur=con.cursor()
        cur.execute("SELECT external_email FROM settings WHERE id=1")
        ext=cur.fetchone()["external_email"]
        con.close()

        if ext:
            mail=EmailMessage()
            mail["From"]=SMTP_EMAIL
            mail["To"]=ext
            mail["Subject"]=subject
            mail.set_content(msg)

            with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
                smtp.login(SMTP_EMAIL,SMTP_PASS)
                smtp.send_message(mail)

    return render_template("compose_mail.html")

# ---------------- RUN ----------------
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
