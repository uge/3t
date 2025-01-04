# Traquito testing
# some pins and things:
#  machine.adc(4) is the core temperature sensor
# GPS RST is GPIO6
# GPS TXD goes to GPIO9  (UART1 Rx)
# GPS RXD goes to GPIO8  (UART1 Tx)
# GPS power ON/OFF is GPIO2
# TCXO AND Si5351 power on/off is GPIO28  (active low as it's a P-type mosfet)
# Si5351 SDA is GPIO4 (SDA)
# Si5351 SCL is GPIO5 (SCL)
# Outputs are on CLK0 and CLK1
#
# libraries I use:
#  https://github.com/inmcm/micropyGPS
#  https://github.com/mycr0ft/upython_si5351
#  in future, maybe use alarms? https://mattyt-micropython.readthedocs.io/en/latest/library/machine.RTC.html
#  see also here for sleep info: https://forum.core-electronics.com.au/t/pi-pico-sleep-dormant-states/12584/18
#
# This version tests the benefits of sleeping while doing things.



from machine import ADC, Pin, lightsleep, I2C, UART, WDT, RTC, freq
from micropyGPS import MicropyGPS
from time import sleep, ticks_us
import SI5351


sensor_temp = ADC(4)
sensor_vsys = ADC(29)
usb_power = Pin(24, Pin.IN)
led = Pin(25, Pin.OUT)               # on-board LED
tx = Pin(28, Pin.OUT, value=1)       # Synth and TCXO power (inverted)
gps = Pin(2, Pin.OUT, value=1)       # GPS power (inverted)
gpsreset = Pin(6, Pin.OUT, value=0)  # GPS reset line



def usbsleep(sleeptime):
# sleep routine that uses a (half-length) regular sleep if there's USB power (so as not to break connection)
# and a lightsleep if it's running on batteries / solar.
    if usb_power():
        sleep(sleeptime/2)
    else:
        lightsleep(sleeptime*1000)


def coretemp():
    return 27 - (sensor_temp.read_u16() * 3.3 / 65536.0 - 0.716)/0.001721

def vsys():
    return sensor_vsys.read_u16() * 3.23 * 3.0 / 16384.0

def initgps():
    gpsuart = UART(1)
    gpsuart.init(baudrate=9600, bits=8, parity=None, stop=1, tx=8, rx=9)
    my_gps = MicropyGPS()


def startgps():
    gps.value(0)
    sleep(0.01)
    gpsreset.value(1)


def stopgps():
    gpsreset.value(0)
    gps.value(1)
    

def testgps():
    # reset and turn on GPS
    startgps()

    cnt=1
    print('Trying to parse GPS:')
    while True:
        if gpsuart.any():
            thischar = gpsuart.read(1).decode()
            stat = my_gps.update(thischar)
            #print(thischar,end='')
            cnt=cnt+1
            if (cnt%300)==0:
                print('        Stat, Fix, sats, CRCfails:',stat, my_gps.fix_type,my_gps.satellites_in_use,my_gps.crc_fails)
            
        #print('time:',my_gps.timestamp)
        #print('sats:',my_gps.satellites_in_use)
        #print('fix:',my_gps.fix_type)
        #sleep(1)
    


def sendtone():
    # turn on TCXO and Synth
    tx.value(0)
    sleep(0.05)

    # init synth
    i2c = I2C(id=0, scl=Pin(5), sda=Pin(4), freq=400000)
    clockgen = SI5351.SI5351( i2c) 
    clockgen.begin()
    clockgen.setClockBuilderData()

    fclock=26e6
    a=36
    b=0
    c=1
    fsynth=fclock*(a+b/c)
    # start transmitting using CLK0 only for now
    print("Set PLLA to {:2.6f}MHz".format(fsynth*1e-6))
    clockgen.setupPLL(a, b, c, pllsource='A')

    a=18
    b=0
    c=10345
    fout=fsynth/(a+b/c)
    print("Set Output #0 to {:2.6f}MHz".format(fout*1e-6))
    clockgen.setupMultisynth( output=0, div=a, num=b, denom=c, pllsource="A", phase_delay=0.0)
    clockgen.enableOutputs(True)
    sleep(2)
    clockgen.enableOutputs(False)
    print('Done. RF Off')
    sleep(1)
    tx.value(1)
    print('Synth and TCXO off')
    

def blinkled(num):
    for a in range(num):
        led.value(1)
        sleep(0.03)
        led.value(0)
        sleep(0.22)  


def sleepy_flash(howlong=10):
    for a in range(howlong*4):
        led.value(1)
        usbsleep(0.01)
        led.value(0)
        #wdt.feed()
        usbsleep(0.24)



#############################################################
#wdt = WDT(timeout=8000)
#wdt.feed()


# This program currently works both with USB connected (for basic debugging)
# and on battery, for power consumption testing
# 48 MHz is OK for USB, 18 MHz is OK without USB. Diminishing returns after that.

print('Vsys  = ',vsys())
print('Tcore = ',coretemp())
if usb_power():
    print('USB power so sleeps will be normal sleeps, shorter and lighter, clock wont change')

if not usb_power():
    print('Changing to 18 MHz clock')
    freq(18000000)

tx.value(1)
led.value(1)
sleep(2)

# bunch of tests of different power states, for my measurements
# LED blinking to tell me what it's doing next.


# init synth
tx.value(0)
sleep(0.1)
i2c = I2C(id=0, scl=Pin(5), sda=Pin(4), freq=200000)
clockgen = SI5351.SI5351(i2c, crystalFreq=26e6)
sleep(0.1)
clockgen.begin()

clockgen.setupPLL(24, 0, 1, pllsource='A')
print("Set PLLA to {:2.6f}MHz".format(clockgen.plla_freq*1e-6))

a=120
b=1
c=10000
clockgen.setupMultisynth( output=0, div=a, num=b, denom=c, pllsource="A", phase_delay=0.0,  inverted=0, powerdown=0)
clockgen.setupMultisynth( output=1, div=a, num=b, denom=c, pllsource="A", phase_delay=0.0,  inverted=1, powerdown=0)
print("Set Output #0 and #1 to {:2.6f}MHz".format(clockgen.plla_freq/(a+b/c)*1e-6))

clockgen.PLLsoftreset()

clockgen.configureOutputs(0x03)

sleep(2000)


for a in range(100):
    clockgen.configureOutputs(0x01)

    sleep(2)

    clockgen.configureOutputs(0x03)

    sleep(2)
    
    clockgen.configureOutputs(0x02)

    sleep(2)
          



sleep(1000)


blinkled(3)
usbsleep(10)



clockgen.enableOutputs(False)
print('Outputs disabled')
blinkled(4)
usbsleep(10)


tx.value(1)
print('TCXO and Synth power down')
blinkled(5)
usbsleep(10)



'''
print('20s GPS powered and enabled')
gps.value(0)
gpsreset.value(1)
usbsleep(10)

gpsreset.value(0)
gps.value(1)
print('GPS off')
'''

# clean up
print('done')
led.value(0)
gpsreset.value(0)
gps.value(1)
gps.value(1)
tx.value(1)    
