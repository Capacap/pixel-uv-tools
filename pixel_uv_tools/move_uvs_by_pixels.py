import bpy
import bmesh
from mathutils import Vector, Matrix


def main(context, resolution, dx, dy):
    
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
        loops[i][uv_layer].uv.x += dx * pixel
        loops[i][uv_layer].uv.y += dy * pixel
    
    # Update the edit mesh
    bmesh.update_edit_mesh(obj.data)
    
    # Free the bmesh memory
    bm.free()


class MoveUVsByPixelsOperator(bpy.types.Operator):
    """Translate the UVs of selected faces using pixels"""
    bl_idname = "uv.move_by_pixels"
    bl_label = "Move UVs by Pixels"
    bl_options = {'REGISTER', 'UNDO'}
    
    resolution: bpy.props.IntProperty(name="Texture Size", description="Width and height of target texture", default=256, min=1)
    dx: bpy.props.IntProperty(name="Delta X", default=0)
    dy: bpy.props.IntProperty(name="Delta Y", default=0)
    
    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and ob.mode == 'EDIT'


    def execute(self, context): 
        main(context, self.resolution, self.dx, self.dy)
        return {'FINISHED'}
    

    def invoke(self, context, event):
        return self.execute(context)