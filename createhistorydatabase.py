import sys
import overpy
import os
from shutil import copyfile
import sqlite3
import time
import xml.etree.ElementTree as etree
import bz2
import re
import osmcsclassify.Config

import osmium

# might not be enough room in the normal temporary directories.
os.environ["SQLITE_TMPDIR"] =  osmcsclassify.Config.historyDbTempDirName

# good guess at how how many actual ways, nodes, and relations need to get
# written out, used for progress indicator, so it doesn't really need to be
# correct.
totalObjectsAprx = 4405627202*1.8

class TestHandler(osmium.SimpleHandler):

    transactionBlockSize = 300000

    def __init__(self, conn):
        osmium.SimpleHandler.__init__(self)
        self.conn = conn
        self.cursor = conn.cursor()
        self.writeCount = 0
        self.writeCountTotal = 0
        self.blockStartTime = time.time()
        self.startTime = time.time()


    def node(self,o):
        self.addObject(o,0)

    def way(self,o):
        self.addObject(o,1)

    def relation(self,o):
        self.addObject(o,2)

    def addObject( self, o, objectType):
        self.writeCount += 1
        self.writeCountTotal += 1

        if ( self.writeCount > TestHandler.transactionBlockSize):
            self.conn.commit()
            self.conn.execute("BEGIN")
            self.writeCount = 0
            howLong =  time.time() - self.blockStartTime
            totalTime = time.time() - self.startTime
            ratioDone = self.writeCountTotal/totalObjectsAprx

            timeLeftHrs = ((totalTime / ratioDone)-totalTime)/3600

            print("{:0.1f}s {:0.0f}K objects, {:0.3f}% Complete, {:0.1f} Hours Remaining".format(howLong,TestHandler.transactionBlockSize/1000,ratioDone*100,timeLeftHrs ))
            self.blockStartTime = time.time()
 
        self.cursor.execute('insert or ignore into changesets ( id,uid) values (?,?) ',(o.changeset,o.uid)).fetchone()

        visible = 1
        if ( o.visible ):
            visible = 1
        else:
            visible = 0

        self.cursor.execute("insert into objects (type,id,version,changeset,visible) VALUES (?,?,?,?,?);",(objectType,o.id,o.version,o.changeset,visible))
        objectId = self.cursor.lastrowid
        keys = self.kvToIndexs(o)

        for key in keys:
            self.cursor.execute("insert into objectskv (objectid, keyid, valueid) values (?,?,?)", (objectId, key[0],key[1]))

    def kvToIndexs(self,o):
        kvs = []

        for key in o.tags:
            (ki) = self.cursor.execute('SELECT keyid FROM keys where keys.key == ? ',(key.k,)).fetchone()
            (vi) = self.cursor.execute('SELECT valueid FROM keyvalues where value == ? ',(key.v,)).fetchone()

            if ki is None:
                self.cursor.execute( "insert into keys (key) values (?)",(key.k,))
                ki = self.cursor.lastrowid
            else:
                ki = ki[0]

            if vi is None:
                self.cursor.execute( "insert into keyvalues (value) values (?)",(key.v,))
                vi = self.cursor.lastrowid
            else:
                vi = vi[0]
 
            kvs.append( (ki, vi))
            
        return kvs

            
def importHistory():

    copyfile("history-schema.sqlite",osmcsclassify.Config.historyDbFileName )

    conn = sqlite3.connect(osmcsclassify.Config.historyDbFileName)
    conn.execute("PRAGMA cache_size = 448576")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA journal_mode = OFF")

    conn.execute("BEGIN")

    ph = TestHandler(conn)

    ph.apply_file(historyPBF)

    conn.commit()
    conn.close()

def importChangeSet():

    print("Importing {}. This will take 6 hours.".format(osmcsclassify.Config.changeSetHistoryOSM))
    
    conn = sqlite3.connect(osmcsclassify.Config.historyDbFileName)
    conn.execute("PRAGMA cache_size = 448576")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("BEGIN")

    cursor = conn.cursor()

    xml = bz2.open(osmcsclassify.Config.changeSetHistoryOSM)

    changesetAttrib = {}

    for event, elem in etree.iterparse(xml, events=('start', 'end', 'start-ns', 'end-ns')):
        if ( event == 'start' and elem.tag == "changeset"):
            changesetAttrib = elem.attrib
        if ( event == 'start' and elem.tag == "tag"):            

            key = elem.attrib['k']
            value = elem.attrib['v']

            (ki) = cursor.execute('SELECT keyid FROM keys where keys.key == ? ',(key,)).fetchone()
            (vi) = cursor.execute('SELECT valueid FROM keyvalues where value == ? ',(value,)).fetchone()

            if ki is None:
                cursor.execute( "insert into keys (key) values (?)",(key,))
                ki = cursor.lastrowid
            else:
                ki = ki[0]

            if vi is None:
                cursor.execute( "insert into keyvalues (value) values (?)",(value,))
                vi = cursor.lastrowid
            else:
                vi = vi[0]
            
            cursor.execute("insert into changesetkv (changeset, keyid, valueid) values (?,?,?)", (changesetAttrib['id'], ki,vi))

        elem.clear()

    conn.commit()
    conn.close()


def makeIndexes():
    print("Add index's to {}".format(osmcsclassify.Config.historyDbFileName))

    conn = sqlite3.connect(osmcsclassify.Config.historyDbFileName)
    conn.execute("PRAGMA cache_size = 448576")

    sqlIndexs = [
        #CREATE TABLE "changesets" ( `uid` INTEGER, `id` INTEGER, PRIMARY KEY(`id`) )
        "CREATE INDEX IF NOT EXISTS 'changesets-uid' ON changesets (uid )",
        # CREATE TABLE "objects" ( `type` INTEGER, `id` INTEGER, `version` INTEGER, `changeset` INTEGER, `visible` INTEGER, `rowid` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE )
        "CREATE INDEX IF NOT EXISTS 'objects-changeset' ON objects (changeset )",
        "CREATE INDEX IF NOT EXISTS 'objects-type-id' ON objects (type,id )",
        #CREATE TABLE "objectskv" ( `objectid` INTEGER, `keyid` INTEGER, `valueid` INTEGER )
        "CREATE INDEX IF NOT EXISTS 'objectskv-objectid' ON objectskv (objectid )"
    ]

    for sql in sqlIndexs:
        print("execute: {}".format(sql))
        conn.execute("BEGIN")
        conn.execute(sql)
        conn.commit()

    conn.close()
            
# importHistory()
#importChangeSet()
makeIndexes()


