import bpy
import bmesh
from math import inf
from mathutils import Vector, Matrix


def main(context, resolution, dx, dy):
    
    # Force face select mode for consistent behavior across selection modes
    obj = context.object
    original_select_mode = tuple(context.tool_settings.mesh_select_mode)
    bpy.ops.mesh.select_mode(type='FACE')

    # Construct and initialize the bmesh
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()

    # Gather the loops of selected faces
    faces = [f for f in bm.faces if f.select]
    loops = [l for f in faces for l in f.loops]
    
    # Calculate the bounds of the selected uvs
    bmin = Vector((inf, inf))
    bmax = Vector((-inf, -inf))
    for f in [f for f in bm.faces if f.select]:
        for l in loops:
            uv = l[uv_layer].uv
            bmin.x = min(bmin.x, uv.x)
            bmin.y = min(bmin.y, uv.y)
            bmax.x = max(bmax.x, uv.x)
            bmax.y = max(bmax.y, uv.y)
            
    # Scale the selection to pixel-aligned dimensions plus the pixel delta
    x_size = bmax.x - bmin.x
    y_size = bmax.y - bmin.y
    x_target_size = round(x_size/(1.0/resolution)) * (1.0/resolution)
    y_target_size = round(y_size/(1.0/resolution)) * (1.0/resolution)
    x_target_size += dx * (1.0/resolution)
    y_target_size += dy * (1.0/resolution)
    x_scale = x_target_size / x_size
    y_scale = y_target_size / y_size
    
    # Construct a matrix to scale the uvs
    transformation = Matrix.LocRotScale(Vector((0.0,0.0,0.0)), None, Vector((x_scale,y_scale,1.0)))
    
    # Calculate the centroid of the uvs to use as the origin point of the transformation
    sum_x = sum([l[uv_layer].uv.x for l in loops])
    sum_y = sum([l[uv_layer].uv.y for l in loops])
    n = len(loops)
    origin = Vector((sum_x/n,sum_y/n,0.0)) if n > 0 else Vector((0.0,0.0,0.0))
    
    # Construct a matrix to translate the uvs to the origin of the transformation
    to_origin = Matrix.Translation(-origin)
    
    # Apply the transformation
    for l in [l for f in bm.faces if f.select for l in f.loops]:
        xyz = l[uv_layer].uv.to_3d() # Only 3d vectors are compatible with 4x4 matricies in blender
        xyz = to_origin @ xyz
        xyz = transformation @ xyz
        xyz = to_origin.inverted() @ xyz
        l[uv_layer].uv = xyz.xy
    
    # Update the edit mesh
    bmesh.update_edit_mesh(obj.data)

    # Restore the user's original selection mode
    context.tool_settings.mesh_select_mode = original_select_mode

    # Free the bmesh memory
    bm.free()


class PixelScaleUvsOperator(bpy.types.Operator):
    """Scale width and height the UVs of selected faces by an amount of pixels on a texture of specified resolution"""
    bl_idname = "uv.pixel_scale_uvs"
    bl_label = "Pixel Scale UVs"
    bl_options = {'REGISTER', 'UNDO'}
    
    resolution: bpy.props.IntProperty(name="Texture Size", description="Width and height of target texture", default=256, min=1)
    dx: bpy.props.IntProperty(name="Delta X", description="Pixels on the x-axis", default=1)
    dy: bpy.props.IntProperty(name="Delta Y", description="Pixels on the y-axis", default=1)
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'


    def execute(self, context):
        main(context, self.resolution, self.dx, self.dy)
        return {'FINISHED'}