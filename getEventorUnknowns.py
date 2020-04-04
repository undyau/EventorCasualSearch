#
# Script to extract participant information from Eventor
# 
# References:
#   https://eventor.orientering.se/Documents/Guide_Eventor_-_Get_data_via_API.pdf
#   https://eventor.orientering.se/api/documentation

import config
import requests
from xml.etree import ElementTree as ET

# Alter these to suit, or convert into run-time arguments
parameters = {
    "fromDate": "2019-01-01",
    "toDate": "2019-12-31"
}

# This will contain the SECRET API key specific to the club/association
headers = {
    'ApiKey': config.apikey   
}

# We need this dictionary of name=spaces to help when we parse the IOF 3.0 format XML for startlists
namespaces = {'ns0': 'http://www.orienteering.org/datastandard/3.0'}



output_file = open("competitors.csv","w")   # Where we will save what we found

#
# Get a list of eventIds for all events in the date range using Eventor API
# The result is in XML format, need to parse that response to get the EventIds
#
print("Getting list of events")
response = requests.get(config.baseUrl + "/events", params=parameters, headers=headers)
if response.status_code != 200:
    print("Unable to access event list using API, error " + str(response.status_code))
    exit(1)
    
tree = ET.ElementTree(ET.fromstring(response.content))
# tree.write("events.xml") # Uncomment this line to get a sample events.xml, can be read with Internet Explorer
root = tree.getroot()
events = root.getchildren()
eventList=[]
for event in events:
    eventId = event.find('EventId')
    if eventId != None:
        eventList.append(eventId.text)
        
print("Found %d events" % len(eventList))


#
# Get a competitor information for all the events we found above
# The result is in XML format, need to parse that response to get the parts we need
#
for eventId in eventList:
    print("Processing event " + eventId)
    startlistParams = {}
    startlistParams['EventId'] = eventId
    response = requests.get(config.baseUrl + "/starts/event/iofxml", params=startlistParams, headers=headers)

    if response.status_code != 200:
        print("Unable to access event list using API, error " + str(response.status_code))
        exit(1)
        
    tree = ET.ElementTree(ET.fromstring(response.content))
    #tree.write("startlist" + eventId + ".xml") # Uncomment this line to get a sample startlist xml, can be read with Internet Explorer
    root = tree.getroot()
    
    # Get the organising club name (no error checking, Eventor sets this data, so minimal room for human error)
    event = tree.find('ns0:Event', namespaces)
    organiser = event.find('ns0:Organiser', namespaces)
    organiserName = organiser.find('ns0:Name', namespaces) 
    organiserNameText = organiserName.text
     
    #process class by class    
    classes = tree.findall('ns0:ClassStart', namespaces)
    for oclass in classes:
        people = oclass.findall('ns0:PersonStart', namespaces)
        if people == None:
            print("Didn't find any PersonStart")  
            
        for person in people:
        
            # If this person is already in an Eventor club as detailed in the 
            # startlist, then skip processing them, not of interest
            clubText = "Missing"
            club = person.find('ns0:Organisation', namespaces)
            if club != None:
                clubId = club.find('ns0:Id', namespaces)
                if clubId != None and clubId.text != None:
                    continue
            
            # meh - while we have the club, lets try to find the name
                clubName = club.find('ns0:Name', namespaces)
                if clubName != None and clubName.text != None:
                    clubText = clubName.text
                    
            # Dig out whatver parts of the competitor name exist            
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
            
            # If we can't find any bits of name, just ignore and carry on
            if (fname == None or fname.text == None) and (given == None or given.text == None):
                continue

            nameText = ""
            if fname == None or fname.text == None:
                nameText = given.text
            elif given == None or given.text == None:
                nameText = fname.text
            else:
                nameText = given.text + " " + fname.text
                
            # Write single line of information to the output file, skip people with funky characters
            try:
                output_file.write(organiserNameText + "," + clubText + "," + nameText + "\n")
            except UnicodeEncodeError:
                continue
            
 
