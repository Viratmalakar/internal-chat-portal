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
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        subject TEXT,
        message TEXT,
        time TEXT
    )
    """)

    con.commit()
    con.close()

init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():

    error = ""

    if request.method == "POST":

        campaign = request.form["campaign"]
        loginid = request.form["loginid"]
        password = request.form["password"]

        # PASSWORD RULE
        if campaign in ["Inbound","Outbound"] and password == "1962":
            session["user"] = loginid
            session["role"] = "agent"
            session["campaign"] = campaign
            return redirect("/dashboard")

        elif campaign == "Support Staff" and password == "1122":
            session["user"] = "Support"
            session["role"] = "admin"
            return redirect("/dashboard")

        else:
            error = "Invalid Login Credentials"

    return render_template("login.html", error=error)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    return f"""
    <h2>Welcome {session.get('user')}</h2>
    <p>Campaign: {session.get('campaign')}</p>
    <a href='/logout'>Logout</a>
    """

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
