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

        totalObjectsAprx = 4405627202*1.8

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

    conn = sqlite3.connect(historyDbFileName)
    conn.execute("PRAGMA cache_size = 448576")
    

# importHistory()
importChangeSet()
# makeIndexes()


