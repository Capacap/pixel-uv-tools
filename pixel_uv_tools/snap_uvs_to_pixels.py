import bpy
import bmesh
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
    use_uv_select = True
    if context.space_data and context.space_data.type == 'VIEW_3D':
        use_uv_select = False
    
    # Gather the loops of selected faces
    faces = [f for f in bm.faces if f.select]
    loops = [l for f in faces for l in f.loops]
    if use_uv_select:
        loops = [l for l in loops if l[uv_layer].select]
    
    # Move the uvs
    pixel = 1.0 / resolution
    for i in range(len(loops)):
        uv = loops[i][uv_layer].uv
        px = round(uv.x / (1.0/resolution)) * (1.0 / resolution)
        py = round(uv.y / (1.0/resolution)) * (1.0 / resolution)
        loops[i][uv_layer].uv = Vector((px, py))
    
    # Update the edit mesh
    bmesh.update_edit_mesh(obj.data)
    
    # Free the bmesh memory
    bm.free()    


class SnapUVsToPixelsOperator(bpy.types.Operator):
    """Snap the UVs of selected faces to nearest pixel on a texture of specified resolution"""
    bl_idname = "uv.snap_to_pixels_custom_resolution"
    bl_label = "Snap UVs to Pixels"
    bl_options = {'REGISTER', 'UNDO'}
    
    resolution: bpy.props.IntProperty(name="Texture Size", description="Width and height of target texture", default=256, min=1)
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        main(context, self.resolution)
        return {'FINISHED'}