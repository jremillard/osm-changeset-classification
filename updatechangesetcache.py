import csv
import urllib.request
import xml.etree.ElementTree as ET
import osmcsclassify
import time

classes = [] 
changeSets = []
with open('data/changesets.csv', newline='',encoding='utf-8') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')

    for row in spamreader:
        if len(classes) == 0:
            classes = row[1:]
        else:
            cs = osmcsclassify.ChangeSet.ChangeSet(row[0])

            changeSets.append( cs)

download_limit = 10000
downloads = 0
for cs in changeSets:
    if ( cs.cached() == False):
        
        if ( downloads < download_limit ):
            print("downloading {}".format(cs.id))
            cs.download()
            cs.save()
            downloads += 1

            if ( downloads % 5) == 0 :
                time.sleep(2)
    else:
        cs.read()

    #if ( cs.cached() ):
    #    print(cs.id)
    #    print(cs.textDump())


