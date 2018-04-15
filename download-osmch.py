import urllib.request
import json

count = 0

with urllib.request.urlopen('https://osmcha.mapbox.com/api/v1/changesets/harmful/?page=1&page_size=100&checked=1&harmful=1') as Iresponse:
    resp = json.load(Iresponse)

    count = resp['count']

pageSize = 100
pageCount = int(count/pageSize)+2

for page in range( 1,pageCount ):
    with urllib.request.urlopen('https://osmcha.mapbox.com/api/v1/changesets/harmful/?page={}&page_size=100&checked=1&harmful=1'.format(page)) as Iresponse:
        resp = json.load(Iresponse)

        for cs in resp['features']:
            p = cs['properties']
            for t in p['tags']:
                if ( t['id'] == 1):
                    print("{},OSMCha,,Y,N,N".format(cs['id']))

