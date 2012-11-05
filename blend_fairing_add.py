import bpy
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

    vertices = [] # a flat list with 3*i elements
    faces = [] # a flat list of vert indices
    
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
                point = [-sin(angle)*radius+1,
                         cos(angle)*radius,
                         height-mid]
                if a==6:
                    if v==0:
                        bottomnode = point
                        print("bottom node = %r" % bottomnode)
                    if v==(len(profile)-1):
                        topnode = point
                        print("top node = %r" % topnode)
                vertices.extend(point) 

    tex_faces = []

    for t in range(len(profile)-1):
        for i in range(12):
            quad = [
                i+ket*t,
                i+1+ket*t,
                i+1+ket*(t+1),
                i+ket*(t+1)
            ]
            faces.extend(quad)
            
            # there is a texture for large parts and one for small parts
            # the large on is below the border. mind the the origin of the uvmap is in the lower left.
            
            border_y = 0.8828125
            # top section is 120 pixels high for a texture of 1024x1024
            
            d_height = profile[t+1][0] - profile[t][0]
            d_radius = profile[t+1][1] - profile[t][1]
            section_size = sqrt(d_height**2 + (d_radius)**2)
            if section_size > 0.1:
                tf = [
                    ((i+1)/12, border_y),
                    ((i)/12,   border_y),
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

    mesh = bpy.data.meshes.new("fairing")

    mesh.vertices.add(len(verts_loc) // 3)
    mesh.faces.add(len(faces) // 4)

    mesh.vertices.foreach_set("co", verts_loc)
    print(dir(mesh.vertices[0]))
    mesh.faces.foreach_set("vertices_raw", faces)
    
    mesh.update()
    
    # create uv coords
    uvtex = mesh.uv_textures.new()
    for n,tf in enumerate(tex_faces):
        datum = uvtex.data[n]
        datum.uv1 = tf[0]
        datum.uv2 = tf[1]
        datum.uv3 = tf[2]
        datum.uv4 = tf[3]
    
    mesh.update()

    # add the mesh as an object into the scene with this utility module
    from bpy_extras import object_utils
    object_utils.object_data_add(bpy.context, mesh)
    
    # add the soldifu modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    bpy.context.selected_objects[0].modifiers['Solidify'].thickness = 0.04
    # apply it
    #bpy.ops.object.modifier_apply(modifier='Solidify')
    # add an edge split modifier
    bpy.ops.object.modifier_add(type='EDGE_SPLIT')
    bpy.context.selected_objects[0].modifiers['EdgeSplit'].split_angle = 0.418879 #radians, 24 degrees
    # set smooth
    bpy.ops.object.shade_smooth()
    # apply it
    #bpy.ops.object.modifier_apply(modifier='EdgeSplit')
    
    # move it to origin if thats not already where it is
    bpy.context.selected_objects[0].location = [0,0,0]
    
    # now add the mesh collider
    bpy.ops.mesh.primitive_cube_add()
    profile = po['profile']
    mid = (profile[0][0] + profile[-1][0]) / 2
    bpy.data.objects['Cube'].scale = [0.2,1,mid*0.9]
    
    # save the file in the desired folder
    part_dir = po['partdir']
    kits_dir = '/Users/nhnifong/fairing-factory/data'
    outpath = os.path.join( kits_dir, part_dir, 'original.blend' )
    bpy.ops.wm.save_as_mainfile(filepath=outpath, check_existing=False)

if __name__ == "__main__":
    rr = redis.StrictRedis(host='localhost', port=6379, db=0)
    execute(rr)
