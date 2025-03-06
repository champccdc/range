from flask import Flask, render_template, request, make_response, redirect
from pveautomate.automate import ProxmoxManager
import getpass, os

PROX_URL = os.getenv("PROXMOX_URL", "https://192.168.3.236:8006") + "/api2/json"

app = Flask(__name__)

proxmox_url = PROX_URL
proxmox_user = "root@pam"
proxmox_password = getpass.getpass(f"Authenticate for {proxmox_user}: ")
node = "ccdc"

SUPER_SECRET = open(".passkey").read().strip()
AUTHK = "yup"

def_user_pw = "neccdc2025"

pm = ProxmoxManager(proxmox_url, proxmox_user, proxmox_password, node)


@app.route("/")
def home():
    return render_template(
        "page.html", render_template("<h2>Home</h2><a href='/login'>Login</a>")
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if request.cookies.get("flash"):
            flash = request.cookies.get("flash")
            pc = render_template("login.html", flash=flash)
            resp = make_response(render_template("page.html", content=pc))
            resp.set_cookie("flash", "", expires=0)
            return resp
        return render_template(
            "page.html", content=render_template("login.html", flash=None)
        )
    else:
        if request.form.get("password") == SUPER_SECRET:
            resp = make_response(redirect(request.args.get("next", "/admin")))
            resp.set_cookie("sk-lol", AUTHK)
            return resp
        else:
            resp = make_response(redirect("/login"))
            resp.set_cookie("flash", "Incorrect Password")
            return resp


@app.route("/logout")
def logout():
    resp = make_response(redirect(request.args.get("next", "/")))
    resp.set_cookie("sk-lol", "", expires=0)
    return resp


@app.route("/admin")
def adm():
    if request.cookies.get("sk-lol") == AUTHK:
        return render_template("admin.html", prox_login=proxmox_user, passw=def_user_pw)
    else:
        return redirect("/login?next=/admin")


@app.route("/ensure", methods=["POST"])
def ensure():
    if request.cookies.get("sk-lol") != AUTHK:
        return redirect("/login")
    else:
        data = request.get_json()

        usernames = data["usernames"].split(",")

        for username in usernames:
            uid = username + "@pve"
            if not pm.check_if_user(uid):
                pm.create_user(username, def_user_pw, "pve")

        return "Wahoo"


@app.route("/range", methods=["POST"])
def mrange():
    if request.cookies.get("sk-lol") != AUTHK:
        return redirect("/login")

    vmids = [int(vm_id) for vm_id in request.get_json()["vmids"].split(",")]
    users = request.get_json()["usernames"].split(",")

    print("Cloning VMs: ", vmids)
    print("For Users: ", users)

    try:
        for user in users:
            pm.create_range(vmids, user + "@pve")
        return "Wahoo"
    except Exception as e:
        return str(e)


@app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "page.html",
            content="<h2>Page not found. Please check spelling and try again</h2>",
        ),
        404,
    )


@app.errorhandler(500)
def uhoh_yikes(e):
    return (
        render_template(
            "page.html",
            content=f"<h2>Internal Server Error</h2><br/><pre><code>{str(e)}</code></pre>",
        ),
        500,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7878)
