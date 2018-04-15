import os
import sys
import glob
import csv
import osmcsclassify

def _find_getch():
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys, tty
    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch

getch = _find_getch()


def validateChangeset(changeSets, row,note):

    cs = row['cs']

    print("-------------------------------------------------")   
    for i, labelValue  in enumerate(row['labels']) :
        if ( labelValue > 0.5 ) :
            print( "{},".format(changeSets.indexToLabels[i]), end='')
    print("note = {}".format(note))

    print(cs.textDumpHuman())
    #print(cs.textDump(1)[0])
    print("press space to leave it, s=SPAM, p=SPAM Bad Tagging, i=Import,b=Import Bad Tagging, t=Bad Tagging, n=Normal, any other quit ")

    k = getch()

    if ( k != ' ') :

        labels = [0] * len( changeSets.indexToLabels)

        if ( k == 'n'):
            pass
        elif ( k == 's'):
            labels[ changeSets.labelsToIndex['SPAM']] = 1
        elif ( k == 'p'):
            labels[ changeSets.labelsToIndex['SPAM']] = 1
            labels[ changeSets.labelsToIndex['Tagging Error']] = 1            
        elif ( k == 'i'):
            labels[ changeSets.labelsToIndex['Import']] = 1
        elif ( k == 'b'):
            labels[ changeSets.labelsToIndex['Import']] = 1
            labels[ changeSets.labelsToIndex['Tagging Error']] = 1            
        elif ( k == 't'):
            labels[ changeSets.labelsToIndex['Tagging Error']] = 1            
        else :
            sys.exit(0)

        row['labels'] = labels
        row['validated'] = True

        changeSets.save()
        

changeSets = osmcsclassify.ChangeSetCollection.ChangeSetCollection()

if ( len(sys.argv) > 1 ) :
    with open(sys.argv[1], mode="rt",encoding='utf-8') as csvfile:
        for line in csvfile:
            line = line.strip('\n')
            row = line.split(' ')
            id = row[0]
            note = " ".join(row[1:])

            for wrow in changeSets.rows:
                cs = wrow['cs']
                if ( cs.id == id):
                    if ( cs.cached() ):
                        cs.read()
                        validateChangeset(changeSets, wrow, note)

else:

    i = len(changeSets.rows)

    while ( i > 0 ):

        # newest changsets are at the end.
        i = i-1

        # re-read it so that find changesets can be run at the same time.
        #changeSets = osmcsclassify.ChangeSetCollection.ChangeSetCollection()

        row = changeSets.rows[i]
        if ( row['validated'] == False):
            cs = row['cs']
            if ( cs.cached() ):
                cs.read()
            else :
                #print("downloading {}".format(cs.id))
                #cs.download()
                #cs.save()
                continue

            validateChangeset(changeSets, row,row['note'])


 