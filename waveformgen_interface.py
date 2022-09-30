"""
This module handles interfacing with the Keysight M8195A
"""

import atexit

import pyvisa


class WaveformGenerator:
    def __init__(self, visa_address="TCPIP0::10.10.10.11::inst0::INSTR", *, 
                visa_library="C:\\WINDOWS\\system32\\visa64.dll", debug=False):
        self.debug = debug
        atexit.register(self.shutdown)

        rm = pyvisa.ResourceManager(visa_library)
        try:
            self.awg = rm.open_resource(visa_address)
        except pyvisa.errors.VisaIOError as e:
            print(f"Error connecting to device string '{visa_address}'. Is the device connected?")
            raise e


    def shutdown(self):
        self.awg.close()


    # put useful functions to control AWG here