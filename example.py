
"""
Install the most up to date version of the library to your system packages:
pip install git+https://github.com/OKState-TWISTER/TWISTER-Automation-Library

Alternatively, you can copy the twister_api directory to your program directory

Regardless of installtion choice, import them the following way:

from twister_api.oscilloscope_interface import Oscilloscope
from twister_api.waveformgen_interface import WaveformGenerator
from twister_api.signalgen_interface import SignalGenerator
import twister_api.twister_utils as twister_utils
import twister_api.fileio as fileio



Initialize instrument objects:

scope = Oscilloscope(debug=True)
awg = WaveformGenerator(debug=True)
psg1 = SignalGenerator(device_no=1, debug=True)
psg2 = SignalGenerator(device_no=2, debug=True)


The VISA address for a particular instrument can be specified if they have changed for some reason.
ex:
scope = Oscilloscope(visa_address="TCPIP0::10.0.0.1::inst0::INSTR", debug=True)
psg2 = SignalGenerator(visa_address="TCPIP0::10.10.10.11::inst0::INSTR", debug=True)




The outputs of the various instruments are controlled using context managers.
Their outputs will be disabled automatically when the program exits the scope of the conext manager

Ex:
To enable the outputs of both PSGs:

with psg1.enable_output(), psg2.enable_output():
    print("PSG outputs are enabled")
    # Do something with analog signal generators
    
# The PSG outputs will be disabled once the code reaches this point.
print("PSG outputs are disabled")



To protect the VDI modules, the LO signal must be enabled before the AWG output can be activated.
If any PSG objects are initialzed, the library will throw an error if you try to enable the AWG when any PSG output is off.
example of improper order:

with awg.enable_output(), psg1.enable_output(), psg2.enable_output():
    # This will throw an error!

To properly use the full stack:

with psg1.enable_output(), psg2.enable_output(), awg.enable_output():
    print("Outputs for PSGs and AWG are enabled")
    # Do work
    
print("Outputs for AWG and PSGs are disabled")




The following is a full basic example program:
"""


from twister_api.oscilloscope_interface import Oscilloscope
from twister_api.waveformgen_interface import WaveformGenerator
from twister_api.signalgen_interface import SignalGenerator
import twister_api.twister_utils as twister_utils
import twister_api.fileio as fileio

scope = Oscilloscope(debug=True)
awg = WaveformGenerator(debug=True)
psg1 = SignalGenerator(device_no=1, debug=True)
psg2 = SignalGenerator(device_no=2, debug=True)


# Enable signal generation. !!!MAKE SURE VDI MODULES ARE POWERED ON!!!
with psg1.enable_output(), psg2.enable_output(), awg.enable_output():
    # MATLAB generated waveform file
    filepath = r"C:\Users\UTOL\Desktop\12.5GHz_sine_6.3950Gsps.bin"
    samplerate = 63.95e9

    # Load waveform onto AWG
    awg.load_waveform(filepath, samplerate)

    # Specify the number of waveform segments (trigger signals) to capture (ex: 10)
    scope.view_n_segments(10)

    # Align the phase of the incident wave and LO signal at the CCD
    # This is currently unstable and may do more harm than good
    twister_utils.peak_phase()

    # Capture signal on scope channel 1
    data = scope.get_waveform_bytes()
    # equivalent to:
    data = scope.get_waveform_bytes(channels=1)

    # if you want to capture the signal and trigger waveforms on channel 1 and 3 respectively:
    signal, trigger = scope.get_waveform_bytes(channels=[1,3])

    # get sample rate from scope:
    scope_sr = scope.get_sample_rate()

    # save waveform data to file:
    dest_filepath = r"C:\Users\UTOL\Desktop\scope_capture1"
    fileio.save_waveform(signal, scope_sr, dest_filepath)

