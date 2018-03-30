import csv
import osmcsclassify
import random
import sys

changeSets = osmcsclassify.ChangeSetCollection.ChangeSetCollection()

errorCount = 0
# first make sure validated changeset are downloaded
for cs in changeSets.rows:
    if ( cs['note'] == 'changeset id mentioned in revert changeset'):
        if ( cs['cs'].cached() == False):        
            try:
                print("downloading validated changeset {}".format(cs))
                cs['cs'].download()
                #cs['cs'].extractFromPlanet()
                cs['cs'].save()
            except:
                print("Unexpected error:", sys.exc_info()[0])
                errorCount += 1

                if ( errorCount > 3):
                    exit(0)


''''
Bad Import                10 ChangeSets
Bad Import Val            10 ChangeSets
Import                    200 ChangeSets
Import Val                200 ChangeSets
Mapping Error             16 ChangeSets
Mapping Error Val         16 ChangeSets
OK                        6892 ChangeSets
OK Val                    6682 ChangeSets
Revert                    738 ChangeSets
Revert Val                738 ChangeSets
SPAM                      218 ChangeSets
SPAM Val                  210 ChangeSets
'''