"""
Class defines the worker for a Device :
    - deviceName ;
    - availability ;
    - power_switch outlet: @IP:port ;
    - serial switch: @IP:port ;
    - router switch IP

It reboots a device connected to a MRP power supply and serial Device,
  listen for data received
  copy the boot log and and wait for a specific boot sequence.

IP address of the device is dynamic, so it needs to get it at each reboot by reading the sequence boot log
and activating DHCP.
  - LOG_DIR is the name of the directory built to set all log files.
  - boot sequence is saved into BOOT_LOG_FILE file
  - IP dynamic address is saved into IP_FILE file a get by by a awk command

After reboot, and activating DHCP, IP is avialable.
Then a setup.sh script is called for a post treatment (ipk install ...) and logs are saved into a SETUP_LOG file.

Usage : python WorkerBootInstall.py  --platform "ref-platform1" --nfs_server "NFS_SERVER" --ipk_url "IPK_URL"


"""


import os
import sys
import subprocess
import time
import argparse

from lib.rsc import power_supply
from lib.io import serial_connections

IP_MOUNT = "10.60.57.90"  ## IP of server used for mounting
NFS_MOUNT_POINT = "/opt/nfs"
NFS_DIR="/mnt/nfs"

END_BOOT_SEQUENCE_STRING="Starting Conso"
SEQUENCE_STRING="Started Update is Completed"
LOG_DIR="CI_logs"
BOOT_LOG_FILE=""+LOG_DIR+"/bootlog.txt"
IP_FILE=""+LOG_DIR+"/ip_address.txt"
SETUP_LOG=""+LOG_DIR+"/setup_log.txt"

def check_string(fname, txt):
    with open(fname) as dataf:
        return any(txt in line for line in dataf)


class WorkerBootInstall():

    def __init__(self):

        ###  MRP IP address + port connected on Serial Device
        devicePowerAddr = "172.21.140.234:1"

        ### Netcom Serial IP address + TCP port (data)
        deviceSerialAddr = "172.21.122.20:2001"

        powerS = devicePowerAddr
        serialC = deviceSerialAddr
        self.ipAddress = None
        self.bootendsequence = END_BOOT_SEQUENCE_STRING
        self.prompt = ' '

        # Create object
        self.serialSwitch = serial_connections.serialconnection(serialC)
        self.powerSwitch = power_supply.power_supply(powerS)

    # external APIs
    def device_reboot(self, logfile=None, timeout=30):

        self.power_reboot()

        # Record boot log in file
        print ("Record boot  logfile : " + logfile+" of the serial  device")

        f = open(logfile, 'w')
        print("search for end sequence = " + self.bootendsequence)
        self.serial_open()
        log = self.serial_recvdata(self.bootendsequence, timeout)
        f.write(log)
        f.close()

        self.changePrompt()
        self.serial_close()

        # to be sure the boot is finished
        time.sleep(5)

    def device_getIpAddress(self):
        ## IP address of the device is dynamic, so it needs to get it at each reboot by reading the sequence boot log.
        command = 'cat '+BOOT_LOG_FILE+' | grep \"ipaddr\" | awk -F \"ipaddr \" \'{ print $2 }\'| head -n 1 | awk -F \", mask\" \'{ print $1 }\' '
        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        # set new dynamic IP address
        self.ipAddress = output.communicate()[0]
        return self.ipAddress

    def changePrompt(self):
        prompt = 'PS1="' + self.prompt + '"'
        print("new prompt = " + prompt)
        self.serialSwitch.sendcmd(prompt)

    # power supply
    def power_reboot(self):
        print("Rebooting Power Supply")
        self.powerSwitch.power_reboot()

    # serial com.
    def serial_open(self):
        self.serialSwitch.open()

    def serial_close(self):
        self.serialSwitch.close()

    def serial_sendCmd(self, cmd=None, timeout=2):
        assert cmd
        self.serialSwitch.sendcmd(cmd, timeout)

    def serial_sendCmdandWaitSequence(self, cmd, sequence, timeout):
        self.serial_open()
        self.serialSwitch.serial_sendCmdandWaitSequence(cmd, sequence, timeout)
        self.serial_close()

    def serial_sendCmdandWaitPrompt(self, cmd, timeout):
        if self.serialSwitch.socketId:
            # close the socket to flush the Rx buffer
            self.serial_close()
            time.sleep(3)
            self.serial_open()
        else:
            sys.exit("ERROR - CIWebeng:serial_sendCmdandWaitPrompt(): No socket opened")

        self.serialSwitch.serial_sendCmdandWaitPrompt(cmd, self.prompt, timeout)

    def serial_recvdata(self, endsequence=None, timeout=300):
        return self.serialSwitch.serial_recvdata(endsequence, timeout)


if __name__ == '__main__':
    worker = WorkerBootInstall()

    # parse arguments of script
    parser = argparse.ArgumentParser(description='Main script to reboot device and manage set-up')

    parser.add_argument('--platform', choices=['ref-platform1', 'ref_platform2'], required=True,
                        help="Specify platform used")

    parser.add_argument('--nfs_server', required=True,
                        help='set the nfs server path where webengine binaries were uploaded. Ex: "/vol/users/ci/" ')

    parser.add_argument('--ipk_url', required=True,
                        help='Url of the ipk to download. Ex: "http://mySiteWeb/ipk" ')

    args = parser.parse_args()

    # Reboot the device
    print("start of device reboot")

    # Record boot log in file
    print("dir path is %s" % os.path.abspath(os.path.dirname(__file__)))
    dirLog = os.path.abspath(os.path.dirname(__file__)) + '/'+LOG_DIR+''
    print("Create boot log at %s " % dirLog)
    if not os.path.exists(dirLog):
        os.makedirs(dirLog)

    bootlog = os.path.join(os.path.abspath(os.path.dirname(__file__)), ''+BOOT_LOG_FILE+'')
    bootTimeout = 120

    worker.device_reboot(bootlog, bootTimeout)
    print("end of device reboot")

    print("Checking device reboot sequence")
    if check_string('+BOOT_LOG_FILE+', ''+SEQUENCE_STRING+''):
        print("Device has correctly rebooted")
        assert True
    else:
        print("Device reboot is not OK")
        assert False

    # Open serial link
    print("Open serial link")
    worker.serial_open()

    print("activating DHCP")
    worker.serial_sendCmd("udhcpc -q -i eth0 ; mount -t nfs -o tcp,nolock " + IP_MOUNT + ":" + args.nfs_server + " "+NFS_DIR+"")

    ipAddress = worker.device_getIpAddress()
    print("Device dynamic IP address is " + ipAddress + " ")

    print("Installing IPK")
    worker.serial_sendCmd("cd "+NFS_DIR+" && mkdir -p "+LOG_DIR+" && echo \"\" > "+IP_FILE+" && chmod 775 "+IP_FILE+"")
    myFile = open(""+IP_FILE+"", "w")
    myFile.write(ipAddress)
    myFile.close()
    worker.serial_sendCmd("cat "+IP_FILE+"")

    worker.serial_sendCmd("source ./setupIb.sh --url " + args.ipk_url + " &> "+SETUP_LOG+" ")

    ### Wait a little
    time.sleep(100)

    print("Reading setup_log.txt file")
    worker.serial_sendCmd("cat "+SETUP_LOG+" ")

    print("Close serial link")
    worker.serial_close()


