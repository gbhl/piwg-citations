#
# This code, written in python 3, uses the Crossref REST API and the crossrefapi python library. Both are well documented
# in the readme files of their GitHub repos. You will need to install the crossrefapi library prior to running this program.
# The code has been tested from the Mac command line. The code does the following:
#
# - Prompts the user for an ISSN, starting year, ending year and prefix for the output tsv file.
# - Pulls all article metadata from Crossref for the specified journal and date range
# - Formats the metadata into a tsv file that conforms to the input requirements of the BHL Import Segments function
# 
# Please note that you will need to acquire a BHL API key and set the BHL_key variable to that value in file config.py
# The procedure for getting a key is described at https://about.biodiversitylibrary.org/tools-and-services/developer-and-data-tools/
# Please note that the output tsv file may require substantial editing before being used to define articles in BHL.
# Please verify that the BHL title record includes an ISSN identifier before running this code. The code can find BHL item id when the volume 
# enumeration value in the item record follows current standards. It can not determine item ids when the enumeration data differs significantly
# from current standards. The code will optionally attempt to match articles in Crossref with existing articles in BHL using openURL. Note that this
# is a slow process.
#
#  Import needed libraries
#
from crossref.restful import Works
from crossref.restful import Journals
import re
import csv
import urllib.parse
import urllib.request
import json
from config import BHL_key

BHL_items = {}       # Build dictionary. Key is volume number.  The other field is the item id.


def get_input ():
    #
    #  Prompt user for required input
    #
    issn = input('Enter ISSN in xxxx-xxxx format: ')                   # Get ISSN
    if None == re.fullmatch(r'^[0-9]{4}-[0-9]{3}[0-9xX]$',issn):  
        print('You must enter the ISSN in xxxx-xxxx format')
        exit()
    
    start_yr = input('Enter starting year in YYYY format: ')           # Get starting year for metadata gathering
    if None == re.fullmatch(r'\d{4}',start_yr):
        print('You must enter the starting year in YYYY format')
        exit()
    
    end_yr = input('Enter ending year in YYYY format: ')               # Get ending year for metadata gathering
    if None == re.fullmatch(r'\d{4}',end_yr):
        print('You must enter the ending year in YYYY format')
        exit()

    oprefix = input('Enter a short prefix for the output file: ')      # Get short prefix for output file. Start and end year are appended.
    if None == re.fullmatch(r'\w+',oprefix):
        print('Enter a short prefix for the output file name. (The date range will be appended to this prefix.')
        exit()
        
    chk_existing = input('Check for existing articles in BHL? (y/n: ')  # Attempt to match Crossref article metadata to existing BHL articles? It's slow.
    if None == re.fullmatch(r'[yYnN]',chk_existing):
        print('Enter y to check for existing articles in BHL and n to decline checking.')
        exit()      
        
    return issn, start_yr, end_yr, oprefix, chk_existing

def auth_collect(auth_in):
    #
    #  Reformat author names. Output format is surname, given name with multiple authors separated by semicolons.
    #
    auth_out = ''
    for author in auth_in:
        auth_out += author['family'].strip()+', '
        auth_out += author['given'].strip()+';'
    return auth_out.rstrip(';')
    
def read_items_BHL():
    #
    # Gather BHL item ids and build dictionary. Key is the volume number. Other field is BHL item id. Note that the code is successful only when
    # volume enumeration from the item record follows current standards. The presence of series in the enumeration data is not handled.
    #
    service_url = 'https://www.biodiversitylibrary.org/api3?'
    
    #
    # Prepare the search command and then call the API. If problems occur, one or more BHL item ids will be missing from the output spreadsheet.
    url=service_url + urllib.parse.urlencode({'op':'GetTitleMetadata','format':'json','id':issn,'idtype':'issn','items':'t','apikey':BHL_key})
    #print(url)
    uh=urllib.request.urlopen(url)
    mydata=uh.read().decode('utf-8')
    resp=json.loads(mydata)

    if 'Status' not in resp or resp['Status'] != 'ok' or len(resp['Result']) == 0:   # Were items successfully read from the BHL database?
        return
    for item in resp['Result'][0]['Items']:   # Process each BHL item returned
        itemID = item['ItemID']
        enum = item['Volume']                # Locate enumeration string
        mtch= re.search('v\.([\d\-\s]+)[=\(]',enum)    # Locate the  volume number(s)
        if mtch == None:
            continue
        try:
            volumes = mtch.group(1).strip()
            mtch = re.fullmatch('\d+',volumes)          # Single volume number?
            if mtch != None:
                BHL_items[mtch.group(0)] = itemID       # enumeration string contains a single volume number
            else:
                mtch = re.fullmatch('(\d+)-(\d+)',volumes) # Volume number range?
                if None != mtch:
                    strtvol = int(mtch.group(1))          # Convert start and end of range to integer format in order to iterate over range.
                    endvol = int(mtch.group(2))
                    for vol in range(strtvol,endvol+1):   # Process each volume number in volume number range
                        BHL_items[str(vol)] = itemID
        except:
            pass
        
    
def wrt_art(amd):
    #
    #  Write metadata for one article to the output file
    #
    #print(amd)
    aitemid = avolume = aissue = aauthors = atitle = adate = adoi = aspage = aepage = ''  # Initialize metadata variables to the empty string
    try:
        aitemid=BHL_items[amd['volume']]   # Use dictionary built from BHL contents to obtain BHL item id. Volume number is the key for dictionary lookup.
    except:
       pass
    try:
        aissue = amd['issue']
    except:
        pass
    try:
        avolume= amd['volume']
    except:
       pass
    try:
        adate = str(amd['published-print']['date-parts'][0][0]) # Get year 
        for date_part in amd['published-print']['date-parts'][0][1:]:   # Get month and day. Left pad with zero to form 2-digit month and day.
           adate += f'-{date_part:02d}'
    except:
        pass
    try:
        adoi = amd['DOI']
    except:
        pass
    try:
        aspage = amd['page'].split('-')[0].strip()
        aepage = amd['page'].split('-')[-1].strip()
    except:
        pass
    try:
        atitle = (amd['title'][0]).replace('\n',' ')   # Replace carriage return with space if present.
    except:
       pass
    #
    # Reformat author names. Output is surname, given name with multiple authors separated by semicolons.
    #
    try:
        #print(amd['author'])
        aauthors = auth_collect(amd['author'])     
    except:
        pass
    apart = ''
    if chk_existing == 'y' or chk_existing == 'Y':   # Did user choose to match Crossref articles to existing BHL articles?
        apart = defined_BHL(atitle,aspage,avolume)
    writer.writerow((atitle,'',aitemid,avolume,aissue,'',adate,'',aauthors,aspage,aepage,'','','',adoi,apart))              # Write a row to the tsv file

def defined_BHL(title,spage,vol):
    #
    # Use openURL to search for matching, pre-existing article in BHL. If found, save part ID in output spreadsheet.
    #
    service_url = 'https://www.biodiversitylibrary.org/openurl?'
    url=service_url + urllib.parse.urlencode({'title':title,'format':'json'})
    #print(url)
    uh=urllib.request.urlopen(url)
    mydata=uh.read().decode('utf-8')
    resp=json.loads(mydata)
    part_id = ''
    try:
        #print(resp)
        for citation in resp['citations']:
            if citation['Genre'] == 'Article':
                if (citation['Volume'] == vol) & (spage == citation['SPage']):
                    #print('part url is: ',citation['PartUrl'])
                    part_id = citation['PartUrl'].split('/')[-1]  # Separate part id from part URL
    except:
        pass  
    return part_id  

#
#  Main routine
#            

issn, start_yr, end_yr, prefix, chk_existing = get_input()             # Prompt for input
#print(issn, start_yr, end_yr, prefix, chk_existing)
read_items_BHL()             # Get BHL item ids for all issues for the selected ISSN
                             
#print('BHL_items built: ',BHL_items)

output_file = open(prefix+'_'+start_yr+'_'+end_yr+'.tsv','w+', newline='', encoding='utf-8')  # Construct filename and open output tsv file
writer = csv.writer(output_file, dialect='excel-tab')
#
# Write column headings to the tsv file
#
writer.writerow(('Title','Translated Title','Item ID','Volume','Issue','Series','Date','Language','Authors','Start Page','End Page','Start Page BHL ID','End Page BHL ID','Additional Page IDs','Article DOI','Part ID'))

works = Works()          # Get ready to use crossrefapi python library

# A few sample commands
#myresults=works.filter(issn='0002-9122', from_pub_date='1922', until_pub_date='1923').sort('issued').select('title', 'DOI', 'volume','issue','page','author','published-print','type')
#myresults=works.filter(issn=issn, until_pub_date=start_yr,from_pub_date=end_yr).count()
#
# Add input parms to the command. Perhaps not the best way to do this.
#
bldcmd = "myresults=works.filter(issn='"+issn+"', from_pub_date='"+start_yr+"', until_pub_date='"+end_yr+"').sort('issued').select('title', 'DOI', 'volume','issue','page','author','published-print','type')"
exec(bldcmd)    # Now that input parms have been added, run the command

for crnt_item in myresults:    # Process each citation returned by Crossref
    if crnt_item['type'] == 'journal-article':
        wrt_art(crnt_item)     # Write article metadata for the current citation to the output file
output_file.close()            # Close the output file

