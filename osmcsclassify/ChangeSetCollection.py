import csv
import osmcsclassify.ChangeSet


class ChangeSetCollection:

    def __init__(self):

        self.rows = []
        self.labelsToIndex = {}
        self.indexToLabels = {}

        self.labelsToIndex['OK'] = 0
        self.indexToLabels[0] = 'OK'
        
        # first column that has data in
        firstDataCol = 3

        with open('trainingdata/changesets.csv', newline='',encoding='utf-8') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')

            row = next(spamreader)

            for r in row[firstDataCol:]:
                label_id = len(self.labelsToIndex)
                self.labelsToIndex[r] = label_id       
                self.indexToLabels[label_id] = r
            
            for row in spamreader:
                if ( len(row[2]) > 0 and row[2] != 'Y'):
                    raise Exception("error for id {}, validation cell must be Y or empty, {}".format(row[0],row[2]))
                if ( len(row) != len(self.labelsToIndex)+firstDataCol-1):
                    # -1 for OK
                    raise Exception("error for id {}, wrong number of category cells.".format(row[0]))
                    
                validated = len(row[2]) > 0 and row[2] == 'Y'

                labels = [0] * len( self.indexToLabels)

                ok = True
                for index in range(firstDataCol, len(row)):
                    if ( row[index] == 'Y'):
                        ok = False
                        labels[index-firstDataCol+1] = 1
                    elif ( row[index] == 'N'):
                        pass
                    else:
                        raise Exception("error for id {}, category cells must be Y,N".format(row[0]))

                if ( ok):
                    labels[0] = 1
                                        
                cs = osmcsclassify.ChangeSet.ChangeSet(row[0])

                self.rows.append( { 'cs':cs,'labels':labels,'validated':validated, 'note':row[1]  })

    def save(self):

        with open('trainingdata/changesets.csv', 'w', encoding='utf-8') as csvfile:
            changesetIds = {}
            csvfile.write("changeset,From,Validated,SPAM,Import,Tagging Error\n")
            for row in self.rows:
                changesetId = row['cs'].id

                if ( changesetId not in changesetIds):
                    validatedY = ''
                    if ( row['validated'] ):
                        validatedY = 'Y'

                    wrow = [ changesetId, row['note'], validatedY ]

                    # 1=skip OK
                    for i in range( 1, len(self.indexToLabels)):
                        if ( row['labels'][i] > 0.5):
                            wrow.append('Y')
                        else:
                            wrow.append('N')
                            
                    csvfile.write(",".join(wrow) + "\n")

                    changesetIds[changesetId] = 1

        
