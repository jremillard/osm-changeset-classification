import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import sys
import numpy as np
import osmcsclassify
import csv
import pickle
import random
import re

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.layers import Dense, Input, GlobalMaxPooling1D
from keras.layers import Conv1D, MaxPooling1D, Embedding
from keras.models import Model

BASE_DIR = ''
GLOVE_DIR = os.path.join(BASE_DIR, 'glove.6B')
MAX_SEQUENCE_LENGTH = 1000
MAX_NUM_WORDS = 200000
EMBEDDING_DIM = 100 # options are 50, 100, 200, 300
VALIDATION_SPLIT = 0.30
dataAugmentationFactor = 8

def readAllChangeSets():

    changeSets = osmcsclassify.ChangeSetCollection.ChangeSetCollection()

    cachedChangeSets = [ cs for cs in changeSets.rows if cs['cs'].cached() ]

    validatedLabel = ' Val'

    
    totals = {}
    for label in changeSets.labelsToIndex:
        totals[label] = 0
        totals[label + validatedLabel] = 0

    for cs in cachedChangeSets:
        cs['cs'].read()
    
    for cs in cachedChangeSets:

        ok = True
        for i in range(len(cs['labels'])):
            label = changeSets.indexToLabels[i]

            if ( cs['labels'][i] > 0 ):                
                ok = False
                totals[label] += 1
                if ( cs['validated']):
                    totals[label + validatedLabel] += 1

                                             
    for k in sorted(totals):
        print("{0:25} {1} ChangeSets".format(k,totals[k]))
    
    random.shuffle(cachedChangeSets)
    
    return (cachedChangeSets,changeSets.labelsToIndex )


def readEmbeddingIndex() :

    fileName = os.path.join(GLOVE_DIR, 'glove.6B.{}d.txt'.format(EMBEDDING_DIM))

    print('Reading GloVe word embedding data from {}.'.format(fileName))

    # GloVe word embedding data can be found at: http://nlp.stanford.edu/projects/glove/
    # Download the glove.6B.zip 

    embeddings_index = {}
    with open(fileName) as f:
        for line in f:
            values = line.split()
            word = values[0]
            coefs = np.asarray(values[1:], dtype='float32')
            embeddings_index[word] = coefs

            # fill in osm terms
            if ( word == "address") :
                embeddings_index['addr'] = coefs

    print('Read {} words.'.format(len(embeddings_index)))
                    
    return embeddings_index

def setupTokenizer(allChangeSets):

    fulltext = []

    for cs in allChangeSets:
        txs = cs['cs'].textDump(1)
        fulltext.extend(txs)

    # finally, vectorize the text samples into a 2D integer tensor
    tokenizer = Tokenizer(num_words=MAX_NUM_WORDS)
    tokenizer.fit_on_texts(fulltext)
    # seeing imports , require that the add/remove/modify counts be seen 
    # if we don't index them, they can't be used.
    numbers1toNasStr = ' '.join( [str(x) for x in range(1,70000)] )
    tokenizer.fit_on_texts([numbers1toNasStr])

    sequences = tokenizer.texts_to_sequences(fulltext)

    sequencesLength = [ len(i) for i in sequences]

    word_index = tokenizer.word_index
    print('Found {} Unique Tokens.'.format(len(word_index)))

    print('Changeset Token Counts: Mean {:0.0f}, Median {:0.0f}, 95% {:0.0f}, 98% {:0.0f}, MAX_SEQUENCE_LENGTH={}'.format( 
        np.mean(sequencesLength),
        np.median(sequencesLength),
        np.percentile(sequencesLength,95),
        np.percentile(sequencesLength,98),
        MAX_SEQUENCE_LENGTH
        ))        

    return tokenizer


def makeEmbeddingMatrix(tokenizer,embeddings_index):

    word_index = tokenizer.word_index
    
    with open("osmcsclassify/cantembed.txt",encoding="utf8",mode="wt") as cantembed:
        
        # prepare embedding matrix
        num_words = min(MAX_NUM_WORDS, len(word_index)+1)
        embedding_matrix = np.zeros((num_words, EMBEDDING_DIM))
        for word, i in word_index.items():
            if i >= MAX_NUM_WORDS:
                continue

            # embed all numbers ourselves.
            if ( re.match(r'^[0-9]+$',word) is not None ):
                
                val = int( word)
                for n in range(0,15):
                    embedding_matrix[i][n] = min(float(val),1.0)
                    val = val / 10
                
            else :
                embedding_vector = embeddings_index.get(word)
                if embedding_vector is not None:
                    # words not found in embedding index will be all-zeros.
                    embedding_matrix[i] = embedding_vector
                else :
                    print(word,file=cantembed)

        return embedding_matrix
    

def changeSetsToDataArrayAndLabels( usedChangeSets, tokenizer, augmentationFactor):
    texts = []
    labels = []

    for cs in usedChangeSets:
        txs = cs['cs'].textDump(augmentationFactor)

        for t in txs:
            labels.append( cs['labels'] )
            texts.append(t)

    sequences = tokenizer.texts_to_sequences(texts)
    data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH,truncating='post',padding='post')

    labels = np.asarray(labels)

    return (data,labels)

def trainingValidationSplit(allChangeSets):

    # only validated changesets are used, they are already shuffled.
    usedChangeSets = [x for x in allChangeSets if x['validated'] ]  

    numberOfValidationChangeSets = int(VALIDATION_SPLIT * len(usedChangeSets))
    
    trainChangeSets = usedChangeSets[0:-numberOfValidationChangeSets]
    validateChangeSets = usedChangeSets[-numberOfValidationChangeSets:]

    return (trainChangeSets,validateChangeSets )

# start of program

(allChangeSets, labels_index) = readAllChangeSets()

(trainChangeSets, validateChangeSets) = trainingValidationSplit(allChangeSets)

tokenizer = setupTokenizer(allChangeSets)

( x_train,y_train) = changeSetsToDataArrayAndLabels(trainChangeSets,tokenizer,dataAugmentationFactor)
( x_val,y_val) = changeSetsToDataArrayAndLabels(validateChangeSets,tokenizer,1)

#labels = to_categorical(np.asarray(labels))
#print('Shape of data tensor:', data.shape)
#print('Shape of label tensor:', labels.shape)

embeddings_index = readEmbeddingIndex()
embedding_matrix = makeEmbeddingMatrix(tokenizer,embeddings_index)

# load pre-trained word embeddings into an Embedding layer
# note that we set trainable = False so as to keep the embeddings fixed
embedding_layer = Embedding(embedding_matrix.shape[0],
                            embedding_matrix.shape[1],
                            weights=[embedding_matrix],
                            input_length=MAX_SEQUENCE_LENGTH
                            ) 

embedding_layer.trainable = False

print('Training model.')

# train a 1D convnet with global maxpooling
sequence_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype='int32')
embedded_sequences = embedding_layer(sequence_input)
x = Conv1D(EMBEDDING_DIM, 5, activation='relu')(embedded_sequences)
x = MaxPooling1D(5)(x)
x = Conv1D(EMBEDDING_DIM, 5, activation='relu')(x)
x = MaxPooling1D(5)(x)
x = Conv1D(EMBEDDING_DIM, 5, activation='relu')(x)
x = GlobalMaxPooling1D()(x)
x = Dense(EMBEDDING_DIM, activation='relu')(x)
preds = Dense(len(labels_index), activation='softmax')(x)

model = Model(sequence_input, preds)
model.compile(loss='categorical_crossentropy',
              optimizer='rmsprop',
              metrics=['acc'])

print(model.summary())

model.fit(x_train, y_train,
          batch_size=128,
          epochs=5,
          validation_data=(x_val, y_val))

model.save('osmcsclassify/V0-model.h5')

with open('osmcsclassify/V0-model.pickle', 'wb') as f:
    # Pickle the 'data' dictionary using the highest protocol available.
    pickle.dump(labels_index, f, pickle.HIGHEST_PROTOCOL)
    pickle.dump(MAX_SEQUENCE_LENGTH,f,pickle.HIGHEST_PROTOCOL)
    pickle.dump(tokenizer, f,pickle.HIGHEST_PROTOCOL)


