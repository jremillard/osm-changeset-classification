import csv
import osmcsclassify
import random

changeSets = osmcsclassify.ChangeSetCollection.ChangeSetCollection()

# first make sure validated changeset are downloaded
for cs in changeSets.rows:
    if ( cs['validated'] and cs['label'] != 'OK'):
        if ( cs['cs'].cached() == False):        
            print("downloading validated changeset {}".format(cs))
            cs['cs'].download()
            cs['cs'].save()
            exit(0)


