import bpy
import bmesh
from mathutils import Vector


def main(context):

    obj = context.object

    # Force face select mode for consistent behavior across selection modes
    original_select_mode = tuple(context.tool_settings.mesh_select_mode)
    bpy.ops.mesh.select_mode(type='FACE')

    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    bm.select_history.validate()

    uv_layer = bm.loops.layers.uv.verify()
    active_edge = bm.select_history.active
    select_faces = [face for face in bm.faces if face.select]

    if not isinstance(active_edge, bmesh.types.BMEdge):
        print("Error, active element is not an edge.")
        return

    if len(select_faces) == 0:
        bpy.ops.mesh.select_linked(delimit={'SEAM'})
        select_faces = [face for face in bm.faces if face.select]

    for face in select_faces:
        for loop in face.loops:
            loop[uv_layer].pin_uv = False

    vert_to_uv = {}
    vert_to_uv[active_edge.verts[0]] = (0.0, 0.0)
    vert_to_uv[active_edge.verts[1]] = (active_edge.calc_length(), 0.0)

    for face in select_faces:
        for loop in face.loops:
            if loop.vert in vert_to_uv:
                loop[uv_layer].uv = vert_to_uv[loop.vert]
                loop[uv_layer].pin_uv = True

    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, use_subsurf_data=False, margin_method='SCALED', margin=0.0)

    for face in select_faces:
        for loop in face.loops:
            loop[uv_layer].pin_uv = False

    # Restore the user's original selection mode
    context.tool_settings.mesh_select_mode = original_select_mode

    bm.free()


class PixelUnwrapActiveEdgeOperator(bpy.types.Operator):
    """Unwrap the active edge first then unwrap the selected faces."""
    bl_idname = "uv.pixel_unwrap_active_edge"
    bl_label = "Pixel Unwrap (Active Edge)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        main(context)
        return {'FINISHED'}
