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

        if self.debug:
            print(f"Initializing Arbitrary Waveform Generator @ {visa_address}")

        rm = pyvisa.ResourceManager(visa_library)
        try:
            self.visa = rm.open_resource(visa_address)
        except pyvisa.errors.VisaIOError as e:
            print(f"Make sure that the M8195A SFP is started:\n" +
                   "Start Menu -> Keysight -> M8195 -> M8195 Soft Front Panel")
            print(f"Error connecting to device string '{visa_address}'. Is the device connected?")
            raise e

        if self.debug:
            idn_string = self.do_query("*IDN?").strip()
            print(f"Connected to Arbitrary Waveform Generator: '{idn_string}'")


    def shutdown(self):
        self.visa.close()





    # put useful functions to control AWG here





    def do_command(self, command, hide_params=False):
        if hide_params:
            (header, data) = command.split(" ", 1)
            if self.debug:
                print(f"Cmd = '{header}'")
        else:
            if self.debug:
                print(f"Cmd = '{command}'")

        # inherent string casting? is this necessary?
        self.visa.write("%s" % command)


    def do_query(self, query):
        if self.debug:
            print(f"Qys = '{query}'")
        result = self.visa.query("%s" % query)
        return result


    def do_query_ieee_block(self, query):
        if self.debug:
            print(f"Qyb = '{query}'")
        result = self.visa.query_binary_values("%s" % query, datatype="s", container=bytes)
        return result
