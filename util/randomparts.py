import json
import redis
from random import random,randint
from pprint import pprint

r = redis.StrictRedis(host='localhost', port=6379, db=0)


def randprofile():
    prop = []
    height = 0
    radius = 1.0
    for i in range(randint(3,10)):
        radius += random()*0.3-0.15
        prop.append([height,radius])
        height += random()*0.5
    return prop

po = {}
po['capped'] = False
po['texture'] = 'whiterivet'
po['kitid'] = 1
po['partid'] = 0
po['partdir'] = 'testpart'
po['profile'] = randprofile()


pprint(po)
r.lpush('part-orders', json.dumps(po))
