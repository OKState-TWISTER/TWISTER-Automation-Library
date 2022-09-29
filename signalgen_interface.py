"""
This module handles interfacing with the Keysight E8257D
"""

import atexit

import pyvisa


class SignalGenerator:
    def __init__(self, device_no=None, visa_address=None, *,
                visa_library="C:\\WINDOWS\\system32\\visa64.dll", debug=False):
        self.debug = debug
        atexit.register(self.shutdown)

        if visa_address is None:
            if device_no:
                # These are the VISA addresses of the two signal generators we have at time of writing
                if device_no == 1:
                    visa_address = "TCPIP0::10.10.10.21::inst0::INSTR"
                elif device_no == 2:
                    visa_address = "TCPIP0::10.10.10.22::inst0::INSTR"
                else:
                    raise ValueError("Valid device_no: 1, 2")

        rm = pyvisa.ResourceManager(visa_library)
        try:
            self.psg = rm.open_resource(visa_address)
        except pyvisa.errors.VisaIOError as e:
            print(f"Error connecting to device string '{visa_address}'. Is the device connected?")
            raise e


    def shutdown(self):
        self.psg.close()


    # put useful functions to control ASGs here
