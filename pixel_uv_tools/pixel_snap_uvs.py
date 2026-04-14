import bpy
import bmesh
from mathutils import Vector, Matrix


def main(context, resolution):
    
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
    
    # Move the uvs
    pixel = 1.0 / resolution
    for i in range(len(loops)):
        uv = loops[i][uv_layer].uv
        px = round(uv.x / (1.0/resolution)) * (1.0 / resolution)
        py = round(uv.y / (1.0/resolution)) * (1.0 / resolution)
        loops[i][uv_layer].uv = Vector((px, py))
    
    # Update the edit mesh
    bmesh.update_edit_mesh(obj.data)

    # Restore the user's original selection mode
    context.tool_settings.mesh_select_mode = original_select_mode

    # Free the bmesh memory
    bm.free()    


class PixelSnapUvsOperator(bpy.types.Operator):
    """Snap the UVs of selected faces to nearest pixel on a texture of specified resolution"""
    bl_idname = "uv.pixel_snap_uvs"
    bl_label = "Pixel Snap UVs"
    bl_options = {'REGISTER', 'UNDO'}
    
    resolution: bpy.props.IntProperty(name="Texture Size", description="Width and height of target texture", default=256, min=1)
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        main(context, self.resolution)
        return {'FINISHED'}