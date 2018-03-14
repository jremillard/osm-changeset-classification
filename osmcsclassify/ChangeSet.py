import xml.etree.ElementTree as ET
import urllib.request
import re
import time
import math
import random

fileCacheVersion = '2'
osmApiBase =  "https://api.openstreetmap.org"

class ChangeSet:
    lastRequestTime = 0

    def urlRequest(self, url):

        now = time.clock()

        minimumRequestSpacing = 1.0/5

        if ( now < ChangeSet.lastRequestTime+minimumRequestSpacing):
            delay = ChangeSet.lastRequestTime+minimumRequestSpacing-now
            if ( delay < 0 ):
                dalay = 0
            print("  get delay {:0.2f} {}".format(delay,url))
            time.sleep(delay)  
        else:
            print("  get {}".format(url))
            
        hdr = { 'User-Agent' : 'OSM changeset classifier/osm-changeset-classification on github' }

        req = urllib.request.Request(url, headers=hdr)
        response = urllib.request.urlopen(req)
        responseStr = response.read()
        responseXML = ET.fromstring(responseStr)

        ChangeSet.lastRequestTime = time.clock()
        
        return responseXML
        
    def __init__(self, id):

        self.id = str(id)
        self.metaTags = {}
        self.elementTags = []

        self.nodesAdded = 0
        self.waysAdded = 0
        self.relationsAdded = 0
        
        self.nodesModified = 0
        self.waysModified = 0
        self.relationsModified = 0

        self.nodesDeleted = 0
        self.waysDeleted = 0
        self.relationsDeleted = 0
        
        self.ignoredKeys = ['created_by']

    def cacheFileName(self):
        return "trainingdata/cache/{}/{}.xml".format(self.id[-2:],self.id)
    def cacheRuntimeFileName(self):
        return "runtimedata/cache/{}.xml".format(self.id)

    def addAddTag( self, osmId, elementType, key,value):        
        if ( not key in self.ignoredKeys):
            self.elementTags = list(filter(lambda x: x['osmId'] != osmId or x['type'] != elementType or x['k'] != key, self.elementTags))
            self.elementTags.append( { 'osmId':osmId, 'type':elementType,'o':'add', 'k':key, 'v':value } )        

    def addModifyTag( self, osmId, elementType, key,value):        
        if ( not key in self.ignoredKeys):
            self.elementTags = list(filter(lambda x: x['osmId'] != osmId or x['type'] != elementType or x['k'] != key, self.elementTags))
            self.elementTags.append( { 'osmId':osmId, 'type':elementType,'o':'modify', 'k':key, 'v':value } )        

    def addExistingTag( self, osmId, elementType, key,value):        
        if ( not key in self.ignoredKeys):    
            self.elementTags = list(filter(lambda x: x['osmId'] != osmId or x['type'] != elementType or x['k'] != key, self.elementTags))
            self.elementTags.append( { 'osmId':osmId, 'type':elementType,'o':'none', 'k':key, 'v':value } )        

    def diffObject( self, previousVersion, newVersion, osmId, elementType):
        lastTags = {}

        if int(previousVersion) < 1:
            raise Exception('previousVersion {} < 1'.format(previousVersion))        
        if int(previousVersion) >= int(newVersion) :
            raise Exception('previousVersion,newVersion {}>={}'.format(previousVersion,newVersion))        

        print("diffObject({},{},{},{})".format(previousVersion, newVersion, osmId, elementType))

        urlHistory = "{}/api/0.6/{}/{}/history".format(osmApiBase,elementType,osmId)

        history = self.urlRequest(urlHistory )
                                
        for revision in history:
            currentTags = {}

            for tag in revision:
                if ( tag.tag == 'tag'):
                    currentTags[tag.attrib['k']] = tag.attrib['v']

            if ( revision.attrib['version'] == previousVersion ):
                lastTags = currentTags

            if ( revision.attrib['version'] == newVersion ):
                for k in currentTags:
                    if ( not k in lastTags) :
                        self.addAddTag( osmId, elementType,k,currentTags[k])                                        
                    elif ( currentTags[k] != lastTags[k]):
                        self.addModifyTag( osmId,elementType,k,currentTags[k])
                    else:
                        self.addExistingTag( osmId,elementType,k,currentTags[k])
                        

    def download(self):
        self.metaTags = {}
        self.elementTags = []

        metaData = "{}/api/0.6/changeset/{}".format(osmApiBase,self.id)
        dump = "{}/api/0.6/changeset/{}/download".format(osmApiBase,self.id)

        body = self.urlRequest(metaData )
        
        for changeset in body.iterfind('changeset'):
            for tag in changeset.iterfind('tag'):
                self.metaTags[ tag.attrib['k'] ] = tag.attrib['v']

        body = self.urlRequest(dump )

        modifiedNodesRevs = {}
        modifiedWaysRevs = {}
        modifiedRelationsRevs = {}

        for create in body.iterfind('delete'):
            for node in create.iterfind('node'):
                self.nodesDeleted += 1
            for node in create.iterfind('way'):
                self.waysDeleted += 1
            for node in create.iterfind('relation'):
                self.relationsDeleted += 1

        # This function is complicated, because a single changset can have many versions of the 
        # same object in it. It can even create an object, then modify it many times.
        # we only care about the changes made at the boundary of the changeset, not the changes 
        # within the changeset, so these internal versions need to be collapsed. 

        for create in body.iterfind('create'):

            for node in create.iterfind('node'):
                self.nodesAdded += 1

                id = node.attrib['id']
                modifiedNodesRevs[id] = (1,1)
                
                for tag in node:
                    if ( tag.tag == 'tag'):                        
                        self.addAddTag( node.attrib['id'],'node',tag.attrib['k'],tag.attrib['v'])
            for node in create.iterfind('way'):
                self.waysAdded += 1

                id = node.attrib['id']
                modifiedWaysRevs[id] = (1,1)

                for tag in node:
                    if ( tag.tag == 'tag'):                        
                        self.addAddTag( node.attrib['id'],'way',tag.attrib['k'],tag.attrib['v'])
            for node in create.iterfind('relation'):
                self.relationsAdded += 1

                id = node.attrib['id']
                modifiedRelationsRevs[id] = (1,1)
                
                for tag in node:
                    if ( tag.tag == 'tag'):                        
                        self.addAddTag( node.attrib['id'],'relation',tag.attrib['k'],tag.attrib['v'])

        for create in body.iterfind('modify'):

            for element in create.iterfind('node'):

                id = element.attrib['id']
                version = element.attrib['version']
                
                if ( id in modifiedNodesRevs ):
                    modifiedNodesRevs[id] = (modifiedNodesRevs[id][0],version)
                else:
                    modifiedNodesRevs[id] = (version,version)

            for element in create.iterfind('way'):

                id = element.attrib['id']
                version = element.attrib['version']

                if ( id in modifiedWaysRevs ):
                    modifiedWaysRevs[id] = (modifiedWaysRevs[id][0],version)
                else:
                    modifiedWaysRevs[id] = (version,version)

            for element in create.iterfind('relation'):

                id = element.attrib['id']
                version = element.attrib['version']

                if ( id in modifiedWaysRevs ):
                    modifiedRelationsRevs[id] = (modifiedRelationsRevs[id][0],version)
                else:
                    modifiedRelationsRevs[id] = (version,version)
        
        for id in modifiedNodesRevs:
            prevRev = int(modifiedNodesRevs[id][0])-1
            lastRev = modifiedNodesRevs[id][1]
            if ( prevRev > 0 ):
                
                # cheap shortcut, nodes without tags don't diff them. 
                tagCount = 0

                for create in body.iterfind('modify'):
                    for element in create.iterfind('node'):
                        if ( element.attrib['id'] == id and element.attrib['version']==lastRev):
                            for tag in element:
                                if ( tag.tag == 'tag'):                        
                                    tagCount += 1
                
                if ( tagCount > 0 ):
                    self.nodesModified += 1
                    self.diffObject(str(prevRev) ,lastRev ,id,'node')
            else:
                for create in body.iterfind('modify'):
                    for element in create.iterfind('node'):
                        if ( element.attrib['id'] == id and element.attrib['version']==lastRev):
                            for tag in element:
                                if ( tag.tag == 'tag'):                        
                                    self.addAddTag( element.attrib['id'],'node',tag.attrib['k'],tag.attrib['v'])


        for id in modifiedWaysRevs:
            prevRev = int(modifiedWaysRevs[id][0])-1
            lastRev = modifiedWaysRevs[id][1]
            if ( prevRev > 0 ):
                self.waysModified += 1
                self.diffObject( str(prevRev), lastRev,id,'way')
            else:
                for create in body.iterfind('modify'):
                    for element in create.iterfind('way'):
                        if ( element.attrib['id'] == id and element.attrib['version']==lastRev):
                            for tag in element:
                                if ( tag.tag == 'tag'):                        
                                    self.addAddTag( element.attrib['id'],'way',tag.attrib['k'],tag.attrib['v'])

        for id in modifiedRelationsRevs:
            prevRev = int(modifiedRelationsRevs[id][0])-1
            lastRev = modifiedRelationsRevs[id][1]
            if ( prevRev > 0 ):
                self.relationsModified += 1
                self.diffObject( str(prevRev), lastRev,id,'relation')
            else:
                for create in body.iterfind('modify'):
                    for element in create.iterfind('relation'):
                        if ( element.attrib['id'] == id and element.attrib['version']==lastRev):
                            for tag in element:
                                if ( tag.tag == 'tag'):                        
                                    self.addAddTag( element.attrib['id'],'relation',tag.attrib['k'],tag.attrib['v'])
            
    def save(self):  
        self.saveFile(self.cacheFileName())

    def indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def saveFile(self,filename):

        a = ET.Element('changeset')
        tree = ET.ElementTree(a)

        a.attrib = { 'schema':fileCacheVersion, 'id': self.id}
    
        counts = ET.SubElement(a, 'counts')
        counts.attrib = { 
            'nodesAdded':str(self.nodesAdded), 
            'waysAdded':str(self.waysAdded),
            'relationsAdded':str(self.relationsAdded),
            'nodesModified':str(self.nodesModified),
            'waysModified':str(self.waysModified),
            'relationsModified':str(self.relationsModified),
            'nodesDeleted':str(self.nodesDeleted),
            'waysDeleted':str(self.waysDeleted),
            'relationsDeleted':str(self.relationsDeleted)
        }

        meta = ET.SubElement(a, 'meta')
        for tag in sorted( self.metaTags ) :
            t = ET.SubElement( meta, 'tag')
            t.attrib = { 'k':tag,'v':self.metaTags[tag] }

        body = ET.SubElement(a, 'body')
        for tag in self.elementTags  :
            t = ET.SubElement( body, 'tag')
            t.attrib = { 'id':tag['osmId'],'type':tag['type'],'o':tag['o'],'k':tag['k'],'v':tag['v'] }

        self.indent(a)

        tree.write(filename)


    def cached(self):
        if ( self.fileVersionOK( self.cacheFileName()) or 
             self.fileVersionOK( self.cacheRuntimeFileName())): 
            return True
        
        return False


    def fileVersionOK(self,filename):
        try:
            tree = ET.parse(filename)
            n =tree.getroot()
            if ( 'schema' in n.attrib and n.attrib['schema'] <= fileCacheVersion):
                return True
        except:
            return False

        return False
        
    def read(self):
        if ( self.fileVersionOK( self.cacheFileName())) :
            self.readFile( self.cacheFileName())
        elif ( self.fileVersionOK( self.cacheRuntimeFileName())):
            self.readFile( self.cacheRuntimeFileName())
            
    def readFile(self, filename):

        self.metaTags = {}
        self.elementTags = []

        #try:
        tree = ET.parse(filename)
        n =tree.getroot()

        counts = n.find('counts')

        self.nodesAdded = int(counts.attrib['nodesAdded'])
        self.waysAdded = int(counts.attrib['waysAdded'])
        self.relationsAdded = int(counts.attrib['relationsAdded'])

        self.nodesModified = int(counts.attrib['nodesModified'])
        self.waysModified = int(counts.attrib['waysModified'])
        self.relationsModified = int(counts.attrib['relationsModified'])

        if ( int(n.attrib['schema']) > 1 ):
            self.nodesDeleted = int(counts.attrib['nodesDeleted'])
            self.waysDeleted = int(counts.attrib['waysDeleted'])
            self.relationsDeleted = int(counts.attrib['relationsDeleted'])
        else:
            self.nodesDeleted = 0
            self.waysDeleted = 0
            self.relationsDeleted = 0

        for meta in n.findall('meta'):
            for tag in meta:
                self.metaTags[tag.attrib['k']] = tag.attrib['v']

        for body in n.findall('body'):
            for tag in body:
                t = { 
                    'osmId':tag.attrib['id'],
                    'type':tag.attrib['type'],
                    'o':tag.attrib['o'],
                    'k':tag.attrib['k'],
                    'v':tag.attrib['v']
                }
                self.elementTags.append( t )
                

    def textDumpHuman(self):

        ret = 'https://www.openstreetmap.org/changeset/{}\n'.format(self.id)

        ret += "Added    {},{},{}\n".format(self.nodesAdded,self.waysAdded,self.relationsAdded   ) 
        ret += "Modified {},{},{}\n".format(self.nodesModified,self.waysModified,self.relationsModified)
        ret += "Deleted  {},{},{}\n".format(self.nodesDeleted,self.waysDeleted,self.relationsDeleted )

        ret += "\nmeta\n"
        for tag in sorted(self.metaTags) :
            ret += "  {}={}\n".format(tag, self.metaTags[tag])

        ret += "\nbody\n"
        for tag in self.elementTags  :
            if ( tag['o'] == 'add'):
                line = "  " + tag['o'] + " "
                firstKey = tag['k'].split(':')[0]
                if ( re.match(r'[a-z]+',firstKey) is None):
                    line += "BAD "
                if ( re.search(r'[A-Z]+',firstKey) is not None):
                    line += "caps "                    
                line += "{}={}\n".format(tag['k'],tag['v'])
                if ( ret.find(line) < 0 ):
                    ret += line

        for tag in self.elementTags  :
             if( tag['o'] == 'modify'):
                line = "  " + tag['o'] + " "
                line += "{}={}\n".format(tag['k'],tag['v'])
                if ( ret.find(line) < 0 ):
                    ret += line
        
        return ret


    def textDump(self, maxCount):

        ret = ''

        ret += "Added {},{},{}\n".format(self.nodesAdded,self.waysAdded,self.relationsAdded   ) 
        ret += "Modified {},{},{}\n".format(self.nodesModified,self.waysModified,self.relationsModified)
        ret += "Deleted {},{},{}\n".format(self.nodesDeleted,self.waysDeleted,self.relationsDeleted )

        for tag in sorted(self.metaTags) :
            ret += "meta "
            ret += ' '.join(re.split(r"[-_:]+", tag)) + " "
            ret += ' '.join(re.split(r"[-_:\"'`]+", self.metaTags[tag])) + " \n"

        retList = []

        usedTags = []
        for tag in self.elementTags  :
            if ( tag['o'] == 'add' or tag['o'] == 'modify'):
                usedTags.append(tag)

        sortIndex = list(range(0,len(usedTags)))

        realMaxCount = math.factorial(len(sortIndex))
        actualCount = min(maxCount,realMaxCount)
        for rr in range(0, actualCount ):
            retCycle = ret

            for i in sortIndex:
                tag = usedTags[i]                
                retCycle += tag['o'] + " "

                firstKey = tag['k'].split(':')[0]
                if ( re.match(r'[a-z_]+',firstKey) is None):
                    retCycle += "bad "
                if ( re.search(r'[A-Z]+',firstKey) is not None):
                    retCycle += "capital "                    
                
                #ret += tag['type'] + " "
                retCycle += tag['k'] + " " 
                retCycle += tag['v'] + " \n"
            
            retCycle += "\n"

            retList.append( retCycle)

            random.shuffle(sortIndex)

        return retList

    #def __repr__(self):
    #    return "{}".format( self.id)


