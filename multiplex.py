import redis
import json
import os
import shutil

# please run from fairing-factory directory

r = redis.StrictRedis(host='localhost', port=6379, db=0)
kits_data = 'data/'
bases = 'premade/'

def partflags(n):
    flags = {}
    for i in range(n):
        flags[str(i)] = False
    return flags

# consume fairing kit orders
while True:
    b = r.brpop('fairing-kit-orders')
    print repr(b)
    order = json.loads(b[1])
    kitid = order['kitid']

    # create new kit directory from kitid
    kitdir = 'fairing_kit_%s' % kitid
    os.mkdir(os.path.join(kits_data,kitdir))
    
    # copy in the appropriate base part
    basepart = '_'.join(['ffkits', order['base-size'], order['texture']])
    base_part_path = os.path.join(bases,basepart)
    shutil.copytree(base_part_path, os.path.join(kits_data,kitdir,basepart))
    
    # create a kit tracker
    kittracker = {
        'kitid': kitid,
        'kitdir': kitdir,
        'time-submitted':order['time-submitted'],
        'parts-finished':partflags(len(order['sections']))
        }
    r.set('kit-trackers:'+str(kitid), json.dumps(kittracker))
    r.expire('kit-trackers:'+str(kitid), 60*60*24*7)

    for i,section in enumerate(order['sections']):
        # create a new part directory for each part inside the kit directory
        partdir = 'ffkits_%s_section_%i' % (kitid,i)
        complete_path = os.path.join( kits_data, kitdir, partdir )
        print complete_path
        os.mkdir(complete_path)

        # create a mesh folder and a texture folder
        os.mkdir(os.path.join(complete_path,'mesh'))
        texdir = os.path.join(complete_path,'textures')
        os.mkdir(texdir)
        
        # copy the texture in
        otexdir = 'textures'
        otexfile = os.path.join(otexdir, order['texture']+'.png')
        shutil.copy(otexfile, texdir)

        # create the part order
        partorder = {
            'kitid': kitid,
            'partid': i,
            'partdir': partdir,
            'profile': section['profile'],
            'texture': order['texture'],
            'capped': section['capped']
            }
        r.lpush('part-orders', json.dumps(partorder))
