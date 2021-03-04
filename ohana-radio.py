#!/usr/bin/env python3

from flask import Flask, request, render_template, send_from_directory, redirect, url_for, abort
from flask_socketio import SocketIO, emit
import os
import subprocess
import json
from bluetooth_ctrl import BluetoothController

WEB_PORT = 9000
WEB_PORT = 80 	# Use this as root

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
PLS_PATH = os.path.join(os.path.expanduser('~'), 'playlists')
PLS_NAME = 'playlist'
CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.ohanaradio.cfg')

app = Flask(__name__, static_url_path='/assets', static_folder='assets')
app.secret_key = 'OCRadio1303153011SecretKey'

socketio = SocketIO(app, cors_allowed_origins="*")

url_list = []
current = 0
CMD_PLAY = "play"
CMD_STOP = "stop"
CMD_PAUSE = "pause"
CMD_CLEAR = "clear"
CMD_ADD = "add"
CMD_NEXT = "next"
CMD_LIST = "playlist"
CMD_DEL = "del"
CMD_CURRENT = "current"
CMD_MOVE = "move"
CMD_SAVE = "save"
CMD_LOAD = "load"

SYS_CMD_PWR_OFF = ['/usr/sbin/poweroff']

IP = None
stop_flag = False

BT_ctrl = BluetoothController()


def run_process(command_list):
    result = subprocess.run(command_list, stdout=subprocess.PIPE)
    # print("Running: {}".format(command_list))

    return str(result.stdout, 'utf-8')


def get_playlist():
    cmd = ['mpc', CMD_LIST]
    ret_val = run_process(cmd)
    if ret_val.endswith('\n'):
        ret_val = ret_val[:-1]
    return ret_val.split('\n')


def sort_playlist():
    # Get playlist
    temp_list = get_playlist()
    url_list = []
    for item in temp_list:
        url_list.append(item.replace('  ', ' '))

    # Get sorted playlist
    sorted_list = url_list.copy()
    sorted_list.sort()

    # Check actual positions compared to sorted
    for i in range(0, len(sorted_list)):
        current_id = url_list.index(sorted_list[i])

        if current_id != i:
            # move from current_id to position i. Note that mpc playlist index starts from 1.
            cmd = ['mpc', CMD_MOVE, str(current_id + 1), str(i + 1)]
            run_process(cmd)

            temp_list = get_playlist()
            url_list = []
            for item in temp_list:
                url_list.append(item.replace('  ', ' '))


def get_mpc_current():
    global current

    # get currently playing
    mpc_current = 0
    cmd = ['mpc']
    status = run_process(cmd).split('\n')

    for i in range(0, len(status)):
        if '[playing]' in status[i]:
            current = int(status[i].split('#')[1].split('/')[0])
            break


def get_song_title():
    cur_cmd = ['mpc', CMD_CURRENT]
    current_text = run_process(cur_cmd)
    # print("CURRENT:", current_text)

    if len(current_text) > 2:
        try:
            song_title = current_text.split(':')[1]
        except:
            song_title = current_text
    else:
        song_title = ''

    return song_title


def read_cfg_file():
    global CONFIG_FILE
    global PLS_PATH

    if not os.path.isfile(CONFIG_FILE):
        cfg_file = open(CONFIG_FILE, "w")
        cfg_file.close()

    if os.path.isfile(CONFIG_FILE):
        cfg_file = open(CONFIG_FILE, "r")
        try:
            data = json.loads(cfg_file.read())
        except:
            data = {}
        cfg_file.close()

    pls_path = data.get('PLS_PATH', PLS_PATH)
    PLS_PATH = pls_path

    bt_dev_mac = data.get('BT_DEV_MAC', '')
    BT_ctrl.set_default_bt_dev_mac(bt_dev_mac)

    bt_dev_name = data.get('BT_DEV_NAME', '')
    BT_ctrl.set_default_bt_dev_name(bt_dev_name)

    BT_ctrl.connect_bt_device(bt_dev_mac)


def update_cfg_file():
    data = {
        'PLS_PATH': PLS_PATH,
        'BT_DEV_NAME': BT_ctrl.get_default_bt_dev_name(),
        'BT_DEV_MAC': BT_ctrl.get_default_bt_dev_mac()
    }

    cfg_file = open(CONFIG_FILE, "w")
    cfg_file.write(json.dumps(data))
    cfg_file.close()


def load_cfg():
    global url_list
    global current

    # Get playlist
    new_url_list = get_playlist()

    # Populate list to display
    url_list = []
    for i in range(0, len(new_url_list)):
        item = new_url_list[i]
        name = item.split(':')[0]
        if name.startswith('http'):
            name = item.split('//')[1].split(':')[0].upper().replace('STREAMING', '').replace('STREAM', '').replace('..', '.')
            if name.startswith('.'):
                name = name[1:]

        data = {"name": name, "href": item, "id": len(url_list) + 1}
        url_list.append(data)

    # get currently playing
    current = 0
    cmd = ['mpc']
    status = run_process(cmd).split('\n')

    for i in range(0, len(status)):
        if '[playing]' in status[i]:
            current = int(status[i].split('#')[1].split('/')[0])


def report():
    get_mpc_current()
    data = {'items': url_list, 'current': current}
    emit('playlist', json.dumps(data))


@app.route('/', methods=['GET', 'POST'])
def home():
    global current

    # print('request:', request)
    load_cfg()

    action = request.args.get('action', '')
    id = int(request.args.get('id', '0'))

    if action == 'add':
        url = request.args.get('url', '').replace('"', '')

        if url != '':
            playlist = get_playlist()

            if url not in playlist:
                cmd = ['mpc', CMD_ADD, url]
                run_process(cmd)
                load_cfg()

    elif action == 'del':
        if (id > 0) and (id <= len(url_list)):

            cmd = ['mpc', CMD_DEL, str(id)]
            run_process(cmd)

            load_cfg()

    elif action == 'sort':
        sort_playlist()
        load_cfg()

    else:
        cur_cmd = ['mpc', CMD_CURRENT]
        current_text = run_process(cur_cmd)
        # print(current_text)
        if len(current_text) > 2:
            try:
                song_title = current_text.split(':')[1]
            except:
                song_title = current_text
        else:
            song_title = ''

        return render_template('index.html', song_title=song_title)

    return redirect(url_for('home'))


@app.route('/uploadpls', methods=['POST'])
def uploadpls():
    f = request.files['file']
    if f:
        content = f.read().decode('utf-8')

        url_list = []
        for line in content.split('\n'):
            if line.startswith('http'):
                url_list.append(line)

        if len(url_list) > 0:
            # Clear current playlist
            cmd = ['mpc', CMD_CLEAR]
            run_process(cmd)

            for url in url_list:
                cmd = ['mpc', CMD_ADD, url]
                run_process(cmd)

            cmd = ['mpc', CMD_PLAY, str(len(url_list) + 1)]
            run_process(cmd)

            load_cfg()

    return redirect(url_for('home'))


@app.route('/downloadpls', methods=['GET'])
def downloadpls():
    file_path = os.path.join(PLS_PATH, PLS_NAME + '.m3u')

    if os.path.isfile(file_path):
        os.remove(file_path)

    # Save current playlist
    cmd = ['mpc', CMD_SAVE, PLS_NAME]
    run_process(cmd)

    if os.path.isfile(file_path):
        return send_from_directory(PLS_PATH, PLS_NAME + '.m3u')
    else:
        print('Not found:', os.path.join(PLS_PATH, PLS_NAME + '.m3u'))
        abort(404)


@app.route('/savepls', methods=['GET'])
def savepls():
    file_path = os.path.join(PLS_PATH, PLS_NAME + '.m3u')

    if os.path.isfile(file_path):
        os.remove(file_path)

    # Save current playlist
    cmd = ['mpc', CMD_SAVE, PLS_NAME]
    run_process(cmd)

    load_cfg()

    return redirect(url_for('home'))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(SCRIPT_PATH, 'assets/favicon.ico', mimetype='image/vnd.microsoft.icon')


@socketio.on('connect')
def do_connect():
    report()


@socketio.on('command')
def do_command(command, item_id=0):
    if command == "vol_dn":
        BT_ctrl.bt_volume_down()
    elif command == "vol_up":
        BT_ctrl.bt_volume_up()
    elif command == "pwr_off":
        cmd = SYS_CMD_PWR_OFF
        run_process(cmd)
    elif command == "mpc_stop":
        cmd = ['mpc', CMD_STOP]
        run_process(cmd)
        report()
    elif command == "mpc_save":
        savepls()
    elif command == "mpc_title":
        song_title = get_song_title()
        data = {'song_title': song_title}
        emit('playlist', json.dumps(data))

    elif command == "mpc_play":
        if (item_id > 0) and (item_id <= len(url_list)):
            cmd = ['mpc', CMD_PLAY, str(item_id)]
            run_process(cmd)

            report()

    elif command == "bt_list":
        bt_dev_list = BT_ctrl.get_bt_client_list()
        emit('bt_devs', json.dumps(bt_dev_list))

    elif command == "bt_connect":
        BT_ctrl.disconnect_bt()
        BT_ctrl.connect_bt_device(item_id)
        update_cfg_file()

    elif command == "bt_disconnect":
        BT_ctrl.disconnect_bt()

    else:
        print("Unknown command:", command)


if __name__ == '__main__':
    cmd = ['mpc', CMD_CLEAR]
    run_process(cmd)
    cmd = ['mpc', CMD_LOAD, PLS_NAME]
    run_process(cmd)

    load_cfg()
    read_cfg_file()
    socketio.run(app, host='0.0.0.0', port=WEB_PORT, debug=False)
    stop_flag = True
