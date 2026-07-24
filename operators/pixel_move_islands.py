import bpy
import bmesh
from math import inf
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


def move_island_to_pixels(bm, uv_layer, island, resolution):
    """Moves the minimum point of the islands bounding box to the nearest pixel corner.
    Zero-size axes are centered inside a texel instead, since a line exactly on a
    pixel boundary samples ambiguously."""
    faces = [bm.faces[i] for i in island]
    pixel = 1.0 / resolution

    bmin = [inf, inf]
    bmax = [-inf, -inf]
    for f in faces:
        for l in f.loops:
            uv = l[uv_layer].uv
            for axis in range(2):
                bmin[axis] = min(bmin[axis], uv[axis])
                bmax[axis] = max(bmax[axis], uv[axis])

    delta = [0.0, 0.0]
    for axis in range(2):
        size = bmax[axis] - bmin[axis]
        if size < 1e-9:
            center = (bmin[axis] + bmax[axis]) / 2
            delta[axis] = (round(center * resolution - 0.5) + 0.5) * pixel - center
        else:
            delta[axis] = round(bmin[axis] * resolution) * pixel - bmin[axis]

    translation = Matrix.LocRotScale(Vector((delta[0], delta[1], 0.0)), None, Vector((1.0, 1.0, 1.0)))

    for f in faces:
        for l in f.loops:
            xyz = translation @ l[uv_layer].uv.to_3d()
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
        move_island_to_pixels(bm, uv_layer, island, resolution)

    bmesh.update_edit_mesh(me)

    # Restore the user's original selection mode
    context.tool_settings.mesh_select_mode = original_select_mode

    bm.free()


class PixelMoveIslandsOperator(bpy.types.Operator):
    """Moves each UV island so that its minimum bounding box corner snaps to the nearest pixel corner"""
    bl_idname = "uv.pixel_move_islands"
    bl_label = "Pixel Move Islands"
    bl_options = {'REGISTER', 'UNDO'}

    resolution: bpy.props.IntProperty(name="Texture Resolution", default=256, min=1)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        main(context, self.resolution)
        return {'FINISHED'}
