"""
This module handles interfacing with the Keysight M8195A.

The M8195 Soft Front Panel must be running on the controller to facilitate comms
(it should startup automatically when the AWG is powered on)

Do not edit this file unless you know what you are doing.
"""

import atexit
from contextlib import contextmanager

import numpy
import pyvisa

import twister_api.signalgen_interface as signalgen_interface


# Module level variable
instance = None

class WaveformGenerator:
    def __init__(self, visa_address="TCPIP0::10.10.10.11::inst0::INSTR", *, 
                visa_library="C:\\WINDOWS\\system32\\visa64.dll", debug=False):
        global instance
        instance = self
        self.debug = debug
        self.debug2 = False
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
            idn_string = self.do_query("*IDN?")
            print(f"Connected to Arbitrary Waveform Generator: '{idn_string}'")


        # Set default configuration:
        self.do_command("*RST")
        if self.debug:
            print("Reset AWG to default config")

        self.do_command(":INSTrument:DACMode MARKer")  # single channel with markers
        if self.debug:
            print(f"Set DAC mode to {self.do_query(':INSTrument:DACMode?')}")


        # selt voltage on all channels to 220mv (for safety)
        for channel in range(1,5):
            self.do_command(f":VOLTage{channel} 0.220")
            if self.debug:
                channel_voltage = float(self.do_query(f":VOLTage{channel}?"))
                print(f"Channel {channel} voltage set to {channel_voltage:.3f} Volts")



    def shutdown(self):
        for channel in range(1,5):
            self.do_command(f":OUTPut{channel}:STATe OFF")
            if self.debug:
                channel_state = self.do_query(f":OUTPut{channel}:STATe?")
                print(f"Set channel {channel} state to {channel_state}")
        self.visa.close()




    def load_waveform(self, filepath, samp_rate):
        """Loads data from file at <filepath> onto AWG"""
        data = numpy.fromfile(filepath, dtype="H")
        length = len(data)  # length of samples

        self.do_command("ABORt")
        self.do_command("TRAC1:DEL:ALL")
        if self.debug:
            print(f"Cleared all segments from trace 1 memory")

        # Set output DAC sample rate
        self.do_command(f":FREQuency:RASTer {samp_rate}")
        if self.debug:
            print(f"Set AWG sample frequency to {self.do_query(':FREQuency:RASTer?')}")

        self.do_command(f":TRACe1:DEFine 1,{length}")
        if self.debug:
            print(f"Defined segment 1 of length {length} on trace 1")
        self.do_command_ieee_block(":TRACe1:DATA 1,0,", data)

        if self.debug:
            print(f"Trace 1 segment, length: {self.do_query(':TRACe1:CATalog?')}")

        # enable waveform generation
        self.do_command(":INIT:IMM")

            


    @contextmanager
    def enable_output(self): #TODO add option to select channels to operate / enable all channels possible
        """Context manager will autmatically disable output when context block is complete."""
        try:
            # Do not enable output if signalgen is initialized and not enabled
            if (signalgen_interface.instance1 is not None and not signalgen_interface.instance1.output_enabled()
            or signalgen_interface.instance2 is not None and not signalgen_interface.instance2.output_enabled()):
                raise RuntimeError("Warning: Enable LO output before enabling AWG")
            # enable output on channel 1 and 3 
            self.do_command(":OUTPut1:STATe ON")
            self.do_command(":OUTPut3:STATe ON")
            if self.debug:
                print(f"Channel 1 state: {self.do_query(':OUTPut1:STATe?')}")
                print(f"Channel 3 state: {self.do_query(':OUTPut3:STATe?')}")

            yield
        except RuntimeError as e:
            print(e)
            raise e
        finally:
            self.do_command(f":OUTPut1:STATe OFF")
            self.do_command(f":OUTPut3:STATe OFF")
            if self.debug:
                print(f"Channel 1 state: {self.do_query(':OUTPut1:STATe?')}")
                print(f"Channel 3 state: {self.do_query(':OUTPut3:STATe?')}")

    
    def output_enabled(self) -> bool: #TODO check if there is a better command for this
        """Returns true if AWG channel 1 output is enabled"""
        c1 = bool(int(self.do_query(':OUTPut1:STATe?')))
        c2 = bool(int(self.do_query(':OUTPut2:STATe?')))
        c3 = bool(int(self.do_query(':OUTPut3:STATe?')))
        c4 = bool(int(self.do_query(':OUTPut4:STATe?')))
        return c1 or c2 or c3 or c4


    ## VISA Utils

    def do_command(self, command, hide_params=False):
        """Executes SCPI command on the AWG."""
        if hide_params:
            header, = command.split(" ", 1)
            if self.debug2:
                print(f"Cmd = '{header}'")
        else:
            if self.debug2:
                print(f"Cmd = '{command}'")
        self.visa.write(str(command))
        self.check_instrument_errors(command, exit_on_error=False)


    def do_command_ieee_block(self, command, values):
        """Send a command and binary values and check for errors."""
        if self.debug2:
            print(f"Cmb = '{command}'")
        self.visa.write_binary_values(str(command), values, datatype='H', is_big_endian=True)
        self.check_instrument_errors(command, exit_on_error=False)


    def do_query(self, query):
        """Send a query, check for errors, return string."""
        if self.debug2:
            print(f"Qys = '{query}'")
        result = self.visa.query(str(query)).strip()
        return result


    def do_query_ieee_block(self, query):
        """Send a query, check for errors, return binary values."""
        if self.debug2:
            print(f"Qyb = '{query}'")
        result = self.visa.query_binary_values(str(query), datatype="s", container=bytes)
        return result


    def check_instrument_errors(self, command, exit_on_error=True):
        """Check for instrument errors."""
        while True:
            error_string = self.visa.query(":SYSTem:ERRor?")
            if error_string:  # If there is an error string value.
                if error_string.find("0,", 0, 2) == -1:  # Not "No error".
                    print(f"ERROR: {error_string}, command: '{command}'")
                    if exit_on_error:
                        print("Exited because of error.")
                        exit()
                else:  # "No error"
                    break