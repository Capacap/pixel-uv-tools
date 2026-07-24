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


def uv_bounds_size(faces, uv_layer):
    """Width and height of the UV bounding box of the given faces"""
    us = [l[uv_layer].uv.x for f in faces for l in f.loops]
    vs = [l[uv_layer].uv.y for f in faces for l in f.loops]
    return max(us) - min(us), max(vs) - min(vs)


def count_subpixel_islands(bm, uv_layer, resolution):
    """Count selected UV islands whose bounding box is under one pixel on either axis.
    Returns (total islands, subpixel islands)."""
    pixel = 1.0 / resolution
    islands = get_uv_islands(bm, uv_layer, True)
    subpixel = 0
    for island in islands:
        faces = [bm.faces[i] for i in island]
        w, h = uv_bounds_size(faces, uv_layer)
        if w < pixel or h < pixel:
            subpixel += 1
    return len(islands), subpixel


def pixel_scale_factor(size, pixel):
    """Factor that scales `size` to the nearest whole number of pixels, at least one.
    A zero-size (degenerate) axis is left unscaled since no factor can give it area."""
    if size < 1e-9:
        return 1.0
    target_size = max(round(size / pixel), 1) * pixel
    return target_size / size


def scale_uv_bounds_to_pixels(bm, uv_layer, island, resolution):
    """Scale the island so its bounding box dimensions are divisible by the pixel size.
    Islands with a subpixel axis are scaled uniformly from their larger axis so their
    proportions survive instead of each axis being forced to a whole pixel count."""
    faces = [bm.faces[i] for i in island]
    pixel = 1.0 / resolution

    x_size, y_size = uv_bounds_size(faces, uv_layer)
    major = max(x_size, y_size)
    minor = min(x_size, y_size)

    if minor < pixel:
        # Subpixel island: scale uniformly from the larger axis so proportions survive.
        # A fully subpixel island is left at its true size. If uniform scaling would
        # push the smaller axis past one pixel it is rounded to its own whole-pixel
        # size, since a fractional multi-pixel axis can never sit on the grid
        factor = pixel_scale_factor(major, pixel) if major >= pixel else 1.0
        minor_scale = factor
        if minor * factor > pixel:
            minor_scale = pixel_scale_factor(minor * factor, pixel) * factor
        if x_size >= y_size:
            x_scale, y_scale = factor, minor_scale
        else:
            x_scale, y_scale = minor_scale, factor
    else:
        x_scale = pixel_scale_factor(x_size, pixel)
        y_scale = pixel_scale_factor(y_size, pixel)

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
