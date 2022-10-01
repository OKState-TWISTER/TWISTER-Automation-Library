"""
This module provides functions to automate many processes that are performed 
frequently with the TWISTER equipment
"""

import math

from oscilloscope_interface import Oscilloscope
from waveformgen_interface import WaveformGenerator
from signalgen_interface import SignalGenerator

class Utils:
    def __init__(self, *, debug=False, 
                oscilloscope_controller: Oscilloscope, 
                waveformgen_controller: WaveformGenerator, 
                signalgen_controller1: SignalGenerator, 
                signalgen_controller2: SignalGenerator):

        # I don't know the correct way to do this in python
        if not isinstance(oscilloscope_controller, Oscilloscope):
            raise TypeError
        if not isinstance(waveformgen_controller, WaveformGenerator):
            raise TypeError
        if not isinstance(signalgen_controller1, SignalGenerator):
            raise TypeError
        if not isinstance(signalgen_controller2, SignalGenerator):
            raise TypeError

        self.scope = oscilloscope_controller
        self.awg = waveformgen_controller
        self.psg1 = signalgen_controller1
        self.psg2 = signalgen_controller2



    # Automatically adjusts the phase on one of the local oscillators 
    # until the received signal is maximized
    def peak_phase(self, psg_to_adjust=1, diff_step=math.pi/8):
        try:
            psg = [self.psg1, self.psg2][psg_to_adjust - 1]
        except IndexError:
            raise IndexError("Valid indices for Analog Signal Generator device: [1, 2]")
        
        
        # oscilloscope:
            # save current oscilloscope settings
            # change to a predefined view with an fft peak measurement
        # awg:
            # save current awg settings
            # set output to sinewave (IF should be near the testing IF i think (take as parameter?))
        
        # assume psg1 phase was originally set to 0 (set it to 0 if not: psg.set_ref_phase())
        # measure received power
        p1 = None

        # adjust psg1 phase + diff step
        psg.phase(diff_step)
        # measure new received power
        p2 = None

        dP = (p2 - p1) / diff_step
        p0 = (p1 + p2) / 2
        phase0 = diff_step / 2

        ephase = math.acos(dP)
        shift1 = 3*math.pi/2 - ephase
        shift2 = math.pi/2 - ephase

        # adjust psg1 phase to phase0 + shift1
        # measure power
        # if power < p0,
        ## adjust psg1 phase to phase0 + shift2
        ## measure power


        # return oscilloscope to original view
        # set awg to original settings
