import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import sys
import numpy as np
import osmcsclassify
import csv
import pickle
import sqlite3
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

with open("newchangesets.txt","wt") as toReview :

    changeSetCount = 1
    for csId in range(45698048,55698048):
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
        
        changeSetCount += 1

