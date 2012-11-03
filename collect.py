import redis
import json
import os
import shutil
import time
import subprocess

# please run from fairing-factory directory
# do not run more than one of this process.

r = redis.StrictRedis(host='localhost', port=6379, db=0)
kits_data = 'data/'
public_dir = '/var/www/Fairing-Factory/kits/'


# consume asset receipts
while True:
    rep = json.laods(r.brpop('asset_receipts'))
    kitid = rep['kitid']
    partid = rep['partid']
    
    # pull down the kit tracker for this part
    kittracker = json.loads(r.get('kit-trackers:'+kitid))

    # set this part finished
    kittracker['parts-finished'][rep['partid']] = True

    if all(kittracker['parts-finished'].values()):
        # kit is finished. 
        kitdir = kittracker['kitdir']

        # zip it
        zipfilename = kitdir+'.zip'
        dest = os.path.join(public_dir, zipfilename)
        os.chdir('data')
        subprocess.check_call(['zip','-r','-9',dest,kitdir])
        os.chdir('..')
        
        took = time.time() - kittracker['time-submitted']
        print "Created Kit %s in %0.3f seconds." % (kitid, took) 
        r.delete('kit-trackers:'+kitid)


    else:
        r.set('kit-trackers:'+kitid, json.dumps(kittracker))
