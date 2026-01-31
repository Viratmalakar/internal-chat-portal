from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3, os
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = "internalchat123"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_db()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,emp_id TEXT UNIQUE,name TEXT,password TEXT,role TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,sender TEXT,receiver TEXT,cc TEXT,subject TEXT,message TEXT,file TEXT,time TEXT)")
    con.commit()
    con.close()

init_db()

def create_admin():
    con=get_db()
    cur=con.cursor()
    cur.execute("SELECT * FROM users WHERE emp_id='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users(emp_id,name,password,role) VALUES('admin','Admin','Bfil@123','admin')")
        con.commit()
    con.close()

create_admin()

@app.route("/",methods=["GET","POST"])
def login():
    if request.method=="POST":
        emp=request.form["emp"]
        pwd=request.form["pwd"]
        con=get_db()
        cur=con.cursor()
        cur.execute("SELECT * FROM users WHERE emp_id=? AND password=?",(emp,pwd))
        user=cur.fetchone()
        con.close()
        if user:
            session["user"]=user["emp_id"]
            session["role"]=user["role"]
            return redirect("/dashboard")
        return "Invalid Login"
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    con=get_db()
    cur=con.cursor()
    cur.execute("SELECT * FROM messages WHERE receiver=? OR cc LIKE ? ORDER BY id DESC",(session["user"],"%"+session["user"]+"%"))
    mails=cur.fetchall()
    con.close()
    return render_template("dashboard.html",mails=mails)

@app.route("/compose",methods=["GET","POST"])
def compose():
    if request.method=="POST":
        to=request.form["to"]
        cc=request.form["cc"]
        subject=request.form["subject"]
        msg=request.form["message"]
        file=request.files["file"]
        filename=""
        if file and file.filename!="":
            filename=file.filename
            file.save(os.path.join(UPLOAD_FOLDER,filename))
        con=get_db()
        cur=con.cursor()
        cur.execute("INSERT INTO messages(sender,receiver,cc,subject,message,file,time) VALUES(?,?,?,?,?,?,?)",(session["user"],to,cc,subject,msg,filename,str(datetime.now())))
        con.commit()
        con.close()
        return redirect("/dashboard")
    return render_template("compose.html")

@app.route("/add_user",methods=["GET","POST"])
def add_user():
    if session.get("role")!="admin":
        return "Unauthorized"
    if request.method=="POST":
        emp=request.form["emp"]
        name=request.form["name"]
        pwd=request.form["pwd"]
        role=request.form["role"]
        con=get_db()
        cur=con.cursor()
        cur.execute("INSERT INTO users(emp_id,name,password,role) VALUES(?,?,?,?)",(emp,name,pwd,role))
        con.commit()
        con.close()
        return redirect("/add_user")
    return render_template("add_user.html")

@app.route("/download")
def download():
    con=get_db()
    df=pd.read_sql("SELECT * FROM messages",con)
    file="chat_report.xlsx"
    df.to_excel(file,index=False)
    return send_file(file,as_attachment=True)

if __name__=="__main__":
    app.run(debug=True)
