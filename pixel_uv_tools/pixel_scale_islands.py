import bpy
import bmesh
from mathutils import Vector, Matrix


def get_uv_islands(bm, uv_layer, only_selected):
    """Returns a list of lists where each list contains the indices of the BMFaces that make up a uv island"""
    faces = [f for f in bm.faces if f.select] if only_selected else bm.faces

    uv_vert_to_faces = {}
    for l in [l for f in faces for l in f.loops]:
        vert = (l[uv_layer].uv.to_tuple(5), l.vert.index)
        if vert not in uv_vert_to_faces:
            uv_vert_to_faces[vert] = [l.face.index]
        else:
            uv_vert_to_faces[vert].append(l.face.index)

    islands = []
    explored = []
    for f in faces:
        if f.index not in explored:
            island = [f.index]
            frontier = [f.index]
            while frontier:
                current = bm.faces[frontier.pop()]
                for l in current.loops:
                    vert = (l[uv_layer].uv.to_tuple(5), l.vert.index)
                    for neighbour in uv_vert_to_faces[vert]:
                        if neighbour != current and neighbour not in island:
                            island.append(neighbour)
                            frontier.append(neighbour)
            islands.append(island)
            explored.extend(island)

    return islands


def scale_uv_bounds_to_pixels(bm, uv_layer, island, resolution):
    """Scale the island so its bounding box dimensions are divisible by the pixel size"""
    faces = [bm.faces[i] for i in island]

    min_x = 1.0
    min_y = 1.0
    max_x = 0.0
    max_y = 0.0
    for f in faces:
        for l in f.loops:
            uv = l[uv_layer].uv
            min_x = min(min_x, uv.x)
            min_y = min(min_y, uv.y)
            max_x = max(max_x, uv.x)
            max_y = max(max_y, uv.y)

    x_size = max_x - min_x
    y_size = max_y - min_y

    x_target_size = round(x_size / (1.0 / resolution)) * (1.0 / resolution)
    y_target_size = round(y_size / (1.0 / resolution)) * (1.0 / resolution)

    x_scale = x_target_size / x_size
    y_scale = y_target_size / y_size
    scale = Matrix.LocRotScale(Vector((0.0, 0.0, 0.0)), None, Vector((x_scale, y_scale, 1.0)))

    uvx = [l[uv_layer].uv.x for f in faces for l in f.loops]
    uvy = [l[uv_layer].uv.y for f in faces for l in f.loops]
    n = len(uvx)
    center = Vector((sum(uvx) / n, sum(uvy) / n, 0.0))
    translation = Matrix.Translation(-center)

    for f in faces:
        for l in f.loops:
            xyz = l[uv_layer].uv.to_3d()
            xyz = translation @ xyz
            xyz = scale @ xyz
            xyz = translation.inverted() @ xyz
            l[uv_layer].uv = xyz.xy


def main(context, resolution):
    ob = context.edit_object
    me = ob.data

    # Force face select mode for consistent behavior across selection modes
    original_select_mode = tuple(context.tool_settings.mesh_select_mode)
    bpy.ops.mesh.select_mode(type='FACE')

    bm = bmesh.from_edit_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()

    islands = get_uv_islands(bm, uv_layer, True)

    for island in islands:
        scale_uv_bounds_to_pixels(bm, uv_layer, island, resolution)

    bmesh.update_edit_mesh(me)

    # Restore the user's original selection mode
    context.tool_settings.mesh_select_mode = original_select_mode

    bm.free()


class PixelScaleIslandsOperator(bpy.types.Operator):
    """Scale each UV island so that the width and height of its bounding box is divisible by the size of the pixels on a texture of specified size"""
    bl_idname = "uv.pixel_scale_islands"
    bl_label = "Pixel Scale Islands"
    bl_options = {'REGISTER', 'UNDO'}

    resolution: bpy.props.IntProperty(name="Texture Resolution", default=256)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        main(context, self.resolution)
        return {'FINISHED'}
