"""
This module handles interfacing with the Keysight DSOV254A.
The oscilloscope is controlled using the VISA standard via the pyvisa package.

Requires KeySight IOLS: 
https://www.keysight.com/zz/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html
"""

import atexit
import struct

import numpy as np
import pyvisa


class Oscilloscope:
    def __init__(self, visa_address="USB0::0x2A8D::0x9027::MY59190106::0::INSTR", *, 
                visa_library="C:\\WINDOWS\\system32\\visa64.dll", debug=False):
        self.debug = debug
        atexit.register(self.shutdown)

        if self.debug:
            print(f"Initializing Oscilloscope @ {visa_address}")

        rm = pyvisa.ResourceManager(visa_library)
        try:
            pyvisa.resources.Resource: self.infiniium  # type hinting
            self.infiniium = rm.open_resource(visa_address)
        except pyvisa.errors.VisaIOError as e:
            print(f"Error connecting to device string '{visa_address}'. Is the device connected?")
            raise e

        # This clears any pervious errors that will stope the scope from
        self.do_command("*CLS")

        if self.debug:
            idn_string = self.do_query("*IDN?")
            print(f"Connected to Oscilloscope: '{idn_string}'")
        
        self.infiniium.timeout = 20000
        self.infiniium.clear()
        # Clear status.
        self.do_command("*CLS")
        
        self.do_command(":SYSTem:HEADer OFF")


    def shutdown(self):
        self.infiniium.close()



    def get_sample_rate(self):
        xinc = self.do_query(":WAVeform:XINCrement?")
        samp_rate = 1 / float(xinc)
        if self.debug:
            print(f"X increment: '{xinc}'\nSample rate: '{samp_rate}'")
        return samp_rate



    def get_fft_peak(self, function):
        power = self.do_query(f":FUNCtion{function}:FFT:PEAK:MAGNitude?").replace('"', "")
        if "9.99999E+37" in power:
            power = "-9999"
        return float(power)


    def view_one_segment(self, trig_channel=None):
        """Sets the scope window to a single waveform segment by measuring the trigger period"""
        auto_source = False
        if not trig_channel:
            trig_channel = self.do_query(":TRIGger:EDGE:SOURce?").replace("CHAN", "")  # this is gross
            auto_source = True
        if self.debug:
            msg = f"Measuring segment length using channel {trig_channel} as trigger"
            if auto_source:
                msg += " (using system trigger source)"
            print(msg)

        self.do_command(f":TIMebase:RANGe 1E-3")
        if self.debug:
            print("Setting timebase to a large value to ensure a period can be measured")
            print(f"Set timebase range to {self.do_query(':TIMebase:RANGe?')}s")

        period = self.do_query(f"MEASure:PERiod? CHANnel{trig_channel}") # this also accepts functions as source
        if self.debug:
            print(f"Period measured to be: {period}")

        if float(period) > 9e37:
            print(f"Error finding period of waveform on channel {trig_channel}. " +
                   "Make sure one period is viewable on screen.")
            return

        self.do_command(f":TIMebase:RANGe {period}")
        if self.debug:
            print(f"Set timebase range to {self.do_query(':TIMebase:RANGe?')}s")

        # period / 2 - 2%
        delay = float(period) * 0.49
        self.do_command(f":TIMebase:POSition {delay:.2E}")
        if self.debug:
            print(f"Set timebase position to {self.do_query(':TIMebase:POSition?')}s")


    def set_waveform_source(self, channel):
        """Set the channel that will be used as the source for get_waveform functions"""
        self.do_command(":WAVeform:STReaming OFF")
        self.do_command(":ACQuire:COMPlete 100")  # take a full measurement

        self.do_command(f":WAVeform:SOURce CHANnel{channel}")
        if self.debug:
            print(f"Set waveform source to channel: {self.do_query(':WAVeform:SOURce?')}")



    def set_trigger_source(self, channel):
        """Sets trigger to rising edge on channel <channel>"""
        # Set trigger more to edge triggered
        self.do_command(":TRIG:MODE EDGE")
        if self.debug:
            print(f"Trigger Mode Changed to: {self.do_query(':TRIG:MODE?')}")

        # Set edge triggering on rising edge
        self.do_command(":TRIG:EDGE:SLOP POS")
        if self.debug:
            print(f"Edge trigger slope set to: {self.do_query(':TRIGger:EDGE:SLOPe?')}")

        # Set trigger source
        self.do_command(f":TRIG:EDGE:SOUR CHAN{channel}")
        if self.debug:
            print(f"Trigger Source Changed to channel: {self.do_query(':TRIGger:EDGE:SOURce?')}")



    def get_waveform_bytes(self, channels : list=None, functions : list=None):
        """Captures 1 byte/sample waveforms from the specified scope channels and/or functions."""
        if channels is None:
            channels = []
        if functions is None:
            functions = []

        # Choose the format of the data returned:
        self.do_command(":WAVeform:FORMat BYTE")
        if self.debug:
            print(f"Waveform format: {self.do_query(':WAVeform:FORMat?')}")

        # Get waveform(s) data.
        data = self._get_waveform_raw(channels, functions)

        processed_data = []
        for waveform in data: # this can probably be made more efficient
            values = struct.unpack("%db" % len(waveform), waveform)
            processed_data.append(values)

        if self.debug: # TODO: make this useful
            print(f"Number of data values: {len(values)}")

        # TODO: if only one channel was captured, unpack it from root list
        return processed_data



    def get_waveform_words(self, channels : list=None, functions : list=None):
        """Captures 2 byte/sample waveforms from the specified scope channels and/or functions."""
        if channels is None:
            channels = []
        if functions is None:
            functions = []

        # Choose the format of the data returned:
        self.do_command(":WAVeform:FORMat WORD")
        if self.debug:
            print(f"Waveform format: {self.do_query(':WAVeform:FORMat?')}")

        # Get waveform(s) data.
        data = self._get_waveform_raw(channels, functions)

        processed_data = []
        for waveform in data: # I believe this is the fastest way to do this in python
            m = (np.take(waveform, np.arange(0,waveform.size,2)).astype(np.int16))<<8
            l = np.take(waveform, np.arange(1,waveform.size,2))
            values = np.array((m+l), dtype=np.int16).tolist() # converting back to list takes a long time
            processed_data.append(values)

        if self.debug:
            print(f"Number of data values: {len(values)}")

        # TODO: if only one channel was captured, unpack it from root list
        return processed_data



    def _get_waveform_raw(self, channels: list, functions: list):
        data = [] # a list of lists (of bytes)
        if self.debug:
            print(f"Waveform points: {self.do_query(':WAVeform:POINts?')}")

        self.do_command(f":DIGitize")  # this command executes more quickly without parameters

        #TODO: enable channels if they aren't already / give warning if channels are disabled

        for channel in channels:
            self.do_command(f":WAVeform:SOURce CHANnel{channel}")
            if self.debug:
                print(f"SCapturing waveform on channel {self.do_query(':WAVeform:SOURce?')}")
            data.append(self.do_query_ieee_block(":WAVeform:DATA?"))

        for function in functions:
            self.do_command(f":WAVeform:SOURce FUNCtion{function}")
            if self.debug:
                print(f"SCapturing waveform on function {self.do_query(':WAVeform:SOURce?')}")
            data.append(self.do_query_ieee_block(":WAVeform:DATA?"))

        return data



    def get_waveform_ascii(self, channel: int):
        # Get the number of waveform points.
        qresult = self.do_query(":WAVeform:POINts?")
        if self.debug:
            print(f"Waveform points: {qresult}")

        # Choose the format of the data returned:
        self.do_command(":WAVeform:FORMat ASCii")
        if self.debug:
            print(f"Waveform format: {self.do_query(':WAVeform:FORMat?')}")

        # Set the channel to capture
        self.do_command(f":WAVeform:SOURce CHANnel{channel}")

        # Get the waveform data.
        self.do_command(f":DIGitize")
        values = "".join(self.do_query(":WAVeform:DATA?")).split(",")
        values.pop()  # remove last element (it's empty)
        print(f"Number of data values: {values}")
        return values



    def enable_channel(self, channel):
        self.do_command(":RUN")
        self.do_command(f":VIEW CHANnel{channel}")




    def do_command(self, command, hide_params=False):
        """Executes SCPI command on the scope."""
        if hide_params:
            (header, data) = command.split(" ", 1)
            if self.debug:
                print(f"Cmd = '{header}'")
        else:
            if self.debug:
                print(f"Cmd = '{command}'")

        self.infiniium.write(str(command))

        if hide_params:
            self.check_instrument_errors(header)
        else:
            self.check_instrument_errors(command)


    def do_query(self, query):
        if self.debug:
            print(f"Qys = '{query}'")
        result = self.infiniium.query(str(query))
        self.check_instrument_errors(query)
        return result.rstrip()


    def do_query_ieee_block(self, query) -> np.ndarray:
        if self.debug:
            print(f"Qyb = '{query}'")
        result = self.infiniium.query_binary_values(str(query), container=np.ndarray, datatype="B")
        self.check_instrument_errors(query, exit_on_error=False)
        return result


    def check_instrument_errors(self, command, exit_on_error=True):
        while True:
            error_string = self.infiniium.query(":SYSTem:ERRor? STRing")
            if error_string:  # If there is an error string value.
                if error_string.find("0,", 0, 2) == -1:  # Not "No error".
                    print(f"ERROR: {error_string}, command: '{command}'")
                    if exit_on_error:
                        print("Exited because of error.")
                        exit()
                else:  # "No error"
                    break
            else:  # :SYSTem:ERRor? STRing should always return string.
                print(f"ERROR: :SYSTem:ERRor? STRing returned nothing, command: '{command}'")
                if exit_on_error:
                    print("Exited because of error.")
                    exit()
