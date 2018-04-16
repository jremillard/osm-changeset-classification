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
import urllib.request
import json
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
print("Getting changests from OSMCha");

changeSets = osmcsclassify.ChangeSetCollection.ChangeSetCollection()


count = 0

with urllib.request.urlopen('https://osmcha.mapbox.com/api/v1/changesets/harmful/?page=1&page_size=100&checked=1&harmful=1') as Iresponse:
    resp = json.load(Iresponse)

    count = resp['count']

pageSize = 100
pageCount = int(count/pageSize)+2

for page in range( 1,pageCount ):
    with urllib.request.urlopen('https://osmcha.mapbox.com/api/v1/changesets/harmful/?page={}&page_size=100&checked=1&harmful=1'.format(page)) as Iresponse:
        resp = json.load(Iresponse)

        for cs in resp['features']:
            p = cs['properties']
            for t in p['tags']:
                if ( t['id'] == 1):
                    csId = cs['id']
                    changeSet = osmcsclassify.ChangeSet.ChangeSet(csId)

                    if ( csId < endChangeSet):
                        changeSet.extractFromPlanet(conn)
                    else:
                        continue
                        #changeSet.download()

                    texts = []  # list of text samples
                    texts.extend( changeSet.textDump(1) )
                                            
                    sequences = tokenizer.texts_to_sequences(texts)

                    data = pad_sequences(sequences, maxlen=maximumSeqLength,truncating='post',padding='post')

                    y = model.predict(data)

                    row = y[0]

                    changeSets.rows.append( { 'cs':changeSet,'labels':row,'validated':False, 'note':'OSMCha ' + startDateStr  })
                    changeSets.save()
                    changeSet.save()


