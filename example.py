from time import perf_counter as time

import matplotlib.pyplot as plt

from oscilloscope_interface import Oscilloscope

scope = Oscilloscope()

scope.set_trigger_source(3)

#scope.do_command(':ACQ:COMP 60')
#scope.do_command(':ACQ:POIN 64')

start = time()
values = scope.get_waveform_words(channels=[2,3,1,4])
end = time()
print(f"Took {end - start} seconds")


print(f"len {len(values)}")

figure, axis = plt.subplots(2, 1)

axis[0].plot(values[0])
axis[0].set_title("Channel 2")
  
axis[1].plot(values[1])
axis[1].set_title("Channel 3")

plt.show()
