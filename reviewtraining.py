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

changesetsCsv = []

with open('trainingdata/changesets.csv', newline='',encoding='utf-8') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')

    next(spamreader)

    for row in spamreader:
        changesetsCsv.append(row)

unValidatedCount = 0
for i,row in enumerate(changesetsCsv):
    if ( len(row[2] ) == 0 ):
        unValidatedCount += 1

validated = 0
for i,row in enumerate(changesetsCsv):
    if ( len(row[2] ) == 0 ):
        cs = osmcsclassify.ChangeSet.ChangeSet(row[0])
        if ( cs.cached() ):
            cs.read()
        else :
            print("downloading {}".format(cs.id))
            cs.download()
            cs.save()

        print("-------------------------------------------------")   
        print(cs.textDump())
        print(",".join(row))
        print("press space to leave it, s=SPAM, i=import, r=revert, e=error, n=Normal, any other quit {:0.0f}% complete".format( 100.0*validated/unValidatedCount ))

        k = getch()

        changesetsCsv[i][2] = 'Y'

        if ( k != ' ') :

            changesetsCsv[i][3] = 'N'
            changesetsCsv[i][4] = 'N'
            changesetsCsv[i][5] = 'N'
            changesetsCsv[i][6] = 'N'

            if ( k == 'n'):
                True
            elif ( k == 's'):
                changesetsCsv[i][3] = 'Y'
            elif ( k == 'r'):
                changesetsCsv[i][4] = 'Y'
            elif ( k == 'i'):
                changesetsCsv[i][5] = 'Y'
            elif ( k == 'e'):
                changesetsCsv[i][6] = 'Y'
            else 
                sys.exit(0)
            
        validated += 1

        with open('trainingdata/changesets.csv', 'w', encoding='utf-8') as csvfile:
            csvfile.write("changeset,From,Validated,SPAM,Revert,Bad Import,Mapping Error\n")
            for wrow in changesetsCsv:
                csvfile.write(",".join(wrow) + "\n")

 