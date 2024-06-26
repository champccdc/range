import requests
import json
import time
import getpass
import urllib3
import csv
from random import randint

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

vm_data_headers = ["VMID", "IP", "OWNER", "HNAME"]
vm_data = []
raw_data = ""

proxmox_url = "https://10.0.1.12:8006/api2/json"
proxmox_user = "root@pam"
proxmox_password = getpass.getpass(f"Authenticate for {proxmox_user}: ")
verify_ssl = False

node = "pve4"


def write_vm_data():
    with open("data.csv", "w", newline="") as file:
        csv_writer = csv.DictWriter(file, fieldnames=vm_data_headers)

        # Write the header
        csv_writer.writeheader()

        # Write the data rows
        csv_writer.writerows(vm_data)


def read_vm_data():
    rd = open("data.csv")
    reader = csv.DictReader(rd)
    vm_data = []
    for l in reader:
        vm_data.append(l)
    raw_data = rd.read()
    rd.close()


def authenticate():
    response = requests.post(
        f"{proxmox_url}/access/ticket",
        data={"username": proxmox_user, "password": proxmox_password},
        verify=verify_ssl,
    )
    response.raise_for_status()
    data = response.json()["data"]
    return data["ticket"], data["CSRFPreventionToken"]


def get_next_vm_id(ticket):
    next_id_url = f"{proxmox_url}/cluster/nextid"
    headers = {"Cookie": f"PVEAuthCookie={ticket}"}
    response = requests.get(next_id_url, headers=headers, verify=verify_ssl)
    response.raise_for_status()
    next_id = response.json()["data"]
    return next_id


def clone_vm(ticket, csrf_token, template_id, new_name, new_id):
    clone_url = f"{proxmox_url}/nodes/{node}/qemu/{template_id}/clone"
    headers = {"Cookie": f"PVEAuthCookie={ticket}", "CSRFPreventionToken": csrf_token}
    payload = {"newid": new_id, "name": new_name, "node": node, "vmid": template_id}
    response = requests.post(
        clone_url, headers=headers, data=payload, verify=verify_ssl
    )
    response.raise_for_status()
    return response.json()["data"]


def assign_permissions(ticket, csrf_token, vm_id, user):
    acl_url = f"{proxmox_url}/access/acl"
    headers = {"Cookie": f"PVEAuthCookie={ticket}", "CSRFPreventionToken": csrf_token}
    payload = {"path": f"/vms/{vm_id}", "users": user, "roles": "Administrator"}
    # print(f"Sending ACL payload: {payload}")
    response = requests.put(acl_url, headers=headers, data=payload, verify=verify_ssl)
    # print(f"ACL response: {response.status_code} - {response.text}")
    response.raise_for_status()


def set_vm_desc(ticket, csrf_token, vm_id, desc):
    conf_url = f"{proxmox_url}/nodes/{node}/qemu/{vm_id}/config"
    headers = {"Cookie": f"PVEAuthCookie={ticket}", "CSRFPreventionToken": csrf_token}
    payload = {
        "description": desc,
    }
    response = requests.put(conf_url, headers=headers, data=payload, verify=verify_ssl)
    response.raise_for_status()


def destroy_vm(node, vmid):
    ticket, csrf_token = authenticate()
    delete_url = f"{proxmox_url}/nodes/{node}/qemu/{vmid}"
    headers = {"Cookie": f"PVEAuthCookie={ticket}", "CSRFPreventionToken": csrf_token}
    response = requests.delete(delete_url, headers=headers, verify=verify_ssl)
    response.raise_for_status()
    for vm in vm_data:
        if str(vm["VMID"]) == str(vmid):
            vm_data.remove(vm)
    write_vm_data()
    print(f"VM {vmid} on node {node} has been destroyed.")


def destroy_range():
    # TODO: why does this skip VMs?
    read_vm_data()
    for vm in vm_data:
        print("Destroying VMID " + str(vm["VMID"]))
        destroy_vm(node, vm["VMID"])


def create_win_range(user=None):
    template_vm_ids = [112, 135, 144]
    if user is None:
        user = input("Owner user (format 'foo@pve' or 'foo@pam'): ")
    uf = user.split("@")[0]
    new_instance_names = [uf + "-win1", uf + "-win2", uf + "-win3"]

    ticket, csrf_token = authenticate()
    for template_id, new_name in zip(template_vm_ids, new_instance_names):

        new_id = get_next_vm_id(ticket)
        clone_vm(ticket, csrf_token, template_id, new_name, new_id)
        time.sleep(2)
        assign_permissions(ticket, csrf_token, new_id, user)

        ip_last_bits = randint(100, 140)
        found = True
        while found:
            if "." + str(ip_last_bits) not in raw_data:
                found = False
            else:
                ip_last_bits = randint(100, 140)

        data = {
            "VMID": str(new_id),
            "IP": "10.0.1." + str(ip_last_bits),
            "OWNER": user,
            "HNAME": new_name,
        }
        vm_data.append(data)

        set_vm_desc(ticket, csrf_token, new_id, "My IP should be set to: " + data["IP"])

        print(
            f"VMID - {new_id}, {new_name} cloned from template {template_id} and permissions assigned to {user}"
        )
        write_vm_data()


if __name__ == "__main__":

    running = True

    while running:
        read_vm_data()
        print(
            """1. Create Windows range VMs for user
2. Destroy single VM
3. Destroy multiple VMs
4. Destroy ALL range VMs
5. Create Windows range VMs for multiple users
Q. Quit"""
        )
        c = input("> ")
        if c == "1":
            create_win_range()
        elif c == "5":
            users = input("Comma-seperated list of users to make VMs for: ")
            for user in users.split(","):
                if not '@' in user:
                    user = user + "@pve"
                create_win_range(user)
        elif c == "2":
            destroy_vm(node, int(input("VMID to destroy (NO CONFIRMATION): ")))
        elif c == "3":
            kaboom = input("Comma-seperated list to remove (NO CONFIRMATION): ")
            for id in kaboom.split(","):
                destroy_vm(node, int(id))
        elif c == "4":
            destroy_range()
        else:
            running = False