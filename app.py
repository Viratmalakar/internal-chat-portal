from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3, os
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = "internalchat123"
UPLOAD_FOLDER="uploads"
os.makedirs(UPLOAD_FOLDER,exist_ok=True)

# ---------- DB ----------
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
    cc TEXT,
    subject TEXT,
    message TEXT,
    file TEXT,
    time TEXT)
    """)
    con.commit()
    con.close()

init_db()

# ---------- DEFAULT ADMIN ----------
def create_admin():
    con=get_db()
    cur=con.cursor()
    cur.execute("SELECT * FROM users WHERE emp_id='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users(emp_id,name,password,role) VALUES('admin','Admin','Bfil@123','admin')")
        con.commit()
    con.close()

create_admin()

# ---------- LOGIN ----------
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

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    con=get_db()
    cur=con.cursor()

    cur.execute("""
    SELECT m.*, 
    u1.name as sender_name,
    u2.name as receiver_name
    FROM messages m
    LEFT JOIN users u1 ON m.sender=u1.emp_id
    LEFT JOIN users u2 ON m.receiver=u2.emp_id
    WHERE receiver=? OR cc LIKE ?
    ORDER BY id DESC
    """,(session["user"],"%"+session["user"]+"%"))

    mails=cur.fetchall()
    con.close()
    return render_template("dashboard.html",mails=mails)

# ---------- COMPOSE ----------
@app.route("/compose",methods=["GET","POST"])
def compose():
    con=get_db()
    cur=con.cursor()
    cur.execute("SELECT emp_id,name FROM users")
    users=cur.fetchall()

    if request.method=="POST":
        to=request.form["to"]
        cc=request.form["cc"]
        subject=request.form["subject"]
        msg=request.form["message"]

        file=request.files["file"]
        fname=""
        if file and file.filename!="":
            fname=file.filename
            file.save(os.path.join(UPLOAD_FOLDER,fname))

        cur.execute("""INSERT INTO messages
        (sender,receiver,cc,subject,message,file,time)
        VALUES(?,?,?,?,?,?,?)""",
        (session["user"],to,cc,subject,msg,fname,str(datetime.now())))
        con.commit()
        return redirect("/dashboard")

    return render_template("compose.html",users=users)

# ---------- ADD USER ----------
@app.route("/add_user",methods=["GET","POST"])
def add_user():
    if request.method=="POST":
        emp=request.form["emp"]
        name=request.form["name"]
        pwd=request.form["pwd"]
        role=request.form["role"]
        con=get_db()
        cur=con.cursor()
        cur.execute("INSERT INTO users(emp_id,name,password,role) VALUES(?,?,?,?)",(emp,name,pwd,role))
        con.commit()
    return render_template("add_user.html")

# ---------- DOWNLOAD ----------
@app.route("/download")
def download():
    con=get_db()
    df=pd.read_sql("""
    SELECT m.sender,u1.name as sender_name,
           m.receiver,u2.name as receiver_name,
           subject,message,time
    FROM messages m
    LEFT JOIN users u1 ON m.sender=u1.emp_id
    LEFT JOIN users u2 ON m.receiver=u2.emp_id
    """,con)

    file="chat_report.xlsx"
    df.to_excel(file,index=False)
    return send_file(file,as_attachment=True)

# ---------- RUN ----------
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
