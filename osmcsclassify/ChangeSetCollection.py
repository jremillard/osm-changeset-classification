import csv
import osmcsclassify.ChangeSet

class ChangeSetCollection:

    def __init__(self):

        self.rows = []
        self.labelsToIndex = {}
        self.indexToLabels = {}

        with open('trainingdata/changesets.csv', newline='',encoding='utf-8') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')

            row = next(spamreader)

            self.labelsToIndex['OK'] = 0
            self.indexToLabels[0] = 'OK'

            for r in row[3:]:
                label_id = len(self.labelsToIndex)
                self.labelsToIndex[r] = label_id       
                self.indexToLabels[label_id] = r
            
            for row in spamreader:
                if ( len(row[2]) > 0 and row[2] != 'Y'):
                    raise Exception("error for id {}, validation cell must be Y or empty, {}".format(row[0],row[2]))
                if ( len(row) != len(self.labelsToIndex)+3-1):
                    # -1 for OK
                    raise Exception("error for id {}, wrong number of category cells.".format(row[0]))
                    
                validated =  len(row[2]) > 0 and row[2] == 'Y'

                label_id = 0 # 'OK'
                for index in range(3, len(row)):
                    if ( row[index] == 'Y'):
                        label_id = index-2
                    elif ( row[index] == 'N'):
                        pass
                    else:
                        raise Exception("error for id {}, category cells must be Y,N".format(row[0]))
                                        
                cs = osmcsclassify.ChangeSet.ChangeSet(row[0])
                label = self.indexToLabels[label_id]

                self.rows.append( { 'cs':cs,'labelIndex':label_id,'validated':validated, 'note':row[1], 'label':label })


        
