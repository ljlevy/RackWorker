# RackWorker

Manage a set of devices (RACK) using a MRP modular power supply and a Serial communication device.

Scripts are writen in python and allow rebooting a device connected to a MRP power supply and serial device.
It listens for data received and copies the boot log and and wait for a specific boot sequence.
IP address of the device is dynamic, so it needs to get it at each reboot by reading the sequence boot log and activating DHCP.

  See : https://github.com/ljlevy/RackWorker/wiki for more details.