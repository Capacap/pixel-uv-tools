bl_info = {
    "name": "Pixel UV Tools",
    "author": "Simon Sorkin",
    "version": (2, 0),
    "blender": (2, 80, 0),
    "location": "Edit Mode > UV and UV Editor > UV",
    "description": "Tools for creating pixel-perfect UVs.",
    "warning": "",
    "doc_url": "",
    "category": "UV",
}


if "bpy" in locals():
    import importlib
    importlib.reload(pixel_move_uvs)
    importlib.reload(pixel_scale_uvs)
    importlib.reload(pixel_snap_uvs)
    importlib.reload(pixel_move_islands)
    importlib.reload(pixel_scale_islands)
    importlib.reload(pixel_snap_islands)
    importlib.reload(pixel_pack_islands)

    importlib.reload(pixel_unwrap_active_edge)
    importlib.reload(pixel_unwrap_centerline)
else:
    import bpy
    from . import pixel_move_uvs
    from . import pixel_scale_uvs
    from . import pixel_snap_uvs
    from . import pixel_move_islands
    from . import pixel_scale_islands
    from . import pixel_snap_islands
    from . import pixel_pack_islands

    from . import pixel_unwrap_active_edge
    from . import pixel_unwrap_centerline

import bpy


class UV_MT_pixel_uv_tools(bpy.types.Menu):
    bl_idname = "UV_MT_pixel_uv_tools"
    bl_label = "Pixel UV Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"

        layout.operator(pixel_move_uvs.PixelMoveUvsOperator.bl_idname, text=pixel_move_uvs.PixelMoveUvsOperator.bl_label)
        layout.operator(pixel_scale_uvs.PixelScaleUvsOperator.bl_idname, text=pixel_scale_uvs.PixelScaleUvsOperator.bl_label)
        layout.separator()

        layout.operator(pixel_snap_uvs.PixelSnapUvsOperator.bl_idname, text=pixel_snap_uvs.PixelSnapUvsOperator.bl_label)
        layout.operator(pixel_snap_islands.PixelSnapIslandsOperator.bl_idname, text=pixel_snap_islands.PixelSnapIslandsOperator.bl_label)
        layout.operator(pixel_pack_islands.PixelPackIslandsOperator.bl_idname, text=pixel_pack_islands.PixelPackIslandsOperator.bl_label)
        layout.separator()

        layout.operator(pixel_unwrap_active_edge.PixelUnwrapActiveEdgeOperator.bl_idname, text=pixel_unwrap_active_edge.PixelUnwrapActiveEdgeOperator.bl_label)
        layout.operator(pixel_unwrap_centerline.PixelUnwrapCenterlineOperator.bl_idname, text=pixel_unwrap_centerline.PixelUnwrapCenterlineOperator.bl_label)


classes = [
    pixel_move_uvs.PixelMoveUvsOperator,
    pixel_scale_uvs.PixelScaleUvsOperator,
    pixel_snap_uvs.PixelSnapUvsOperator,
    pixel_move_islands.PixelMoveIslandsOperator,
    pixel_scale_islands.PixelScaleIslandsOperator,
    pixel_snap_islands.PixelSnapIslandsOperator,
    pixel_pack_islands.PixelPackIslandsOperator,
    pixel_unwrap_active_edge.PixelUnwrapActiveEdgeOperator,
    pixel_unwrap_centerline.PixelUnwrapCenterlineOperator,
    UV_MT_pixel_uv_tools,
]


def draw_submenu(self, context):
    self.layout.separator()
    self.layout.menu(UV_MT_pixel_uv_tools.bl_idname)


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_uv_map.append(draw_submenu)
    bpy.types.IMAGE_MT_uvs.append(draw_submenu)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    bpy.types.VIEW3D_MT_uv_map.remove(draw_submenu)
    bpy.types.IMAGE_MT_uvs.remove(draw_submenu)


if __name__ == "__main__":
    register()
