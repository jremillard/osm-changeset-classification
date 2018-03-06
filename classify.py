import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import sys
import numpy as np
import osmcsclassify
import csv
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.models import load_model 

BASE_DIR = ''
GLOVE_DIR = os.path.join(BASE_DIR, 'glove.6B')
MAX_SEQUENCE_LENGTH = 600
MAX_NUM_WORDS = 20000
EMBEDDING_DIM = 100 # options are 50, 100, 200, 300

# first, build index mapping words in the embeddings set
# to their embedding vector

#print('Indexing word vectors.')

embeddings_index = {}
f = open(os.path.join(GLOVE_DIR, 'glove.6B.{}d.txt'.format(EMBEDDING_DIM)))
for line in f:
    values = line.split()
    word = values[0]
    coefs = np.asarray(values[1:], dtype='float32')
    embeddings_index[word] = coefs
f.close()

#print('Found %s word vectors.' % len(embeddings_index))

# second, prepare text samples and their labels
#print('Processing text dataset')

labels_index = {}  # dictionary mapping label name to numeric id

changesets = []
texts = []  # list of text samples
labels = []

if len(sys.argv) > 1:
    with open('trainingdata/changesets.csv', newline='',encoding='utf-8') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')

        for row in spamreader:
            if len(labels_index) == 0:
                labels_index['OK'] = 0
                
                for r in row[2:]:
                    label_id = len(labels_index)
                    labels_index[r] = label_id       

        cs = osmcsclassify.ChangeSet.ChangeSet(row[0])
        if ( cs.cached() ):
            cs.read()


else :

    with open('trainingdata/changesets.csv', newline='',encoding='utf-8') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')

        for row in spamreader:

            if len(labels_index) == 0:
                labels_index['OK'] = 0
                
                for r in row[2:]:
                    label_id = len(labels_index)
                    labels_index[r] = label_id       

            else:
                cs = osmcsclassify.ChangeSet.ChangeSet(row[0])
                if ( cs.cached() ):
                    cs.read()
                    
                    label_id = 0 # 'OK'
                    for index in range(2, len(row)):
                        if ( row[index] == 'Y'):
                            label_id = index-1

                    texts.append( cs.textDump() )
                    changesets.append(cs)
                    labels.append( label_id)
                            
#print('Found %s texts.' % len(texts))

# finally, vectorize the text samples into a 2D integer tensor
tokenizer = Tokenizer(num_words=MAX_NUM_WORDS)
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)

sequencesLength = [ len(i) for i in sequences]

word_index = tokenizer.word_index

data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH,truncating='post',padding='post')

#print('Preparing embedding matrix.')

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
        1
        # print("Can't embed {}".format(word))


model = load_model('osmcsclassify/V0-model.h5') 

#print(model.summary())

y = model.predict(data)

print("ID             " + "\t".join(labels_index) + "\tStatus")

for i,row in enumerate(y):
    bad = False
    if ( not labels is None ):
        #if ( np.argmax(row) != labels[i]):
        #    bad = True
        if ( np.max(row)-np.min(row) < 0.50):
            bad = True
        
    if ( bad):
        print("{:15}".format(changesets[i].id),end='')
        for label in labels_index:
            print("{:0.2f}".format(row[labels_index[label]]), end='\t')
        print("BAD")

        print("{}\n\n".format(texts[i]))




