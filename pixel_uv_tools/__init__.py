bl_info = {
    "name": "Pixel UV Tools",
    "author": "Simon Sorkin",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Edit Mode > UV and UV Editor > UV",
    "description": "Tools for creating pixel-perfect UVs.",
    "warning": "",
    "doc_url": "",
    "category": "UV",
}


if "bpy" in locals():
    import importlib
    importlib.reload(move_uvs_by_pixels)
    importlib.reload(scale_uvs_by_pixels)
    importlib.reload(snap_uvs_to_pixels)
    importlib.reload(snap_uv_island_bounds_to_pixels)
    importlib.reload(pack_islands_pixel_margin)
    importlib.reload(smart_follow_quads)
    importlib.reload(regular_polygon_projection)
else:
    import bpy
    from . import move_uvs_by_pixels
    from . import scale_uvs_by_pixels
    from . import snap_uvs_to_pixels
    from . import snap_uv_island_bounds_to_pixels
    from . import pack_islands_pixel_margin
    from . import smart_follow_quads
    from . import regular_polygon_projection


import bpy


classes = [
    move_uvs_by_pixels.MoveUVsByPixelsOperator,
    scale_uvs_by_pixels.ScaleUVsByPixelsOperator,
    snap_uvs_to_pixels.SnapUVsToPixelsOperator,
    snap_uv_island_bounds_to_pixels.SnapUvIslandBoundsToPixelsOperator,
    pack_islands_pixel_margin.PackIslandsPixelMarginOperator,
    smart_follow_quads.SmartFollowQuadsOperator,
    regular_polygon_projection.RegularPolygonProjectOperator
]


def viewport_menu(self, context):
    layout = self.layout
    layout.operator_context = "INVOKE_DEFAULT"
    layout.separator()
    
    layout.operator(move_uvs_by_pixels.MoveUVsByPixelsOperator.bl_idname, text=move_uvs_by_pixels.MoveUVsByPixelsOperator.bl_label)
    layout.operator(scale_uvs_by_pixels.ScaleUVsByPixelsOperator.bl_idname, text=scale_uvs_by_pixels.ScaleUVsByPixelsOperator.bl_label)
    layout.separator()

    layout.operator(snap_uvs_to_pixels.SnapUVsToPixelsOperator.bl_idname, text=snap_uvs_to_pixels.SnapUVsToPixelsOperator.bl_label)
    layout.operator(snap_uv_island_bounds_to_pixels.SnapUvIslandBoundsToPixelsOperator.bl_idname, text=snap_uv_island_bounds_to_pixels.SnapUvIslandBoundsToPixelsOperator.bl_label)
    layout.separator()

    layout.operator(smart_follow_quads.SmartFollowQuadsOperator.bl_idname, text=smart_follow_quads.SmartFollowQuadsOperator.bl_label)
    layout.operator(pack_islands_pixel_margin.PackIslandsPixelMarginOperator.bl_idname, text=pack_islands_pixel_margin.PackIslandsPixelMarginOperator.bl_label)
    layout.separator()

    layout.operator(regular_polygon_projection.RegularPolygonProjectOperator.bl_idname, text=regular_polygon_projection.RegularPolygonProjectOperator.bl_label)


def image_menu(self, context):
    layout = self.layout
    layout.operator_context = "INVOKE_DEFAULT"
    layout.separator()
    
    layout.operator(move_uvs_by_pixels.MoveUVsByPixelsOperator.bl_idname, text=move_uvs_by_pixels.MoveUVsByPixelsOperator.bl_label)
    layout.operator(scale_uvs_by_pixels.ScaleUVsByPixelsOperator.bl_idname, text=scale_uvs_by_pixels.ScaleUVsByPixelsOperator.bl_label)
    layout.separator()
    
    layout.operator(snap_uvs_to_pixels.SnapUVsToPixelsOperator.bl_idname, text=snap_uvs_to_pixels.SnapUVsToPixelsOperator.bl_label)
    layout.operator(snap_uv_island_bounds_to_pixels.SnapUvIslandBoundsToPixelsOperator.bl_idname, text=snap_uv_island_bounds_to_pixels.SnapUvIslandBoundsToPixelsOperator.bl_label)
    layout.separator()

    layout.operator(smart_follow_quads.SmartFollowQuadsOperator.bl_idname, text=smart_follow_quads.SmartFollowQuadsOperator.bl_label)
    layout.operator(pack_islands_pixel_margin.PackIslandsPixelMarginOperator.bl_idname, text=pack_islands_pixel_margin.PackIslandsPixelMarginOperator.bl_label)


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_uv_map.append(viewport_menu)
    bpy.types.IMAGE_MT_uvs.append(image_menu)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    bpy.types.VIEW3D_MT_uv_map.remove(viewport_menu)
    bpy.types.IMAGE_MT_uvs.remove(image_menu)


if __name__ == "__main__":
    register()