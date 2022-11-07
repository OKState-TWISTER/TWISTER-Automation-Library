from time import perf_counter as time

import matplotlib.pyplot as plt

from oscilloscope_interface import Oscilloscope
from waveformgen_interface import WaveformGenerator
from signalgen_interface import SignalGenerator
import twister_utils

scope = Oscilloscope(debug=True)
awg = WaveformGenerator(debug=True)
psg1 = SignalGenerator(device_no=1, debug=True)
psg2 = SignalGenerator(device_no=2, debug=True)

#scope.set_trigger_source(3)
#scope.view_one_segment()

filepath = r"C:\Users\UTOL\Desktop\12.5GHz_sine_6.3950Gsps.bin"
samplerate = 63.95e9

with awg.enable_output():
    start = time()
    awg.load_waveform(filepath, samplerate)
    end = time()
    print(f"time: {end-start}")
    input()

