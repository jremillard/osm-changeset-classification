import os
import sys
import numpy as np
import osmcsclassify
import csv
import pickle
import random

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.layers import Dense, Input, GlobalMaxPooling1D
from keras.layers import Conv1D, MaxPooling1D, Embedding
from keras.models import Model

BASE_DIR = ''
GLOVE_DIR = os.path.join(BASE_DIR, 'glove.6B')
MAX_SEQUENCE_LENGTH = 600
MAX_NUM_WORDS = 200000
EMBEDDING_DIM = 100 # options are 50, 100, 200, 300
VALIDATION_SPLIT = 0.35

def readAllChangeSets():

     # dictionary mapping label name to numeric id
    labels_index = {}
    index_labels = {}
    usedChangeSets = []
    totals = {}

    with open('trainingdata/changesets.csv', newline='',encoding='utf-8') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        
        for row in spamreader:

            if len(labels_index) == 0:
                totals[ 'Total' ] = 0
                totals[ 'Validated' ] = 0
                
                labels_index['OK'] = 0
                index_labels[0] = 'OK'

                totals[ 'OK' ] = 0
                totals[ 'OK Validated' ] = 0

                for r in row[3:]:
                    label_id = len(labels_index)
                    labels_index[r] = label_id       
                    index_labels[label_id] = r

                    totals[ r ] = 0
                    totals[ r+' Validated' ] = 0

            else:
                if ( len(row[2]) > 0 and row[2] != 'Y'):
                    raise Exception("error for id {}, validation cell must be Y or empty, {}".format(row[0],row[2]))
                if ( len(row) != len(labels_index)+3-1):
                    # -1 for OK
                    raise Exception("error for id {}, wrong number of category cells.".format(row[0]))
                    
                validated =  len(row[2]) > 0 and row[2] == 'Y'

                label_id = 0 # 'OK'
                for index in range(3, len(row)):
                    if ( row[index] == 'Y'):
                        label_id = index-2
                    elif ( row[index] == 'N'):
                        pass
                    else:
                        raise Exception("error for id {}, category cells must be Y,N".format(row[0]))
                
                    
                cs = osmcsclassify.ChangeSet.ChangeSet(row[0])
                if ( cs.cached() ):
                    cs.read()                
                    usedChangeSets.append( { 'cs':cs,'label':label_id, 'validated':validated })

                    label = index_labels[label_id]

                    if ( validated ):
                        totals[ 'Validated' ] += 1
                        totals[ label+' Validated' ] += 1

                    totals[ 'Total' ] += 1
                    totals[ label ] += 1
                                    
    random.shuffle(usedChangeSets)

    for k in sorted(totals):
        print("{0:25} {1} ChangeSets".format(k,totals[k]))
    
    return (usedChangeSets,labels_index )


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
            labels.append( cs['label'] )
            texts.append(t)

    sequences = tokenizer.texts_to_sequences(texts)
    data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH,truncating='post',padding='post')

    labels = to_categorical(np.asarray(labels))

    return (data,labels)

def trainingValidationSplit(allChangeSets):

    # only validated changesets are used, they are already shuffled.
    usedChangeSets = [x for x in allChangeSets if x['validated'] ]  

    numberOfValidationChangeSets = int(VALIDATION_SPLIT * len(usedChangeSets))
    
    trainChangeSets = usedChangeSets[0:-numberOfValidationChangeSets]
    validateChangeSets = usedChangeSets[-numberOfValidationChangeSets:]

    return (trainChangeSets,validateChangeSets )

(allChangeSets, labels_index) = readAllChangeSets()

(trainChangeSets, validateChangeSets) = trainingValidationSplit(allChangeSets)

tokenizer = setupTokenizer(allChangeSets)

( x_train,y_train) = changeSetsToDataArrayAndLabels(trainChangeSets,tokenizer,10)
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
          epochs=12,
          validation_data=(x_val, y_val))

model.save('osmcsclassify/V0-model.h5')

with open('osmcsclassify/V0-model.pickle', 'wb') as f:
    # Pickle the 'data' dictionary using the highest protocol available.
    pickle.dump(labels_index, f, pickle.HIGHEST_PROTOCOL)
    pickle.dump(MAX_SEQUENCE_LENGTH,f,pickle.HIGHEST_PROTOCOL)
    pickle.dump(tokenizer, f,pickle.HIGHEST_PROTOCOL)


