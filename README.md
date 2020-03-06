# Python-ReadBluetoothScale
Passively listen for and read weight from Etekcity ESF24 Bluetooth scale with python<br/>
<br/>
I wanted to be able to track the measurements from the scale without using the VeSyncFit app 
and also didn't want to have to manually trigger something to read from the scale when i stepped on it.
This script will passively listen for bluetooth advertisements from the scale, which will be sent out 
when stepping onto it, and then read the weight measurement.  There is no built in recording mechanism 
so it's up to you to do something with the weight value.
<br/>
<br/>
The code is heavily commented but I am very new to bluetooth so if I got any of the
terminology wrong please forgive me. 


# Requirements
Tested on a Raspberry Pi 4 with Python3.7.  To install the required libs do: 
<br/>`sudo apt-get install libbluetooth-dev libglib2.0-dev libboost-python-dev libboost-thread-dev`
<br/>`sudo pip3 install bluepy`

# Instructions
The only change that should be required is to set the SCALE_ADDRESS variable in the script to the mac address 
of your scale.  This can be found using the following command:<br/>
`sudo hcitool -i hci0 lescan`<br/>
My scale was named 'QN-Scale1', though I can't promise that will be the case for everyone.

# Useful CLI commands
Set the weight to lbs:<br/>
`sudo gatttool -b <scale_mac>  --char-write --handle=0x0013 --value=0x1309150210b91d0019`

Set the weight to kg:<br/>
`sudo gatttool -b <scale_mac>  --char-write --handle=0x0013 --value=0x1309150110b91d0018`
