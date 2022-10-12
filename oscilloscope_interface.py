"""
This module handles interfacing with the Keysight DSOV254A.
The oscilloscope is controlled using the VISA standard via the pyvisa package.

Requires KeySight IOLS: 
https://www.keysight.com/zz/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html
"""

import atexit
import struct

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
            self.infiniium = rm.open_resource(visa_address)
        except pyvisa.errors.VisaIOError as e:
            print(f"Error connecting to device string '{visa_address}'. Is the device connected?")
            raise e

        if self.debug:
            idn_string = self.do_query("*IDN?").strip()
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
        power = self.do_query(f":FUNCtion{function}:FFT:PEAK:MAGNitude?").strip().replace('"', "")
        if "9.99999E+37" in power:
            power = "-9999"
        return float(power)

    
    # Set the channel that will be used as the source for get_waveform functions
    def set_waveform_source(self, channel):
        self.do_command(":WAVeform:STReaming OFF")
        self.do_command(":ACQuire:COMPlete 100")  # take a full measurement

        self.do_command(f":WAVeform:SOURce CHANnel{channel}")
        if self.debug:
            print(f"Set waveform source to channel: {self.do_query(':WAVeform:SOURce?')}")


    # Sets trigger to rising edge on channel <channel>
    def set_trigger_source(self, channel):
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


    def get_waveform_bytes(self):
        # Get the number of waveform points.
        qresult = self.do_query(":WAVeform:POINts?")
        if self.debug:
            print(f"Waveform points: {qresult}")

        # Choose the format of the data returned:
        self.do_command(":WAVeform:FORMat BYTE")
        if self.debug:
            print(f"Waveform format: {self.do_query(':WAVeform:FORMat?')}")

        # Get the waveform data.
        # TODO: change this channel to whatever waveform source is
        self.do_command(":DIGitize CHANnel1")
        sData = self.do_query_ieee_block(":WAVeform:DATA?")

        # Unpack signed byte data.
        values = struct.unpack("%db" % len(sData), sData)
        if self.debug:
            print(f"Number of data values: {len(values)}")
        return values


    def get_waveform_words(self):
        # Get the number of waveform points.
        qresult = self.do_query(":WAVeform:POINts?")
        if self.debug:
            print(f"Waveform points: {qresult}")

        # Choose the format of the data returned:
        self.do_command(":WAVeform:FORMat WORD")
        if self.debug:
            print(f"Waveform format: {self.do_query(':WAVeform:FORMat?')}")

        # Get the waveform data.
        # TODO: change this channel to whatever waveform source is
        self.do_command(":DIGitize CHANnel1")
        sData = self.do_query_ieee_block(":WAVeform:DATA?")

        if self.debug:
            print(f"length: {len(sData)}")

        # Unpack signed byte data.
        # values = struct.unpack("%db" % (len(sData)/1), sData)
        values = []
        for m, l in zip(sData[0::2], sData[1::2]):
            values.append(int.from_bytes([m, l], byteorder="big", signed=True))

        if self.debug:
            print(f"Number of data values: {len(values)}")

        return values


    def get_waveform_ascii(self):
        # Get the number of waveform points.
        qresult = self.do_query(":WAVeform:POINts?")
        if self.debug:
            print(f"Waveform points: {qresult}")

        # Choose the format of the data returned:
        self.do_command(":WAVeform:FORMat ASCii")
        if self.debug:
            print(f"Waveform format: {self.do_query(':WAVeform:FORMat?')}")

        # Get the waveform data.
        # TODO: change this channel to whatever waveform source is
        self.do_command(":DIGitize CHANnel1")
        values = "".join(self.do_query(":WAVeform:DATA?")).split(",")
        values.pop()  # remove last element (it's empty)
        print("Number of data values: %d" % len(values))
        return values


    def do_command(self, command, hide_params=False):
        if hide_params:
            (header, data) = command.split(" ", 1)
            if self.debug:
                print(f"Cmd = '{header}'")
        else:
            if self.debug:
                print(f"Cmd = '{command}'")

        # inherent string casting? is this necessary?
        self.infiniium.write("%s" % command)

        if hide_params:
            self.check_instrument_errors(header)
        else:
            self.check_instrument_errors(command)


    def do_query(self, query):
        if self.debug:
            print(f"Qys = '{query}'")
        result = self.infiniium.query("%s" % query)
        self.check_instrument_errors(query)
        return result


    def do_query_ieee_block(self, query):
        if self.debug:
            print(f"Qyb = '{query}'")
        result = self.infiniium.query_binary_values("%s" % query, datatype="s", container=bytes)
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
