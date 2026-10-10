
## Press ctrl + shift Q

import bpy
from mathutils import Vector
import math
from math import sqrt, radians
import gpu

from time import time
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d
from mathutils import geometry


# -----------------
### 2D <> 3D
# -----------------


def location_to_region(worldcoords):
    ''' return 2d location '''
    from bpy_extras import view3d_utils
    return view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, worldcoords)

def region_to_location(viewcoords, depthcoords):
    ''' return normalized 3d vector '''
    from bpy_extras import view3d_utils
    return view3d_utils.region_2d_to_location_3d(bpy.context.region, bpy.context.space_data.region_3d, viewcoords, depthcoords)

def get_view_origin_position():
    from bpy_extras import view3d_utils
    region = bpy.context.region
    rv3d = bpy.context.region_data
    view_loc = view3d_utils.region_2d_to_origin_3d(region, rv3d, (region.width/2.0, region.height/2.0))
    return view_loc

def get_viewvector(context):
    return context.space_data.region_3d.view_rotation @ Vector((0,0,-1))

# -----------------
### Vector utils
# -----------------

def CrossVectorCoord(foo, bar, size):
    '''Return the coord in space of a cross vector between the two point with specified size'''
    ###middle location between 2 vector is calculated by adding the two vector and divide by two
    ##mid = (foo + bar) / 2
    between = foo - bar
    #create a generic Up vector (on Y or Z)
    up = Vector([1.0,0,0])
    new = Vector.cross(up, between)#the cross product return a 90 degree Vector
    if new == Vector([0.0000, 0.0000, 0.0000]):
        #new == 0 if up vector and between are aligned ! (so change up vector)
        up = Vector([0,-1.0,0])
        new = Vector.cross(up, between)#the cross product return a 90 degree Vector

    perpendicular = foo + new
    coeff = VectorLengthCoeff(size, foo, perpendicular)
    #position the point in space by adding the new vector multiplied by coeff value to get wanted lenght
    return (foo + (new * coeff))

def VectorLength(A,B):
    ''''take two Vector and return length'''
    return sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2 + (A[2] - B[2])**2)

def VectorLengthCoeff(size, A, B):
    '''
    Calculate the vector lenght
    return the coefficient to multiply this vector
    to obtain a vector of the size given in paramerter
    '''
    Vlength = sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2 + (A[2] - B[2])**2)
    if Vlength == 0:
        print('problem Vector lenght == 0 !')
        return (1)
    return (size / Vlength)

def circle_2d(coord, r, num_segments):
    '''create circle, ref: http://slabode.exofire.net/circle_draw.shtml'''
    cx, cy = coord
    points = []
    theta = 2 * 3.1415926 / num_segments
    c = math.cos(theta) #precalculate the sine and cosine
    s = math.sin(theta)
    x = r # we start at angle = 0
    y = 0
    for i in range(num_segments):
        #bgl.glVertex2f(x + cx, y + cy) # output vertex
        points.append((x + cx, y + cy))
        # apply the rotation matrix
        t = x
        x = c * x - s * y
        y = s * t + c * y

    return points

## raycast

def raycast_objects(context, event):
    """
    Execute ray cast
    return object hit, hit world location and normal of hitted face
    """

    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    ray_target = ray_origin + view_vector

    def visible_objects_and_duplis():
        """Loop over (object, matrix) pairs (mesh only)"""

        depsgraph = context.evaluated_depsgraph_get()
        for dup in depsgraph.object_instances:
            if dup.is_instance:  # Real dupli instance
                obj = dup.instance_object
                yield (obj, dup.matrix_world.copy())
            else:  # Usual object
                obj = dup.object
                yield (obj, obj.matrix_world.copy())

    def obj_ray_cast(obj, matrix):
        """Wrapper for ray casting that moves the ray into object space"""

        # get the ray relative to the object
        matrix_inv = matrix.inverted()
        ray_origin_obj = matrix_inv @ ray_origin
        ray_target_obj = matrix_inv @ ray_target
        ray_direction_obj = ray_target_obj - ray_origin_obj

        # cast the ray
        success, location, normal, face_index = obj.ray_cast(ray_origin_obj, ray_direction_obj)

        if success:
            return location, normal, face_index
        else:
            return None, None, None

    # cast rays and find the closest object
    best_length_squared = -1.0
    best_obj = None
    face_normal = None
    hit_loc = None
    for obj, matrix in visible_objects_and_duplis():
        if obj.type == 'MESH':
            hit, normal, _face_index = obj_ray_cast(obj, matrix)
            if hit is not None:
                hit_world = matrix @ hit
                # scene.cursor.location = hit_world
                length_squared = (hit_world - ray_origin).length_squared
                if best_obj is None or length_squared < best_length_squared:
                    # print('length_squared',length_squared)
                    best_length_squared = length_squared
                    best_obj = obj
                    face_normal = normal
                    hit_loc = hit_world

    if best_obj is not None:
        best_original = best_obj.original
        return best_original, hit_loc, face_normal
    
    return None, None, None

## raycast on GP

def get_gp_draw_plane(context):
    '''return tuple with plane coordinate and normal
    of the current drawing accordign to geometry'''

    settings = context.scene.tool_settings
    orient = settings.gpencil_sculpt.lock_axis # 'VIEW', 'AXIS_Y', 'AXIS_X', 'AXIS_Z', 'CURSOR'
    loc = settings.gpencil_stroke_placement_view3d # 'ORIGIN', 'CURSOR', 'SURFACE', 'STROKE'
    mat = context.object.matrix_world if context.object else None
    
    # -> placement
    if loc == "CURSOR":
        plane_co = context.scene.cursor.location
    else: # ORIGIN (also on origin if set to 'SURFACE', 'STROKE')
        if not context.object:
            plane_co = None
        else:
            plane_co = context.object.matrix_world.to_translation()

    # -> orientation
    if orient == 'VIEW':
        plane_no = context.space_data.region_3d.view_rotation @ Vector((0,0,1))

    elif orient == 'AXIS_Y':#front (X-Z)
        plane_no = Vector((0,1,0))
        plane_no.rotate(mat)

    elif orient == 'AXIS_X':#side (Y-Z)
        plane_no = Vector((1,0,0))
        plane_no.rotate(mat)

    elif orient == 'AXIS_Z':#top (X-Y)
        plane_no = Vector((0,0,1))
        plane_no.rotate(mat)

    elif orient == 'CURSOR':
        plane_no = Vector((0,0,1))
        plane_no.rotate(context.scene.cursor.matrix)
    
    return plane_co, plane_no

def raycast_on_gp(context, event):
    ## get axis
    plane_co, plane_no = get_gp_draw_plane(context)

    #projected on given plane from view (intersect on plane with a vector from view origin)
    region = context.region
    rv3d = context.region_data
    co = event.mouse_region_x, event.mouse_region_y

    view_mat = rv3d.view_matrix.inverted()

    depth_3d = view_mat @ Vector((0, 0, -1000))
    org = region_to_location(co, view_mat.to_translation())
    view_point = region_to_location(co, depth_3d)
    hit = geometry.intersect_line_plane(org, view_point, plane_co, plane_no)

    if hit and plane_no:
        return context.object, hit, plane_no

    return None, None, None


# -----------------
### Drawing and operator
# -----------------

def draw_callback_px(self, context):
    # 50% alpha, 2 pixel width line
    # shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
    # new bgl.glEnable(bgl.GL_BLEND)
    # new bgl.glLineWidth(2)
    
    shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
    shader.uniform_float("lineWidth", 3)

    # Draw clicked path
    for chain in self.bones:
        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": chain})
        shader.bind()
        shader.uniform_float("color", (0.9, 0.1, 0.2, 0.8))
        batch.draw(shader)

    # Draw aligned circle on bones boundary (clearer with aligned chains)
    # up = Vector((0,0,1))
    for chain, normals in zip(self.bones, self.norms):
        for p, n in zip(chain, normals):
            ## no...
            # circle3d = [(n.rotation_difference(up) @ cp) + p for cp in self.circle_pts]
            ## yes.
            circle3d = [(n.to_track_quat('-Z', 'Z') @ cp) + p for cp in self.circle_pts]
            circle3d.append(circle3d[0])
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": circle3d})
            shader.bind()
            shader.uniform_float("color", (0.9, 0.1, 0.2, 0.8))
            batch.draw(shader)


            ## 2D (need post_pixel):: draw_circle_2d(position, color, radius, segments=32) draw_circle_2d(location_to_region(p), (0.9, 0.1, 0.2, 0.8), 2, segments=32)

    # Draw current path (tail to be, if shift isn't pressed)
    if self.bones:
        mouse3d = region_to_location(self.mouse, self.bones[-1][-1])
        if not self.pressed_shift:
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": [self.bones[-1][-1], mouse3d]})
            shader.bind()
            shader.uniform_float("color", (1.0, 0.8, 0.1, 0.7))#yellow
            batch.draw(shader)
        
    """ #draw debug line showing mouse path
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": self.mouse_path})
    shader.bind()
    shader.uniform_float("color", (0.5, 0.5, 0.5, 0.5))#grey-light
    batch.draw(shader) """

    # restore opengl defaults
    # new bgl.glLineWidth(1)
    # new bgl.glDisable(bgl.GL_BLEND)

    ## not available in POST_VIEW, need POST_PIXEL for text


class PSR_OT_RETARGET_draw_rig(bpy.types.Operator):
    bl_idname = "view3d.retarget_planar_snap_rig_draw"
    bl_label = "Surface Rig"
    bl_description = "Launch a modal operator to draw a bones on planar surfaces\nPlace on surface contact and GREASE PENCIL)"
    bl_options = {'REGISTER', 'UNDO'}

    def create_armature(self, context):

        tmp = context.active_object

        wm = context.window_manager
        amt = None 
        for o in context.selected_objects:
            if o.type == 'ARMATURE':
                amt = o
                if not amt.data or amt.data.library is not None:
                    return
                amt_data = amt.data

        if not amt:
            amt_name = '2d'
            if self.hitted_obj:
                # TODO handle multiple names to choose before applying (how to propose choice menu during modal ?)
                amt_name = self.hitted_obj[0].name 
            amt_data = bpy.data.armatures.new(amt_name + '_armature')
            amt = bpy.data.objects.new(amt_name + '_rig', amt_data)
            context.collection.objects.link(amt)

        # use bpy to get global context ()
        context.view_layer.objects.active = amt

        bpy.ops.object.mode_set(mode='EDIT')
        
        for i, chain in enumerate(self.bones):
            chain_len = len(chain)
            prev_bone = None
            for count, bid in enumerate(range(chain_len-1)):

                b = amt_data.edit_bones.new(f'{str(i).zfill(2)}_{str(bid).zfill(2)}')
                b.head = chain[bid]
                b.tail = chain[bid+1]

                b.align_roll(self.norms[i][count])
                
                if wm.psr_retarget_align_on_x:# align X to normal instead of Z
                    b.roll += radians(-90)

                if not prev_bone:
                    prev_bone = b
                else:
                    b.parent = prev_bone
                    b.use_connect = True
                    prev_bone = b

        bpy.ops.object.mode_set(mode='OBJECT')
        context.view_layer.objects.active = tmp
        tmp.select_set(True, view_layer = context.view_layer)

    def modal(self, context, event):

        #Update of the header text
        info = "Confirm: (Enter/Space),   Cancel: (Esc),   Erase Last: (Rclick/Delete),   New bone chain: (Shift+LClick)"

        info += ",   Align X to Normal: (X) " + str( bool(bpy.types.WindowManager.psr_retarget_align_on_x))
        if context.object.type == 'ARMATURE':
            info += ",   Show Bones Axes: (S) " + str( bool(context.object.data.show_axes))
        
        if context.object.type == 'GREASEPENCIL':
            info += ",   Canvas: (C) " + str( bool(context.space_data.overlay.use_gpencil_grid)) \
            + ",   Axis: (A) " + str(context.scene.tool_settings.gpencil_sculpt.lock_axis)
        
        context.area.header_text_set(info)

        # Allow navigation
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'LEFT_ALT'}:
            return {'PASS_THROUGH'}
        context.area.tag_redraw()
        self.pressed_shift = event.shift

        if event.type in {'MOUSEMOVE'}:#, 'INBETWEEN_MOUSEMOVE'
            self.mouse = (event.mouse_region_x, event.mouse_region_y)
        # use 3D cursor for symetry
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # print('in ray')
            if context.object and context.object.type == 'GREASEPENCIL': # implicit if selected... context.window_manager.psr_gp_rig
                obj, loc, norm = raycast_on_gp(context, event) # GP raycast
            else:
                obj, loc, norm = raycast_objects(context, event) # Objects raycast

            if loc:
                if obj and obj not in self.hitted_obj:
                    self.hitted_obj.append(obj)

                norm = obj.matrix_world.to_quaternion() @ norm

                if not self.bones:
                    # print('add new chain')
                    self.bones.append([loc]) # 2D:(event.mouse_region_x, event.mouse_region_y)
                    self.norms.append([norm])
                
                else:
                    if self.pressed_shift:
                        # print('add new chain')
                        if len(self.bones[-1]) == 1: # if one "floating" head bone, delete before new
                            self.bones.pop()
                            self.norms.pop()
                        self.bones.append([loc]) # 2D:(event.mouse_region_x, event.mouse_region_y)
                        self.norms.append([norm]) # 2D:(event.mouse_region_x, event.mouse_region_y)
                    
                    else:
                        # print('add bone to chain')
                        self.bones[-1].append(loc) # 2D:(event.mouse_region_x, event.mouse_region_y)
                        self.norms[-1].append(norm)
        
        if event.type in ('BACK_SPACE', 'DEL', 'RIGHTMOUSE') and event.value == 'PRESS':
            if self.bones:
                if len(self.bones[-1]) == 1:
                    self.bones.pop() # del bones[-1] #kill chain
                    self.norms.pop()
                else:
                    self.bones[-1].pop()
                    self.norms[-1].pop()

        if event.type in {'X'} and event.value == 'PRESS':
            bpy.types.WindowManager.psr_retarget_align_on_x = not bpy.types.WindowManager.psr_retarget_align_on_x

        if event.type in {'S'} and context.object.type == 'ARMATURE' and event.value == 'PRESS':
            context.object.data.show_axes = not context.object.data.show_axes

        if event.type in {'C'} and context.object.type == 'GREASEPENCIL' and event.value == 'PRESS':
            context.space_data.overlay.use_gpencil_grid = not context.space_data.overlay.use_gpencil_grid

        if event.type in {'A'} and context.object.type == 'GREASEPENCIL' and event.value == 'PRESS':
            context.scene.tool_settings.gpencil_sculpt.lock_axis = next_lock_axis(context.scene.tool_settings.gpencil_sculpt.lock_axis)


        if event.type in {'ESC'}:
            #timer time
            # context.window_m  anager.event_timer_remove(self.draw_event)
            # print('STOPPED')
            self.stop_modal(context)
            return {'CANCELLED'}

        if event.type in {'RET', 'SPACE', 'NUMPAD_ENTER'}:
            self.create_armature(context)
            self.stop_modal(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def stop_modal(self, context):
        context.area.header_text_set(None)
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')


    def invoke(self, context, event):
        # print('In invoke')
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            # self.report({'ERROR'}, "Must be in Object mode")
            # return {'CANCELLED'}
        
        if context.area.type != 'VIEW_3D':
            self.report({'ERROR'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}
        
        ## ortho seems OK for raycast
        # if not context.area.spaces[0].region_3d.is_perspective:
        #     self.report({'WARNING'}, "Orthographic view: less Accurate")

        args = (self, context)
        # Add the region OpenGL drawing callback
        # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_VIEW')
        # self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')#2D

        self.color = (0.6, 0.1, 0.1, 0.6)
        self.mouse_path = [] #coordinate list of the mouse path
        self.mouse = (0, 0) #actualised tuple of mouse coordinate
        self.bones = []
        self.norms = []
        self.hitted_obj = []
        self.circle_pts = circle_2d((0,0), 0.02, 12)
        self.circle_pts = [Vector((p[0], p[1], 0)) for p in self.circle_pts]

        #already in modal
        # display_text = 'Confirm: (Enter/Space), Cancel: (Esc)\
        # , Erase Last: (Rclick/Delete), new bone chain: (Shift+LClick), \
        #     Align X to Normal: (X)'
        # if context.object.type == 'GREASEPENCIL':
        #     display_text = display_text +', Canvas: (C), Axis: (A)'
        
        # elif context.object.type == 'ARMATURE':
        #     display_text = display_text +', Show Bones Axes: (S)'
        
        # context.area.header_text_set(display_text)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    @classmethod
    def poll(cls, context):
       return (context.active_object is not None)

def next_lock_axis(orient):
    if orient == 'VIEW':
        return 'AXIS_Y'

    elif orient == 'AXIS_Y':#front (X-Z)
        return 'AXIS_X'

    elif orient == 'AXIS_X':#side (Y-Z)
        return 'AXIS_Z'
    
    elif orient == 'AXIS_Z':#top (X-Y)
        return 'CURSOR'

    else:# orient == 'CURSOR':
        return 'VIEW'
    

##  Base panel
# class PSR_PT_RETARGET_draw_rig_panel(bpy.types.Panel):
#     bl_label = "Surface rig"
#     bl_space_type = "VIEW_3D"
#     bl_region_type = "UI"
#     bl_category = "Tool"

#     # @classmethod
#     # def poll(cls, context):
#     #     return (context.object is not None)

#     def draw(self, context):
#         layout = self.layout
#         if context.object is None:
#             layout.label(text='Select an object')
#             return
#         button = layout.row()
#         text = 'Draw GP Surface Rig' if context.object.type == 'GREASEPENCIL' else 'Draw Surface Rig'
#         button.operator("view3d.retarget_planar_snap_rig_draw", text=text, icon='GREASEPENCIL')
#         # layout.prop(bpy.context.window_manager, 'psr_gp_rig') # Tacite via selection
#         layout.prop(bpy.context.window_manager, 'psr_retarget_align_on_x')
#         button.active = context.object.type != 'ARMATURE'
#         if context.object.type == 'ARMATURE':
#             box = layout.box()
#             col = box.column()
#             col.label(text='Armature:')
#             col.prop(context.object.data, 'show_axes', text = 'Show Bones Axes')
#         elif context.object.type == 'GREASEPENCIL':
#             box = layout.box()
#             col = box.column()
#             col.label(text='Grease Pencil:')
#             row = col.row(align=True)
#             row.prop(context.space_data.overlay, 'use_gpencil_grid', text = 'Canvas')
#             row.prop(context.scene.tool_settings.gpencil_sculpt, 'lock_axis', text = 'Axis')


# -----------------
### Register
# -----------------

classes = (
PSR_OT_RETARGET_draw_rig,
#PSR_PT_RETARGET_draw_rig_panel
)


def register():
    bpy.types.WindowManager.psr_retarget_align_on_x = bpy.props.BoolProperty(
        name="Align X to Normal", default=False, 
        description="Align X axis of the bone to the surface normal instead of Z")

    # bpy.types.WindowManager.psr_gp_rig = bpy.props.BoolProperty(
    #     name="Grease Pencil", default=False, 
    #     description="Use selected grease pencil surface if selected")

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for p in ['psr_retarget_align_on_x']:# 'psr_gp_rig'
        if p in bpy.context.window_manager:
            del bpy.context.window_manager[p]

