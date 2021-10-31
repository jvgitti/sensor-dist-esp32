
import machine, time
from machine import Pin
import network
from umqtt.simple import MQTTClient

led_verd = Pin(5,Pin.OUT)
led_verm = Pin(21,Pin.OUT)

# coloque aqui as informacoes de sua internet
WiFi_SSID = "Praieiro_Cima"
WiFi_PASS = "bachagostoso"
ligado = False
dist_min = 10


class Lcd():
      
    PINS = ['A','B','C','D','E','F']

    PIN_NAMES = ['RS','E','D4','D5','D6','D7']

    pins = {}

    PIN_MODE = Pin.OUT

    LCD_WIDTH = 16  
    LCD_CHR = True
    LCD_CMD = False

    LINES = {
        0: 0x80, 
        1: 0xC0, 
    }

    E_PULSE = 50
    E_DELAY = 50

    def init(self):
        for pin, pin_name in zip(self.PINS, self.PIN_NAMES):
            self.pins['LCD_'+pin_name] = Pin(pin, self.PIN_MODE)
        self.lcd_byte(0x33,self.LCD_CMD)
        self.lcd_byte(0x32,self.LCD_CMD)
        self.lcd_byte(0x28,self.LCD_CMD)
        self.lcd_byte(0x0C,self.LCD_CMD)
        self.lcd_byte(0x06,self.LCD_CMD)
        self.lcd_byte(0x01,self.LCD_CMD)

    def clear(self):
        self.lcd_byte(0x01,self.LCD_CMD)

    def set_line(self, line):
        self.lcd_byte(self.LINES[line], self.LCD_CMD)

    def set_string(self, message):
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
      
        self.pin_action('LCD_RS', mode)
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

        self.pin_action('LCD_E', True)
        self.pin_action('LCD_E', False)

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

        self.pin_action('LCD_E', True)
        self.pin_action('LCD_E', False)

    def pin_action(self, pin, high):
        
        if high:
            self.pins[pin].value(1)
        else:

            self.pins[pin].value(0)

class sensor_dist:
   
    def __init__(self, trigger_pin, echo_pin, echo_timeout_us=500*2*30):

        self.echo_timeout_us = echo_timeout_us
        self.trigger = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        self.trigger.value(0)

        self.echo = Pin(echo_pin, mode=Pin.IN, pull=None)

    def _send_pulse_and_wait(self):

        self.trigger.value(0)
        time.sleep_us(5)
        self.trigger.value(1)
        time.sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_time = machine.time_pulse_us(self.echo, 1, self.echo_timeout_us)
            return pulse_time
        except OSError as ex:
            if ex.args[0] == 110:
                raise OSError('Out of range')
            raise ex

    def distance_mm(self):

        pulse_time = self._send_pulse_and_wait()
        pulse_time * 100 // 582 
        mm = pulse_time * 100 // 582
        
        return mm

    def distance_cm(self):
        pulse_time = self._send_pulse_and_wait()
        cms = (pulse_time / 2) / 29.1
        return cms
        
def sub_cb(topic, msg):
  if topic == b'sensor/power':
    global ligado
    if msg == b'liga':
      ligado = True
    if msg == b'desliga':
      ligado = False
  elif topic == b'sensor/dist':
    global dist_min
    dist_min = eval(msg)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
  print('connecting to network...')
  wlan.connect(WiFi_SSID, WiFi_PASS)
  while not wlan.isconnected():
    pass
print('network config:', wlan.ifconfig())
# coloque aqui o endereco do broker
client = MQTTClient('23424234','broker.hivemq.com',port=1883)

client.set_callback(sub_cb)
client.connect()
client.subscribe('sensor/power')
client.subscribe('sensor/dist') 
sensor = sensor_dist(trigger_pin=13, echo_pin=12)
lcd = Lcd()

# coloque aqui os pinos do LCD
lcd.PINS = [19,23,18,17,16,15]
lcd.init()

while True:
  
  lcd.set_line(0)
  lcd.set_string("Sistema")
  lcd.set_line(1)
  lcd.set_string("Desativado")
  
  led_verd.value(0)
  led_verm.value(0)
  
  time.sleep_us(60000)
  
  client.wait_msg()
  
  while ligado:
    distance = sensor.distance_cm()
    lcd.set_line(0)
    lcd.set_string("DISTANCIA:")
    lcd.set_line(1)
    lcd.set_string(str(distance) + ' cm')
  
    if distance >= dist_min:
      led_verd.value(1)
      led_verm.value(0)
    else:
      led_verd.value(0)
      led_verm.value(1)
    
    time.sleep_us(60000)
    client.check_msg()




