
import machine, time
from machine import Pin

class Lcd():
      # Pinout, change within or outside class for your use case
    PINS = ['A','B','C','D','E','F']
    # Pin names, don't change
   
    PIN_NAMES = ['RS','E','D4','D5','D6','D7']

    # Dict of pins
    pins = {}

    # Pin mode, push-pull control
    PIN_MODE = Pin.OUT

    # Define some device constants
    LCD_WIDTH = 16    # Maximum characters per line
    # Designation of T/F for character and command modes
    LCD_CHR = True
    LCD_CMD = False

    LINES = {
        0: 0x80, # LCD RAM address for the 1st line
        1: 0xC0, # LCD RAM address for the 2nd line
        # Add more if desired
    }

    # Timing constants
    E_PULSE = 50
    E_DELAY = 50

    def init(self):
        # Initialise pins
        for pin, pin_name in zip(self.PINS, self.PIN_NAMES):
            # setattr(self, 'LCD_'+pin_name,   # Unsupported
            #     pyb.Pin(pin, self.PIN_MODE))
            self.pins['LCD_'+pin_name] = Pin(pin, self.PIN_MODE)
        # Initialise display
        self.lcd_byte(0x33,self.LCD_CMD)
        self.lcd_byte(0x32,self.LCD_CMD)
        self.lcd_byte(0x28,self.LCD_CMD)
        self.lcd_byte(0x0C,self.LCD_CMD)
        self.lcd_byte(0x06,self.LCD_CMD)
        self.lcd_byte(0x01,self.LCD_CMD)

    def clear(self):
        # Clear the display
        self.lcd_byte(0x01,self.LCD_CMD)

    def set_line(self, line):
        # Set the line that we're going to print to
        self.lcd_byte(self.LINES[line], self.LCD_CMD)

    def set_string(self, message):
        # Pad string out to LCD_WIDTH
        # message = message.ljust(LCD_WIDTH," ")
        m_length = len(message)
        if m_length < self.LCD_WIDTH:
            short = self.LCD_WIDTH - m_length
            blanks=str()
            for i in range(short):
                blanks+=' '
            message+=blanks
        for i in range(self.LCD_WIDTH):
            self.lcd_byte(ord(message[i]), self.LCD_CHR)

    def lcd_byte(self, bits, mode):
        # Send byte to data pins
        # bits = data
        # mode = True  for character
        #        False for command

        self.pin_action('LCD_RS', mode) # RS

        # High bits
        self.pin_action('LCD_D4', False)
        self.pin_action('LCD_D5', False)
        self.pin_action('LCD_D6', False)
        self.pin_action('LCD_D7', False)
        if bits&0x10==0x10:
            self.pin_action('LCD_D4', True)
        if bits&0x20==0x20:
            self.pin_action('LCD_D5', True)
        if bits&0x40==0x40:
            self.pin_action('LCD_D6', True)
        if bits&0x80==0x80:
            self.pin_action('LCD_D7', True)

        # Toggle 'Enable' pin
        self.pin_action('LCD_E', True)
        self.pin_action('LCD_E', False)

        # Low bits
        self.pin_action('LCD_D4', False)
        self.pin_action('LCD_D5', False)
        self.pin_action('LCD_D6', False)
        self.pin_action('LCD_D7', False)
        if bits&0x01==0x01:
            self.pin_action('LCD_D4', True)
        if bits&0x02==0x02:
            self.pin_action('LCD_D5', True)
        if bits&0x04==0x04:
            self.pin_action('LCD_D6', True)
        if bits&0x08==0x08:
            self.pin_action('LCD_D7', True)

        # Toggle 'Enable' pin
        self.pin_action('LCD_E', True)
        self.pin_action('LCD_E', False)

    def pin_action(self, pin, high):
        # Pin high/low functions, set as function for portability
        if high:
            self.pins[pin].value(1)
        else:

            self.pins[pin].value(0)

class HCSR04:
    """
    Driver to use the untrasonic sensor HC-SR04.
    The sensor range is between 2cm and 4m.
    The timeouts received listening to echo pin are converted to OSError('Out of range')
    """
    # echo_timeout_us is based in chip range limit (400cm)
    def __init__(self, trigger_pin, echo_pin, echo_timeout_us=500*2*30):
        """
        trigger_pin: Output pin to send pulses
        echo_pin: Readonly pin to measure the distance. The pin should be protected with 1k resistor
        echo_timeout_us: Timeout in microseconds to listen to echo pin. 
        By default is based in sensor limit range (4m)
        """
        self.echo_timeout_us = echo_timeout_us
        # Init trigger pin (out)
        self.trigger = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        self.trigger.value(0)

        # Init echo pin (in)
        self.echo = Pin(echo_pin, mode=Pin.IN, pull=None)

    def _send_pulse_and_wait(self):
        """
        Send the pulse to trigger and listen on echo pin.
        We use the method `machine.time_pulse_us()` to get the microseconds until the echo is received.
        """
        self.trigger.value(0) # Stabilize the sensor
        time.sleep_us(5)
        self.trigger.value(1)
        # Send a 10us pulse.
        time.sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_time = machine.time_pulse_us(self.echo, 1, self.echo_timeout_us)
            return pulse_time
        except OSError as ex:
            if ex.args[0] == 110: # 110 = ETIMEDOUT
                raise OSError('Out of range')
            raise ex

    def distance_mm(self):
        """
        Get the distance in milimeters without floating point operations.
        """
        pulse_time = self._send_pulse_and_wait()

        # To calculate the distance we get the pulse_time and divide it by 2 
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.34320 mm/us that is 1mm each 2.91us
        # pulse_time // 2 // 2.91 -> pulse_time // 5.82 -> pulse_time * 100 // 582 
        mm = pulse_time * 100 // 582
        return mm

    def distance_cm(self):
        """
        Get the distance in centimeters with floating point operations.
        It returns a float
        """
        pulse_time = self._send_pulse_and_wait()

        # To calculate the distance we get the pulse_time and divide it by 2 
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.034320 cm/us that is 1cm each 29.1us
        cms = (pulse_time / 2) / 29.1
        return cms
        
sensor = HCSR04(trigger_pin=13, echo_pin=12)
lcd = Lcd()
lcd.PINS = [19,23,18,17,16,15]
lcd.init()
lcd.set_line(0) # First line
lcd.set_string("DISTANCIA:") # Send a string
lcd.set_line(1) # Second line

while True:
  distance = sensor.distance_cm()
  lcd.set_line(0) # First line
  lcd.set_string("DISTANCIA:") # Send a string
  lcd.set_line(1) # Second line
  lcd.set_string(str(distance) + ' cm') # Again
  print('Distance:', distance, 'cm')
  
  if distance >= 10:
    led_verd.value(1)
    led_verm.value(0)
  else:
    led_verd.value(0)
    led_verm.value(1)
    
  time.sleep_us(60000)
    


