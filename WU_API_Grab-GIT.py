#!/usr/bin/env python3

## Sort out dependencies

import requests
import json
from Adafruit_IO import Client, RequestError, Feed
import logging
from time import sleep

## Initialise Variables
ADAFRUIT_IO_USERNAME = "xxx"
ADAFRUIT_IO_KEY = "xxx"

aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

## Set Up Feeds
try:
    statid_feed = aio.feeds('statid')
except RequestError:
    test = Feed(name='statid')
    statid_feed = aio.create_feed(test)

try:
    latloc_feed = aio.feeds('lat')
except RequestError:
    test = Feed(name='lat')
    latloc_feed = aio.create_feed(test)

try:
    lonloc_feed = aio.feeds('lon')
except RequestError:
    test = Feed(name='lon')
    lonloc_feed = aio.create_feed(test)

try:
    time_feed = aio.feeds('tim')
except RequestError:
    test = Feed(name='tim')
    time_feed = aio.create_feed(test)

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
    htindx_feed = aio.feeds('heatindex')
except RequestError:
    test = Feed(name='heatindex')
    htindx_feed = aio.create_feed(test) 

try:
    dwpnt_feed = aio.feeds('dewpoint')
except RequestError:
    test = Feed(name='dewpoint')
    dwpnt_feed = aio.create_feed(test) 

try:
    wnddr_feed = aio.feeds('winddir')
except RequestError:
    test = Feed(name='winddir')
    wnddr_feed = aio.create_feed(test)

try:
    wndspd_feed = aio.feeds('windspeed')
except RequestError:
    test = Feed(name='windspeed')
    wndspd_feed = aio.create_feed(test)

try:
    wndgst_feed = aio.feeds('windgust')
except RequestError:
    test = Feed(name='windgust')
    wndgst_feed = aio.create_feed(test)

try:
    wndchll_feed = aio.feeds('windchill')
except RequestError:
    test = Feed(name='windchill')
    wndchll_feed = aio.create_feed(test)

try:
    rnfll_feed = aio.feeds('rainfall')
except RequestError:
    test = Feed(name='rainfall')
    rnfll_feed = aio.create_feed(test)

try:
    rnrt_feed = aio.feeds('rainfallrate')
except RequestError:
    test = Feed(name='rainfallrate')
    rnrt_feed = aio.create_feed(test)

def main():
    try:
        while True:
            print('fetching data')

            f=requests.get('https://api.weather.com/v2/pws/observations/current?stationId=INOTTI184&format=json&units=h&apiKey=2770a2c198f74b78b0a2c198f77b787c')
                   
            data = json.loads(f.text)
            clean = {}
            for key, value in data.items():
                if key in ('imperial', 'metric', 'uk_hybrid'):
                        clean['units'] = key
                        for k,v in value.items():
                            clean[k] = v
                else:
                        clean[key] = value
                        
            for i in data['observations']:
                gmt = (i['obsTimeUtc'])
                winddir = (i['winddir'])
                humidity = (i['humidity'])
                latitude = (i['lat'])
                longtitude = (i['lon'])
                stationID = (i['stationID'])
                ukhybrid = (i['uk_hybrid'])
                
                for x,y in ukhybrid.items():
                    if x == 'temp':
                        temp = y
                    if x == 'heatIndex':
                        heatIndex = y
                    if x == 'dewpt':
                        dewpt = y
                    if x == 'windChill':
                        windChill = y
                    if x == 'windSpeed':
                        windSpeed = y
                    if x == 'windGust':
                        windGust = y
                    if x == 'pressure':
                        pressure = y
                    if x == 'precipRate':
                        precipRate = y
                    if x == 'precipTotal':
                        precipTotal = y

            print('Station ID     :', stationID)
            print('Location       :', latitude, longtitude)
            print('Time           :', gmt)
            print('Ext Temp       :', temp,'C')
            print('Humidity       :', humidity,'RH%')
            print('Heat Index     :', heatIndex,'C')
            print('Dew Point      :', dewpt,'C')
            print('Wind Direction :', winddir)
            print('Wind Speed     :', windSpeed,' kmh')
            print('Wind Gust      :', windGust,' kmh')
            print('Wind Chill     :', windChill, 'C')
            print('Rainfall       :', precipTotal,'mm')
            print('Rain Rate      :', precipRate,'mm')

            #feeds
            aio.send_data(statid_feed.key, stationID)
            aio.send_data(latloc_feed.key, latitude)
            aio.send_data(lonloc_feed.key, longtitude)
            aio.send_data(time_feed.key, gmt)
            aio.send_data(temp_feed.key, temp)
            aio.send_data(humi_feed.key, humidity)
            aio.send_data(htindx_feed.key, heatIndex)
            aio.send_data(dwpnt_feed.key, dewpt)
            aio.send_data(wnddr_feed.key, winddir)
            aio.send_data(wndspd_feed.key, windSpeed)
            aio.send_data(wndgst_feed.key, windGust)
            aio.send_data(wndchll_feed.key, windChill)
            aio.send_data(rnfll_feed.key, precipTotal)
            aio.send_data(rnrt_feed.key, precipRate)

            sleep(300)

    except KeyboardInterrupt:
        sys.exit(0)
            
if __name__ == "__main__":
    main()
    
            
            
