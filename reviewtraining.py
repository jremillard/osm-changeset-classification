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


def validateChangeset(i, row, changesetsCsv, cs, note):
    print("-------------------------------------------------")   
    print(cs.textDumpHuman())
    print(",".join(row))
    if ( len(note) > 0 ):
        print(note)
    print("press space to leave it, s=SPAM, b=bad import, i=import, r=revert, e=error, n=Normal, any other quit ")

    k = getch()

    changesetsCsv[i][2] = 'Y'

    if ( k != ' ') :

        changesetsCsv[i][3] = 'N'
        changesetsCsv[i][4] = 'N'
        changesetsCsv[i][5] = 'N'
        changesetsCsv[i][6] = 'N'
        changesetsCsv[i][7] = 'N'

        if ( k == 'n'):
            True
        elif ( k == 's'):
            changesetsCsv[i][3] = 'Y'
        elif ( k == 'r'):
            changesetsCsv[i][4] = 'Y'
        elif ( k == 'b'):
            changesetsCsv[i][5] = 'Y'
        elif ( k == 'i'):
            changesetsCsv[i][6] = 'Y'
        elif ( k == 'e'):
            changesetsCsv[i][7] = 'Y'
        else :
            sys.exit(0)
        
    with open('trainingdata/changesets.csv', 'w', encoding='utf-8') as csvfile:
        changesetIds = {}
        csvfile.write("changeset,From,Validated,SPAM,Revert,Bad Import,Import,Mapping Error\n")
        for wrow in changesetsCsv:
            if ( wrow[0] not in changesetIds):
                changesetIds[wrow[0]] = 1
                csvfile.write(",".join(wrow) + "\n")
            else:
                print("removing duplicate changeset {}".format(wrow[0]))



changesetsCsv = []

with open('trainingdata/changesets.csv', newline='',encoding='utf-8') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')

    next(spamreader)

    for row in spamreader:
        changesetsCsv.append(row)

if ( len(sys.argv) > 1 ) :
    with open(sys.argv[1], mode="rt",encoding='utf-8') as csvfile:
        for line in csvfile:
            line = line.strip('\n')
            row = line.split(' ')
            id = row[0]
            note = " ".join(row[1:])

            for i,row in enumerate(changesetsCsv):
                if ( row[0] == id):
                    cs = osmcsclassify.ChangeSet.ChangeSet(row[0])
                    if ( cs.cached() ):
                        cs.read()
                        validateChangeset(i, row, changesetsCsv, cs,note)

else:

    unValidatedCount = 0
    for i,row in enumerate(changesetsCsv):
        if ( len(row[2] ) == 0 ):
            unValidatedCount += 1

    # looking for non-validated but downloaded changesets
    validated = 0
    for i,row in enumerate(changesetsCsv):
        if ( len(row[2]) == 0 or row[2] != 'Y' ):
            cs = osmcsclassify.ChangeSet.ChangeSet(row[0])
            if ( cs.cached() ):
                cs.read()
            else :
                #print("downloading {}".format(cs.id))
                #cs.download()
                #cs.save()
                continue

            validateChangeset(i, row, changesetsCsv, cs,"")


 