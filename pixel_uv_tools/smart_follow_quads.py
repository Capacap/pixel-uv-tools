import bpy
import bmesh
import math
from mathutils import Vector


def main(context, mode):
    
    # Construct and initialize the bmesh
    obj = context.object
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.verify()
    
    # UV selection is ignored if the operator is run through the 3d viewport
    use_uv_selection = True
    if context.space_data and context.space_data.type == 'VIEW_3D':
        use_uv_selection = False
    
    # Hide all faces that do not have their UVs selected if using UV selection
    if use_uv_selection:
        for face in bm.faces:
            for loop in face.loops:
                if not loop[uv_layer].select:
                    face.hide = True
    
    # Initialize the face and uv selections
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.hide(unselected=True)
    bpy.ops.uv.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='DESELECT')
        
    for face in bm.faces:
        if not face.hide:
            # Select the current face and expand the selection to the rest of its UV island
            face.select = True
            bpy.ops.mesh.select_linked(delimit={'UV'})
            bpy.ops.uv.select_all(action='SELECT')
            
            # Gather the selected faces
            faces = [f for f in bm.faces if f.select]
            
            # Assign a score to each face based on similarity of 
            scores = [] 
            for i in range(len(faces)):
                
                f = faces[i]
                score = -math.inf
                
                # Only quads qualify
                if len(f.loops)==4:
                    # Calculate the length of each side of the face
                    sides = []
                    for l in f.loops:
                        a = l.vert.co
                        b = l.link_loop_next.vert.co
                        sides.append((a-b).length)
                    
                    # Calculate a score based on how similar each pair of opposing sides are
                    score_a = max(sides[0],sides[2]) - abs(sides[0]-sides[2])
                    score_b = max(sides[1],sides[3]) - abs(sides[1]-sides[3])
                    score = score_a + score_b
                    
                scores.append(score)
            
            # Find the face with the highest score
            best = None
            hiscore = -math.inf
            for i in range(len(faces)):    
                if scores[i] > hiscore:
                    hiscore = scores[i]
                    best = faces[i] 
            
            # Only proceed if at least one quad exists
            if best is not None:     
                
                # Centroid
                loops = [l for f in faces for l in f.loops]
                sum_x = sum([l[uv_layer].uv.x for l in loops])
                sum_y = sum([l[uv_layer].uv.y for l in loops])
                n = len(loops)
                centroid = Vector((sum_x/n,sum_y/n))
                  
                # Calculate the distance between each sides uvs
                uv_sides = []
                for l in best.loops:
                    a = l[uv_layer].uv
                    b = l.link_loop_next[uv_layer].uv
                    uv_sides.append((a-b).length)
                    
                # Construct vectors to act as the perpendicular sides of the rectangle
                side_a = Vector(((uv_sides[0] + uv_sides[1]) * 0.5, 0.0))
                side_b = Vector((0.0, (uv_sides[1] + uv_sides[3]) * 0.5))
                
                # Make the uvs of the quad perfectly even
                best.loops[3][uv_layer].uv = best.loops[3][uv_layer].uv + side_b
                best.loops[2][uv_layer].uv = best.loops[3][uv_layer].uv + side_a
                best.loops[1][uv_layer].uv = best.loops[2][uv_layer].uv - side_b
                best.loops[0][uv_layer].uv = best.loops[1][uv_layer].uv - side_a
                
                # Set the ideal quad as the active element
                bm.faces.active = best
                
                # Preform the Follow Active Quads operation
                bpy.ops.uv.follow_active_quads(mode=mode)
                
                # New Centroid
                loops = [l for f in faces for l in f.loops]
                sum_x = sum([l[uv_layer].uv.x for l in loops])
                sum_y = sum([l[uv_layer].uv.y for l in loops])
                n = len(loops)
                new_centroid = Vector((sum_x/n,sum_y/n))
                
                # Move the new centroid to the original centroid
                for l in loops:
                    l[uv_layer].uv += centroid - new_centroid
            
            # Hide the UV island so that its faces does not get processed again
            bpy.ops.mesh.hide(unselected=False)
    
    # Reveal all hidden faces
    bpy.ops.mesh.reveal()
    
    # Free the bmesh memory
    bm.free()


class SmartFollowQuadsOperator(bpy.types.Operator):
    """Follow ideal quad of each selected uv island"""
    bl_idname = "uv.smart_follow_quads"
    bl_label = "Smart Follow Quads"
    bl_options = {'REGISTER', 'UNDO'}
    
    mode: bpy.props.EnumProperty(items=[
    ('EVEN', 'Even', 'Space all UVs evenly'), 
    ('LENGTH', 'Length', 'Average space UVs edge length of each loop'), 
    ('LENGTH_AVERAGE', 'Length Average', 'Average space UVs edge length of each loop')], 
    name="Edge Length Mode", default='EVEN')
    
    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and ob.mode == 'EDIT'

    def execute(self, context):
        main(context, self.mode)
        return {'FINISHED'}