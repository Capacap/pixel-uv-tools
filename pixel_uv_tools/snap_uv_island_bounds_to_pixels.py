import bpy
import bmesh
import math
from mathutils import Vector, Matrix


def main(context, resolution):
    
    # Construct and initialize the bmesh
    obj = context.object
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()
    
    # UV selection is ignored if the operator is run through the 3d viewport
    use_uv_selection = True
    if context.space_data and context.space_data.type == 'VIEW_3D':
        use_uv_selection = False
    
    # Hide all faces that do not have their UVs selected if using UV selection
    if use_uv_selection:
        for face in bm.faces:
            for loop in face.loops:
                if not loop[uv_layer].select:
                    face.hide = True
    
    # Initialize the face and uv selections
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.hide(unselected=True)
    bpy.ops.uv.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='DESELECT')
        
    for face in bm.faces:
        if not face.hide:
            # Select the current face and expand the selection to the rest of its UV island
            face.select = True
            bpy.ops.mesh.select_linked(delimit={'UV'})
            bpy.ops.uv.select_all(action='SELECT')
            
            # Calculate the bounds of the uv island
            bmin = Vector((math.inf, math.inf))
            bmax = Vector((-math.inf, -math.inf))
            for f in [f for f in bm.faces if f.select]:
                for l in f.loops:
                    uv = l[uv_layer].uv
                    bmin.x = min(bmin.x, uv.x)
                    bmin.y = min(bmin.y, uv.y)
                    bmax.x = max(bmax.x, uv.x)
                    bmax.y = max(bmax.y, uv.y)
                    
            # Calculate the scale needed to make the uv islands width and height proportional to the size of the pixels
            x_size = bmax.x - bmin.x
            y_size = bmax.y - bmin.y
            x_target_size = round(x_size/(1.0/resolution))*(1.0/resolution)
            y_target_size = round(y_size/(1.0/resolution))*(1.0/resolution)
            x_scale = x_target_size/x_size
            y_scale = y_target_size/y_size

            # Calculate the translation needed to snap the minimum point of the bounds to the nearest pixel corner
            px = round(bmin.x / (1.0/resolution)) * (1.0 / resolution)
            py = round(bmin.y / (1.0/resolution)) * (1.0 / resolution)
            pixel_corner = Vector((px, py))
            
            # Construct a matrix to move and scale the uvs
            transformation = Matrix.LocRotScale((pixel_corner - bmin).to_3d(), None, Vector((x_scale,y_scale,1.0)))
            
            # Construct a matrix to translate the uvs to the origin of the transformation
            to_origin = Matrix.Translation(-bmin.to_3d())
            
            # Apply the transformation
            for l in [l for f in bm.faces if f.select for l in f.loops]:
                xyz = l[uv_layer].uv.to_3d() # Only 3d vectors are compatible with 4x4 matricies in blender
                xyz = to_origin @ xyz
                xyz = transformation @ xyz
                xyz = to_origin.inverted() @ xyz
                l[uv_layer].uv = xyz.xy
            
            # Hide the UV island so that its faces does not get processed again
            bpy.ops.mesh.hide(unselected=False)
    
    # Reveal all hidden faces
    bpy.ops.mesh.reveal()
    
    # Free the bmesh memory
    bm.free()
    

class SnapUvIslandBoundsToPixelsOperator(bpy.types.Operator):
    """Snap the corners of each selected uv island's bounding box to the nearest pixel corners on a texture of specified size"""
    bl_idname = "uv.snap__uv_island_bounds_to_pixels"
    bl_label = "Snap UV Island Bounds to Pixels"
    bl_options = {'REGISTER', 'UNDO'}
    
    resolution: bpy.props.IntProperty(name="Texture Size", description="Width and height of target texture", default=256, min=1)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        main(context, self.resolution)
        return {'FINISHED'}