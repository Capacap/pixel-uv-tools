import bpy


class PixelPackIslandsOperator(bpy.types.Operator):
    """Pack UV Islands so that they fit the pixel grid of a texture of specified resolution"""
    bl_idname = "uv.pixel_pack_islands"
    bl_label = "Pixel Pack Islands"
    bl_options = {'REGISTER', 'UNDO'}

    resolution: bpy.props.IntProperty(name="Texture Resolution", description="Resolution of target texure", default=256)

    margin: bpy.props.IntProperty(name="Pixel Margin", description="Amount of pixels to use as margin around each island", default=2)

    udim_source: bpy.props.EnumProperty(items=[
        ('CLOSEST_UDIM', 'Closest UDIM', 'Pack islands to closest UDIM'),
        ('ACTIVE_UDIM', 'Active UDIM', 'Pack islands to active UDIM image tile or UDIM grid tile where 2D cursor is located'),
        ('ORIGINAL_AABB', 'Original bounding box', 'Pack to starting bounding box of islands')],
        name="UDIM Source", default='CLOSEST_UDIM')

    rotate: bpy.props.BoolProperty(name="Rotate", description="Rotate islands to improve layout", default=True)

    scale: bpy.props.BoolProperty(name="Scale", description="Scale islands to fill unit square", default=True)

    merge_overlap: bpy.props.BoolProperty(name="Merge Overlapping", description="Overlapping islands stick together", default=False)

    pin: bpy.props.BoolProperty(name="Lock Pinned Islands", description="Constrain islands containing any pinned UV's", default=False)

    pin_method: bpy.props.EnumProperty(items=[
        ('SCALE', 'Scale', 'Pinned islands won\'t rescale'),
        ('ROTATION', 'Rotation', 'Pinned islands won\'t rotate'),
        ('ROTATION_SCALE', 'Rotation and Scale', 'Pinned islands will translate only'),
        ('LOCKED', 'All', 'Pinned islands are locked in place')],
        name="Pin Method", default='LOCKED')

    shape_method: bpy.props.EnumProperty(items=[
        ('CONCAVE', 'Exact Shape', 'Uses exact geometry'),
        ('CONVEX', 'Boundary Shape', 'Uses convex hull'),
        ('AABB', 'Bounding Box', 'Uses bounding boxes')],
        name="Shape Method", default='AABB')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):

        # Force face select mode for consistent behavior across selection modes
        original_select_mode = tuple(context.tool_settings.mesh_select_mode)
        bpy.ops.mesh.select_mode(type='FACE')

        margin = self.margin / self.resolution

        pack_args = dict(
            udim_source=self.udim_source,
            rotate_method='CARDINAL',
            merge_overlap=self.merge_overlap,
            margin_method='FRACTION',
            margin=margin,
            pin=self.pin,
            pin_method=self.pin_method,
            shape_method=self.shape_method,
        )

        # Initial pack with user settings
        bpy.ops.uv.pack_islands(rotate=self.rotate, scale=self.scale, **pack_args)

        # Snap island dimensions to pixel grid
        bpy.ops.uv.pixel_scale_islands(resolution=self.resolution)

        # Re-pack without rotate/scale to tighten gaps after snapping
        bpy.ops.uv.pack_islands(rotate=False, scale=False, **pack_args)

        # Snap island positions to pixel grid
        bpy.ops.uv.pixel_move_islands(resolution=self.resolution)

        # Restore the user's original selection mode
        context.tool_settings.mesh_select_mode = original_select_mode

        return {'FINISHED'}
