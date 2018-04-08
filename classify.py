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

changesets = []
texts = []  # list of text samples
labels = None

conn = sqlite3.connect(osmcsclassify.Config.historyDbFileName)

if len(sys.argv) > 1:

    for arg in sys.argv[1:]:
        cs = osmcsclassify.ChangeSet.ChangeSet(arg)
        if ( cs.cached()  ):
            cs.read()
        else :            
            #cs.download()
            cs.extractFromPlanet(conn)
            #cs.saveFile(cs.cacheRuntimeFileName())

        #print(cs.textDump(1)[0])            
        texts.extend( cs.textDump(1) )
        changesets.append(cs)

else :
    labels = []

    changeSets = osmcsclassify.ChangeSetCollection.ChangeSetCollection()

    cachedChangeSets = [ cs for cs in changeSets.rows if cs['cs'].cached() ]

    for cs in cachedChangeSets:

        if ( cs['validated'] == False):

            if ( cs['cs'].cached()  ):
                cs['cs'].read()
            else:
                cs['cs'].extractFromPlanet(conn)

            #print(cs['cs'].textDump(1)[0])            
            texts.extend( cs['cs'].textDump(1) )
            changesets.append(cs['cs'])
            labels.append( cs['labels'])

labels_index ={}
maximumSeqLength = 0
tokenizer = {}

with open('osmcsclassify/V0-model.pickle', 'rb') as f:
    labels_index = pickle.load(f)
    maximumSeqLength = pickle.load(f)
    tokenizer = pickle.load(f)

model = load_model('osmcsclassify/V0-model.h5') 
                            
sequences = tokenizer.texts_to_sequences(texts)
#print(sequences[0])

data = pad_sequences(sequences, maxlen=maximumSeqLength,truncating='post',padding='post')

y = model.predict(data)

print("ID             " + "\t".join(labels_index) + "\tStatus")

if ( not labels is None ):
    with open("toreview.txt","wt") as toReview :
        for i,row in enumerate(y):
            #print(row)
            bad = False
            for labelIndex in labels[i]:
                if (  labels[i][labelIndex] > 0.5 and row[labelIndex] < 0.5):
                    bad = True
                if (  labels[i][labelIndex] < 0.5 and row[labelIndex] > 0.5):
                    bad = True
                            
            if ( bad  ):

                if ( changesets[i].cached() == False):
                    changesets[i].save()

                print("{:15}".format(changesets[i].id),end='')
                print("{} ".format(changesets[i].id),end='',file=toReview)
                for label in labels_index:
                    print("{:0.2f}".format(row[labels_index[label]]), end='\t',)
                    print("{}={:0.2f}".format(label,row[labels_index[label]]), end=' ',file=toReview)
                if bad:
                    print("BAD")
                print("",file=toReview)
                #print("{}\n\n".format(texts[i]))
            
else :
    for i,row in enumerate(y):
        print(changesets[i].textDumpHuman())
        print("{:15}".format(changesets[i].id),end='')
        for label in labels_index:
            print("{:0.2f}".format(row[labels_index[label]]), end='\t')
        print("")
            #print("{}\n\n".format(texts[i]))

