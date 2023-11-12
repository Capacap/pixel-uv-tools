import bpy
import bmesh
import math
from mathutils import Vector, Quaternion, Matrix


def generate_matrices(vertices):
    
    # Create a set if matricies evenly rotated to a total of 360 degrees
    matrices = []
    for i in range(vertices):
        angle = i * math.radians(360.0/vertices)
        rotation = Quaternion(Vector((0.0,0.0,1.0)), angle)
        matrix = Matrix.LocRotScale(Vector((0.0,0.0,0.0)),rotation,Vector((1.0,1.0,1.0)))
        matrices.append(matrix)
    
    # Create a matrix to project 'up' facing polygons over
    north_pole = Matrix.LocRotScale(Vector((0.0,0.0,0.0)),Quaternion(Vector((1.0,0.0,0.0)), math.radians(90.00)),Vector((1.0,1.0,1.0)))
    matrices.append(north_pole)
    
    # Create a matrix to project 'down' facing polygons over
    south_pole = Matrix.LocRotScale(Vector((0.0,0.0,0.0)),Quaternion(Vector((1.0,0.0,0.0)), math.radians(-90.0)),Vector((1.0,1.0,1.0)))
    matrices.append(south_pole)
    
    return matrices


def find_best_matrix(normal, matrices, cap_penalty):
    
    # Find the matrix that has the'forward' vector closest to being parallel but opposite to the normal 
    min_angle = 3.14
    min_index = 0

    if not normal.length>0.0:
        return matrices[-2] # Fallback return the 'up' matrix if normal is a zero vector
    
    # Compare each matrix 'forward' vector to the normal
    for i, matrix in enumerate(matrices):
        forward = matrix @ Vector((0.0,1.0,0.0))
        angle = -normal.angle(forward)
        
        # The 'up' and 'down' matricies are penalised by the cap_penalty parameter
        if i >= len(matrices) - 2:
            angle += math.radians(cap_penalty)
        
        # The matrix with the smalles angle between its 'forward' vector and the normal is chosen
        if angle < min_angle:
            min_angle = angle
            min_index = i
            
    return matrices[min_index]


def sign(x):
    
    # Simple sign function
    return 1 if x >= 0 else -1


def orthographic_project_to_2d(point, matrix):
    
    # Calculate the x and y axes of the projection plane
    x_axis = matrix @ Vector((1.0,0.0,0.0))
    y_axis = matrix @ Vector((0.0,0.0,1.0))
    
    # Project the point onto the x and y axes and calculate their lengths
    x = sign(point.dot(x_axis)) * point.project(x_axis).length
    y = sign(point.dot(y_axis)) * point.project(y_axis).length
    
    return Vector((x,y))


def main(context, vertices, cap_penalty, use_seams):
    
    # Construct and initialize the bmesh
    obj = context.object
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()
    
    # Initialize the face and uv selections
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.hide(unselected=True)
    bpy.ops.uv.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # Generate a set of matrices to project out uvs onto
    matrices = generate_matrices(vertices)
    
    # Generate new seams if not using existing seams
    seam_cache = []
    if not use_seams:
        # Cache the existing seams of the mesh
        seam_cache = [e for e in bm.edges if e.seam]
        
        # Mark edge as seam if the faces on each side of it project over different sides of the polygon
        for e in bm.edges:
            if len(e.link_faces) > 1: # Exclude edges that are linked to one or no faces
                m0 = find_best_matrix(e.link_faces[0].normal, matrices, cap_penalty)
                m1 = find_best_matrix(e.link_faces[1].normal, matrices, cap_penalty)
                e.seam = m0 != m1
    
    # Offset and margin will be used to space out the uv islands
    offset = 0.0
    margin = 1/64
    
    for face in bm.faces:
        if not face.hide:
            # Select the current face and expand the selection to the rest of its UV island
            face.select = True
            bpy.ops.mesh.select_linked(delimit={'SEAM'})
            
            # Gather the faces of the region
            faces = [f for f in bm.faces if f.select]
            
            # Calculate the avarage normal of the region
            normal = Vector((0.0,0.0,0.0))
            for f in faces:
                normal += f.normal
            
            if normal.length > 0.0:
                normal /= len(faces)
            else:
                normal = Vector((0.0,0.0,1.0)) # Fallback if the normal of the region is a zero vector
        
            # Find the matrix that best matches the region's normal
            best_matrix = find_best_matrix(normal, matrices, cap_penalty)
            
            # Project the uvs of each face in the region onto a 2d space defined by the orientation of the matrix
            for f in faces:
                for l in f.loops:
                    l[uv_layer].uv = orthographic_project_to_2d(l.vert.co, best_matrix) + Vector((offset,0.0))
            
            # Calculate the width of the uv island
            min_x = math.inf
            max_x = -math.inf
            for f in faces:
                for l in f.loops:
                    x = l[uv_layer].uv.x
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)  
            uv_width = max_x - min_x
            
            # Add the width to the offset
            offset = offset + uv_width + margin
            
            # Hide the UV island so that its faces does not get processed again
            bpy.ops.mesh.hide(unselected=False)
    
    # Reveal all hidden faces
    bpy.ops.mesh.reveal()
    
    # Clear generated seams
    if not use_seams:
        for e in bm.edges:
            e.seam = False
    
        # Restore cached seams
        for e in seam_cache:
            e.seam = True
    
    # Free the bmesh memory
    bm.free()
    

class RegularPolygonProjectOperator(bpy.types.Operator):
    """Project the UV vertices of the mesh over the sides and caps of a regular polygon cylinder"""
    bl_idname = "uv.regular_polygon_project"
    bl_label = "Regular Polygon Projection"
    bl_options = {'REGISTER', 'UNDO'}
    
    vertices : bpy.props.IntProperty(name='Vertices', default=4, min=3)
    cap_penalty : bpy.props.IntProperty(name='Cap Penalty', description="A higher penaly makes faces not choose to project over the caps of the regular polygon cylinder", default=0, min=0, max=90, step=1)
    use_seams : bpy.props.BoolProperty(name='Use Seams', description="Group faces using edges marked as seams rather than the angle limit", default=False)
    
    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and ob.mode == 'EDIT'

    def execute(self, context):
        main(context, self.vertices, self.cap_penalty, self.use_seams)
        return {'FINISHED'}