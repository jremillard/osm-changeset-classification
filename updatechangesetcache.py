import csv
import osmcsclassify
import random

changeSets = []
with open('trainingdata/changesets.csv', newline='',encoding='utf-8') as csvfile:
    changesets = csv.reader(csvfile, delimiter=',')

    # eat the header
    next(changesets)

    for row in changesets:
        cs = osmcsclassify.ChangeSet.ChangeSet(row[0])
        changeSets.append( cs)

download_limit = 100000
downloads = 0

random.shuffle(changeSets)

for cs in changeSets:
    if ( cs.cached() == False):        
        if ( downloads < download_limit ):
            print("downloading {}".format(cs.id))
            cs.download()
            cs.save()
            downloads += 1



