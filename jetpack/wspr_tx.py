from logging import Logger
from machine import Pin, I2C

from . import si5351

_TCXO_FREQ = const(26000000)

class wspr_tx:

    power: Pin
    scl: Pin
    sda: Pin
    power: Pin
    i2c: I2C
    pll: si5351.SI5351

    def __init__(self):
        self.power = Pin(28, Pin.OUT, value=1)       # Synth and TCXO power
        self.sda = Pin(4)
        self.scl = Pin(5)
        self.i2c = I2C(0, scl=self.scl, sda=self.sda, freq=100000)
        self.pll = si5351.SI5351(self.i2c, xtal_freq=_TCXO_FREQ)

    def power_on(self, on: bool):
        if on:
            self.power.value(0)
        else:
            self.power.value(1)

    def reset(self):
        self.pll.reset()
        self.pll.init(xtal_load_c=si5351.CRYSTAL_LOAD_0PF,
                     xo_freq=_TCXO_FREQ,
                     corr=0)

    def controller(self):
        return self.i2c

