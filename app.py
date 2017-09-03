import os
import sys
import json
import requests
import re
import forecastio
import config
import config

from flask import Flask, request
from pprint import pprint
from pymessenger import Bot
from utils import wit_response
from random import randint
from funcs import getCups


app = Flask(__name__)
PAGE_ACCESS_TOKEN = "EAAFRuLyX57wBAIeN5HGCKldCUJZARWhRRIIuaQiPctC9n5OuovuESHO4iZAXtCkfD8rh9uq8ZAXdipNJzZAUJBsiuvzlF6EweShMrvWiZBByBCdjeSQ2aZCZAftTsUEuIcAfqB979xNZCBH7PdPmscsBdZAC6Yc2QxHqYSLfbpfuAjgZDZD"
bot = Bot(PAGE_ACCESS_TOKEN)
listOfGifs = ["https://media2.giphy.com/media/26n6MSDzWXSf98qK4/giphy.gif", "https://media1.giphy.com/media/rrXfsgLwkKyEU/giphy.gif", "http://www.ohmagif.com/wp-content/uploads/2014/07/funny-dog-drinking-water-from-hose.gif", "https://media.giphy.com/media/xTiTncVep2khPGhK1i/giphy.gif", "https://media.giphy.com/media/PAujV4AqViWCA/giphy.gif", "https://media.giphy.com/media/l3vR3EssQ5ALagr7y/giphy.gif"]
botId = "330171427455152"

@app.route('/', methods=['GET'])
def verify(): # verify webhook
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == "secure_token": #os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    log(data)
    stickerAttachment = None
    locationAttachment = None
    text = None

    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging in entry['messaging']:
                #save ids
                senderId = messaging['sender']['id']
                recipientId = messaging['recipient']['id']
                if messaging.get('message'):
                    if 'text' in messaging['message']:
                        text = messaging['message']['text']
                    else:
                        text = None
                    if 'attachments' in messaging['message']:
                        if 'coordinates' in messaging['message']['attachments'][0]['payload']:
                            locationAttachment = messaging['message']['attachments'][0]['payload']
                            stickerAttachment = None
                        elif 'sticker_id' in messaging['message']['attachments'][0]['payload']:
                            locationAttachment = None
                            stickerAttachment = messaging['message']['attachments'][0]['payload']
                    else:
                        attachment = None

                    #echo response
    response = None
    if text != None:
        entity, value, name = wit_response(text)
        #print "NAME APP: %s" %name
        if name == "water_calc" and botId != senderId:
            response = "I'll try to calculate how much water you need to drink, but first I need some informations from you. ^_^"
            bot.send_text_message(senderId, response)
            response = "Tell me, how old are you?"
            bot.send_text_message(senderId, response)
            print "WATER_CALC", config.kg, config.age
        elif name == "age_of_person" and botId != senderId:
            config.age = int(value)
            response = "Cool, thanks. I will remember now, you are %d" %config.age
            bot.send_text_message(senderId, response)
            response = "One more question, how much do you weight?"
            bot.send_text_message(senderId, response)
            print "AGE_OF_PERSON", config.kg, config.age
        elif name == "greetings" and botId != senderId:
            response = "Hi there, I am Aqua Bot your personal water drinking bot. How can I help you? "
            bot.send_text_message(senderId, response)
            print "GREETINGS", config.kg,  config.age
        elif name == "help" and botId != senderId:
            response = "I can remind you to drink water every day, I can calculate how much water do you need (based on your age, weigh and temperature in your city), but also I can give you some cool water facts! ^_^"
            bot.send_text_message(senderId, response)
            print "HELP", config.kg, config.age
        elif name == "weigth" and botId != senderId:
            config.kg = int(re.findall(r'\d+', value)[0])
            response = "Great, now I know even more about you. Just one more thing!"
            bot.send_text_message(senderId, response)
            response = "Can you send me your location to check temperature in your city? :)"
            bot.send_text_message(senderId, response)
            print "WEIGTH", config.kg, config.age
        elif name == "thanks" and botId != senderId:
            response = "You're welcome! <3"
            bot.send_text_message(senderId, response)
            print "THANKS", config.kg, config.age
        elif response == None and botId != senderId:
            response = "Sorry, I didn't understand you. :("
            bot.send_text_message(senderId, response)
        return "ok", 200
    else:
        if stickerAttachment != None:
            bot.send_image_url(senderId, listOfGifs[randint(0,len(listOfGifs))])
        elif locationAttachment != None:
            longi = locationAttachment['coordinates']['long']
            lati = locationAttachment['coordinates']['lat']
            s1, s2, s3 = getCups(lati, longi)
            bot.send_image_url(senderId, listOfGifs[randint(0,len(listOfGifs)-1)])
            bot.send_text_message(senderId, s1)
            bot.send_text_message(senderId, s2+s3)
        return "ok", 200

def log(message): #simple logging function
    pprint(message)
    sys.stdout.flush()

if __name__ == '__main__':
    app.run(debug=True, port = 80)
