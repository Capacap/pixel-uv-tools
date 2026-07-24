import bpy


class PixelUnwrapOperator(bpy.types.Operator):
    """Unwrap the selected faces with Blender's angle based unwrap, then pack and snap the result to the pixel grid"""
    bl_idname = "uv.pixel_unwrap"
    bl_label = "Pixel Unwrap"
    bl_options = {'REGISTER', 'UNDO'}

    img_size: bpy.props.IntProperty(name="Texture Size", description="Width and height of target texture", default=256, min=1)
    margin: bpy.props.IntProperty(name="Packing Margin", description="Margin around UV Islands in pixels", default=2, min=0)
    shape_method: bpy.props.EnumProperty(items=[
        ('CONCAVE', 'Exact Shape', 'Uses exact geometry'),
        ('CONVEX', 'Boundary Shape', 'Uses convex hull'),
        ('AABB', 'Bounding Box', 'Uses bounding boxes')
    ], name="Shape Method", default='AABB')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'

    def execute(self, context):
        # Blender's unwrap respects seams, selection, and pinned UVs
        bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, use_subsurf_data=False, margin_method='SCALED', margin=0.0)

        # Equalize island density before packing so pixel scaling treats all islands alike
        bpy.ops.uv.average_islands_scale(scale_uv=False, shear=False)

        # Pack, snap island sizes and positions to the pixel grid
        bpy.ops.uv.pixel_pack_islands(resolution=self.img_size, margin=self.margin, shape_method=self.shape_method)

        return {'FINISHED'}
