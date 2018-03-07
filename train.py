import os
import sys
import numpy as np
import osmcsclassify
import csv
import pickle
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.layers import Dense, Input, GlobalMaxPooling1D
from keras.layers import Conv1D, MaxPooling1D, Embedding
from keras.models import Model


BASE_DIR = ''
GLOVE_DIR = os.path.join(BASE_DIR, 'glove.6B')
MAX_SEQUENCE_LENGTH = 600
MAX_NUM_WORDS = 20000
EMBEDDING_DIM = 100 # options are 50, 100, 200, 300
VALIDATION_SPLIT = 0.35

# first, build index mapping words in the embeddings set
# to their embedding vector

print('Indexing word vectors.')

'''
GloVe embedding data can be found at:
http://nlp.stanford.edu/data/glove.6B.zip
(source page: http://nlp.stanford.edu/projects/glove/)
'''

embeddings_index = {}
f = open(os.path.join(GLOVE_DIR, 'glove.6B.{}d.txt'.format(EMBEDDING_DIM)))
for line in f:
    values = line.split()
    word = values[0]
    coefs = np.asarray(values[1:], dtype='float32')
    embeddings_index[word] = coefs
f.close()

print('Found %s word vectors.' % len(embeddings_index))

# second, prepare text samples and their labels
print('Processing text dataset')


labels_index = {}  # dictionary mapping label name to numeric id

texts = []  # list of text samples
labels = []  # list of label ids

with open('trainingdata/changesets.csv', newline='',encoding='utf-8') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')

    for row in spamreader:

        if len(labels_index) == 0:
            labels_index['OK'] = 0
            
            for r in row[3:]:
                label_id = len(labels_index)
                labels_index[r] = label_id       

        else:
            cs = osmcsclassify.ChangeSet.ChangeSet(row[0])
            if ( cs.cached() ):
                cs.read()
                
                label_id = 0 # 'OK'
                for index in range(3, len(row)):
                    if ( row[index] == 'Y'):
                        label_id = index-2

                labels.append( label_id )
                texts.append( cs.textDump() )
                            
print('Found %s texts.' % len(texts))

# finally, vectorize the text samples into a 2D integer tensor
tokenizer = Tokenizer(num_words=MAX_NUM_WORDS)
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)

sequencesLength = [ len(i) for i in sequences]

print('Word Count: Mean {:0.0f}, Median {:0.0f}, 95% {:0.0f}, 98% {:0.0f}, MAX_SEQUENCE_LENGTH={}'.format( 
    np.mean(sequencesLength),
    np.median(sequencesLength),
    np.percentile(sequencesLength,95),
    np.percentile(sequencesLength,98),
    MAX_SEQUENCE_LENGTH
    ))

word_index = tokenizer.word_index
print('Found %s unique tokens.' % len(word_index))

data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH,truncating='post',padding='post')


labels = to_categorical(np.asarray(labels))
print('Shape of data tensor:', data.shape)
print('Shape of label tensor:', labels.shape)

# split the data into a training set and a validation set
indices = np.arange(data.shape[0])
np.random.shuffle(indices)
data = data[indices]
labels = labels[indices]
num_validation_samples = int(VALIDATION_SPLIT * data.shape[0])

x_train = data[:-num_validation_samples]
y_train = labels[:-num_validation_samples]
x_val = data[-num_validation_samples:]
y_val = labels[-num_validation_samples:]

print('Preparing embedding matrix.')

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


# load pre-trained word embeddings into an Embedding layer
# note that we set trainable = False so as to keep the embeddings fixed
embedding_layer = Embedding(num_words,
                            EMBEDDING_DIM,
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
          epochs=15,
          validation_data=(x_val, y_val))

model.save('osmcsclassify/V0-model.h5')


with open('osmcsclassify/V0-model.pickle', 'wb') as f:
    # Pickle the 'data' dictionary using the highest protocol available.
    pickle.dump(labels_index, f, pickle.HIGHEST_PROTOCOL)
    pickle.dump(MAX_SEQUENCE_LENGTH,f,pickle.HIGHEST_PROTOCOL)
    pickle.dump(tokenizer, f,pickle.HIGHEST_PROTOCOL)

print(labels_index)

