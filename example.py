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

filepath = r"C:\Users\UTOL\Desktop\Waveforms\M2N8_1.00Gbd_54.0Gsps_0.90Beta.bin"
samplerate = 54e9

with psg1.enable_output(), psg2.enable_output():
    with awg.enable_output():
        start = time()
        awg.load_waveform(filepath, samplerate)
        end = time()
        print(f"time: {end-start}")
        input()

