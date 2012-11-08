import bpy
import bmesh
from bpy_extras import object_utils
from mathutils import *
from math import *
import redis
import json
import os


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
    
    for v,row in enumerate(profile):
        height = row[0]
        radius = row[1]
        ket = 13
        center = (1.0, 0.0, 0.0)
        # create a semicircle centered at (1,0,0) and 
        for a,angle in enumerate([(j/(ket-1))*pi for j in range(ket)]):
                point = (-sin(angle)*radius+1,
                         cos(angle)*radius,
                         height-mid)
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
            if section_size > 0.2:
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
    
    return vertices, faces, tex_faces


def execute(r):
    
    res = r.rpop('part-orders')
    if not res: return
    
    # remove prior parts
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    po = json.loads(res.decode())
        
    verts_loc, faces, tex_faces = add_fairing(po['profile'])
    
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
    
    # add the soldify modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    bpy.context.selected_objects[0].modifiers['Solidify'].thickness = 0.04
    # apply it
    bpy.ops.object.modifier_apply(modifier='Solidify')
    # add an edge split modifier
    bpy.ops.object.modifier_add(type='EDGE_SPLIT')
    bpy.context.selected_objects[0].modifiers['EdgeSplit'].split_angle = 0.418879 #radians, 24 degrees
    # set smooth
    bpy.ops.object.shade_smooth()
    # apply it
    bpy.ops.object.modifier_apply(modifier='EdgeSplit')
    
    # move it to origin if thats not already where it is
    bpy.context.selected_objects[0].location = [0,0,0]
    
    # now add the mesh collider
    bpy.ops.mesh.primitive_cube_add()
    profile = po['profile']
    mid = abs(profile[0][0] - profile[-1][0]) / 2
    print(mid)
    bpy.data.objects['Cube'].scale = [0.2,1,mid*0.9]
    
    rkey = 'kit-trackers:'+str(po['kitid'])
    print("looking for "+rkey)
    ktrack = json.loads(r.get(rkey).decode())
    thiskit = ktrack['kitdir']

    # save the file in the desired folder
    part_dir = po['partdir']
    kits_dir = 'data'
    outpath = os.path.join( kits_dir, thiskit, part_dir, 'original.blend' )
    print(outpath)
    bpy.ops.wm.save_as_mainfile(filepath=outpath, check_existing=False)

if __name__ == "__main__":
    rr = redis.StrictRedis(host='localhost', port=6379, db=0)
    execute(rr)
