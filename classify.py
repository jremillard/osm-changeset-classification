import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import sys
import numpy as np
import osmcsclassify
import csv
import pickle
from keras.preprocessing.sequence import pad_sequences
from keras.models import load_model 

changesets = []
texts = []  # list of text samples
labels = None

if len(sys.argv) > 1:

    for arg in sys.argv[1:]:
        cs = osmcsclassify.ChangeSet.ChangeSet(arg)
        if ( cs.cached() ):
            cs.read()
        else :
            cs.download()
            cs.saveFile(cs.cacheRuntimeFileName())

        texts.extend( cs.textDump(1) )
        changesets.append(cs)

else :
    labels = []

    with open('trainingdata/changesets.csv', newline='',encoding='utf-8') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        next(spamreader)

        for row in spamreader:
            if not ( len(row[2]) > 0 and row[2] == 'Y' ):            
                cs = osmcsclassify.ChangeSet.ChangeSet(row[0])
                if ( cs.cached() ):
                    cs.read()
                    
                    label_id = 0 # 'OK'
                    for index in range(3, len(row)):
                        if ( row[index] == 'Y'):
                            label_id = index-2

                    texts.extend( cs.textDump(1) )
                    changesets.append(cs)

                    labels.append( label_id)

labels_index ={}
maximumSeqLength = 0
tokenizer = {}

with open('osmcsclassify/V0-model.pickle', 'rb') as f:
    labels_index = pickle.load(f)
    maximumSeqLength = pickle.load(f)
    tokenizer = pickle.load(f)

model = load_model('osmcsclassify/V0-model.h5') 
                            
sequences = tokenizer.texts_to_sequences(texts)

data = pad_sequences(sequences, maxlen=maximumSeqLength,truncating='post',padding='post')

y = model.predict(data)

print("ID             " + "\t".join(labels_index) + "\tStatus")

if ( not labels is None ):
    with open("toreview.txt","wt") as toReview :
        for i,row in enumerate(y):
            bad = False
            close = False
            if ( np.argmax(row) != labels[i]):
                bad = True
                #if ( row[labels_index['SPAM']] < 0.009999 and row[labels_index['OK']] > 0.99):
                #    bad = True

            if ( np.max(row)-np.min(row) < 0.50):
                close = True
                close = False
            
            if ( bad or close):
                print("{:15}".format(changesets[i].id),end='')
                print("{} ".format(changesets[i].id),end='',file=toReview)
                for label in labels_index:
                    print("{:0.2f}".format(row[labels_index[label]]), end='\t',)
                    print("{}={:0.2f}".format(label,row[labels_index[label]]), end=' ',file=toReview)
                if bad:
                    print("BAD")
                elif close:
                    print("Close")
                print("",file=toReview)
                #print("{}\n\n".format(texts[i]))
            
else :
    for i,row in enumerate(y):
        print("{:15}".format(changesets[i].id),end='')
        for label in labels_index:
            print("{:0.2f}".format(row[labels_index[label]]), end='\t')
        print("")
            #print("{}\n\n".format(texts[i]))

