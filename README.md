# OpenStreetMap Changeset Classifier for SPAM

This repository contains a classifier for OpenStreetMap changesets. It is used to
detect SPAM in the OpenStreetMap database. 

## Data
The data directory contains the training data. The data/changeset.csv is a two column CSV file where column one is the changeset id and column two is the SPAM
classification either Y or N. 

Inside the data directory is a data\cache directory. It contains the actual 
contents of the changesets listed in data\changeset.csv. The cached changeset
files are custom XML files, that have the changeset comments, and a diff of
the tags modified by the changeset.

## Tools
updatechangesetcache.py insures that the data\cache directory is up to date
with all of the changeset listed in data\changeset.csv are downloaded
in the data\cache directory.

train.py trains the classifier. The classifier is heavily based on the [Keras newsgroup text classification sample application](https://blog.keras.io/using-pre-trained-word-embeddings-in-a-keras-model.html)  . Instead of using the news group data, it instead uses the OSM changeset tags pulled from the data\cache directory.

In the osmclassify\ directory is a ChangeSet class for downloading, loading, saving the cached changset files in data\cached.

## Known Dependencies 

1. The GloVe embedding here http://nlp.stanford.edu/data/glove.6B.zip
(source page: http://nlp.stanford.edu/projects/glove/), and must be installed 
into a glove.6B directory that is not checked in.
2. Keras 
3. Python 3.x
4. A GPU is not required


## Collaborators on this project are wanted! 
- The most important thing is the curate the data\changeset.csv file. If you are OSM mapper that is passinate about keeping SPAM out of OSM, please send 
me new SPAM changesets via the github issue tracker or via a pull request. Simply the changeset id is enough. 
- The classifier by itself is much good unless it is integrated into actual 
tools that the OpenStreetMap community can use. I am eager to get this component 
actually integrated into an actual tool. 

## Extensions

The code can be easily extended to detect any type of changeset that is tag
heavy. If data is curated, the following changeset types could be detected.
- Imports 
- Automated Edits
- Pokémon Go  
- Beginner Mistakes 





