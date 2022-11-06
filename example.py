from time import perf_counter as time

import matplotlib.pyplot as plt

from oscilloscope_interface import Oscilloscope
from waveformgen_interface import WaveformGenerator
from signalgen_interface import SignalGenerator
import twister_utils

scope = Oscilloscope(debug=True)
#awg = WaveformGenerator(debug=True)
psg1 = SignalGenerator(device_no=1, debug=True)
psg2 = SignalGenerator(device_no=2, debug=True)

#scope.set_trigger_source(3)
#scope.view_one_segment()

filepath = r"C:\Users\UTOL\Desktop\MRI-Testbed-main\M4N4_10.00Gbd_54.0Gsps_0.90Beta.bin"
samplerate = 55e9

#with awg.enable_output():
while True:
    start = time()
    twister_utils.peak_phase(debug=False)
    end = time()
    print(f"took {end-start} seconds")
    input()
