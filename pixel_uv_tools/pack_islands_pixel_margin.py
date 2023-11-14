import bpy

class PackIslandsPixelMarginOperator(bpy.types.Operator):
    """Same as Pack Islands but margin is specified in pixels on a texture of specified resolution"""
    bl_idname = "uv.pack_islands_pixel_margin"
    bl_label = "Pack Islands Pixel Margin"
    bl_options = {'REGISTER', 'UNDO'}
    
    resolution: bpy.props.IntProperty(name="Texture Size", description="Width and height of target texture", default=256, min=1)
    margin: bpy.props.IntProperty(name="Pixel Margin", description="Amount of pixels to use as margin around each island", default=2, min=0)
    udim_source: bpy.props.EnumProperty(items=[
    ('CLOSEST_UDIM', 'Closest UDIM', 'Pack islands to closest UDIM'), 
    ('ACTIVE_UDIM', 'Active UDIM', 'Pack islands to active UDIM image tile or UDIM grid tile where 2D cursor is located'), 
    ('ORIGINAL_AABB', 'Original bounding box', 'Pack to starting bounding box of islands')], 
    name="UDIM Source", default='CLOSEST_UDIM')
    rotate: bpy.props.BoolProperty(name="Rotate", description="Rotate islands to improve layout", default=True)
    rotate_method: bpy.props.EnumProperty(items=[
    ('AXIS_ALIGNED', 'Axis Aligned', 'Rotated to a minimal rectangle, either vertical or horizontal'), 
    ('CARDINAL', 'Cardinal', 'Only 90 degree rotations are allowed'), 
    ('ANY', 'Any', 'Any angle is allowed for rotation')], 
    name="Rotation Method", default='CARDINAL')
    scale: bpy.props.BoolProperty(name="Scale", description="Scale islands to fill unit square", default=True)
    merge_overlap : bpy.props.BoolProperty(name="Merge Overlapping", description="Overlapping islands stick together", default=False)
    pin: bpy.props.BoolProperty(name="Lock Pinned Islands", description="Constrain islands containing any pinned UV’s", default=False)
    pin_method: bpy.props.EnumProperty(items=[
    ('SCALE', 'Scale', 'Pinned islands won’t rescale'), 
    ('ROTATION', 'Rotation', 'Pinned islands won’t rotate'), 
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
        
        # UV selection is ignored if the operator is run through the 3d viewport
        use_uv_selection = True
        if context.space_data and context.space_data.type == 'VIEW_3D':
            use_uv_selection = False
        
        # Ensure that all UVs are selected not using uv selection
        if not use_uv_selection:
            bpy.ops.uv.select_all(action='SELECT')
        
        # Calculate the fraction margin
        margin = self.margin/self.resolution
        
        # Preform the pack islands operation
        bpy.ops.uv.pack_islands(udim_source=self.udim_source, 
                        rotate=self.rotate, 
                        rotate_method=self.rotate_method, 
                        scale=self.scale, 
                        merge_overlap=self.merge_overlap, 
                        margin_method='FRACTION', 
                        margin=margin, 
                        pin=self.pin, 
                        pin_method=self.pin_method, 
                        shape_method=self.shape_method)
        
        return {'FINISHED'}