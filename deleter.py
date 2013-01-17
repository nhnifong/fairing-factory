import sys
import os
import shutil
import time
from datetime import datetime, timedelta

trdir = sys.argv[1]

def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.fromtimestamp(t)

while True:
    # remove all files older than 24 hours
    for filename in os.listdir(trdir):
        fullname = os.path.join(trdir, filename)
        age = datetime.now() - modification_date(fullname)
        if age > timedelta(days=1):
            print 'removing %s, age: %r' % (fullname, age) 
            os.remove(fullname)
    time.sleep(60*60)
