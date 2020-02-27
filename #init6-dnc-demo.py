#!/usr/bin/env python3

# modules to import include API modules for Meraki and Webex Teams
import time
from meraki import DashboardAPI
from webexteamssdk import WebexTeamsAPI

# script installer should ensure MERAKI_DASHBOARD_API_KEY environment variable set/exported
#  then we can spark up an instance of the API for query
dashboard=DashboardAPI()

# script installer should ensure WEBEX_TEAMS_ACCESS_TOKEN environment variable set/exported
#  then spark up an instance of the API for query
webexTeamsRoom=WebexTeamsAPI()

# assign global variables, pre-captured from the API using Postman and ready for the API calls 
myNetwork='L_619244948763443757'
switchSerial='Q2HP-2R6D-DE2Z'
poePort=8
myWebexRoom='Y2lzY29zcGFyazovL3VzL1JPT00vNmUwYTQ2MzAtNTAzNC0xMWVhLTk2OTgtODMwZmVjZGNhOGM4'

# assign globals relating to the endpoint to be used for proximity check
operatorClientName='iPhone'

# first time run status
assocStatus=''

# infinite loop - determine operator location and act accordingly
while True:

    # fetch AP associate and disassociate events for operator's wireless client
    associateEvents=dashboard.events.getNetworkEvents(myNetwork,productType="wireless",clientName=operatorClientName,includedEventTypes="association")
    lastAssocTime=associateEvents['events'][0]['occurredAt']

    disassociateEvents=dashboard.events.getNetworkEvents(myNetwork,productType="wireless",clientName=operatorClientName,includedEventTypes="disassociation")
    lastDisAssocTime=disassociateEvents['events'][0]['occurredAt']

    print ('Last seen joining the network at ',lastAssocTime)
    
    # catch last iteration association status
    prevAssocStatus=assocStatus

    # if the most recent status is to disassociate then set status variable
    if lastDisAssocTime > lastAssocTime:
        assocStatus='DISASSOCIATED'

        # and if this is different from the previous status, then trigger a config change in the Meraki dashboard for the PoE switch port, and Webex Teams messages
        if prevAssocStatus != assocStatus:
            print ('***CHANGE***')
            webexTeamsRoom.messages.create(roomId=myWebexRoom,text=time.ctime()+' - Operator is leaving the vicinity of the machine')
            portStatus=dashboard.switch_ports.updateDeviceSwitchPort(switchSerial,str(poePort),name="Light Off",poeEnabled=False)
            webexTeamsRoom.messages.create(roomId=myWebexRoom,text=time.ctime()+' - Machine shutdown sequence activated')

    # otherwise if the most recent status is to associate then set status accordingly
    else:
        assocStatus='ASSOCIATED'

        # and if this indicates a change in location, then trigger the config change in the Meraki dashboard and notify the Webex Teams room
        if prevAssocStatus != assocStatus:
            print ('***CHANGE***')
            webexTeamsRoom.messages.create(roomId=myWebexRoom,text=time.ctime()+' - Operator is returning to the vicinity of the machine')
            portStatus=dashboard.switch_ports.updateDeviceSwitchPort(switchSerial,str(poePort),name="Light On",poeEnabled=True)
            webexTeamsRoom.messages.create(roomId=myWebexRoom,text=time.ctime()+' - Machine startup sequence activated')

    print ('Currently ',assocStatus)

    # wait 5 seconds before polling location status again
    time.sleep(5)
    