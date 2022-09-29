"""
This module provides functions to automate many processes that are performed 
frequently with the TWISTER equipment
"""

from oscilloscope_interface import Oscilloscope
#from 
from signalgen_interface import SignalGenerator

class Utils:
    def __init__(self, *, debug=False, 
                oscilloscope_controller, waveformgen_controller, 
                signalgen_controller1, signalgen_controller2):
        # I don't know the correct way to do this in python

        if not isinstance(oscilloscope_controller, Oscilloscope):
            raise TypeError

        if not isinstance(signalgen_controller1, SignalGenerator):
            raise TypeError
        if not isinstance(signalgen_controller2, SignalGenerator):
            raise TypeError

        # type hinting aids in development but is ignored at runtime
        self.scope: Oscilloscope
        self.awg: None
        self.psg1: SignalGenerator
        self.psg2: SignalGenerator

        self.scope = oscilloscope_controller
        self.awg = waveformgen_controller
        self.psg1 = signalgen_controller1
        self.psg2 = signalgen_controller2



    # Automatically adjusts the phase on one of the local oscillators 
    # until the received signal is maximized
    def peak_phase(self):
        pass
        # oscilloscope:
            # save current oscilloscope settings
            # change to a predefined view with an fft peak measurement
        # awg:
            # save current awg settings
            # set output to sinewave (IF should be near the testing IF i think (take as parameter?))
        # adjust phase on psg1 slightly
        # measure peak with averages on scope
        ## implement algorithm for finding peak

        # return oscilloscope to original view
        # set awg to original settings