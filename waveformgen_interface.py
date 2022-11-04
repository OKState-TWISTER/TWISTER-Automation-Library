"""
This module handles interfacing with the Keysight M8195A.

The M8195 Soft Front Panel must be running on the controller to facilitate comms
(it should startup automatically when the AWG is powered on)

Do not edit this file unless you know what you are doing.
"""

import atexit
from contextlib import contextmanager

import pyvisa

import signalgen_interface


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
                print(f"Channel {channel} voltage set to {float(self.do_query(':VOLTage1?')):.3f} Volts")

       #:INIT:IMM # start data generation."""


    def shutdown(self):
        for channel in range(1,5):
            self.do_command(f":OUTPut{channel}:STATe OFF")
            if self.debug:
                channel_state = self.do_query(f":OUTPut{channel}:STATe?")
                print(f"Set channel {channel+1} state to {channel_state}")
        self.visa.close()



    # put useful functions to control AWG here

    """To prepare your module for arbitrary waveform generation follow these steps:
• Set Instrument Mode (number of channels), Memory Sample Rate Divider,
and memory usage of the channels (Internal/Extended).
• Define a segment using the various forms of the
o :TRAC[1|2|3|4]:DEF command.
• Fill the segment with sample values using
o :TRAC[1|2|3|4]:DATA.
• Signal generation starts after calling INIT:IMM.
• Use the :TRAC[1|2|3|4]:CAT? query to read the length of a waveform loaded
into the memory of a channel. Use the :TRAC[1|2|3|4]:DEL:ALL command to
delete a waveform from the memory of a channel"""


    def load_waveform(self, filepath, freq):
        """Loads data from file at <filepath> onto AWG"""
        # TODO: might need to clear segment before sending new data "TRAC1:DEL:ALL"
        with open(filepath, 'rb') as fh:
            data = fh.read()
        newdata = []
        for m, l in zip(data[0::2], data[1::2]): # swap the byte order just for fun
            newdata.append(l)
            newdata.append(m)
        data = bytes(newdata)
        data = data.zfill(5632*2)
        length = len(data)/2  # length of samples (ignore marker byte)
        #Console.WriteLine("Set memory mode to external for channel " + channel.ToString());
        #fIO.WriteString(string.Format(":TRAC{0}:MMOD EXT", channel), true);

        self.do_command(f":FREQuency:RASTer {freq}")
        if self.debug:
            print(f"Set AWG sample frequency to {self.do_query(':FREQuency:RASTer?')}")

        self.do_command(f":TRACe1:DEFine 1,{length}")

        self.do_command_ieee_block(":TRAC1:DATA 1,0,", data)

        print(self.do_query(":TRAC1:CAT?"))

        self.do_command(":INIT:IMM")

            


    @contextmanager
    def enable_output(self):
        #TODO: do not enable output if signalgen is initialized and not enabled
        try:
            # enable output on channel 1 and 3 
            self.do_command(":OUTPut1:STATe ON")
            self.do_command(":OUTPut3:STATe ON")
            if self.debug:
                print(f"Channel 1 state: {self.do_query(':OUTPut1:STATe?')}")
                print(f"Channel 3 state: {self.do_query(':OUTPut3:STATe?')}")

            yield
        finally:
            self.do_command(f":OUTPut1:STATe OFF")
            self.do_command(f":OUTPut3:STATe OFF")
            if self.debug:
                print(f"Channel 1 state: {self.do_query(':OUTPut1:STATe?')}")
                print(f"Channel 3 state: {self.do_query(':OUTPut3:STATe?')}")


    ## VISA Utils

    def do_command(self, command, hide_params=False):
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
        """Send a command and binary values and check for errors"""
        if self.debug2:
            print(f"Cmb = '{command}'")
        self.visa.write_binary_values(str(command), values, datatype='B') #is_big_endian=False?# might try 'H'
        self.check_instrument_errors(command, exit_on_error=False)


    def do_query(self, query):
        if self.debug2:
            print(f"Qys = '{query}'")
        result = self.visa.query(str(query)).strip()
        return result


    def do_query_ieee_block(self, query):
        if self.debug2:
            print(f"Qyb = '{query}'")
        result = self.visa.query_binary_values(str(query), datatype="s", container=bytes)
        return result


    def check_instrument_errors(self, command, exit_on_error=True):
        """Check for instrument errors"""
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
