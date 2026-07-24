import bpy
import bmesh
from math import inf
from mathutils import Vector, Matrix


def round_to_nearest_even(number):
    return int(number) if int(number) % 2 == 0 else int(number) + 1


def even_pixel_scale_factor(size, pixel):
    """Factor that scales `size` to the nearest even number of pixels, at least two.
    Unlike pixel_scale_islands.pixel_scale_factor, which rounds to whole pixels, the even
    count keeps both bounds on pixel corners when the island is centered on one.
    A zero-size (degenerate) axis is left unscaled since no factor can give it area."""
    if size < 1e-9:
        return 1.0
    target_size = max(round_to_nearest_even(size / pixel), 2) * pixel
    return target_size / size


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
    pixel = 1.0 / resolution

    if min(x_size, y_size) < pixel:
        # Scale uniformly from the larger axis so subpixel proportions survive instead
        # of the smaller axis being inflated to the two-pixel floor. If uniform scaling
        # would push the smaller axis past one pixel it is rounded to its own whole-pixel
        # size, since a fractional multi-pixel axis can never sit on the grid
        major = max(x_size, y_size)
        minor = min(x_size, y_size)
        factor = even_pixel_scale_factor(major, pixel) if major >= pixel else 1.0
        minor_scale = factor
        if minor * factor > pixel:
            minor_scale = max(round(minor * factor / pixel), 1) * pixel / minor
        if x_size >= y_size:
            x_scale, y_scale = factor, minor_scale
        else:
            x_scale, y_scale = minor_scale, factor
    else:
        x_scale = even_pixel_scale_factor(x_size, pixel)
        y_scale = even_pixel_scale_factor(y_size, pixel)

    def snap_center(value, size):
        # Axes with an even pixel count center on a pixel corner, which lands both
        # bounds on corners. Any other size (subpixel or an odd whole-pixel count)
        # moves its minimum bound to a pixel corner instead, so subpixel axes stay
        # inside a single texel row or column and odd axes stay on the grid. Zero
        # axes center inside a texel, since a line exactly on a pixel boundary
        # samples ambiguously
        if size < 1e-9:
            return (round(value * resolution - 0.5) + 0.5) * pixel
        half_pixels = size * resolution / 2
        if abs(half_pixels - round(half_pixels)) < 1e-6:
            return round(value * resolution) * pixel
        corner = round((value - size / 2) * resolution) * pixel
        return corner + size / 2

    target = Vector((snap_center(bcenter.x, x_size * x_scale),
                     snap_center(bcenter.y, y_size * y_scale)))

    transformation = Matrix.LocRotScale((target - bcenter).to_3d(), None, Vector((x_scale, y_scale, 1.0)))
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
