# OpenStreetMap Changeset Classifier for SPAM

This repository contains a classifier for OpenStreetMap changesets. It is used to
detect SPAM in the OpenStreetMap database. 

## Data
The data directory contains the training data. The data/changeset.csv is a two column CSV file where column one is the changeset id and column two is the SPAM
classification either Y or N. 

Inside the data directory is a data\cache directory. It contains the actual 
contents of the changesets listed in data\changeset.csv. The cached changeset
files are custom XML files, that have the changeset comments, and a diff of
the tags modified by the changeset. These files are checked in so downloading
and processing the raw OSM data is not required.

The data/changeset.csv file was seeded with the file that Frederik Ramm posted to the talk-us list in Feb-2018 containing nodes that he suspected of being SPAM.

## Tools
updatechangesetcache.py insures that the data\cache directory is up to date
by downloading all of the changeset listed in data\changeset.csv.

train.py trains the classifier. The classifier is heavily based on the [Keras newsgroup text classification sample application](https://blog.keras.io/using-pre-trained-word-embeddings-in-a-keras-model.html)  . Instead of using the news group data, it instead uses the OSM changeset tags pulled from the data\cache directory. This is a pretty crude start, but the SPAM
activity in OpenStreetMap is currently (2018) unsophisticated, so it should work well enough on the existing database for awhile.

In the osmclassify\ directory is a ChangeSet class for downloading, loading, saving the cached changset files in data\cached. The files in data\cache are
a custom format streamlined for this task that are not standard OSM files.

## Known Dependencies 

1. The GloVe embedding here http://nlp.stanford.edu/data/glove.6B.zip
(source page: http://nlp.stanford.edu/projects/glove/), and must be installed 
into a glove.6B directory that is not checked in because it is too large.
2. Keras 
3. Python 3.x
4. A GPU is not required

## Collaborators on this project are wanted! 
- The most important part of this repository is the the data\changeset.csv file. If you are OSM'er that is passionate about keeping SPAM out of OSM, please send 
me new SPAM changesets via the github issue tracker or via a pull request. Simply Giving me the changeset id, and saying it is SPAM is enough. 
- This classifier by itself is not much good unless it is integrated into
actual tools that the OpenStreetMap community can use. 

## Extensions

The code can be easily extended to detect any type of changeset that is tag
heavy. If data is curated, the following changeset types could be detected.
- Imports 
- Automated Edits
- Pokémon Go  
- Beginner Mistakes 





