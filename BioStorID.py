#
# This program pulls all BHL part ids and the corresponding BioStor ids from BHL.  It formats this information as a tsv file with two
#  columns.  The file will be uploaded to a tab in Google Sheets and then the vlookup function will be used to add BioStor ids
#  to another tab within the same spreadsheet.
#
#  The user is prompted to enter the BHL title id.
#  Sample function call in Google Sheets
#  =VLOOKUP(A381,BioStor!A:B,2,false)
#
#  Load needed libraries
#
import urllib.parse
import urllib.request
import json
import re
import csv
from config import BHL_key   # Use the BHL API key assigned to the person running the program
#
# Global variables
#    
service_url = 'https://www.biodiversitylibrary.org/api3?'
#
# Function definition
#
def get_input ():
    #
    #  Prompt user for the BHL title id
    #
    titleid = input('Enter BHL title id: ')
    if None == re.fullmatch(r'\d+',titleid):
        print('You must enter the title id in nnnnnn format')
        exit()
    return (titleid)

def opn_output():
    #
    #  Open the output tsv file and write column headings to it
    #
    global fileh
    fileh = open('BioStor.tsv','w+',newline='', encoding='utf-8')
    writer = csv.writer(fileh, dialect='excel-tab')
    writer.writerow(('BHL part id','BioStor id'))
    return (writer)
#
#
#     Main Routine
#
titleid = get_input()           # Prompt the user for the title id 
tsvfile = opn_output()     # Open the output tsv file and write column headings to it

#  Get all items for the selected title
#
url = service_url + urllib.parse.urlencode({'op':'GetTitleMetadata', 'id': titleid,'items':'t','format': 'json','apikey':BHL_key})
uh=urllib.request.urlopen(url)
#print(url)
mydata=uh.read().decode('utf-8')
resp=json.loads(mydata)
if 'Status' not in resp or resp['Status'] != 'ok':# Successful API invocation?
    print('==== Failure to retrieve items ====')         # Exit if unsuccessful
    print(mydata)
    exit()

for item in resp['Result'][0]['Items']:                       # Process each item for this title
    crnt_item = item['ItemID']
    url = service_url + urllib.parse.urlencode({'op':'GetItemMetadata','id':crnt_item,'parts':'t','format':'json','apikey':BHL_key})
    #print(url)
    uh = urllib.request.urlopen(url)
    mydata=uh.read().decode('utf-8')
    resp2 = json.loads(mydata)
    #print(resp2)
    if 'Status' not in resp2 or resp2['Status'] != 'ok':
        print('==== Failure to retrieve  parts ====')
        print(mydata)
        exit()
    if 'Parts' not in resp2['Result'][0].keys():   
        continue
    for part in resp2['Result'][0]['Parts']:                  # Process each part for this item
        url = service_url + urllib.parse.urlencode({'op':'GetPartMetadata','id':part['PartID'],'format':'json','apikey':BHL_key})
        #print(url)
        uh = urllib.request.urlopen(url)
        mydata8 = uh.read().decode('utf-8')
        resp8 = json.loads(mydata8)
        partID = resp8['Result'][0]['PartID']
        for identifier in resp8['Result'][0]['Identifiers']:  # Check each identifier looking for the BioStor identifier
            if identifier['IdentifierName'] =='BioStor':
                BioStorID=identifier['IdentifierValue']
            else:
                BioStorID=''
        print(partID)
        tsvfile.writerow((partID,BioStorID))

fileh.close()   # Close the output tsv file
    



