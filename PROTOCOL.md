### Definitions of json objects stored in redis
# note, this was written by hand and is probably not valid json. it's just a guide

#### fairing-kit-orders
    {
        'kitid': 12345,       # a unique monotonically increasing number taken from the redis key 'kitid-tick'
        'base-size': '2m',   # the diameter in meters of the base part. must be in the set ['hm', '1m', '2m', '3m', '5m']
        'texture': 'whiterivet', # one of the available named textures
        'time-submitted': 1351891592.06305, # the time the order was submitted in floating seconds since the epoch
        'sections': [ # a list of sections
            {
                'profile': [ # a list of up to 50 [height,radius] pairs (lists)
		    [0.0, 1.0], 
                    [0.4, 1.1],
                    [0.9, 1.1],
		    [1.0, 1.0]
                ],
                'capped': false # does this part form a cap (should it have connections nodes on top?
            },
            ... # up to 12 sections.
        ],
	'symmetry': 2 #2 or 4, but later 2,3,4,6,8
    }

the json object clients post to the API look just like the above without the kitid and time-submitted keys

#### part-orders
    {
        'kitid':   12345,  # the kit this part came from
        'partid':  0,      # the part number in this kit, numbered 0 and up from the bottom
	'partdir': 'kit_12345_section_0',    #the directory (relative to the kit dir) that will contain the part cfg and mu files.
        'profile': [...] # follows the same format as the profile key in a fairing-kit-order
	'texture': 'whiterivet' # same as above
        'capped': false # follows the same fomat as the capped key in a fairing-kit-order
	'symmetry': 2 # same as above
    }

#### part-receipts
    {
        'kitid': 12345,
        'partid': 0,
        'partdir': 'kit_12345_section_0' # yes I know that is redundant. but this is the definitive location, and the dir should not be constructed from the ids.
    }

#### kit-trackers
These will be keyed by 'kit-trackers:<kitid>'
    {
        'kitid':12345,
	'kitdir':'fairing_kit_12345' # the directory where the kit is being stored.
	'time-submitted': 1351891592.06305, # the time the order was submitted in floating seconds since the epoch
        'parts-finished': {
            '0':true,
	    '1':true,
            '2':false
        }
    }