import redis
import json
import os
import shutil
import time
import subprocess

r = redis.StrictRedis(host='localhost', port=6379, db=0)
kits_data = 'data/'

# do not run more than one of this script.

while True:
    rec = r.brpop('part-receipts')[1]
    if rec is None: continue
    print repr(rec)
    rec = json.loads(rec)
    
    kitid = rec['kitid']
    partid = rec['partid']
    partdir = rec['partdir']
    
    trkey = 'kit-trackers:'+str(kitid)
    tracker = r.get(trkey)
    if tracker is None: continue
    tracker = json.loads(tracker)
    kitdir = tracker['kitdir']

    pf = tracker['parts-finished']
    pf[str(partid)] = True
    
    if all(pf.values()):
        # all parts are finished
        os.chdir('data')

        kitzip = kitdir + '.zip'
        # -r for recursive
        # -9 for best compression
        # -m to delete original (move)
        download_dir = '/var/www/FairingFactory/downloads'
        dkitzip = os.path.join(download_dir, kitzip)
        subprocess.check_call(['zip','-r','-9','-m',dkitzip,kitdir])

        os.chdir('..')

        # delete kit tracker from redis
        r.delete(trkey)

        took = time.time() - float(tracker['time-submitted'])
        print "finished kit in %0.4f seconds" % took
    
    else:
        # return the kit tracker to redis
        r.set(trkey, json.dumps(tracker))








