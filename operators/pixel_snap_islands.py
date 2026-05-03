import bpy
import bmesh
from math import inf
from mathutils import Vector, Matrix


def round_to_nearest_even(number):
    return int(number) if int(number) % 2 == 0 else int(number) + 1


def get_uv_islands(bm):

    islands = []
    select_faces = [face for face in bm.faces if face.select]
    for face in select_faces:
        face.select = False

    processed = []
    for face in select_faces:
        if face not in processed:
            face.select = True
            bpy.ops.mesh.select_linked(delimit={'SEAM'})
            island = [face for face in select_faces if face.select]
            islands.append(island)
            processed.extend(island)
            for face in island:
                face.select = False

    for face in bm.faces:
        face.select = face in select_faces

    return islands


def snap_uv_island_to_pixels(island_faces, uv_layer, resolution):

    island_loops = [loop for face in island_faces for loop in face.loops]

    bmin = Vector((inf, inf))
    bmax = Vector((-inf, -inf))
    for loop in island_loops:
        uv = loop[uv_layer].uv
        bmin.x = min(bmin.x, uv.x)
        bmin.y = min(bmin.y, uv.y)
        bmax.x = max(bmax.x, uv.x)
        bmax.y = max(bmax.y, uv.y)
    bcenter = (bmin + bmax) / 2

    x_size = bmax.x - bmin.x
    y_size = bmax.y - bmin.y
    x_target_size = round_to_nearest_even(x_size / (1.0 / resolution)) * (1.0 / resolution)
    y_target_size = round_to_nearest_even(y_size / (1.0 / resolution)) * (1.0 / resolution)
    x_scale = x_target_size / x_size
    y_scale = y_target_size / y_size

    px = round(bcenter.x / (1.0 / resolution)) * (1.0 / resolution)
    py = round(bcenter.y / (1.0 / resolution)) * (1.0 / resolution)
    pixel_corner = Vector((px, py))

    transformation = Matrix.LocRotScale((pixel_corner - bcenter).to_3d(), None, Vector((x_scale, y_scale, 1.0)))
    to_origin = Matrix.Translation(-bcenter.to_3d())
    for loop in island_loops:
        xyz = loop[uv_layer].uv.to_3d()
        xyz = to_origin @ xyz
        xyz = transformation @ xyz
        xyz = to_origin.inverted() @ xyz
        loop[uv_layer].uv = xyz.xy


def main(context, resolution):

    obj = context.object

    # Force face select mode for consistent behavior across selection modes
    original_select_mode = tuple(context.tool_settings.mesh_select_mode)
    bpy.ops.mesh.select_mode(type='FACE')

    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()

    for island in get_uv_islands(bm):
        snap_uv_island_to_pixels(island, uv_layer, resolution)

    bmesh.update_edit_mesh(obj.data)

    # Restore the user's original selection mode
    context.tool_settings.mesh_select_mode = original_select_mode

    bm.free()


class PixelSnapIslandsOperator(bpy.types.Operator):
    """Snap UV islands to pixel boundaries"""
    bl_idname = "uv.pixel_snap_islands"
    bl_label = "Pixel Snap Islands"
    bl_options = {'REGISTER', 'UNDO'}

    resolution: bpy.props.IntProperty(name="Resolution", description="Width and height of target texture", default=256, min=1)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        main(context, self.resolution)
        return {'FINISHED'}
