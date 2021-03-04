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


class BluetoothController:
    def __init__(self):
        self.current_device_name = ""
        self.current_device_mac = ""
        self.discovered_devices = {}

    @staticmethod
    def __run_process__(command):
        cmd = command.split(" ")
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        return str(result.stdout, 'utf-8')

    def set_default_bt_dev_mac(self, mac_address):
        self.current_device_mac = mac_address

    def get_default_bt_dev_mac(self):
        return self.current_device_mac

    def set_default_bt_dev_name(self, name):
        self.current_device_name = name

    def get_default_bt_dev_name(self):
        return self.current_device_name

    def bt_volume_up(self):
        if self.current_device_name is not None:
            cmd = 'amixer -D bluealsa set "' + self.current_device_name + ' - A2DP" 10%+'
            self.__run_process__(cmd)

    def bt_volume_down(self):
        if self.current_device_name is not None:
            cmd = 'amixer -D bluealsa set "' + self.current_device_name + ' - A2DP" 10%-'
            self.__run_process__(cmd)

    def get_bt_client_list(self):
        self.__run_process__(CMD_POWER_ON)

        response = self.__run_process__(CMD_SCAN)

        self.discovered_devices = {}
        dev_ids = []
        for line in response.split("\n"):
            if "Scanning" not in line and '\t' in line:
                dev_text = line.strip()
                dev_data = dev_text.split('\t')
                dev_ids.append(dev_data)
                self.discovered_devices[dev_data[0]] = dev_data[1]
        return dev_ids

    def connect_bt_device(self, mac_address):
        self.current_device_name = self.discovered_devices.get(mac_address, self.current_device_name)
        self.current_device_mac = mac_address

        self.__run_process__(CMD_POWER_ON)
        self.__run_process__(CMD_TRUST + mac_address)

        response = self.__run_process__(CMD_CONNECT + mac_address)
        if "successful" not in response.lower():
            return 1

        return 0

    def disconnect_bt(self):
        # Get paired devices
        response = self.__run_process__(CMD_LIST_PAIRED)
        for word in response.split(" "):
            if ":" in word:
                self.__run_process__(CMD_DISCONNECT + word)
