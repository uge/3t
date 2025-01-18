from machine import Pin, UART
from micropyGPS import MicropyGPS
import asyncio
import time
import logging 

logger = logging.getLogger(__name__)

class GPSmodule:
    uart: UART
    gps_power: Pin
    gps_reset: Pin
    uart_tx_pin: Pin
    uart_tx_pin: Pin
    mpyGPS: MicropyGPS
    status_task: asyncio.Task
    rx_loop_task: asyncio.Task
    gps_state_lock: asyncio.Lock

    def __init__(self) -> None:
        self.mpyGPS = MicropyGPS()
        self.gps_state_lock = asyncio.Lock()

        '''
        Initial values for power and reset 
            Power -> pFET control set to 1     -> power disabled
            Reset -> active low reset set to 0 -> reset asserted
        '''
        self.gps_power = Pin(2, Pin.OUT, value=1) # Initially turn of PFET power control
        self.gps_reset = Pin(6, Pin.OUT, value=0) # Intiially assert active low reset
        
        '''
        Initial values for UART GPIO pins set to high impedence inputs for
        leakage reduction from PI UART TX to GPS receiver without power on IO
        '''
        self.uart_tx_pin = Pin(8, Pin.IN)         
        self.uart_rx_pin = Pin(9, Pin.IN) 

        self.uart = UART(1,tx=self.uart_tx_pin, rx=self.uart_rx_pin)
        self.uart.init(baudrate=9600, bits=8, parity=None, stop=1, flow=0)

    def _shutdown(self) -> None:
        return

    async def power_on(self, on: bool):
        if on:
            self.uart_tx_pin.init(mode=Pin.OUT) # Enable output driver on tx
            self.gps_reset.value(0)
            self.gps_power.value(0)
            time.sleep(0.25)
            self.gps_reset.value(1)
            logger.debug("Starting GPS tasks")
            self.rx_loop_task = asyncio.create_task( self._rx_loop() )
            self.status_task = asyncio.create_task( self._status() )
            await asyncio.sleep(0)
            logger.debug("GPS Power ON done")
            await asyncio.sleep(5)
        else:
            logger.debug("Killing GPS tasks")
            if self.rx_loop_task:
                self.rx_loop_task.cancel()
                self.rx_loop_task = None
            if self.status_task:
                self.status_task.cancel()
                self.status_task = None

            self.uart_tx_pin.init(mode=Pin.IN) # Disable output driver on tx to prevent leakage
            logger.debug("GPS Power OFF")
            self.gps_reset.value(0)
            self.gps_power.value(1)

    async def _rx_loop(self):
        logger.debug("UART RX task starting")
        self.sreader = asyncio.StreamReader(self.uart)

        while True:
            s = await self.sreader.readline()
            try:
                msg = s.decode()
                logger.debug(msg.strip())
                async with self.gps_state_lock:
                    for c in msg:
                        self.mpyGPS.update(c)
            except Exception as e:
                logger.error(e)

    async def _status(self):
        logger.debug("GPS status printer task starting")
        while True:
            s = await asyncio.sleep(5)
            async with self.gps_state_lock:
                logger.info(self.mpyGPS.timestamp)
                logger.info(self.mpyGPS.longitude)
                logger.info(self.mpyGPS.latitude) 
