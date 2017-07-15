"""

Class gives APIs to manage the power supply device
It is based on telnet connection to MRP Power Device using its IP address
It writes and reads for commands (login, password ...)

"""

import time
import telnetlib
import socket
import sys
import re

MRP_LOGIN = "root"
MRP_PASSWD = "baytech"
MRP_STATE_ON = "On"
MRP_STATE_OFF = "Off"


class power_supply():

    # Initialize the class
    def __init__(self, address):

        self.address = address
        self.MRPaddress, self.devicePort = address.split(":")
        self.telnetSession = None
        self.TimetoSleep = 30 ## Time in seconds
        print("address is " + address + " ")
        print("MRPaddress is " + self.MRPaddress + " ")

    def _connect_MRP(self):

        connection_OK="OK"

        try:
            self.telnetSession = telnetlib.Telnet(self.MRPaddress)

            # wait for login prompt
            print("Wait for login")
            self.telnetSession.read_until("PD login:", self.TimetoSleep)

            ## enter user login
            print("Writing login")
            self.telnetSession.write(MRP_LOGIN + '\r\n')

            # wait for password prompt
            print("Waiting for password")
            self.telnetSession.read_until("Password:", self.TimetoSleep)

            ## enter password
            self.telnetSession.write(MRP_PASSWD + '\r\n')
            print("Writing  password")

            ## wait for prompt
            print("Waiting for MRP-101>")
            data = self.telnetSession.read_until("MRP-101>", self.TimetoSleep)

            result = re.search("Port in use", str(data))
            if result:
                print("MRP supply is busy.Telnet socket already in use")
                return True

            ## Get status
            self.telnetSession.write("status" + '\r\n')
            data = self.telnetSession.read_until("Type Help for a list of commands", self.TimetoSleep)
            print("Power status is: %s" % data)

            return False

        except (socket.error, OSError, ValueError) as err:
            connection_OK="KO"
            print("Telnet socket error: %s" % err)
            sys.exit(1)

        except:
            connection_OK="KO"
            print("Error in Telnet connection")
            sys.exit(1)

        finally:
            assert("OK" == connection_OK)



    def _disconnect_MRP(self):
        self.telnetSession.write("Exit" + '\r\n')
        self.telnetSession.close()


    def _send_MRP(self, state):
        print("state to set is %s" % state)
        print("port is %s" % self.devicePort)

        if state == MRP_STATE_OFF:
            print("string to set is %s" % MRP_STATE_OFF + ' ' + self.devicePort)
            self.telnetSession.write(MRP_STATE_OFF + ' ' + self.devicePort + '\r\n')
            self.telnetSession.read_until("MRP-101>", self.TimetoSleep)

        elif state == MRP_STATE_ON:
            print("string to set is %s" % MRP_STATE_ON + ' ' + self.devicePort)
            self.telnetSession.write(MRP_STATE_ON + ' ' + self.devicePort + '\r\n')
            self.telnetSession.read_until("MRP-101>", self.TimetoSleep)

    # external API
    def power_reboot(self):

        print("Connecting to MRP")
        self._connect_MRP()
        time.sleep(10)

        print("Set MRP port to Off")
        self._send_MRP(MRP_STATE_OFF)
        time.sleep(10)

        print("Set MRP port to On")
        self._send_MRP(MRP_STATE_ON)
        time.sleep(10)

        print("Disconnecting from MRP")
        self._disconnect_MRP()




if __name__ == '__main__':

    devicePowerAddr = "172.21.140.234:1"
    testU = power_supply(devicePowerAddr)

    ''' 
    Same as : 
    testU.power_reboot()
    time.sleep(10) 
    '''

    print("Connecting to MRP")
    testU._connect_MRP()
    time.sleep(10)

    print("Set MRP port to Off")
    testU._send_MRP(MRP_STATE_OFF)
    time.sleep(10)

    print("Set MRP port to On")
    testU._send_MRP(MRP_STATE_ON)
    time.sleep(10)

    print("Disconnecting from MRP")
    testU._disconnect_MRP()

