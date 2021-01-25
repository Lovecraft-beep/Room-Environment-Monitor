#!/usr/bin/env python3
print("***********************")
print("* Environment Monitor *")
print("*                     *")
print("*  2021 - Lockdown 3  *")
print("* Enviro+ & PM Sensor *")
print("*                     *")
print("***********************")
# Code comes from all over the shop

# setup imports
from Adafruit_IO import Client, RequestError, Feed

from time import sleep

import os

try:
	from smbus2 import SMBus
except ImportError:
	from smbus import SMBus

import colorsys
import sys
import ST7735
try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from bme280 import BME280
from pms5003 import PMS5003, ReadTimeoutError as pmsReadTimeoutError, SerialTimeoutError
from enviroplus import gas
from subprocess import PIPE, Popen
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from fonts.ttf import RobotoMedium as UserFont
import logging

import ST7735

# set up keys
ADAFRUIT_IO_USERNAME = "##################"
ADAFRUIT_IO_KEY = "####################"

aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

# set up feeds
try:
	temp_feed = aio.feeds('temperature')
except RequestError:
	test = Feed(name='temperature')
	temp_feed = aio.create_feed(test)

try:
	humi_feed = aio.feeds('humidity')
except RequestError:
	test = Feed(name='humidity')
	humi_feed = aio.create_feed(test)

try:
	light_feed = aio.feeds('light')
except RequestError:
	test = Feed(name='light')
	light_feed = aio.create_feed(test)

try:
	press_feed = aio.feeds('pressure')
except RequestError:
	test = Feed(name='pressure')
	press_feed = aio.create_feed(test)

try:
	oxy_feed = aio.feeds('oxidised')
except RequestError:
	test = Feed(name='oxidised')
	oxy_feed = aio.create_feed(test)

try:
	reduced_feed = aio.feeds('reduced')
except RequestError:
	test = Feed(name='reduced')
	reduced_feed = aio.create_feed(test)

try:
	nh3_feed = aio.feeds('nh3')
except RequestError:
	test = Feed(name='nh3')
	nh3_feed = aio.create_feed(test)

try:
	pm1_feed = aio.feeds('pm1')
except RequestError:
	test = Feed(name='pm1')
	pm1_feed = aio.create_feed(test)
try:
	pm25_feed = aio.feeds('pm25')
except RequestError:
	test = Feed(name='pm25')
	pm25_feed = aio.create_feed(test)

try:
	pm10_feed = aio.feeds('pm10')
except RequestError:
	test = Feed(name='pm10')
	pm10_feed = aio.create_feed(test)

# set up logs
logging.basicConfig(
	format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S')

logging.info("""

Press Ctrl+C to exit!

""")
# set up sensors
bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)
pms5003 = PMS5003()

# Create ST7735 LCD display class
st7735 = ST7735.ST7735(
    port=0,
    cs=1,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=10000000
)

# Initialize display
st7735.begin()

WIDTH = st7735.width
HEIGHT = st7735.height

# Set up canvas and font
img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
draw = ImageDraw.Draw(img)
font_size_small = 10
font_size_large = 20
font = ImageFont.truetype(UserFont, font_size_large)
smallfont = ImageFont.truetype(UserFont, font_size_small)
x_offset = 2
y_offset = 2

message = ""

# The position of the top bar
top_pos = 25

# Create a values dict to store the data
variables = ["temperature",
             "pressure",
             "humidity",
             "light",
             "oxidised",
             "reduced",
             "nh3",
             "pm1",
             "pm25",
             "pm10"]

units = ["C",
         "hPa",
         "%",
         "Lux",
         "kO",
         "kO",
         "kO",
         "ug/m3",
         "ug/m3",
         "ug/m3"]

# Define warning limits
limits = [[4, 18, 28, 35],
          [250, 950, 1015, 1080],
          [20, 30, 60, 70],
          [-1, -1, 30000, 100000],
          [-1, -1, 40, 50],
          [-1, -1, 450, 550],
          [-1, -1, 200, 300],
          [-1, -1, 50, 100],
          [-1, -1, 50, 100],
          [-1, -1, 50, 100]]

# RGB palette for values on the combined screen
palette = [(0, 0, 255),           # Dangerously Low
           (0, 255, 255),         # Low
           (0, 255, 0),           # Normal
           (255, 255, 0),         # High
           (255, 0, 0)]           # Dangerously High

values = {}

# Get the temperature of the CPU for compensation
def get_cpu_temperature():
	with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        	temp = f.read()
        	temp = int(temp) / 1000.0
	return temp

def save_data(idx, data):
    variable = variables[idx]
    # Maintain length of list
    values[variable] = values[variable][1:] + [data]
    unit = units[idx]
    message = "{}: {:.1f} {}".format(variable[:4], data, unit)

# Displays all the text on the LCD
def display_everything():
    draw.rectangle((0, 0, WIDTH, HEIGHT), (0, 0, 0))
    column_count = 2
    row_count = (len(variables) / column_count)
    for i in range(len(variables)):
        variable = variables[i]
        data_value = values[variable][-1]
        unit = units[i]
        x = x_offset + ((WIDTH // column_count) * (i // row_count))
        y = y_offset + ((HEIGHT / row_count) * (i % row_count))
        message = "{}: {:.1f} {}".format(variable[:4], data_value, unit)
        lim = limits[i]
        rgb = palette[0]
        for j in range(len(lim)):
            if data_value > lim[j]:
                rgb = palette[j + 1]
        draw.text((x, y), message, font=smallfont, fill=rgb)
    st7735.display(img)

# Cycle the sensors once to stabalise readings
cpu_temp = get_cpu_temperature()
cpu_temps = [get_cpu_temperature()] * 5
factor = 2.25
# Smooth out with some averaging to decrease jitter
cpu_temps = cpu_temps[1:] + [cpu_temp]
avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
raw_temp = bme280.get_temperature()
comp_temp = raw_temp - ((avg_cpu_temp - raw_temp) / factor)

# Pressures
press_reading = bme280.get_pressure()

# Humidity
humid_reading = bme280.get_humidity()

# Light meter
light_reading = ltr559.get_lux()

# Gas Sensor
data = gas.read_all()
oxide_reading = data.oxidising / 1000
reduc_reading = data.reducing / 1000
nh3_reading = data.nh3 / 1000

# PM Sensor
try:
	data = pms5003.read()
except pmsReadTimeoutError:
	logging.warning("Failed to read PMS5003")
else:
	pm1m_reading = float(data.pm_ug_per_m3(1.0))
	pm10m_reading = float(data.pm_ug_per_m3(10))
	pm25m_reading = float(data.pm_ug_per_m3(2.5))

sleep(60)

def main():
	factor = 2.25

	cpu_temps = [get_cpu_temperature()] * 5
	for v in variables:
		values[v] = [1] * WIDTH

	# main loop
	try:
		while True:
		# Temp first
			cpu_temp = get_cpu_temperature()

			# Smooth out with some averaging to decrease jitter
			cpu_temps = cpu_temps[1:] + [cpu_temp]
			avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
			raw_temp = bme280.get_temperature()
			comp_temp = raw_temp - ((avg_cpu_temp - raw_temp) / factor)

			# Pressures
			press_reading = bme280.get_pressure()

			# Humidity
			humid_reading = bme280.get_humidity()

			# Light meter
			light_reading = ltr559.get_lux()

			# Gas Sensor
			data = gas.read_all()
			oxide_reading = data.oxidising / 1000
			reduc_reading = data.reducing / 1000
			nh3_reading = data.nh3 / 1000

			# PM Sensor
			try:
				data = pms5003.read()
			except pmsReadTimeoutError:
				logging.warning("Failed to read PMS5003")
			else:
				pm1m_reading = float(data.pm_ug_per_m3(1.0))
				pm10m_reading = float(data.pm_ug_per_m3(10))
				pm25m_reading = float(data.pm_ug_per_m3(2.5))

			# Write to logs
			logging.info("Compensated temperature: {:05.2f} *C".format(comp_temp))
			logging.info("Pessure: {:05.2f} *HPa".format(press_reading))
			logging.info("Humidity: {:05.2f} *RH%".format(humid_reading))
			logging.info("Light: {:05.2f} *lux".format(light_reading))
			logging.info("Oxidised: {:05.2f} *kO".format(oxide_reading))
			logging.info("Reduced: {:05.2f} *k0".format(reduc_reading))
			logging.info("nH3: {:05.2f} *kO".format(nh3_reading))
			logging.info("Particulate Matter <1 micron: {:05.2f} *ug/m3".format(pm1m_reading))
			logging.info("Particulate Matter <2.5 micron: {:05.2f} *ug/m3".format(pm25m_reading))
			logging.info("Particulate Matter <10 micron: {:05.2f} *ug/m3".format(pm10m_reading))

			# Process data for Display
			save_data(0, comp_temp)
			save_data(1, press_reading)
			save_data(2, humid_reading)
			save_data(3, light_reading)
			save_data(4, oxide_reading)
			save_data(5, reduc_reading)
			save_data(6, nh3_reading)
			save_data(7, pm1m_reading)
			save_data(8, pm25m_reading)
			save_data(9, pm10m_reading)

			# Write to LCD
			display_everything()

			# Write data to Dashboard
			try:
				aio.send_data(temp_feed.key, comp_temp)
				aio.send_data(humi_feed.key, humid_reading)
				aio.send_data(light_feed.key, light_reading)
				aio.send_data(press_feed.key, press_reading)
				aio.send_data(oxy_feed.key, oxide_reading)
				aio.send_data(reduced_feed.key, reduc_reading)
				aio.send_data(nh3_feed.key, nh3_reading)
				aio.send_data(pm1_feed.key, pm1m_reading)
				aio.send_data(pm10_feed.key, pm10m_reading)
				aio.send_data(pm25_feed.key, pm25m_reading)
			except RequestError:
				os.system("sudo reboot")

			# wait a while
			sleep(300)

	#Exit Well
	except KeyboardInterrupt:
			sys.exit(0)

if __name__ == "__main__":
	main()
