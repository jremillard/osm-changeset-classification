# OpenStreetMap Changeset Classifier For Detecting SPAM, Imports, Reverts and Mapping Errors

This repository contains a classifier for OpenStreetMap changesets. It is used to
detect SPAM, tagging errors, imports, and imports with tagging issues in the OpenStreetMap database. 


## Tools

createhistorydatabase.py - Makes a custom sqlite database from the raw history and changeset download files.

updatechangesetcache.py insures that the trainingdata/cache directory is up to date
by extracting all of the changeset listed in trainingdata/changeset.csv from the sqlite history database.

train.py trains the classifier. The classifier is heavily based on the [Keras newsgroup text classification sample application](https://blog.keras.io/using-pre-trained-word-embeddings-in-a-keras-model.html)  . Instead of using the news group data, it instead uses the OSM changeset tags pulled from the trainingdata/cache directory. 

classify.py runs the trained classifier. If no parameters are supplied it will run the classifier over the training data and report misclassified changeset. If you supply 
a changeset number on the, it will download the changeset and classify it. For example, python classify.py 5071219, will classify changeset 5071219.

reviewtrainingdata.py is an interactive terminal program that prompts the user to classify un un-validated changesets. 

In the osmclassify/ directory is a ChangeSet class for downloading, loading, saving the cached changeset files in trainingdata/cached. The files in trainingdata/cache are
a custom format streamlined for this project that are not standard OSM files. 
They are a true difference introduced by the changeset.

## Data
The trainingdata/ directory contains the training data.

The trainingdata/changeset.csv is a CSV file where columns are:
- changeset id - The OSM Changset ID.
- From/Note - Where the row came from.
- Validated - Y,N if the changeset have been manually validated with reviewtrainingdata.py
- SPAM - Y,N if the changeset was 
- Import - Y,N - An import
- Tagging Error - Y,N - 

The trainingdata/cache directory contains the actual 
contents of the changesets listed in trainingdata/changeset.csv. The cached changeset
files are custom XML files, that have the changeset comments, and a diff of
the tags modified by the changeset. These files are checked in so downloading
and processing the raw OSM data is not required.

The trainingdata/changeset.csv file was seeded from many sources. 
- Frederik Ramm posted a csv file to the talk-us list in Feb-2018 containing nodes that he suspected of being SPAM.
- Random changsets 
- Using regular expressions of the changset dump, changesets that are reverting another changesets. 
- Using regular expressions of the changset dump, changesets that are mentioned in the command of a revert changeset as reverted.
- Running intermediate versions of the classifier millions of changesets from 2017.

## Known Dependencies 

1. The GloVe embedding here http://nlp.stanford.edu/data/glove.6B.zip
(source page: http://nlp.stanford.edu/projects/glove/), and must be installed 
into a glove.6B directory that is not checked in because it is too large.
2. Keras 
3. Python 3.x
4. A GPU is not required.

## Collaborators are Wanted! 
- The most important part of this repository is the the trainingdata/changeset.csv file. If you are OSM'er that is passionate about keeping SPAM out of OSM, please send 
me new SPAM changesets via the github issue tracker or via a pull request. Simply giving me the changeset id and saying it is SPAM is enough. 
- This classifier by itself is not much good unless it is integrated into
actual tools that the OpenStreetMap community can use. 

