import forecastio
import sys
import json
import os
import config
from pprint import pprint
from urllib2 import urlopen

reload(sys)
sys.setdefaultencoding('UTF8')

def calculateWater(age, kg):
    print "VREDNOST:", age, kg
    lbs = 2.20462262 * kg
    final = ((lbs/2.2)*age) / 28.3
    cups = final/8
    return cups


def getCups(lat, lon, age, kg):
    apikey = os.environ['FORECAST_KEY']
    forecast = forecastio.load_forecast(apikey, lat, lon)
    #pprint(forecast.json['currently']['apparentTemperature'])
    #print getplace(lat, lng)
    temp = forecast.json['currently']['apparentTemperature']
    town, city = getplace(lat, lon)
    string = ""
    if town == None and city != None:
        string = "Currently in %s it's around %.1f degrees.  " %(city, temp)
    elif town == None and city == None:
        string = "I see that temperature at your location is around %.1f degrees " %(temp)
    if town != None and city != None:
        string = "Currently in %s, %s it's around %.1f degrees.  " %(city, town, temp)

    cups = calculateWater(age, kg)
    stringCups = ""
    if temp > 25:
        stringWeather = "Since the weather is \xF0\x9F\x8C\x9E, "
        StringCups = "you should drink around %d cups (0.2l) of water today! ^_^" %(cups+1)
    else:
        stringWeather = "Since the weather is \xE2\x98\x81, "
        stringCups = "you should drink around %d cups (0.2l) of water today! ^_^" %(cups-1)
    stringCups.encode('unicode_escape')
    return string, stringWeather, stringCups

def getplace(lat, lon):
    url = "http://maps.googleapis.com/maps/api/geocode/json?"
    url += "latlng=%s,%s&sensor=false" % (lat, lon)
    v = urlopen(url).read()
    j = json.loads(v)
    print "JSON ADDRESS:", j
    components = j['results'][0]['address_components']
    country = town = None
    for c in components:
        if "country" in c['types']:
            country = c['long_name']
        if "postal_town" in c['types']:
            town = c['long_name']
    return town, country



#print getCups(44.819042,20.420215, 22, 95)
