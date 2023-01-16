"""
Created on Wed Jan 14  2023

@author: joaovie

Script to comunicate with Keithley 2410 SourceMeter via RS232 Serial Communication Protocol.
Fast Live Plotting of the measured current vs time via Pyformulas multithreaded screen.

Sets the source meter to measure current and switches between 0 and 3V (To "simulate" AC current).
Inputs:
Name of the test
Intrument visa address
Duration of the test
Max voltage

Output:
If filewrite is toggled
    Measured values (Current [A], Time [s]) to txt file
    Saved final plot
"""

import pyformulas as pf
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import numpy as np
import time
import pyvisa
import os

Filewrite=False
prototype='Moister_Prototype - Working keithley'
# spacing='4mm_Spacing'
# Sensor="0.5cm spacing"
spacing='Test'
Sensor="1"

Sensorfolder = './' + prototype + '/' + spacing + '/' + Sensor #Wafer + '/' + Sensor + '/results.txt'
filename =   './' + prototype + '/' +  spacing + '/' + Sensor + '/results.txt'

if Filewrite:
    try:
        os.makedirs(Sensorfolder)
    except:
        os.makedirs(Sensorfolder)

rm = pyvisa.ResourceManager()
rm.list_resources()

instrument = 'ASRL5::INSTR' # Visa address
myDmm = rm.open_resource(instrument)
print(myDmm.query("*IDN?"))
time.sleep(1)

myDmm.write('*RST')
myDmm.write('*CLS')
myDmm.write('SYST:REM') #Remote mode ON
myDmm.write(":SENS:FUNC 'CURR'") # Select current measurement function
myDmm.write(':SOUR:FUNC VOLT') # Select voltage source function
#myDmm.write(':SOUR:VOLT 3') #sets voltage to 3V
myDmm.write(':SOUR:VOLT:MODE FIX')
myDmm.write(':SENS:CURR:PROT 1') # Set 0.5A compliance limit
myDmm.write(':SENS:CURR:RANG:AUTO ON') #Enables auto range for current measurement
time.sleep(3)

def get_current(inst):
    inst.write('MEAS?')
    data=inst.read_raw()
    floats = [float(x) for x in ((data.decode()).replace('\r\n', '')).split(',')]
    return floats[1]

if Filewrite:
    fileID = open(filename, 'w')
    fileID.write( 'I(A),T(s) \n')

fig = plt.figure()

screen = pf.screen(title='Plot')

T = 220 #seconds
t1 = time.time()
count = 0
timer = [0]
vec = [get_current(myDmm)]
volt=3 # Max voltage

try:
    while timer[-1]<=T:
        count = count+1;
        myDmm.write(':SOUR:VOLT '+ str(volt))
        time.sleep(0.5)
        vec.append(get_current(myDmm))
        myDmm.write(':SOUR:VOLT 0')
        time.sleep(0.5)
        timer.append( time.time()-t1 )
        if Filewrite:
            fileID.write('%f,%f \n'%(vec[count], timer[count]))

        fig, ax = plt.subplots()
        plt.plot(timer, vec, c='black')
        ax.xaxis.set_major_locator(MultipleLocator(20))
        ax.xaxis.set_minor_locator(MultipleLocator(5))
        plt.xlabel('Time [s]')
        plt.ylabel('I [A]')

        fig.canvas.draw()

        image = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))

        screen.update(image)
except KeyboardInterrupt:
    print('Stopped by user')
    pass
screen.close()

fig = plt.figure(figsize=(10,5))
plt.plot(timer, vec)
plt.xlabel('Time(s)')
plt.ylabel('Current (A)')
plt.title(spacing + '/' + Sensor +'\n Current Variation')
plt.draw()
if Filewrite:
    plt.savefig(Sensorfolder+'/fig.png')
plt.show()


#fileID.close()
myDmm.write('OUTP OFF')
print('Turned off power')
