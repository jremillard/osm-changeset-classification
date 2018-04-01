import osmcsclassify
import sys
import sqlite3

changeSets = osmcsclassify.ChangeSetCollection.ChangeSetCollection()

conn = sqlite3.connect(osmcsclassify.Config.historyDbFileName)

errorCount = 0
# first make sure validated changeset are downloaded
for cs in changeSets.rows:
    if ( cs['note'] == 'changeset id mentioned in revert changeset'):
        if ( cs['cs'].cached() == False):        
            cs['cs'].extractFromPlanet(conn)
            cs['cs'].save()


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