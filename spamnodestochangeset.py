import csv
import urllib.request
import xml.etree.ElementTree as ET
import pprint
import time

with open("trainingdata/spamnodes.csv") as f:
    nodes = f.read().splitlines()
 

changesetDb = []
with open('trainingdata/changesets.csv', newline='',encoding='utf-8') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    next(spamreader) # skip header.
    for row in spamreader:
        changesetDb.append(row)

osmApiBase =  "https://api.openstreetmap.org"
nodeCount = 0
for node in nodes:
    url = "{}/api/0.6/node/{}/history".format(osmApiBase,node)
    try:
        with urllib.request.urlopen(url) as response:
            bodyStr = response.read()
            #print(bodyStr)
            body = ET.fromstring(bodyStr)

            #for revision in body:
            #    print(revision.tag, revision.attrib)
            #    for tags in revision:
            #        print("  {} {}".format(tags.tag, tags.attrib))
            
            #exit(0)
            
            changeset = ''        
            for revision in body:
                for tag in revision:
                    if ( tag.tag == 'tag' and tag.attrib['k'] == 'description') :
                        if ( len(changeset) == 0 ):
                            changeset = revision.attrib['changeset']

            print("node {} changeset {}".format( node, changeset))

            alreadyIn = False
            for row in changesetDb:
                if ( row[0] == changeset) :
                    alreadyIn = True

            if (alreadyIn == False):
                changesetDb.append( [changeset,'Y'] )

            if ( nodeCount % 5) == 0 :
                time.sleep(2)

            nodeCount = nodeCount + 1
    except:
        print("error fetching {}".format(url))

with open('data/changesets.csv', 'w', encoding='utf-8') as csvfile:
    csvfile.write("changeset,Notes,SPAM\n")
    for row in changesetDb:
        csvfile.write(",".join(row) + "\n")





