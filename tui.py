import requests
import json
import time
import getpass
import urllib3
import csv,os
from random import randint

from pveautomate.automate import ProxmoxManager

PROX_URL = os.getenv("PROXMOX_URL", "https://192.168.3.236") + "/api2/json"

if __name__ == "__main__":
    proxmox_url = PROX_URL
    proxmox_user = "root@pam"
    proxmox_password = getpass.getpass(f"Authenticate for {proxmox_user}: ")
    node = "ccdc"

    manager = ProxmoxManager(proxmox_url, proxmox_user, proxmox_password, node)

    running = True

    while running:
        manager.read_vm_data()
        print(
            """1. Create Windows range VMs for user
2. Destroy single VM
3. Destroy multiple VMs
4. Destroy ALL range VMs
5. Create Windows range VMs for multiple users
6. Create new user
Q. Quit"""
        )
        c = input("> ")
        if c == "1":
            manager.create_range([100,101])
        elif c == "5":
            users = input("Comma-seperated list of users to make VMs for: ")
            for user in users.split(","):
                if not '@' in user:
                    user = user + "@pve"
                manager.create_range([100,101], user)
        elif c == "2":
            manager.destroy_vm(int(input("VMID to destroy (NO CONFIRMATION): ")))
        elif c == "3":
            kaboom = input("Comma-seperated list to remove (NO CONFIRMATION): ")
            for id in kaboom.split(","):
                manager.destroy_vm(int(id))
        elif c == "4":
            manager.destroy_range()
        elif c == "6":
            manager.create_user(input("Username: "), getpass.getpass("Password: "), 'pve')
        else:
            running = False
