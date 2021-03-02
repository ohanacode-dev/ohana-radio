# ohana-radio, a Flask based python internet radio web interface #

The idea is to enable controlling a central radio via any web enabled device (phone). This project is intended only for linux. 
It is tested on Ubuntu20.
We are using Media Player Daemon to play an internet radio stream and Media Player Client to controll it.

# Why another MPC web interface

I love myMPD and how it works, but it is quite complex to add my own buttons and functions. I am hoping to create a more minimalistic interface and source code and simplify adding custom functions.

### Setting up ###

The script uses mpd and mpc to play a stream and python Flask to display the web interface. Install them all.

    sudo apt install mpd mpc python3-pip
    pip3 install flask		# To be able to run as user
    sudo pip3 install flask	# To be able to run as root

The next step is to configure the configuration file: 
    
    /etc/mpd.conf.

In the first section: Files and directories, change all paths to a folder in your home location like: 

    /home/<user>/.mpd/

Change user from mpd to your user name.

In the Audio Output section, to find the correct setting I had to run: 

    aplay -l

and got response:

    card 0: Generic [HD-Audio Generic], device 3: HDMI 0 [HDMI 0]
        Subdevices: 1/1
        subdevice #0: subdevice #0
    card 1: Generic_1 [HD-Audio Generic], device 0: ALC256 Analog [ALC256 Analog]
        Subdevices: 1/1
        Subdevice #0: subdevice #0

So my setting is:

    audio_output {
        type		"alsa"
        name		"Generic_1" 

Now restart your computer or try just the mpd service:

    sudo systemctl restart mpd.service

Try the mpd settings using:

    mpd --stdout --no-daemon --verbose

If any errors are displayed, you need to solve them and restart the mpd service. For your conveniance, there is an mpd.conf example file in this folder.

Test MPC:

    mpc help
    mpc add https://stream.vanillaradio.com:8028/live
    mpc play
    mpc stop

Run the radio script:

    chmod +x ohana-radio.py
    sudo ./ohana-radio.py

Currently the web interface will listen to port 80, so to access it, it must be ran as root. The address on the same computer is: 

    http://localhost

From remote computer use:

    http://192.168.x.x

or what ever the IP address is.
If you wish to use it without root priviledges, you need to change the port at the start of the ohana-radio.py script from WEB_PORT=80 to some other value like WEB_PORT=8888. To access it, use your computers IP address and the port 8888. On the same computer this will be 

    http://localhost:8888

or if it is on a remote computer: 

    http://192.168.x.x:8888 

An automated script, setupRadio.sh is also provided to help with the setup.

## Setting up on a single board computer ##

I used an OrangePi Zero to build an internet radio. On an Armbian OS it was enough to install mpc and mpd. No additional configuration was required. 
Added an audio amplifier with a potentiometer for volume control. Used 3 push buttons connected to GPIO pins for previous, next and play/pause.
My script to control the mpc functions via gpio is preset here as gpioctl.py. To start it, run: 
```
sudo apt install python3-dev
pip3 install OrangePi.GPIO
chmod +x gpiocmd.py
sudo ./gpiocmd.py
```

A usefull way to run it is to add it to sudoers as:
my_user_name	ALL=(ALL) NOPASSWD: path_to_gpiocmd.py
Then you can run it without a password.
Even better, run it as a cron job: sudo crontab -e
Append: <path_to_gpiocmd.py>	

## Streaming audio from another linux machine ##

Tried using pulse audio to stream audio to my internet radio, but the bandwidth was too high. Instead I installed on my desktop computer icecast and darkice:
```
sudo apt-get install icecast2 darkice

```

Start the server:
```
service icecast2 start
```

Create a darkice configuration file /etc/darkice.cfg with following content (do check the password):
```
[general]
duration = 0
bufferSecs = 5
reconnect = yes

[input]
device = default
sampleRate = 44100
bitsPerSample = 16
channel = 2

[icecast2-0]
bitrateMode = abr
format = vorbis
bitrate = 96

# Make sure your server 
server = localhost
port = 8000
password = your_icecast_password
mountPoint = defaultaudio.ogg
name = Your stream name
description = Streaming audio from my desktop
url = http://localhost
genre = my own
public = yes
localDumpFile = dump.ogg
```

Now start darkice:
```
darkice
```

On your internet radio add a playlist entry:
http://<your_server_ip>:8000/defaultaudio.ogg


To setup a streaming service on your comuter, you can also use my script: setupStreaming.sh
NOTE: It is conveniant if you set your computer IP address to static so the URL does not change through router restart.

## Raspberry Pi Zero W to bluetooth speaker ##

1. sudo apt install bluealsa

2. usermod -a -G lp,audio pi

3. To connect run: 
	bluetoothctl
	power on
	scan on
	# Here you observe all discovered devices so you can copy your device MAC address 
	# (DEV_ID, something like 00:1A:7D:DA:71:13)
	pair <DEV_ID>
	trust <DEV_ID>
	connect <DEV_ID>
	quit

4. After this, to connect from a script, create: /home/pi/bt_reconnect.sh

	#!/bin/bash

	address="<DEV_ID>"

	if ! hcitool con | grep -q ${address}; then
		bluetoothctl power on
		bluetoothctl connect ${address}
	fi
	
5. Run this as cronjob at 5 minutes: crontab -e

	*/5 * * * * /home/pi/bt_reconnect.sh

6. Basic test by playing a sound: 

	aplay -D bluealsa:HCI=hci0,DEV=00:1A:7D:DA:71:13,PROFILE=a2dp /usr/share/sounds/alsa/Front_Center.wav

7. nano ~/.asoundrc

	defaults.bluealsa.interface "hci0"
	defaults.bluealsa.device "DEV=<DEV_ID>"
	defaults.bluealsa.profile "a2dp"
	defaults.bluealsa.delay 10000

8. test settings:

	aplay -D bluealsa /usr/share/sounds/alsa/Front_Center.wav

9. find out your devices controll name: 

	amixer -D bluealsa
 
This should display in the first row something like:
	Simple mixer control 'MX400 - A2DP',0
	...
So my device control name is: 'MX400 - A2DP'

10. configure MPD: sudo nano /etc/mpd.conf

	audio_output {
	  type          "alsa"
	  name          "Any name you wish"
	  device        "bluealsa"
	  mixer_device  "bluealsa"
	  mixer_control "MX400 - A2DP"
	}

11. After a reboot this should play audio to your bluetooth speaker.

## Contact ##

* [My busines web page](http://www.ohanacode-dev.com)
* [My personal web page](http://www.radinaradionica.com)

