import os
import sys
import json
import requests
import re
import forecastio
import config
import time
import redis
import fbApi
import schedule
import datetime
import threading

from flask import Flask, request
from pprint import pprint
from pymessenger import Bot
from utils import wit_response
from random import randint
from funcs import getCups
from flask_sqlalchemy import SQLAlchemy
from threading import Thread
from threading import Timer

app = Flask(__name__)
app.config['DEBUG'] = False
app.debug = False
app.use_reloader = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
bot = Bot(os.environ['BOT_ID'])
listOfGifs = ["https://media2.giphy.com/media/26n6MSDzWXSf98qK4/giphy.gif", "https://media1.giphy.com/media/rrXfsgLwkKyEU/giphy.gif", "http://www.ohmagif.com/wp-content/uploads/2014/07/funny-dog-drinking-water-from-hose.gif", "https://media.giphy.com/media/xTiTncVep2khPGhK1i/giphy.gif", "https://media.giphy.com/media/PAujV4AqViWCA/giphy.gif", "https://media.giphy.com/media/l3vR3EssQ5ALagr7y/giphy.gif", "https://media2.giphy.com/media/unFLKoAV3TkXe/giphy.gif"]
listOfReminder = ["https://media.giphy.com/media/Oa18RxR2OiU4o/giphy.gif", "https://media.giphy.com/media/nfnF2zVPRemXu/giphy.gif", "https://media.giphy.com/media/Bqn8Z7xdPCFy0/giphy.gif"]
botId = os.environ['BOT_FB_ID']
#r = redis.from_url(os.environ.get("REDIS_URL"))

# Create our database model
class User(db.Model):
    __tablename__ = "users"
    userID = db.Column(db.BigInteger, primary_key=True)
    messagesPerDay = db.Column(db.Integer, unique=False)
    def __init__(self, userID, messagesPerDay):
        self.userID = userID
        self.messagesPerDay = messagesPerDay
    def __repr__(self):
        return 'UID: %r get %r messages per day.' %(self.userID, self.messagesPerDay)

@app.route('/', methods=['GET'])
def verify(): # verify webhook
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200

@app.before_first_request
def dictInit():
    print 'startup: pid %d before request' % os.getpid()

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    #log(data)
    stickerAttachment = None
    locationAttachment = None
    text = None
    edgeCases = False
    answer = None
    if data['object'] == 'page':
        for entry in data['entry']:
            if entry.get('messaging'):
                for messaging in entry['messaging']:
                    #save ids
                    senderId = messaging['sender']['id']
                    recipientId = messaging['recipient']['id']
                    if messaging.get('message'):
                        edgeCases = False
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
                    else:
                        print "EDGE CASE"
                        edgeCases = True
            elif entry.get('standby'):
                for standby in entry['standby']:
                    senderId = standby['sender']['id']
                    recipientId = standby['recipient']['id']
                    answer = standby['postback']['title']


    #echo response
        if senderId!=botId and edgeCases==False and senderId not in config.dict:
            config.dict[senderId] = {}
            config.dict[senderId]['age'] = 0
            config.dict[senderId]['kg'] = 0
            config.dict[senderId]['insideCalc'] = 0
            config.dict[senderId]['dontUnderstand'] = 0
            #r.hmset("userDict", dict)
            print "DICT INITIALIZED"


        if edgeCases == False:
            #print "ceo dict", config.dict, "ID ", senderId
            if senderId in config.dict:
                print "sender id", config.dict[senderId], threading.current_thread(), os.getpid()

        if botId != senderId and edgeCases==False and answer==None:
            response = None
            if text != None:
                entity, value, name = wit_response(text)
                print "NAME", name
                #print "NAME APP: %s" %name
                if name == "water_calc" or answer:
                    response = "I'll try to calculate how much water you need to drink, but first I need some informations from you. ^_^"
                    bot.send_text_message(senderId, response)
                    config.dict[senderId]['insideCalc'] = 1
                    time.sleep(3)
                    response = "Tell me, how old are you?"
                    bot.send_text_message(senderId, response)
                    print "WATER_CALC", config.dict[senderId]['kg'], config.dict[senderId]['age']
                    return "ok", 200
                elif name == "age_of_person" and config.dict[senderId]['insideCalc']==1:
                    config.dict[senderId]['age'] = int(value)
                    response = "Cool, thanks. I will remember now, you are %d" %config.dict[senderId]['age']
                    bot.send_text_message(senderId, response)
                    time.sleep(2)
                    config.dict[senderId]['insideCalc'] = 1
                    response = "One more question, how much do you weight?"
                    bot.send_text_message(senderId, response)
                    print "AGE_OF_PERSON", config.dict[senderId]['kg'], config.dict[senderId]['age']
                elif name == "greetings":
                    response = "Hi there, I am Aqua Bot your personal water drinking bot. How can I help you? \xF0\x9F\x92\xA7"
                    button1 = fbApi.create_buttons("postback","Water calculator",payload="How much water should I drink?")
                    button2 = fbApi.create_buttons("postback","Water reminder",payload="Remind me to drink waret")
                    bot.send_button_message(senderId,response,[button1,button2])
                    #bot.send_text_message(senderId, response)
                    print "GREETINGS", config.dict[senderId]['kg'], config.dict[senderId]['age']
                elif name == "help":
                    response = "I can remind you to drink water every day, I can calculate how much water do you need (based on your age, weigh and temperature in your city), but also I can give you some cool water gifs (I exchange GIFs for stickers)! ^_^"
                    bot.send_text_message(senderId, response)
                    print "HELP", config.dict[senderId]['kg'], config.dict[senderId]['age']
                elif name == "weigth" and config.dict[senderId]['insideCalc']==1:
                    config.dict[senderId]['kg'] = int(re.findall(r'\d+', value)[0])
                    response = "Great, now I know even more about you. Just one more thing!"
                    bot.send_text_message(senderId, response)
                    time.sleep(3)
                    response = "Can you send me your location to check temperature in your city? :)"
                    bot.send_text_message(senderId, response)
                    print "WEIGTH", config.dict[senderId]['kg'], config.dict[senderId]['age']
                elif name == "thanks":
                    response = "You're welcome! <3"
                    bot.send_text_message(senderId, response)
                    print "THANKS", config.dict[senderId]['kg'], config.dict[senderId]['age']
                elif name == "cancel" and config.dict[senderId]['insideCalc']==1:
                    config.dict[senderId]['insideCalc'] = 0
                    bot.send_image_url(senderId, "https://media0.giphy.com/media/LyJ6KPlrFdKnK/giphy.gif")
                    bot.send_action(senderId,"typing_on")
                    time.sleep(3)
                    bot.send_action(senderId,"typing_off")
                    response = "Ok... Canceled"
                    bot.send_text_message(senderId, response)
                elif response == None:
                    response = "Sorry, I didn't understand you. :("
                    bot.send_text_message(senderId, response)
                    if config.dict[senderId]['dontUnderstand'] % 3 == 0:
                        time.sleep(2)
                        response = "If you dont know what I am capable for, type 'help'"
                        bot.send_text_message(senderId, response)
                    config.dict[senderId]['dontUnderstand'] += 1
                    print "SORRY", config.dict[senderId]['dontUnderstand']
                return "ok", 200
            else:
                if stickerAttachment != None:
                    bot.send_image_url(senderId, listOfGifs[randint(0,len(listOfGifs))])
                    return "ok", 200
                elif locationAttachment != None and config.dict[senderId]['insideCalc']==1:
                    bot.send_image_url(senderId, listOfGifs[randint(0,len(listOfGifs)-1)])
                    longi = locationAttachment['coordinates']['long']
                    lati = locationAttachment['coordinates']['lat']
                    s1, s2, s3 = getCups(lati, longi, config.dict[senderId]['age'], config.dict[senderId]['kg'])
                    time.sleep(3)
                    bot.send_text_message(senderId, s1)
                    time.sleep(2)
                    bot.send_text_message(senderId, s2+s3)
                    config.dict[senderId]['insideCalc'] = 0
                    time.sleep(3)
                    button1 = fbApi.create_buttons("postback","Yes",payload="x")
                    button2 = fbApi.create_buttons("postback","No",payload="y")
                    bot.send_button_message(senderId,"Do you want me to remind you to drink water?",[button1,button2])
                    return "ok", 200
        if answer != None:
            if answer=="Yes" or answer=="Water reminder":
                b1 = fbApi.create_buttons("postback","Once",payload="1")
                b2 = fbApi.create_buttons("postback","Twice",payload="2")
                b3 = fbApi.create_buttons("postback","Three times",payload="3")
                bot.send_button_message(senderId,"how many times a day I should remind you??",[b1,b2,b3])
            elif answer=="Water calculator":
                response = "I'll try to calculate how much water you need to drink, but first I need some informations from you. ^_^"
                bot.send_text_message(senderId, response)
                config.dict[senderId]['insideCalc'] = 1
                time.sleep(3)
                response = "Tell me, how old are you?"
                bot.send_text_message(senderId, response)
                print "WATER_CALC", config.dict[senderId]['kg'], config.dict[senderId]['age']
            elif answer=="No":
                bot.send_text_message(senderId, "Ok, maybe next time :/")
            elif answer=="Once":
                writeToDB(senderId, 1)
            elif answer=="Twice":
                writeToDB(senderId, 2)
            elif answer=="Three times":
                writeToDB(senderId, 3)
        return "ok", 200


def writeToDB(senderId, times):
    reg = User(senderId, times)
    x  = db.engine.execute("select count(*) from users u where \"userID\" = "+senderId)
    y = x.fetchall()[0][0]
    if y == 0:
        db.session.add(reg)
        db.session.commit()
        bot.send_text_message(senderId, "Ok, I will remind you! :)")
    else:
        db.engine.execute("UPDATE USERS SET \"messagesPerDay\" = "+str(times)+" where \"userID\" = "+senderId)
        bot.send_text_message(senderId, "Ok, I updated the period of reminding :)")

def send_button(recipient_id, text, buttons):
    bot.send_message(recipient_id, {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": text,
                    "buttons": buttons
                }
            }
        })

def log(message): #simple logging function
    pprint(message)
    sys.stdout.flush()

def reminder(period):
    if period == "morning":
        users = db.engine.execute("select \"userID\" from users")
        img = listOfReminder[0]
        res = "Good morning, "
    elif period == "noon":
        users = db.engine.execute("select \"userID\" from users where \"messagesPerDay\" between 2 and 3")
        img = listOfReminder[1]
        res = "Hey brother, "
    elif period == "evening":
        users = db.engine.execute("select \"userID\" from users where \"messagesPerDay\" = 3")
        img = listOfReminder[2]
        res = "Good evening, "
    for user in users:
        bot.send_image_url(user[0], img)
        bot.send_text_message(user[0], res+"it's time for some cold water \xF0\x9F\x98\x8B")

def pending():
    while True:
        schedule.run_pending()
        print "time: ", datetime.datetime.now(), threading.current_thread()
        time.sleep(2)

thread = Thread(target = pending, args = ())
thread.start()

def test():
    bot.send_text_message(1474780072615755, "it's time for some cold water \xF0\x9F\x98\x8B")

#-2 hours because of heroku time
schedule.every().day.at("7:05").do(reminder, period="morning")  #9
schedule.every().day.at("11:00").do(reminder, period="noon")    #13
schedule.every().day.at("17:00").do(reminder, period="evening") #19
schedule.every().day.at("10:13").do(reminder, period="evening") #19

#schedule.every().day.at("8:18").do(reminder, period=("evening")) #test


if __name__ == '__main__':
    app.run(debug=False, port = 80)
