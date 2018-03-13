import csv
import osmcsclassify
import random

changeSetTrainDb = []
changeSets = []
with open('trainingdata/changesets.csv', newline='',encoding='utf-8') as csvfile:
    changeSetTrainFile = csv.reader(csvfile, delimiter=',')

    # eat the header
    next(changeSetTrainFile)

    for row in changeSetTrainFile:
        cs = osmcsclassify.ChangeSet.ChangeSet(row[0])
        changeSets.append( cs)
        changeSetTrainDb.append(row)

download_limit = 100000
downloads = 0

if ( False) :

    testId = '2677986'
    cs = osmcsclassify.ChangeSet.ChangeSet(testId)
    cs.download()
    cs.textDumpHuman()
    exit(0)

# first make sure validated changeset are downloaded
for i,cs in enumerate( changeSets):
    if ( len(changeSetTrainDb[i][2]) > 0 and changeSetTrainDb[i][2] == 'Y' ):
        if ( cs.cached() == False):        
            print("downloading {}".format(cs.id))
            cs.download()
            cs.save()
            downloads += 1

# if they are all downloaded, then randomly 
# download the un-validated changesets.

random.shuffle(changeSets)

for cs in changeSets:
    if ( cs.cached() == False):        
        if ( downloads < download_limit ):
            print("downloading {}".format(cs.id))
            cs.download()
            cs.save()
            downloads += 1



