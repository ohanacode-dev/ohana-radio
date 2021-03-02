#!/bin/bash

cd $(dirname "$0")

sudo apt install mpd mpc python3-pip
sudo pip3 install Flask Flask-SocketIO==4.3.2

