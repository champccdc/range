from flask import Flask, render_template, request
from pveautomate.automate import ProxmoxManager
import getpass,os

PROX_URL = os.getenv("PROXMOX_URL", "https://192.168.3.236:8006") + "/api2/json"

app = Flask(__name__)

proxmox_url = PROX_URL
proxmox_user = "root@pam"
proxmox_password = getpass.getpass(f"Authenticate for {proxmox_user}: ")
node = "ccdc"

def_user_pw = "ChangeMeWheee"

pm = ProxmoxManager(proxmox_url, proxmox_user, proxmox_password, node)


@app.route('/')
def home():
    return render_template('index.html', prox_login=proxmox_user, passw=def_user_pw)

@app.route('/ensure', methods=['POST'])
def ensure():
    data = request.get_json()

    usernames = data['usernames'].split(',')

    for username in usernames:
        uid = username + "@pve"
        if not pm.check_if_user(uid):
            pm.create_user(username, def_user_pw, 'pve')

    return "Wahoo"

@app.route('/range', methods=['POST'])
def mrange():
    vmids = [int(vm_id) for vm_id in request.get_json()['vmids'].split(',')]
    users = request.get_json()['usernames'].split(',')

    print("Cloning VMs: ", vmids)
    print("For Users: ", users)

    try:
        for user in users:
            pm.create_range(vmids, user+'@pve')
        return "Wahoo"
    except Exception as e:
        return str(e)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7878)
