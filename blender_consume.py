import bpy
import bmesh
from bpy_extras import object_utils
from mathutils import *
from math import *
import redis
import json
import os
import time
from optparse import OptionParser

conf = json.loads(open('config/develop.json').read())

def add_fairing(profile):
    """
    This function takes inputs and returns vertex and face arrays.
    no actual mesh data creation is done here.
    """

    vertices = [] # a list of tuples
    faces = [] # a list of tuples
    
    bottomnode = None
    topnode = None
    
    mid = (profile[0][0] + profile[-1][0]) / 2
    avgradius = (profile[0][1] + profile[-1][1]) / 2
    
    for v,row in enumerate(profile):
        height = row[0]
        radius = row[1]
        ket = 13
        center = (avgradius, 0.0, 0.0)
        # create a semicircle 
        for a,angle in enumerate([(j/(ket-1))*pi for j in range(ket)]):
                point = (-sin(angle) * radius + center[0],
                         cos(angle) * radius + center[1],
                         height-mid + center[2])
                if a==6:
                    if v==0:
                        bottomnode = point
                        print("bottom node = %s" % repr(bottomnode))
                    if v==(len(profile)-1):
                        topnode = point
                        print("top node = %s" % repr(topnode))
                vertices.append(point) 

    tex_faces = []

    for t in range(len(profile)-1):
        for i in range(12):
            quad = [
                i+1+ket*t,
                i+ket*t,
                i+ket*(t+1),
                i+1+ket*(t+1)
            ]
            faces.append(quad)
            
            # there is a texture for large parts and one for small parts
            # the large on is below the border. mind the the origin of the uvmap is in the lower left.
            
            border_y = 0.8828125
            # top section is 120 pixels high for a texture of 1024x1024
            
            d_height = profile[t+1][0] - profile[t][0]
            d_radius = profile[t+1][1] - profile[t][1]
            section_size = sqrt(d_height**2 + (d_radius)**2)
            if section_size > 0.08:
                che = min(border_y, section_size/2)
                tf = [
                    ((i+1)/12, che),
                    ((i)/12,   che),
                    ((i)/12,   0),
                    ((i+1)/12, 0),
                ]
            else:
                tf = [
                    ((i+1)/12, 1),
                    ((i)/12,   1),
                    ((i)/12,   border_y),
                    ((i+1)/12, border_y),
                ]
            tex_faces.append(tf)
            
    #texFaces = [
    #    [(0.732051,0), (1,0), (0.541778,1)],
    #    [(0.541778,1), (0,0), (0.732051,0)],
    #    [(0.541778,1), (1,0), (0,0)],
    #    [(1,0), (0.732051,0), (0,0)]
    #]
    
    return vertices, faces, tex_faces, topnode, bottomnode


def execute(r):
    
    res = r.brpop(conf['redis-prefix']+':part-orders')[1]

    if not res: return
    
    # remove prior parts
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    po = json.loads(res.decode())
        
    verts_loc, faces, tex_faces, tnode, bnode = add_fairing(po['profile'])
    
    print('I made %i faces' % len(faces))

    mesh = bpy.data.meshes.new("Fairing")
    mesh.uv_textures.new()
    bm = bmesh.new()

    for v_co in verts_loc:
        bm.verts.new(v_co)

    for f_idx in faces:
        bm.faces.new([bm.verts[i] for i in f_idx])
        
    # set uv coords (bmesh way)
    if bm.loops.layers.uv.items():
        uv_layer = bm.loops.layers.uv.active
    else:
        uv_layer = bm.loops.layers.uv.new()
    
    print('numfaces: %i, numuvfaces: %i' % (len(bm.faces), len(tex_faces)))
    for n,face in enumerate(bm.faces):
        #print("-face-")
        for m,loop in enumerate(face.loops):
            pass
            myuv = tex_faces[n][m]
            loop[uv_layer].uv.x = myuv[0]
            loop[uv_layer].uv.y = myuv[1]
            
    if bm.faces.layers.tex.items():
        tex_layer = bm.faces.layers.tex[0]
    else:
        tex_layer = bm.faces.layers.tex.new()
    
    
    # update mesh with new coords
    bm.to_mesh(mesh)
    mesh.update()

    # add the mesh as an object into the scene with this utility module
    object_utils.object_data_add(bpy.context, mesh)
    visible_mesh = bpy.context.selected_objects[0].name
    
    # add the soldify modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    bpy.data.objects[visible_mesh].modifiers['Solidify'].thickness = -0.04
    # apply it
    bpy.ops.object.modifier_apply(modifier='Solidify')
    # add an edge split modifier
    bpy.ops.object.modifier_add(type='EDGE_SPLIT')
    bpy.data.objects[visible_mesh].modifiers['EdgeSplit'].split_angle = 0.418879 #radians, 24 degrees
    # set smooth
    bpy.ops.object.shade_smooth()
    # apply it
    bpy.ops.object.modifier_apply(modifier='EdgeSplit')
    
    # move it to origin if thats not already where it is
    bpy.data.objects[visible_mesh].location = [0,0,0]
    
    # now add the mesh collider
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_cube_add()
    profile = po['profile']
    mid = abs(profile[0][0] - profile[-1][0]) / 2
    avgradius = (profile[0][1] + profile[-1][1]) / 2
    print(mid)
    collider = "node_collider"
    bpy.context.selected_objects[0].name = collider
    bpy.data.objects[collider].scale = [0.05, avgradius*0.5 ,mid*0.9]
    bpy.data.objects[collider].location = [max(po['profile'])+0.025, 0,0]
    bpy.ops.object.transform_apply(scale=True, location=True)
    
    # retrieve kit tracker
    rkey = conf['redis-prefix']+':kit-trackers:'+str(po['kitid'])
    print("looking for "+rkey)
    ktrack = json.loads(r.get(rkey).decode())
    thiskit = ktrack['kitdir']

    # save the file in the desired folder
    part_dir = po['partdir']
    kits_dir = 'data'
    daefilename = 'original_%i_%i.dae' % (po['kitid'], po['partid'])
    outpath = os.path.join( kits_dir, thiskit, part_dir, daefilename )
    print(outpath)
    bpy.ops.wm.collada_export(filepath=outpath, check_existing=False)
    
    #compute a mass for the part
    totlen = 0
    c,d = po['profile'][0]
    for a,b in po['profile'][1:]:
        totlen += sqrt((a-c)**2 + (b-d)**2)
        c,d = a,b
    mass = totlen * 0.05
    
    # write a part.cfg file in that folder
    cfg_template = open('part.cfg').read()
    cfg_template = cfg_template.replace('<KIT>', str(po['kitid']))
    cfg_template = cfg_template.replace('<SECTION>', str(po['partid']))
    cfg_template = cfg_template.replace('<MASS>', mass.__format__('0.4f'))
    cfg_template = cfg_template.replace('<DAE_FILE>', daefilename)
    cfg_template = cfg_template.replace('<TEXTURE_FILE>', po['texture']+'.png')
    
    # -X Z Y
    # the slight offsets help to control which way the fairing is ejected, but I don't totally understand it.
    cfg_template = cfg_template.replace('<NODE_TOP_X>', (-tnode[0]-0.000048).__format__('0.6f'))
    cfg_template = cfg_template.replace('<NODE_TOP_Y>', (-tnode[2]-0.00022).__format__('0.6f'))
    cfg_template = cfg_template.replace('<NODE_TOP_Z>', (tnode[1]).__format__('0.6f'))
    
    cfg_template = cfg_template.replace('<NODE_BOTTOM_X>', (-bnode[0]-0.000048).__format__('0.6f'))
    cfg_template = cfg_template.replace('<NODE_BOTTOM_Y>', (-bnode[2]+0.00022).__format__('0.6f'))
    cfg_template = cfg_template.replace('<NODE_BOTTOM_Z>', (bnode[1]).__format__('0.6f'))
    
    if po['capped']:
        cfg_template = cfg_template.replace('<COMMENT>', '//')
    else:
        cfg_template = cfg_template.replace('<COMMENT>', '')
        
    cfg_outpath = os.path.join( kits_dir, thiskit, part_dir, 'part.cfg' )
    fout = open(cfg_outpath, 'w')
    fout.write(cfg_template)
    fout.close()
    
    # write part receipt into redis
    receipt = {
        'kitid': po['kitid'],
        'partid': po['partid'],
        'partdir': po['partdir']
    }
    r.lpush(conf['redis-prefix']+':part-receipts', json.dumps(receipt))

if __name__ == "__main__":
    rr = redis.StrictRedis(host='localhost', port=6379, db=0)
    while True:
        execute(rr)
