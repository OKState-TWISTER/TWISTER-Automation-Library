"""
This module provides functions to automate many processes that are performed 
frequently with the TWISTER equipment
"""

from math import pi, sqrt, sin, cos, asin, acos

from oscilloscope_interface import Oscilloscope
from waveformgen_interface import WaveformGenerator
from signalgen_interface import SignalGenerator

class Utils:
    def __init__(self, *, debug=False, 
                oscilloscope_controller: Oscilloscope, 
                waveformgen_controller: WaveformGenerator, 
                signalgen_controller1: SignalGenerator, 
                signalgen_controller2: SignalGenerator):
        self.debug = debug

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

    # 
    def peak_phase(self, psg_to_adjust=1, diff_step=pi/8):
        """todo description
        diff_step must be less than or equal to 1/2 of the upconverted LO period
        if the upconverters have a multiplier of n, then actual period will be (2pi)/n
        for the maximum upconverter multiplier (12 as of this writing)
        diff_step <= math.pi/6"""
        try:
            psg = [self.psg1, self.psg2][psg_to_adjust - 1]
        except IndexError:
            raise IndexError("Valid indices for Analog Signal Generator device: [1, 2]")

        ### awg:
            # save current awg settings
            # set output to sinewave (IF should be near the testing IF i think (take as parameter?))
        
        ### scope
        # save current oscilloscope settings
        #setup_bytes = self.scope.do_query_ieee_block(":SYSTem:SETup?")
        # default setup
        #self.scope.do_command("*RST")
        # autoscale for trigger
        #self.scope.do_command(":AUToscale")
        #self.scope.do_command(":FUNCtion1:AVERage CHANnel1,16")
        # may need to set y scale
        
        # execute algo
        psg.set_phase_reference()
        # measure point 1
        p1 = float(self.scope.do_query(':MEASure:VPP? FUNCtion1'))
        if self.debug:
            print(f"Measured vpp at p1: {p1}")

        # advance phase by diff_step
        psg.set_phase(diff_step)
        # measure new received power
        p2 = float(self.scope.do_query(':MEASure:VPP? FUNCtion1'))
        if self.debug:
            print(f"Measured vpp at p2: {p2}")

        # advance phase by another diff_step
        psg.set_phase(2*diff_step)
        # measure new received power
        p3 = float(self.scope.do_query(':MEASure:VPP? FUNCtion1'))
        if self.debug:
            print(f"Measured vpp at p3: {p3}")

        if 9.99999e37 in [p1, p2, p3]:
            print("Error measuring peak, measured signal saturated (adjust channel 1 scale)")
            return

        # describe the received amplitude as A*sin(w*x+phi)
        w = acos((p1+p3)/(2*p2))/diff_step

        A = sqrt(p1**2 + ((p2-p1*cos(w))/sin(w))**2)

        phi = asin(p1/A)

        # peak of sine wave is at pi/2 - phi
        psg.set_phase(pi/2 - phi)

        # reload original scope settings
        #self.scope.do_command_ieee_block(":SYSTem:SETup", setup_bytes)
        # set awg to original settings
