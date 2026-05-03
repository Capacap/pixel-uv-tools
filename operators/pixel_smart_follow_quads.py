import bpy
import bmesh
import math
from mathutils import Vector


def main(context, mode, resolution):

    obj = context.object
    pixel = 1.0 / resolution

    # Force face select mode for consistent behavior across selection modes
    original_select_mode = tuple(context.tool_settings.mesh_select_mode)
    bpy.ops.mesh.select_mode(type='FACE')

    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()

    # UV selection is ignored if the operator is run through the 3D viewport
    use_uv_selection = True
    if context.space_data and context.space_data.type == 'VIEW_3D':
        use_uv_selection = False

    # Hide all faces that do not have their UVs selected if using UV selection
    if use_uv_selection:
        for face in bm.faces:
            for loop in face.loops:
                if not loop[uv_layer].select:
                    face.hide = True

    bpy.ops.mesh.hide(unselected=True)
    bpy.ops.uv.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='DESELECT')

    for face in bm.faces:
        if not face.hide:
            # Select the current face and expand the selection to the rest of its UV island
            face.select = True
            bpy.ops.mesh.select_linked(delimit={'UV'})
            bpy.ops.uv.select_all(action='SELECT')

            faces = [f for f in bm.faces if f.select]

            # Score each face on how close its 3D shape is to a regular rectangle
            scores = []
            for f in faces:
                score = -math.inf
                if len(f.loops) == 4:
                    sides = []
                    for l in f.loops:
                        a = l.vert.co
                        b = l.link_loop_next.vert.co
                        sides.append((a - b).length)

                    score_a = max(sides[0], sides[2]) - abs(sides[0] - sides[2])
                    score_b = max(sides[1], sides[3]) - abs(sides[1] - sides[3])
                    score = score_a + score_b

                scores.append(score)

            best = None
            hiscore = -math.inf
            for i in range(len(faces)):
                if scores[i] > hiscore:
                    hiscore = scores[i]
                    best = faces[i]

            if best is not None:

                # Original island centroid so we can restore position after Follow Active Quads
                loops = [l for f in faces for l in f.loops]
                n = len(loops)
                centroid = Vector((
                    sum(l[uv_layer].uv.x for l in loops) / n,
                    sum(l[uv_layer].uv.y for l in loops) / n,
                ))

                # Current UV edge lengths of the seed quad
                uv_sides = []
                for l in best.loops:
                    a = l[uv_layer].uv
                    b = l.link_loop_next[uv_layer].uv
                    uv_sides.append((a - b).length)

                # Averaged side lengths snapped to an integer pixel count (minimum 1 px)
                avg_horizontal = (uv_sides[0] + uv_sides[2]) * 0.5
                avg_vertical   = (uv_sides[1] + uv_sides[3]) * 0.5
                side_len_h = max(1, round(avg_horizontal * resolution)) * pixel
                side_len_v = max(1, round(avg_vertical * resolution)) * pixel

                side_a = Vector((side_len_h, 0.0))
                side_b = Vector((0.0, side_len_v))

                # Rebuild the seed quad as a pixel-sized rectangle
                best.loops[3][uv_layer].uv = best.loops[3][uv_layer].uv + side_b
                best.loops[2][uv_layer].uv = best.loops[3][uv_layer].uv + side_a
                best.loops[1][uv_layer].uv = best.loops[2][uv_layer].uv - side_b
                best.loops[0][uv_layer].uv = best.loops[1][uv_layer].uv - side_a

                bm.faces.active = best
                bpy.ops.uv.follow_active_quads(mode=mode)

                # New centroid after Follow Active Quads propagated the layout
                loops = [l for f in faces for l in f.loops]
                n = len(loops)
                new_centroid = Vector((
                    sum(l[uv_layer].uv.x for l in loops) / n,
                    sum(l[uv_layer].uv.y for l in loops) / n,
                ))
                centroid_delta = centroid - new_centroid

                # Snap the seed quad's anchor corner to the nearest pixel corner after the centroid shift
                anchor = best.loops[0][uv_layer].uv + centroid_delta
                snap_delta = Vector((
                    round(anchor.x * resolution) * pixel - anchor.x,
                    round(anchor.y * resolution) * pixel - anchor.y,
                ))

                total_delta = centroid_delta + snap_delta
                for l in loops:
                    l[uv_layer].uv += total_delta

            bpy.ops.mesh.hide(unselected=False)

    bpy.ops.mesh.reveal()

    # Restore the user's original selection mode
    context.tool_settings.mesh_select_mode = original_select_mode

    bm.free()


class PixelSmartFollowQuadsOperator(bpy.types.Operator):
    """Find the most regular quad in each UV island, snap it to the pixel grid, then Follow Active Quads from that seed"""
    bl_idname = "uv.pixel_smart_follow_quads"
    bl_label = "Pixel Smart Follow Quads"
    bl_options = {'REGISTER', 'UNDO'}

    resolution: bpy.props.IntProperty(name="Texture Size", description="Width and height of target texture", default=256, min=1)
    mode: bpy.props.EnumProperty(items=[
        ('EVEN', 'Even', 'Space all UVs evenly'),
        ('LENGTH', 'Length', 'Space UVs by edge length of each loop'),
        ('LENGTH_AVERAGE', 'Length Average', 'Average space UVs edge length of each loop')],
        name="Edge Length Mode", default='EVEN')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        main(context, self.mode, self.resolution)
        return {'FINISHED'}
