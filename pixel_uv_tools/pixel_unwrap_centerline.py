import bpy
import bmesh
from mathutils import Vector


def place_and_pin_centerline_uvs(faces, uv_layer):

    # Get faces to operate on and verts on the centerline
    face_set = set(faces)
    centerline_set = {loop.vert for face in faces for loop in face.loops if abs(loop.vert.co.x) < 1e-5}

    # Early exit if there are not enough centerline verts to work with
    if len(centerline_set) < 2:
        return

    # Build adjacency restricted to edges that belong to this island's faces
    neighbors = {v: [] for v in centerline_set}
    for v in centerline_set:
        for edge in v.link_edges:
            other = edge.other_vert(v)
            if other in centerline_set and any(f in face_set for f in edge.link_faces):
                neighbors[v].append(other)

    # Find an endpoint: a centerline vert with exactly one centerline neighbour in this island
    start = None
    for v in centerline_set:
        if len(neighbors[v]) == 1:
            start = v
            break

    # Closed loop fallback: just pick any vert
    if start is None:
        start = next(iter(centerline_set))

    # Walk the edge chain
    chain = [start]
    visited = {start}
    current = start
    while True:
        next_vert = None
        for other in neighbors[current]:
            if other not in visited:
                next_vert = other
                break
        if next_vert is None:
            break
        chain.append(next_vert)
        visited.add(next_vert)
        current = next_vert

    # Build UV positions along V axis based on 3D edge distance
    vert_uv = {chain[0]: Vector((0.0, 0.0))}
    for i in range(1, len(chain)):
        distance = (chain[i].co - chain[i - 1].co).length
        vert_uv[chain[i]] = vert_uv[chain[i - 1]] + Vector((0.0, -distance))

    # Apply UVs and pin so the unwrapper preserves the centerline placement
    for face in faces:
        for loop in face.loops:
            if loop.vert in vert_uv:
                loop[uv_layer].uv = vert_uv[loop.vert]
                loop[uv_layer].pin_uv = True


def snap_uv_island_centerline_to_pixels(faces, uv_layer, img_size, centerline_adjustment):

    # Get loops of faces in the input set
    loops = [l for f in faces for l in f.loops]

    # Find the UV position of the first centerline vert
    uv = Vector((0.0, 0.0))
    for l in loops:
        if abs(l.vert.co.x) < 1e-5:
            uv = l[uv_layer].uv
            break

    # Calculate the offset needed to snap the centerline to the pixel grid
    dx = (round(uv.x / (1.0 / img_size)) * (1.0 / img_size)) - uv.x
    dy = (round(uv.y / (1.0 / img_size)) * (1.0 / img_size)) - uv.y

    # Optionally shift by half a pixel so the centerline lands on pixel centers instead of edges
    if centerline_adjustment == 'CENTER':
        dx += (1.0 / img_size) / 2.0
        dy += (1.0 / img_size) / 2.0

    # Translate the entire island
    for l in loops:
        l[uv_layer].uv.x += dx
        l[uv_layer].uv.y += dy


def main(context, operator):
    
    # Get object
    obj = context.object

    # Get operator parameter data
    img_size     = operator.img_size
    margin       = operator.margin
    shape_method = operator.shape_method
    adjustment   = operator.centerline_adjustment

    # Save the user's selection mode and force face mode for consistent behavior
    original_select_mode = tuple(context.tool_settings.mesh_select_mode)
    bpy.ops.mesh.select_mode(type='FACE')

    # Prepare bmesh data
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()

    # Capture the user's face selection and hidden state as indices so they survive bpy.ops calls
    selected_indices = {f.index for f in bm.faces if f.select}
    hidden_indices   = {f.index for f in bm.faces if f.hide}

    # Early exit if no faces are selected
    if not selected_indices:
        bm.free()
        return

    # Hide all unselected faces to prevent them being processed
    bpy.ops.mesh.hide(unselected=True)

    # Process each seam-delimited island individually
    processed = True
    while processed:
        processed = False
        bm.faces.ensure_lookup_table()
        for face in bm.faces:
            if not face.hide:
                processed = True

                # Select all faces that belong to the same island using seam edges as a delimiter
                bpy.ops.mesh.select_all(action='DESELECT')
                face.select = True
                bpy.ops.mesh.select_linked(delimit={'SEAM'})

                # Pin centerline UVs so the unwrapper builds around them
                faces = [f for f in bm.faces if f.select]
                place_and_pin_centerline_uvs(faces, uv_layer)

                # Perform the UV unwrap
                bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, use_subsurf_data=False, margin_method='SCALED', margin=0.0)

                # Hide the processed island so it is not visited again
                bpy.ops.mesh.hide(unselected=False)
                break

    # Clear all pins left over from the unwrap phase
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pin(clear=True, invert=False)

    # Restore the user's original hidden faces by selecting them then hiding them
    bpy.ops.mesh.select_all(action='DESELECT')
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select = f.index in hidden_indices
    bpy.ops.mesh.hide(unselected=False)
    bpy.ops.mesh.select_all(action='DESELECT')

    # Restore the user's original face selection
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select = f.index in selected_indices

    # Scale, pack, and snap island bounds to the pixel grid
    bpy.ops.uv.average_islands_scale(scale_uv=False, shear=False)
    bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=True, rotate_method='CARDINAL', scale=True, merge_overlap=False, margin_method='FRACTION', margin=margin / img_size, pin=False, pin_method='LOCKED', shape_method=shape_method)
    bpy.ops.uv.pixel_snap_islands(resolution=img_size)

    # Snap centerlines to pixel boundaries as the final step so pixel_snap_islands cannot undo the alignment
    bpy.ops.mesh.hide(unselected=True)
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()

    for face in bm.faces:
        if not face.hide:
            face.select = True
            bpy.ops.mesh.select_linked(delimit={'UV'})

            faces = [f for f in bm.faces if f.select]
            snap_uv_island_centerline_to_pixels(faces, uv_layer, img_size, adjustment)

            bpy.ops.mesh.hide(unselected=False)

    # Restore hidden faces and selection to leave the mesh as the user had it
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action='DESELECT')
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select = f.index in hidden_indices
    bpy.ops.mesh.hide(unselected=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    for f in bm.faces:
        f.select = f.index in selected_indices

    # Restore the user's original selection mode
    context.tool_settings.mesh_select_mode = original_select_mode

    # Free bmesh memory
    bm.free()


class PixelUnwrapCenterlineOperator(bpy.types.Operator):
    """Unwrap the selected faces while prioritizing the vertices at the x-centerline"""
    bl_idname = "uv.pixel_unwrap_centerline"
    bl_label = "Pixel Unwrap (Centerline)"
    bl_options = {'REGISTER', 'UNDO'}

    img_size: bpy.props.IntProperty(name="Texture Size", description="Width and height of target texture", default=256, min=1)
    margin: bpy.props.IntProperty(name="Packing Margin", description="Margin around UV Islands in pixels", default=2, min=0)
    shape_method: bpy.props.EnumProperty(items=[
        ('CONCAVE', 'Exact Shape', 'Uses exact geometry'),
        ('CONVEX', 'Boundary Shape', 'Uses convex hull'),
        ('AABB', 'Bounding Box', 'Uses bounding boxes')
    ], name="Shape Method", default='AABB')
    centerline_adjustment: bpy.props.EnumProperty(items=[
        ('CORNER', 'Pixel Corner', 'Adjust to pixel corner'),
        ('CENTER', 'Pixel Center', 'Adjust to pixel center')
    ], name="Centerline Adjustment", default='CORNER')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        main(context, self)
        return {'FINISHED'}
