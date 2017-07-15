"""
Class gives APIs to manage serial connections with a device
Address is expected to be: "xxx.xx.xxx.xxx:PORT", where
     "xxx.xx.xxx.xxx" is IP address of the device
     "PORT" the port of the Device connected to the SerialDevice

It is based on socket connection. It listens for data and also allows to send commands.

"""

import socket
import time
import re
from _socket import SHUT_RDWR


class serialconnection():

    global timeToSleep

    timeToSleep=5

    def __init__(self, address):
        ## Initialise the class with default values
        ipaddr, port = address.split(":")
        self.SerialDeviceAddress = str(ipaddr)
        self.devicePort = int(port)
        self.socketId = None
        print("Serial Device address:port is %s" % address)

    def open(self):
        # open a socket on SerialDevice with Device port
        print("SerialDeviceAddress is %s" % self.SerialDeviceAddress)
        print("devicePort is %s" % self.devicePort)
        self.socketId = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketId.connect((self.SerialDeviceAddress, self.devicePort))
        time.sleep(timeToSleep)

    def close(self):
        self.socketId.shutdown(SHUT_RDWR)
        self.socketId.close()
        time.sleep(3)
        self.socketId = None

    def sendcmd(self, cmd=None, timeout=3):
        assert cmd
        self.socketId.send(cmd + '\n')
        time.sleep(timeout)  # for asynchronous issue w Device

    def serial_sendCmdandWaitSequence(self, cmd=None, sequence=None, timeout=300):
        assert cmd, sequence
        print('send command = ' + cmd)
        self.sendcmd(cmd)
        print("wait until sequence " + sequence + " received")
        self.serial_recvdata(sequence, timeout)

    def serial_sendCmdandWaitPrompt(self, cmd=None, prompt=None, timeout=300):
        assert cmd
        print("send command = " + cmd)
        self.sendcmd(cmd)
        print("wait until prompt detected: " + prompt)
        self.serial_recvdata(prompt, timeout)

    def serial_recvdata(self, endsequence=None, timeout=300):
        print("start of serial receive data")
        print("search for endsequence =" + endsequence)
        print("timeout setting =" + str(timeout))
        self.socketId.settimeout(timeout)
        total_data = [];
        data = ''
        while True:
            try:
                data = self.socketId.recv(4096)
                if data:
                    print
                    'buffer data received = ' + data
                    if endsequence:
                        if re.search(endsequence, data):
                            print("endsequence detected. Exit")
                            total_data.append(data)
                            break
                    total_data.append(data)
                else:
                    print
                    'Error. should not go throw this case'
                    break
            except:
                print
                'socket timeout'
                break

        print
        'end of rcv data'
        return ''.join(total_data)


if __name__ == '__main__':

    ### Unitary test to create a directory and make a log  file listing all directories in the root dir
    connection_ok="OK"
    DeviceAddr = "172.21.122.20:2001"
    testU = serialconnection(DeviceAddr)

    print("Opening socket")

    try:
       ### Open serial
       testU.open()
       time.sleep(timeToSleep)

       testU.sendcmd("mkdir -p /opt/nfs")

       print("Sending commands")
       testU.sendcmd("pwd >> /opt/nfs/log.txt")
       time.sleep(timeToSleep)
       print("Closing socket")

       ### Close serial
       testU.close()

    except (TimeoutError) as err:
        connection_ok= "KO"
        print("Socket error: "+str(err)+"")

    finally:
       assert("OK" == connection_ok)

