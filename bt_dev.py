#!/usr/bin/env python3
'''
Helper script to connect/disconnect from bluetooth device and control volume
'''

import subprocess

CMD_POWER_ON = "bluetoothctl power on"
CMD_SCAN = "hcitool -i hci0 scan"
CMD_TRUST = "bluetoothctl trust "
CMD_CONNECT = "bluetoothctl connect "
CMD_DISCONNECT = "bluetoothctl disconnect "
CMD_PAIR = "bluetoothctl pair "
CMD_LIST_PAIRED = "bluetoothctl paired-devices"


def run_process(command):
    cmd = command.split(" ")
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    return str(result.stdout, 'utf-8')


def get_bt_client_list():
    run_process(CMD_POWER_ON)

    response = run_process(CMD_SCAN)

    dev_ids = []
    for line in response.split("\n"):
        if "Scanning" not in line and '\t' in line:
            dev_text = line.strip()
            dev_ids.append(dev_text.split('\t'))

    return dev_ids


def connect_bt_device(mac_address):
    run_process(CMD_POWER_ON)
    run_process(CMD_TRUST + mac_address)

    response = run_process(CMD_CONNECT + mac_address)
    if "successful" not in response.lower():
        return 1

    return 0


def disconnect_bt():
    # Get paired devices
    response = run_process(CMD_LIST_PAIRED)
    for word in response.split(" "):
        if ":" in word:
            response = run_process(CMD_DISCONNECT + word)
            if "successful" not in response.lower():
                return 1
            else:
                return 0
