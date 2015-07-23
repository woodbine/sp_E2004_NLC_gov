# -*- coding: utf-8 -*-
import os
import re
import requests
import scraperwiki
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup
from dateutil.parser import parse

# Set up variables
entity_id = 'E2004_NLC_gov'

url = "http://www.northlincs.gov.uk/your-council/about-your-council/policy-and-budgets/supplier-payments/"
errors = 0
# Set up functions
def validateFilename(filename):
    filenameregex = '^[a-zA-Z0-9]+_[a-zA-Z0-9]+_[a-zA-Z0-9]+_[0-9][0-9][0-9][0-9]_[0-9][0-9]$'
    dateregex = '[0-9][0-9][0-9][0-9]_[0-9][0-9]'
    validName = (re.search(filenameregex, filename) != None)
    found = re.search(dateregex, filename)
    if not found:
        return False
    date = found.group(0)
    year, month = int(date[:4]), int(date[5:7])
    now = datetime.now()
    validYear = (2000 <= year <= now.year)
    validMonth = (1 <= month <= 12)
    if all([validName, validYear, validMonth]):
        return True
def validateURL(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=20)
        count = 1
        while r.status_code == 500 and count < 4:
            print ("Attempt {0} - Status code: {1}. Retrying.".format(count, r.status_code))
            count += 1
            r = requests.get(url, allow_redirects=True, timeout=20)
        sourceFilename = r.headers.get('Content-Disposition')

        if sourceFilename:
            ext = os.path.splitext(sourceFilename)[1].replace('"', '').replace(';', '').replace(' ', '')
        else:
            ext = os.path.splitext(url)[1]
        validURL = r.status_code == 200
        validFiletype = ext in ['.csv', '.xls', '.xlsx']
        return validURL, validFiletype
    except:
        raise
def convert_mth_strings ( mth_string ):

    month_numbers = {'JAN': '01', 'FEB': '02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09','OCT':'10','NOV':'11','DEC':'12' }
    #loop through the months in our dictionary
    for k, v in month_numbers.items():
#then replace the word with the number

        mth_string = mth_string.replace(k, v)
    return mth_string
# pull down the content from the webpage
html = urllib2.urlopen(url)
soup = BeautifulSoup(html)
# find all entries with the required class
try:
    next_pages = soup.find('span', 'pagination-next')
except: pass
try:
    next_links = next_pages.find('a')['href']
except: pass
while next_links:
    block = soup.find('table', 'oDataGrid')
    links = block.findAll('a', href = True)
    for link in links:
        url_link = 'http://www.northlincs.gov.uk/your-council/about-your-council/policy-and-budgets/supplier-payments/' + link['href']
        if 'id16' in url_link:
            html_csv = urllib2.urlopen(url_link)
            sp_link = BeautifulSoup(html_csv)
            try:
                csv_link = sp_link.find('div', 'oAssetAttachmentDetailInner').a['href']
            except: break
            if '.csv' in csv_link:
                try:
                    url_link = 'http://www.northlincs.gov.uk' + csv_link
                    csvFiles = sp_link.find('div', 'oAssetAttachmentDetailInner').a['title']
                    csvfile = csvFiles.replace('_', ' ').replace('-', ' ').replace('MASTER', ' ').replace('February.csv', 'February 2015.csv').replace('DECEMEBER.csv', 'December 2014.csv ')
                    csvM = csvfile.split(' ')
                    csvMth = csvM[4][:3]
                    csvYr = csvM[5][:4]
                    if len(csvM) == 10:
                        csvMth = csvM[6][:3]
                        csvYr = csvM[7][:4]
                    if len(csvM) == 9 and csvM[4] == '':
                        csvMth = csvM[5][:3]
                        csvYr = csvM[6][:4]
                    csvMth = convert_mth_strings(csvMth.upper())
                    filename = entity_id + "_" + csvYr + "_" + csvMth
                    todays_date = str(datetime.now())
                    file_url = url_link.strip()
                    validFilename = validateFilename(filename)
                    validURL, validFiletype = validateURL(file_url)
                    if not validFilename:
                        print filename, "*Error: Invalid filename*"
                        print file_url
                        errors += 1
                        continue
                    if not validURL:
                        print filename, "*Error: Invalid URL*"
                        print file_url
                        errors += 1
                        continue
                    if not validFiletype:
                        print filename, "*Error: Invalid filetype*"
                        print file_url
                        errors += 1
                        continue
                    scraperwiki.sqlite.save(unique_keys=['l'], data={"l": file_url, "f": filename, "d": todays_date })
                    print filename

                except: pass
    try:
        next_pages = soup.find('span', 'pagination-next')
    except: break
    try:
        next_links = next_pages.find('a')['href']
    except: break
    html_next = urllib2.urlopen('http://www.northlincs.gov.uk/your-council/about-your-council/policy-and-budgets/supplier-payments' + next_links)
    soup = BeautifulSoup(html_next)




if errors > 0:
    raise Exception("%d errors occurred during scrape." % errors)