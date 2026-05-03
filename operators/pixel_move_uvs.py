import bpy
import bmesh
from mathutils import Vector


def main(context, resolution, dx, dy):

    # Force face select mode for consistent behavior across selection modes
    obj = context.object
    original_select_mode = tuple(context.tool_settings.mesh_select_mode)
    bpy.ops.mesh.select_mode(type='FACE')

    # Construct and initialize the bmesh
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()

    # Gather the loops of selected faces
    faces = [f for f in bm.faces if f.select]
    loops = [l for f in faces for l in f.loops]

    # Move the uvs
    pixel = 1.0 / resolution
    for i in range(len(loops)):
        loops[i][uv_layer].uv.x += dx * pixel
        loops[i][uv_layer].uv.y += dy * pixel

    # Update the edit mesh
    bmesh.update_edit_mesh(obj.data)

    # Restore the user's original selection mode
    context.tool_settings.mesh_select_mode = original_select_mode



class PixelMoveUvsOperator(bpy.types.Operator):
    """Translate the UVs of selected faces using pixels. Invoke without dx/dy to enter interactive mode in the UV editor."""
    bl_idname = "uv.pixel_move_uvs"
    bl_label = "Pixel Move UVs"
    bl_options = {'REGISTER', 'UNDO'}

    resolution: bpy.props.IntProperty(name="Texture Size", description="Width and height of target texture", default=256, min=1)
    dx: bpy.props.IntProperty(name="Delta X", default=0)
    dy: bpy.props.IntProperty(name="Delta Y", default=0)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and ob.mode == 'EDIT'

    def execute(self, context):
        main(context, self.resolution, self.dx, self.dy)
        return {'FINISHED'}

    def invoke(self, context, event):
        # Force face select mode and set up bmesh
        obj = context.object
        self._original_select_mode = tuple(context.tool_settings.mesh_select_mode)
        bpy.ops.mesh.select_mode(type='FACE')

        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()

        faces = [f for f in bm.faces if f.select]
        if not faces:
            context.tool_settings.mesh_select_mode = self._original_select_mode
            self.report({'WARNING'}, "No faces selected")
            return {'CANCELLED'}

        # Snapshot original UV positions for live preview and cancel
        self._original_uvs = {}
        for f in faces:
            for l in f.loops:
                self._original_uvs[l.index] = l[uv_layer].uv.copy()

        self._initial_mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        self._bm = bm
        self._uv_layer = uv_layer
        self._faces = faces
        self._obj = obj
        self._current_dx = 0
        self._current_dy = 0

        context.area.header_text_set("Pixel Move: dx=0 dy=0  (LMB/Enter to confirm, RMB/Esc to cancel)")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            screen_pixels_per_uv_pixel = 20
            mouse_dx = event.mouse_region_x - self._initial_mouse.x
            mouse_dy = event.mouse_region_y - self._initial_mouse.y
            dx = round(mouse_dx / screen_pixels_per_uv_pixel)
            dy = round(mouse_dy / screen_pixels_per_uv_pixel)
            pixel = 1.0 / self.resolution

            if dx != self._current_dx or dy != self._current_dy:
                self._current_dx = dx
                self._current_dy = dy

                # Apply offset from original positions
                for f in self._faces:
                    for l in f.loops:
                        orig = self._original_uvs[l.index]
                        l[self._uv_layer].uv.x = orig.x + dx * pixel
                        l[self._uv_layer].uv.y = orig.y + dy * pixel

                bmesh.update_edit_mesh(self._obj.data)
                context.area.tag_redraw()
                context.area.header_text_set(f"Pixel Move: dx={dx} dy={dy}  (LMB/Enter to confirm, RMB/Esc to cancel)")

            return {'RUNNING_MODAL'}

        elif event.type in {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
            # Confirm - store final values for undo/redo panel
            self.dx = self._current_dx
            self.dy = self._current_dy
            self._cleanup(context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            # Cancel - restore original UV positions
            for f in self._faces:
                for l in f.loops:
                    l[self._uv_layer].uv = self._original_uvs[l.index].copy()
            bmesh.update_edit_mesh(self._obj.data)
            self._cleanup(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def _cleanup(self, context):
        context.area.header_text_set(None)
        context.tool_settings.mesh_select_mode = self._original_select_mode
