from oscilloscope_interface import Oscilloscope

scope = Oscilloscope()

scope.set_trigger_source(3)

#scope.do_command(':ACQ:COMP 60')
scope.do_command(':ACQ:POIN 64')


scope.set_waveform_source(2)
values = scope.get_waveform_words(2, reenable_display=True)

print(f"len {len(values)}")

with open('trash.me', 'w') as file:
    for x in values:
        file.write(str(x))
        file.write("\n")

