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
                    self.name = "psg1"
                elif device_no == 2:
                    visa_address = "TCPIP0::10.10.10.22::inst0::INSTR"
                    self.name = "psg2"
                else:
                    raise ValueError("Valid device_no: 1, 2")

        rm = pyvisa.ResourceManager(visa_library)
        try:
            pyvisa.resources.Resource: self.visa  # type hinting
            self.visa = rm.open_resource(visa_address)
        except pyvisa.errors.VisaIOError as e:
            print(f"Error connecting to device string '{visa_address}'. Is the device connected?")
            raise e


    def shutdown(self):
        self.visa.close()


    
    def set_frequency(self, frequency: float):
        self.do_command(f":FREQuency:FIXed {frequency:.2E}")
        if self.debug:
            print(f"Set {self.name} frequency to {self.do_query(':FREQuency:FIXed?')}")


    def set_phase(self, degree: float):
        self.do_command(f":PHASe {degree}DEG")
        if self.debug:
            print(f"Set {self.name} phase to {self.do_query(':PHASe?')} radians")


    def set_phase_reference(self):
        self.do_command(":PHASe:REFerence")
        if self.debug:
            print(f"Set {self.name} phase reference")



    def do_command(self, command):
        """Executes SCPI command on the PSG."""
        self.visa.write(str(command))


    def do_query(self, query):
        result = self.visa.query(str(query))
        return result.rstrip()