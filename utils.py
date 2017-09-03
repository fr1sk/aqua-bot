from wit import Wit
from pprint import pprint
import re

accessToken = "P5AVH7DHOLYCOTO6MZ2KMD7YKZHVYAVZ"
client = Wit(accessToken)

def wit_response(msg):
    resp = client.message(msg)
    entity = None
    value = None
    name = None
    maxConfidenceEntity = None

    try:
        x = 0
        for singleEntity in list(resp['entities']):
            if maxConfidenceEntity == None:
                maxConfidenceEntity = resp['entities'][singleEntity]
                name = singleEntity
            else:
                if resp['entities'][singleEntity][0]['confidence'] > maxConfidenceEntity[0]['confidence']:
                    maxConfidenceEntity = resp['entities'][singleEntity]
                    name = singleEntity
            #print name
        entity = list(resp['entities'][singleEntity])
        value = resp['entities'][singleEntity][0]['value']
    except:
        pass

    #print "NAME UTILS: %s" %name
    #print "age: %s" %type(int(value))
    #print int(re.findall(r'\d+', value)[0])
    return(entity, value, name)

print wit_response("I have 95 kg")
#wit_response("22 years old")
