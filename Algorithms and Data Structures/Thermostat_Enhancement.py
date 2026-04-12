#------------------------------------------------------------------
# Thermostat - Enhanced Version (Category Two: Algorithms & Data Structures)
#------------------------------------------------------------------

from time import sleep
from datetime import datetime
from statemachine import StateMachine, State
import board
import adafruit_ahtx0
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
import serial
from gpiozero import Button, PWMLED
from threading import Thread
from math import floor
from collections import deque  

## DEBUG flag
DEBUG = True

## Initialize I2C and Sensor
i2c = board.I2C()
thSensor = adafruit_ahtx0.AHTx0(i2c)

## Initialize Serial
ser = serial.Serial(
        port='/dev/ttyS0',
        baudrate = 115200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
)

## LEDs
redLight = PWMLED(18)
blueLight = PWMLED(23)

class ManagedDisplay():
    def __init__(self):
        self.lcd_rs = digitalio.DigitalInOut(board.D17)
        self.lcd_en = digitalio.DigitalInOut(board.D27)
        self.lcd_d4 = digitalio.DigitalInOut(board.D5)
        self.lcd_d5 = digitalio.DigitalInOut(board.D6)
        self.lcd_d6 = digitalio.DigitalInOut(board.D13)
        self.lcd_d7 = digitalio.DigitalInOut(board.D26)
        self.lcd_columns = 16
        self.lcd_rows = 2 
        self.lcd = characterlcd.Character_LCD_Mono(self.lcd_rs, self.lcd_en, 
                    self.lcd_d4, self.lcd_d5, self.lcd_d6, self.lcd_d7, 
                    self.lcd_columns, self.lcd_rows)
        self.lcd.clear()

    def cleanupDisplay(self):
        self.lcd.clear()
        for pin in [self.lcd_rs, self.lcd_en, self.lcd_d4, self.lcd_d5, self.lcd_d6, self.lcd_d7]:
            pin.deinit()

    def updateScreen(self, message):
        self.lcd.clear()
        self.lcd.message = message

screen = ManagedDisplay()

class TemperatureMachine(StateMachine):
    "Enhanced State Machine with Data Smoothing and Preference Logging"

    off = State(initial = True)
    heat = State()
    cool = State()

    cycle = (
        off.to(heat) |
        heat.to(cool) |
        cool.to(off)
    )

    def __init__(self):
        super(TemperatureMachine, self).__init__()
        self.setPoint = 72
        self.endDisplay = False
        
        # ALGORITHM DATA STRUCTURES
        # 1. Sliding window for temperature smoothing (max 10 items)
        self.temp_history = deque(maxlen=10)
        
        # 2. Preference tracking for "Comfort Range"
        self.user_goal_high = 72
        self.user_goal_low = 72

    #--------------------------------------------------------------
    # ALGORITHM 1: SENSOR SMOOTHING (Moving Average)
    #--------------------------------------------------------------
    def get_stabilized_temp(self):
        raw_temp = self.getFahrenheit()
        self.temp_history.append(raw_temp)
        
        # Calculate the average of the data structure
        avg_temp = sum(self.temp_history) / len(self.temp_history)
        return avg_temp

    #--------------------------------------------------------------
    # ALGORITHM 2: PREFERENCE LOGGER
    #--------------------------------------------------------------
    def update_user_history(self):
        if self.setPoint > self.user_goal_high:
            self.user_goal_high = self.setPoint
        if self.setPoint < self.user_goal_low:
            self.user_goal_low = self.setPoint

    def on_enter_heat(self):
        self.updateLights()
        if(DEBUG): print("* State: HEAT")

    def on_exit_heat(self):
        redLight.off()

    def on_enter_cool(self):
        self.updateLights()
        if(DEBUG): print("* State: COOL")
    
    def on_exit_cool(self):
        blueLight.off()

    def on_enter_off(self):
        redLight.off()
        blueLight.off()
        if(DEBUG): print("* State: OFF")
    
    def processTempStateButton(self):
        self.cycle()

    def processTempIncButton(self):
        self.setPoint += 1
        self.update_user_history() 
        self.updateLights()

    def processTempDecButton(self):
        self.setPoint -= 1
        self.update_user_history() 
        self.updateLights()

    def updateLights(self):
        # Utilizing the stabilized algorithm output 
        temp = floor(self.get_stabilized_temp())
        redLight.off()
        blueLight.off()
    
        if self.current_state == self.heat:
            if temp < self.setPoint:
                redLight.pulse()
            else:
                redLight.on()
        elif self.current_state == self.cool:
            if temp > self.setPoint:
                blueLight.pulse()
            else:
                blueLight.on()

    def run(self):
        myThread = Thread(target=self.manageMyDisplay)
        myThread.start()

    def getFahrenheit(self):
        t = thSensor.temperature
        return (((9/5) * t) + 32)
    
    def setupSerialOutput(self, stabilized_temp):
        # Updated serial string 
        return f"{self.current_state.id},{floor(stabilized_temp)},{self.setPoint},{self.user_goal_low},{self.user_goal_high}\n"

    def manageMyDisplay(self):
        counter = 1
        altCounter = 1
        while not self.endDisplay:
            # Process Algorithms
            current_avg = self.get_stabilized_temp()
            
            current_time = datetime.now()
            lcd_line_1 = current_time.strftime("%m-%d %H:%M\n")
    
            # Update line 2 logic to rotate between average temp and comfort range
            if(altCounter < 5):
                lcd_line_2 = f"Avg Temp: {floor(current_avg)}F"
            elif(altCounter < 10):
                lcd_line_2 = f"{self.current_state.id.upper()} SP:{self.setPoint}"
            else:
                # Display comfort range from Algorithm 2
                lcd_line_2 = f"Range:{self.user_goal_low}-{self.user_goal_high}"
            
            altCounter += 1
            if(altCounter > 15):
                self.updateLights()
                altCounter = 1
    
            screen.updateScreen(lcd_line_1 + lcd_line_2)
    
            if((counter % 30) == 0):
                ser.write(self.setupSerialOutput(current_avg).encode('utf-8'))
                counter = 1
            else:
                counter += 1
            sleep(1)

        screen.cleanupDisplay()

## Initialize System
tsm = TemperatureMachine()
tsm.run()

## Buttons
redButton = Button(24)
redButton.when_pressed = tsm.processTempStateButton

blueButton = Button(25)
blueButton.when_pressed = tsm.processTempIncButton

greenButton = Button(12)
greenButton.when_pressed = tsm.processTempDecButton

## Main Loop
repeat = True
while repeat:
    try:
        sleep(30)
    except KeyboardInterrupt:
        print("Cleaning up. Exiting...")
        repeat = False
        tsm.endDisplay = True
        sleep(1)