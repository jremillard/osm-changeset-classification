import osmcsclassify
import sys
import sqlite3

changeSets = osmcsclassify.ChangeSetCollection.ChangeSetCollection()

conn = sqlite3.connect(osmcsclassify.Config.historyDbFileName)

errorCount = 0
# first make sure validated changeset are downloaded
for cs in changeSets.rows:
    if ( cs['note'] == 'changeset id mentioned in revert changeset' or cs['validated'] == False):
        if ( cs['cs'].cached() == False):        
            cs['cs'].extractFromPlanet(conn)
            cs['cs'].save()


''''
Bad Import                131 ChangeSets
Bad Import Val            131 ChangeSets
Import                    712 ChangeSets
Import Val                712 ChangeSets
Mapping Error             69 ChangeSets
Mapping Error Val         69 ChangeSets
OK                        21283 ChangeSets
OK Val                    7245 ChangeSets
Revert                    853 ChangeSets
Revert Val                853 ChangeSets
SPAM                      319 ChangeSets
SPAM Val                  312 ChangeSets
'''