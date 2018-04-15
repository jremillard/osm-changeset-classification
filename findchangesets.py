import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import sys
import numpy as np
import osmcsclassify
import csv
import pickle
import sqlite3
import random
import datetime
from keras.preprocessing.sequence import pad_sequences
from keras.models import load_model 


labels_index ={}
maximumSeqLength = 0
tokenizer = {}

with open('osmcsclassify/V0-model.pickle', 'rb') as f:
    labels_index = pickle.load(f)
    maximumSeqLength = pickle.load(f)
    tokenizer = pickle.load(f)

model = load_model('osmcsclassify/V0-model.h5') 

conn = sqlite3.connect(osmcsclassify.Config.historyDbFileName)
conn.execute("PRAGMA cache_size = 448576")

startDateStr = str(datetime.datetime.today()).split()[0]

# start of 2014
startChangeSet = 20000000
endChangeSet = conn.execute('select max(id) from changesets').fetchone()[0]
print("Searching for interesting changesets between {} and {}".format( startChangeSet, endChangeSet))

changeSets = osmcsclassify.ChangeSetCollection.ChangeSetCollection()

with open("newchangesets.txt","wt") as toReview :

    changeSetCount = 1
    while (True):
        csId = random.randint( startChangeSet, endChangeSet)

        cs = osmcsclassify.ChangeSet.ChangeSet(csId)
        cs.extractFromPlanet(conn)
        texts = []  # list of text samples
        texts.extend( cs.textDump(1) )
                                
        sequences = tokenizer.texts_to_sequences(texts)

        data = pad_sequences(sequences, maxlen=maximumSeqLength,truncating='post',padding='post')

        y = model.predict(data)

        for i,row in enumerate(y):
            score = row[labels_index['OK']]
            selectedIndex = np.argmax(row)
            if ( selectedIndex > 0 or score < 0.5):
                for label in labels_index:
                    if ( labels_index[label] == selectedIndex):
                        print("{},{},{:0.1f},{},https://www.openstreetmap.org/changeset/{}".format( csId,label,row[labels_index[label]],changeSetCount,csId))
                        print("{},{},{:0.1f},{},https://www.openstreetmap.org/changeset/{}".format( csId,label,row[labels_index[label]],changeSetCount,csId),file=toReview)

                        # 1 in 10 imports get saved, otherwise save it. Because this program runs for days, 
                        # load up file fresh, and save it out again.
                        if ( selectedIndex != labels_index['Import'] or random.random() > 0.9):
                            changeSets = osmcsclassify.ChangeSetCollection.ChangeSetCollection()
                            changeSets.rows.append( { 'cs':cs,'labels':row,'validated':False, 'note':'Crawl ' + label + ' ' + startDateStr  })
                            changeSets.save()
                            cs.save()

        changeSetCount += 1

