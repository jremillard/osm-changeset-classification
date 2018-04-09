import osmcsclassify
import sys
import sqlite3
import os.path

conn = None
if ( os.path.isfile(osmcsclassify.Config.historyDbFileName)):
    conn = sqlite3.connect(osmcsclassify.Config.historyDbFileName)

changeSets = osmcsclassify.ChangeSetCollection.ChangeSetCollection()

for cs in changeSets.rows:
    if ( cs['cs'].cached() == False):        
        if ( conn not None)
            cs['cs'].extractFromPlanet(conn)
        else:
            cs['cs'].download()
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
SPAM                      319 ChangeSets
SPAM Val                  312 ChangeSets
'''