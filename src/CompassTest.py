# Tom on 16 Oct 2024
# trying out the crappy amazon magnetometer boards
#   Axes: Z: up.  X: to the right (cables to body). Y: away from cables.
# using https://github.com/robert-hh/QMC5883
#
# Working! After some calibration (see constants below) it seems to produce accurate angles
# currently it prints out r, theta, phi.
#   r should stay at 1.0 if it's calibrated.
#   heading is 90-phi

from machine import SoftI2C, Pin
from qmc5883l import QMC5883L
from time import sleep, ticks_us
from math import atan2, acos, copysign

calibrate=False

i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=400000)
#print('\nI2C scan says',i2c.scan())

qmc = QMC5883L(i2c=i2c,offset=30)
qmc.set_sampling_rate(0)
qmc.set_oversampling(0)

x, y, z, t = qmc.read_scaled()
print('Temperature = ',t)

if calibrate:
  maxx=x; minx=x; maxy=y; miny=y; maxz=z; minz=z;
else:
   # these are the calibration constants, typed in from the serial monitor after some calibration.
   # Not too far from +-0.5
   minx=-0.581; maxx=0.424
   miny=-0.483; maxy=0.521
   minz=-0.533; maxz=0.440
   
count=0

try:
    while True:
        count=count+1
        x, y, z, _ = qmc.read_scaled()
        if calibrate:
            if x>maxx: maxx=x
            if y>maxy: maxy=y
            if z>maxz: maxz=z
            if x<minx: minx=x
            if y<miny: miny=y
            if z<minz: minz=z
        xcal = (x-(maxx+minx)/2)/(maxx-minx)*2
        ycal = (y-(maxy+miny)/2)/(maxy-miny)*2
        zcal = (z-(maxz+minz)/2)/(maxz-minz)*2
        mag = (xcal**2+ycal**2+zcal**2)**0.5
        theta = acos(zcal/mag) * 180.0/3.142
        phi = copysign(1.0,ycal) * acos(xcal/((xcal**2+ycal**2)**0.5)) * 180.0/3.142
        
        #head = atan2(ycal,xcal)*180/3.1416 + 180
        
        if count%4==0:
            if calibrate:
                print('X: %6.3f, %6.3f, %6.3f    Y: %6.3f, %6.3f, %6.3f    Z: %6.3f, %6.3f, %6.3f     Scaled: %4.2f,  %4.2f,  %4.2f ' %
                  (minx, x, maxx, miny, y, maxy, minz, z, maxz, xcal, ycal, zcal))
            else:
                print(' r, theta, phi = %5.3f,  %5.1f, %5.1f ' % (mag,theta,phi))
                #print('Raw: %6.3f, %6.3f,  %6.3f' % (x, y, z))

                
        sleep(0.005)
except KeyboardInterrupt:
    print('Done')