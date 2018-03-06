import xml.etree.ElementTree as ET
import urllib
import re

fileCacheVersion = '1'
osmApiBase =  "https://api.openstreetmap.org"

class ChangeSet:

    def __init__(self, id):

        self.id = id
        self.metaTags = {}
        self.elementTags = []

        self.nodesAdded = 0
        self.waysAdded = 0
        self.relationsAdded = 0
        
        self.nodesModified = 0
        self.waysModified = 0
        self.relationsModified = 0

    def cacheFileName(self):
        return "trainingdata/cache/{}.xml".format(self.id)

    def addAddTag( self, osmId, elementType, key,value):        
        self.elementTags.append( { 'osmId':osmId, 'type':elementType,'o':'add', 'k':key, 'v':value } )        
    def addModifyTag( self, osmId, elementType, key,value):        
        self.elementTags.append( { 'osmId':osmId, 'type':elementType,'o':'modify', 'k':key, 'v':value } )        

    def diffObject( self, baselineVersion, osmId, elementType):
        lastTags = {}

        urlHistory = "{}/api/0.6/{}/{}/history".format(osmApiBase,elementType,osmId)

        with urllib.request.urlopen(urlHistory) as historyResp:
            historyStr = historyResp.read()
            history = ET.fromstring(historyStr)
                                
            for revision in history:
                currentTags = {}
                for tag in revision:
                    if ( tag.tag == 'tag'):
                        currentTags[tag.attrib['k']] = tag.attrib['v']

                if ( revision.attrib['version'] == baselineVersion ):
                    for k in currentTags:
                        if ( not k in lastTags) :
                            self.addAddTag( osmId, elementType,k,currentTags[k])                                        
                        elif ( currentTags[k] != lastTags[k]):
                            self.addModifyTag( osmId,elementType,k,currentTags[k])
                            
                    break

                lastTags = currentTags

    def download(self):
        self.metaTags = {}
        self.elementTags = []

        metaData = "{}/api/0.6/changeset/{}".format(osmApiBase,self.id)
        dump = "{}/api/0.6/changeset/{}/download".format(osmApiBase,self.id)
        with urllib.request.urlopen(metaData) as response:
            bodyStr = response.read()
            body = ET.fromstring(bodyStr)

            for changeset in body.iterfind('changeset'):
                for tag in changeset.iterfind('tag'):
                    self.metaTags[ tag.attrib['k'] ] = tag.attrib['v']
        
        with urllib.request.urlopen(dump) as response:
            bodyStr = response.read()
            body = ET.fromstring(bodyStr)

            for create in body.iterfind('create'):

                for node in create.iterfind('node'):
                    self.nodesAdded += 1
                    for tag in node:
                        if ( tag.tag == 'tag'):                        
                            self.addAddTag( node.attrib['id'],'node',tag.attrib['k'],tag.attrib['v'])
                for node in create.iterfind('way'):
                    self.waysAdded += 1
                    for tag in node:
                        if ( tag.tag == 'tag'):                        
                            self.addAddTag( node.attrib['id'],'way',tag.attrib['k'],tag.attrib['v'])
                for node in create.iterfind('relation'):
                    self.relationsAdded += 1
                    for tag in node:
                        if ( tag.tag == 'tag'):                        
                            self.addAddTag( node.attrib['id'],'relation',tag.attrib['k'],tag.attrib['v'])

            for create in body.iterfind('modify'):

                for element in create.iterfind('node'):
                    self.nodesModified += 1
                    self.diffObject( element.attrib['version'],element.attrib['id'],'node')

                for element in create.iterfind('way'):
                    self.waysModified += 1
                    self.diffObject(element.attrib['version'],element.attrib['id'],'way')

                for element in create.iterfind('relation'):
                    self.relationsModified += 1
                    self.diffObject(element.attrib['version'],element.attrib['id'],'relation')
                
    def save(self):            

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
            'relationsModified':str(self.relationsModified)
        }

        meta = ET.SubElement(a, 'meta')
        for tag in sorted( self.metaTags ) :
            t = ET.SubElement( meta, 'tag')
            t.attrib = { 'k':tag,'v':self.metaTags[tag] }

        body = ET.SubElement(a, 'body')
        for tag in self.elementTags  :
            t = ET.SubElement( body, 'tag')
            t.attrib = { 'id':tag['osmId'],'type':tag['type'],'o':tag['o'],'k':tag['k'],'v':tag['v'] }

        tree.write(self.cacheFileName())

    def cached(self):
        try:
            tree = ET.parse(self.cacheFileName())
            n =tree.getroot()
            if ( 'schema' in n.attrib and n.attrib['schema'] == fileCacheVersion):
                return True
        except:
            return False

        return False
        
    def read(self):
        self.metaTags = {}
        self.elementTags = []

        #try:
        tree = ET.parse(self.cacheFileName())
        n =tree.getroot()

        counts = n.find('counts')

        self.nodesAdded = int(counts.attrib['nodesAdded'])
        self.wayAdded = int(counts.attrib['waysAdded'])
        self.relationAdded = int(counts.attrib['relationsAdded'])

        self.nodesModified = int(counts.attrib['nodesModified'])
        self.wayModified = int(counts.attrib['waysModified'])
        self.relationModified = int(counts.attrib['relationsModified'])

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
                

    def textDump(self):

        ret = ''

        for tag in sorted(self.metaTags) :
            ret += "meta "
            ret += ' '.join(re.split(r"[-_:]+", tag)) + " "
            ret += ' '.join(re.split(r"[-_:\"'`]+", self.metaTags[tag])) + " \n"

        for tag in self.elementTags  :
            ret += tag['o'] + " "
            #ret += tag['type'] + " "
            ret += ' '.join(re.split(r"[-_:\"'`]+", tag['k'])) + " " 
            ret += ' '.join(re.split(r"[-_:\"'`]+", tag['v'])) + " \n"
        
        ret += "\n"

        ret = re.sub(r" [0-9]+ "," number ",ret)
        ret = re.sub(r" addr "," address ",ret)

        return ret

    #def __repr__(self):
    #    return "{}".format( self.id)


