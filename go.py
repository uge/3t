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

import logging
import sys
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)

from machine import ADC, Pin, lightsleep, I2C, UART, WDT, RTC, freq
from micropyGPS import MicropyGPS
from time import sleep, ticks_us
import asyncio

try:
    del sys.modules["jetpack.gps"]
except:
    pass

import jetpack.gps
import jetpack.wspr_tx 
import time 

sensor_temp = ADC(4)
sensor_vsys = ADC(29)
usb_power = Pin(24, Pin.IN)
led = Pin(25, Pin.OUT)               # on-board LED
tx = Pin(28, Pin.OUT, value=1)       # Synth and TCXO power (inverted)

logger.info("CPU frequency %s" % freq())
freq(48000000)

async def GPS_main():
    f = jetpack.wspr_tx.wspr_tx()
    logger.info("Turn on si")
    f.power_on(True)
    await asyncio.sleep(1)
    logger.info("SI on")
    print(f.i2c.scan())
    print(f.i2c.readfrom_mem(96, 0, 1)) 
    f.reset()
    f.pll.set_freq(0, 25000000)
    f.pll.output_enable(0,True)
    f.pll.drive_strength(0, 3)
    await asyncio.sleep(5)
    f.power_on(False)
    logger.info("Scanned")
    

    # gpso = jetpack.gps.GPSmodule()
    # await gpso.power_on(True)
    # await asyncio.sleep(60.0)
    # await gpso.power_on(False)
    # gpso._shutdown()

asyncio.get_event_loop().run_until_complete(GPS_main())

logger.info("Normal exit")

