import config
import requests
from xml.etree import ElementTree as ET

parameters = {
    "fromDate": "2019-11-01",
    "toDate": "2019-11-30"
}

headers = {
    'ApiKey': config.apikey
}

namespaces = {'ns0': 'http://www.orienteering.org/datastandard/3.0'}

# Get a list of eventIds for all events in the date range

fd = open("competitors.csv","w")

print("Getting list of events")
response = requests.get(config.baseUrl + "/events", params=parameters, headers=headers)
if response.status_code != 200:
    print("Unable to access event list using API, error " + str(response.status_code))
    exit(1)
    
tree = ET.ElementTree(ET.fromstring(response.content))
root = tree.getroot()
events = root.getchildren()
eventList=[]
for event in events:
    eventId = event.find('EventId')
    if eventId != None:
        eventList.append(eventId.text)
        
print("Found %d events" % len(eventList))


# Get all competitors and their clubs at all events in the list
for eventId in eventList:
    print("Processing event " + eventId)
    startlistParams = {}
    startlistParams['EventId'] = eventId
    response = requests.get(config.baseUrl + "/starts/event/iofxml", params=startlistParams, headers=headers)

    if response.status_code != 200:
        print("Unable to access event list using API, error " + str(response.status_code))
        exit(1)
        
    tree = ET.ElementTree(ET.fromstring(response.content))
    root = tree.getroot()
    classes = tree.findall('ns0:ClassStart', namespaces)

    for oclass in classes:
        people = oclass.findall('ns0:PersonStart', namespaces)
        if people == None:
            print("Didn't find any PersonStart")  
        for person in people:
            personObj = person.find('ns0:Person', namespaces)
            if personObj == None:
                print("Didn't find personObj")
                continue
            name = personObj.find('ns0:Name', namespaces)
            if name == None:
                print("Didn't find Name")
                continue
            fname = name.find('ns0:Family', namespaces)
            given = name.find('ns0:Given', namespaces)
            if (fname == None or fname.text == None) and (given == None or given.text == None):
                print("Didn't find Family or Given")
                continue
                
            clubText = "Missing"
            club = person.find('ns0:Organisation', namespaces)
            if club != None: 
                clubName = club.find('ns0:Name', namespaces)
                if clubName != None and clubName.text != None:
                    clubText = clubName.text

            nameText = ""
            if fname == None or fname.text == None:
                nameText = given.text
            elif given == None or given.text == None:
                nameText = fname.text
            else:
                nameText = given.text + " " + fname.text
                
#            print(nameText + "," + clubText)
            fd.write(clubText + "," + nameText + "\n")
            
 
