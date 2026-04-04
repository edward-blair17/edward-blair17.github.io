from time import sleep, time
from datetime import datetime
from threading import Thread
from math import floor
import board
import adafruit_ahtx0
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
import serial
from gpiozero import Button, PWMLED
from statemachine import StateMachine, State

# =========================================================
# CONFIGURATION SECTION (Centralized Mapping)
# =========================================================
CONFIG = {
    'RED_LED_PIN': 18,
    'BLUE_LED_PIN': 23,
    'BUTTON_STATE_PIN': 24,
    'BUTTON_INC_PIN': 25,
    'BUTTON_DEC_PIN': 12,
    'LCD_RS': board.D17,
    'LCD_EN': board.D27,
    'LCD_D4': board.D5,
    'LCD_D5': board.D6,
    'LCD_D6': board.D13,
    'LCD_D7': board.D26,
    'SERIAL_PORT': '/dev/ttyS0',
    'BAUD_RATE': 115200,
    'HYSTERESIS_OFFSET': 0.5,  
    'DEFAULT_SETPOINT': 72,
    'DEBUG': True
}


# =========================================================
# TOOLBOX 1: THE HARDWARE INTERFACE
# =========================================================
class HardwareToolbox:
    """Manages all physical sensors and indicators."""

    def __init__(self):
        self.i2c = board.I2C()
        try:
            self.thSensor = adafruit_ahtx0.AHTx0(self.i2c)
        except Exception as e:
            print(f"CRITICAL ERROR: Sensor not found: {e}")
            self.thSensor = None

        self.redLight = PWMLED(CONFIG['RED_LED_PIN'])
        self.blueLight = PWMLED(CONFIG['BLUE_LED_PIN'])
        self.last_known_temp = CONFIG['DEFAULT_SETPOINT']

    def read_temperature_f(self):
        """Defensive wrapper for sensor reading."""
        try:
            if self.thSensor:
                t_celsius = self.thSensor.temperature
                t_fahrenheit = ((9 / 5) * t_celsius) + 32
                self.last_known_temp = t_fahrenheit
                return t_fahrenheit
            return self.last_known_temp
        except Exception as e:
            if CONFIG['DEBUG']:
                print(f"Warning: Sensor Read Failed ({e}). Using last good value.")
            return self.last_known_temp

    def update_indicators(self, state, current_temp, setpoint):
        """Control LEDs with Failsafe logic."""
        # Trigger if temp is significantly away from setpoint
        offset = CONFIG['HYSTERESIS_OFFSET']

        if state == "heat":
            self.blueLight.off()
            if current_temp < (setpoint - offset):
                self.redLight.pulse()
            elif current_temp >= setpoint:
                self.redLight.on()

        elif state == "cool":
            self.redLight.off()
            if current_temp > (setpoint + offset):
                self.blueLight.pulse()
            elif current_temp <= setpoint:
                self.blueLight.on()

        else:
            # Failsafe: Zero-State (Talking Point 3)
            self.redLight.off()
            self.blueLight.off()


# =========================================================
# TOOLBOX 2: THE SCREEN MANAGER
# =========================================================
class ScreenToolbox:
    """Manages the 16x2 LCD output logic."""

    def __init__(self):
        self.lcd_rs = digitalio.DigitalInOut(CONFIG['LCD_RS'])
        self.lcd_en = digitalio.DigitalInOut(CONFIG['LCD_EN'])
        self.lcd_d4 = digitalio.DigitalInOut(CONFIG['LCD_D4'])
        self.lcd_d5 = digitalio.DigitalInOut(CONFIG['LCD_D5'])
        self.lcd_d6 = digitalio.DigitalInOut(CONFIG['LCD_D6'])
        self.lcd_d7 = digitalio.DigitalInOut(CONFIG['LCD_D7'])

        self.lcd = characterlcd.Character_LCD_Mono(
            self.lcd_rs, self.lcd_en, self.lcd_d4,
            self.lcd_d5, self.lcd_d6, self.lcd_d7, 16, 2
        )
        self.lcd.clear()

    def update_display(self, temp, setpoint, state_name):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        line1 = f"{current_time}"
        line2 = f"{state_name.upper()} T:{floor(temp)} S:{setpoint}"
        self.lcd.message = f"{line1}\n{line2}"

    def cleanup(self):
        self.lcd.clear()
        for pin in [self.lcd_rs, self.lcd_en, self.lcd_d4, self.lcd_d5, self.lcd_d6, self.lcd_d7]:
            pin.deinit()


# =========================================================
# MAIN THERMOSTAT LOGIC
# =========================================================
class ThermostatController(StateMachine):
    off = State(initial=True)
    heat = State()
    cool = State()

    cycle = off.to(heat) | heat.to(cool) | cool.to(off)

    def __init__(self):
        super(ThermostatController, self).__init__()
        self.hw = HardwareToolbox()
        self.screen = ScreenToolbox()
        self.setpoint = CONFIG['DEFAULT_SETPOINT']
        self.running = True

        # Serial Setup
        self.ser = serial.Serial(CONFIG['SERIAL_PORT'], CONFIG['BAUD_RATE'], timeout=1)

        # Button Setup
        self.btn_state = Button(CONFIG['BUTTON_STATE_PIN'])
        self.btn_inc = Button(CONFIG['BUTTON_INC_PIN'])
        self.btn_dec = Button(CONFIG['BUTTON_DEC_PIN'])

        self.btn_state.when_pressed = self.cycle_state
        self.btn_inc.when_pressed = self.inc_setpoint
        self.btn_dec.when_pressed = self.dec_setpoint

    def cycle_state(self):
        self.cycle()
        if CONFIG['DEBUG']: print(f"Mode: {self.current_state.id}")

    def inc_setpoint(self):
        self.setpoint += 1

    def dec_setpoint(self):
        self.setpoint -= 1

    def run(self):
        """Main Loop using Non-blocking timing."""
        last_serial_time = 0
        last_display_time = 0

        try:
            while self.running:
                current_time = time()
                current_temp = self.hw.read_temperature_f()

                # Update physical hardware every loop for responsiveness
                self.hw.update_indicators(self.current_state.id, current_temp, self.setpoint)

                # Update Display every 2 seconds
                if current_time - last_display_time > 2:
                    self.screen.update_display(current_temp, self.setpoint, self.current_state.id)
                    last_display_time = current_time

                # Update Serial Server every 30 seconds
                if current_time - last_serial_time > 30:
                    status = f"{self.current_state.id},{floor(current_temp)},{self.setpoint}\n"
                    self.ser.write(status.encode('utf-8'))
                    last_serial_time = current_time

                sleep(0.1)  
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        print("\nSafety Shutdown Initiated...")
        self.running = False
        self.hw.update_indicators("off", 0, 0)  
        self.screen.cleanup()
        self.ser.close()


if __name__ == "__main__":
    thermostat = ThermostatController()
    thermostat.run()