#
#  This code illustrates an approach in which article metadata is obtained from a combination of an OCRed table of contents
#  and BHL page level metadata. In order for this approach to work, the BHL page level metadata must be complete and correct.
#  The following metadata fields are derived from the OCRed table of contents:
#    - title
#    - author
#    - starting page number
#  The following article metadata fields are derived from the BHL page level metadata:
#    - volume
#    - issue
#    - year
#    - BHL starting page id
#  Initially, the code made an educated guessed the ending page and page id. The results were poor and the code was removed.
#  Successful parsing of the table of contents is dependent on the exact format of the table of contents. This code was written for the early issues of Papilio.
#  For example, see https://www.biodiversitylibrary.org/pagetext/10373385. General format of the table of contents in this publication is:
#   <surname>,<first name or initials>.
#   <title 1> <starting page number 1>
#   <title 2> <starting page number 2>
#
#  Import needed libraries
#
import re
import csv
import urllib.parse
import urllib.request
import json
from config import BHL_key

BHL_pages = {}       # Build dictionary. Key is the page number.  Other fields include item id, volume, issue,
                              # year and page id. All fields of these fields come from the BHL page level metadata.

art_list = []   # List of metadata fields derived from the TOC. This includes author, title and starting page number.

def get_input ():
    #
    #  Prompt user for the BHL item id
    #
    itemid = input('Enter BHL item id: ')
    if None == re.fullmatch(r'\d+',itemid):
        print('You must enter the item id in nnnnnn format')
        exit()
    return (itemid)

def read_pages_BHL(itemid):
    #
    # Gather BHL page level metadata for this item and build a dictionary called BHL_pages. Dictionary key is the page number.
    #
    service_url = 'https://www.biodiversitylibrary.org/api3?'
    
    #
    # Prepare the search command and then call the BHL API
    url=service_url + urllib.parse.urlencode({'op':'GetItemMetadata','format':'json','id':itemid,'pages':'t','apikey':BHL_key})
    #print(url)
    uh=urllib.request.urlopen(url)
    mydata=uh.read().decode('utf-8')
    resp=json.loads(mydata)
    #print(resp)
    if 'Status' not in resp or resp['Status'] != 'ok':
        print('Unable to read BHL page level metadata for item.')
        exit()

    for page in resp['Result'][0]['Pages']:   # Process each BHL page returned. Collect page level metadata for each page.
        pageid = page['PageID'] 
        itemid = page['ItemID']
        vol = page['Volume']
        issue = page['Issue']
        year = page['Year']
        number = ''
        for pagenum in page['PageNumbers']:
            if pagenum['Prefix'] == 'Page':
               number = pagenum['Number']
            if number:
                BHL_pages[number] = {'itemid' : itemid,  'year': year, 'vol': vol, 'issue': issue, 'pageid': pageid}
               
    
def wrt_md():
    #
    #  Write metadata to the output file. The output file is a tsv file in the format expected by the BHL Create Segments function.
    #

    aitemid = avolume = aissue = aauthors = atitle = adate = aspage = aepage = aspageid = aepageid = ''  # Initialize metadata variables to the empty string
    for article in art_list:  # Process each article. art_list is derived from the OCRed table of contents.
        aspage = article['spage']
        try:
            aitemid=BHL_pages[aspage]['itemid']   # Use dictionary built from BHL page level metadata to obtain BHL item id. 
        except:
            pass

        try:
            avolume= BHL_pages[aspage]['vol']   # Use dictionary built from BHL page level metadata to obtain volume. 
        except:
            pass

        try:
            aissue = BHL_pages[aspage]['issue']  # Use dictionary built from BHL page level metadata to obtain issue. 
        except:
            pass
            
        atitle = article['title'].replace('\n',' ')   # Replace carriage return with space if present.
        adate = BHL_pages[aspage]['year']  # Use dictionary built from BHL page level metadata to obtain year.. 
    
        aauthors = article['author']  # Author was obtained from the OCRed table of contents.
        aspageid = BHL_pages[aspage]['pageid']  # Use dictionary built from BHL page level metadata to obtain BHL starting page id.

        writer.writerow((atitle,'',aitemid,avolume,aissue,'',adate,'',aauthors,aspage,aepage,aspageid,aepageid,'',''))              # Write a row to the tsv file
  
#
#  Main routine
#            

itemid = get_input()                                        # Prompt for input
read_pages_BHL(itemid)                                 # Get all BHL page level metadata for the item id. Save in BHL_pages.

#print(BHL_pages)
output_file = open('BHL_art_md.tsv','w+', newline='', encoding='utf-8')
writer = csv.writer(output_file, dialect='excel-tab')
#
# Write column headings to the tsv file
#
writer.writerow(('Title','Translated Title','Item ID','Volume','Issue','Series','Date','Language','Authors','Start Page','End Page','Start Page BHL ID','End Page BHL ID','Additional Page IDs','Article DOI'))
crnt_title = crnt_page = crnt_auth = ''
fhand = open('TOC_OCR.txt')   # Open the file that contains the BHL OCR text for the table of contents.

for line in fhand:       # Process every line in the table of contents.
    if line.isspace():   # Empty line? 
        continue          # Ignore blank lines
    if line.rstrip().endswith('.'):  # Author name found?  In this table of contents, all author names end with a period. Nothing follows the period on the line.
        crnt_auth = line.strip()
        if crnt_auth.lower().find('page') == 0:   # Don't mistake the word page for an author name
            crnt_auth = ''
        else:
            end_surnm = crnt_auth.find(',')
            crnt_auth = crnt_auth[0].upper()+crnt_auth[1:end_surnm].lower()+crnt_auth[end_surnm:] 
            if crnt_auth[-1] == '.' and crnt_auth[-3] != ' ':  # Remove a period that follows a given name. Retain a period that follows an initial.
                crnt_auth = crnt_auth.rstrip('.')
        continue
    match = re.search(r'(\d+)\s*$',line) # Page number appears at the end of a line. Title precedes page number.
    if match:
        crnt_page = match.group(1)
        crnt_title = crnt_title+line[:match.start(1)]
        art_list.append({'title':crnt_title,'author':crnt_auth,'spage':crnt_page})  # Title, author and start page for an article found. Save values.
        crnt_title = '' 
    else:                                      # Found a partial title
        crnt_title = crnt_title+line.strip()+' '

#print(art_list)
wrt_md()   # Write all article metadata to a tsv file. The file is formatted as expected by the BHL Create Segments function.
output_file.close() 


