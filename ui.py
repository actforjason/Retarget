import bpy
from bpy.props import StringProperty
from bpy.props import BoolProperty
from bpy.props import FloatProperty
from bpy.props import PointerProperty,EnumProperty
from bpy.types import Context, Operator, Menu, Panel, UIList
from bl_operators.presets import AddPresetBase

from . import operators, bone_utils, support
from . import preset_handler
from .rigging import surface as rig_op
from .action import ops

def menu_header(layout):
    row = layout.row()
    row.separator()

    row = layout.row()
    row.label(text="Retarget", icon='ARMATURE_DATA')


class OP_ActivateRetargetTab(Operator):
    """Open Retarget tab in viewport"""
    bl_idname = "object.retarget_open_tab"
    bl_label = "Open Retarget Tab"
    bl_options = {'REGISTER', 'UNDO'}

    tab: EnumProperty(items=[
                            ("preset","Preset Tab",""),
                            ("action","Action Manager Tab",""),
                             ],
                             name="Tab",
                             default='action')

    def execute(self, context):
        if self.tab == "preset":
            tab = bpy.context.preferences.addons[
        __package__
    ].preferences.preset
        else:
            tab = bpy.context.preferences.addons[
        __package__
    ].preferences.action_manager
        target_area = None
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    target_area = area
                    break
            if target_area:
                break
        if not target_area:
            return {'CANCELLED'}
        
        view3d = next(space for space in target_area.spaces if space.type == 'VIEW_3D')
        view3d.show_region_ui = True

        def open_tab():
            region = next(r for r in target_area.regions if r.type == 'UI')
            try:
                if region.active_panel_category != tab:
                    region.active_panel_category = tab
                    region.tag_redraw()
                    target_area.tag_redraw()
            except AttributeError:
                pass

        bpy.app.timers.register(open_tab, first_interval=0.1)
        return {'FINISHED'}
    
class BindingsMenu(Menu):
    bl_label = "Binding"
    bl_idname = "OBJECT_MT_retarget_binding_menu"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(operators.ConstrainToArmature.bl_idname)

        row = layout.row()
        row.operator(operators.UnbindArmature.bl_idname)

        row = layout.row()
        row.operator(operators.ConstraintStatus.bl_idname)

        row = layout.row()
        row.operator(operators.SelectConstrainedControls.bl_idname)

        row = layout.row()
        row.operator(operators.AlignBone.bl_idname)

        row = layout.row()
        row.operator(operators.Mirror.bl_idname)

        row = layout.row()
        row.operator(operators.BindToMetarig.bl_idname)

        row = layout.row()
        row.prop(context.scene.retarget_action, "armature_mode", icon='ARMATURE_DATA')

        row = layout.row()
        row.operator(OP_ActivateRetargetTab.bl_idname)


class ConvertMenu(Menu):
    bl_label = "Conversion"
    bl_idname = "OBJECT_MT_retarget_convert_menu"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(operators.ConvertGameFriendly.bl_idname)

        row = layout.row()
        row.operator(operators.ConvertBoneNaming.bl_idname)

        row = layout.row()
        row.operator(operators.ExtractMetarig.bl_idname)

        row = layout.row()
        row.operator(operators.ApplyAsRestPose.bl_idname)

        row = layout.row()
        row.operator(operators.CreateTransformOffset.bl_idname)

        row = layout.row()
        row.operator(operators.ApplyRotation.bl_idname)

        row = layout.row()
        row.operator(operators.MergeHeadTails.bl_idname)


class AnimMenu(Menu):
    bl_label = "Animation"
    bl_idname = "OBJECT_MT_retarget_anim_menu"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(operators.ActionRangeToScene.bl_idname)

        row = layout.row()
        row.operator(operators.AdjustAnimation.bl_idname)

        row = layout.row()
        row.operator(operators.BakeConstrainedActions.bl_idname)

        row = layout.row()
        row.operator("object.retarget_action_import_fbx")

        row = layout.row()
        row.operator_context = 'INVOKE_DEFAULT'
        row.operator(operators.RenameActionsFromFbxFiles.bl_idname)

        row = layout.row()
        row.operator(operators.AddRoot.bl_idname)

        row = layout.row()
        row.operator(operators.AddRootMotion.bl_idname)

class Rigging(Menu):
    bl_label = "Rigging"
    bl_idname = "OBJECT_MT_retarget_rigging_menu"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("object.retarget_action_reset_transform")

        row = layout.row()
        row.operator(rig_op.PSR_OT_RETARGET_draw_rig.bl_idname)

def pose_context_options(self, context):
    layout = self.layout
    menu_header(layout)

    # use an operator enum property to populate a sub-menu
    layout.operator('wm.call_menu_pie', text="Pie Retarget").name = 'VIEW3D_MT_PIE_Retarget'
    layout.menu(BindingsMenu.bl_idname)
    layout.menu(ConvertMenu.bl_idname)
    layout.menu(AnimMenu.bl_idname)
    layout.menu(Rigging.bl_idname)

    layout.separator()


def armature_context_options(self, context):
    layout = self.layout
    menu_header(layout)

    row = layout.row()
    row.operator(operators.MergeHeadTails.bl_idname)


def action_header_buttons(self, context):
    layout = self.layout
    row = layout.row()
    row.operator(operators.ActionRangeToScene.bl_idname, icon='PREVIEW_RANGE', text='To Scene Range')

#nla option
class VIEW3D_PT_retarget_nla_range_option(Menu):
    bl_label = "NLA Option"
    bl_idname = "OBJECT_MT_retarget_nla_range_option"
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.prop(scene, "retarget_active_track")

        row = layout.row()
        row.prop(scene, "retarget_active_strip")

def action_nla_header_buttons(self, context):
    layout = self.layout
    scene = context.scene

    row = layout.row()

    op = row.operator(operators.ActionNlaRangeToScene.bl_idname, icon='PREVIEW_RANGE', text='NLA To Scene Range')
    op.active_track = scene.retarget_active_track
    op.active_strip = scene.retarget_active_strip

    row.menu(VIEW3D_PT_retarget_nla_range_option.bl_idname, text = '', icon='DOWNARROW_HLT')

#pie menu short cut

    
class VIEW3D_MT_PIE_Retarget(Menu):
    bl_idanme = 'VIEW3D_MT_PIE_Retarget'
    bl_label = "RETARGET"

    @classmethod
    def poll(cls, context):
        if context.mode not in ['POSE', 'OBJECT']:
            return False
       
        return True

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        
        gap = pie.column()

        menu = gap.box()
        my_text = "BINDING".center(40)
        menu.label(text= my_text, icon='LINKED')
        menu.operator(operators.ConstrainToArmature.bl_idname)
        menu.operator(operators.UnbindArmature.bl_idname)
        menu.operator(operators.ConstraintStatus.bl_idname)
        menu.operator(operators.SelectConstrainedControls.bl_idname)
        menu.operator(operators.AlignBone.bl_idname)
        menu.operator(operators.Mirror.bl_idname)
        menu.operator(operators.BindToMetarig.bl_idname)

        gap = pie.column()
    
        menu = gap.box()
        my_text = "CONVERSION".center(40)
        menu.label(text= my_text, icon='BONE_DATA')
        menu.operator(operators.ConvertGameFriendly.bl_idname)
        menu.operator(operators.ConvertBoneNaming.bl_idname)
        menu.operator(operators.ExtractMetarig.bl_idname)
        menu.operator(operators.ApplyAsRestPose.bl_idname)
        menu.operator(operators.CreateTransformOffset.bl_idname)
        menu.operator(operators.ApplyRotation.bl_idname)
        menu.operator(operators.MergeHeadTails.bl_idname)

        gap = pie.column()
        my_text = "Open Retarget Tab".center(40)
        gap.operator(OP_ActivateRetargetTab.bl_idname, text=my_text ,icon='UV_ISLANDSEL')

        menu = gap.box()
        my_text = "ANIMATION".center(40)
        menu.label(text= my_text, icon='OUTLINER_DATA_ARMATURE')
        menu.operator(operators.ActionRangeToScene.bl_idname)
        menu.operator(operators.AdjustAnimation.bl_idname)
        menu.operator(operators.BakeConstrainedActions.bl_idname)
        menu.operator("object.retarget_action_import_fbx")
        menu.operator(operators.AddRoot.bl_idname)
        menu.operator(operators.AddRootMotion.bl_idname)

        gap = pie.column()

        menu = gap.box()
        my_text = "RIGGING".center(40)
        menu.label(text= my_text, icon='CON_GEOMETRYATTRIBUTE')
        menu.operator("object.retarget_action_reset_transform")
        menu.operator(rig_op.PSR_OT_RETARGET_draw_rig.bl_idname)
        
        # gap = pie.column()
        # gap.separator()


        my_text = "ARMATURE MODE".center(40)
        gap.prop(context.scene.retarget_action, "armature_mode", text= my_text, icon='ARMATURE_DATA')

#---------

#rename action

class ActionRemoveRenameData(bpy.types.Operator):
    """Remove action rename data"""
    bl_idname = "object.retarget_remove_action_rename_data"
    bl_label = "Retarget remove rename data"

    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode in ['POSE', 'OBJECT']

    def execute(self, context):
        for action in bpy.data.actions:
            action.retarget_name_candidates.clear()

        return {'FINISHED'}


class ActionMakeActive(bpy.types.Operator):
    """Apply next action and adjust timeline"""
    bl_idname = "object.retarget_make_action_active"
    bl_label = "Retarget apply action"

    @classmethod
    def poll(cls, context):
        return context.mode in ['POSE', 'OBJECT']

    def execute(self, context):
        ob = ops.get_ob_or_armature(context, context.active_object)
        if not ob:
            return {'CANCELLED'}
        
        to_rename = [a for a in bpy.data.actions if len(a.retarget_name_candidates) > 1 and operators.validate_actions(a, ob.path_resolve)]

        if len(to_rename) == 0:
            return {'CANCELLED'}

        if not ob.animation_data.action:
            action = to_rename.pop()
        else:
            try:
                idx = to_rename.index(ob.animation_data.action)
            except ValueError:
                action = to_rename.pop()
            else:
                action = to_rename[idx - 1]

        ob.animation_data.action = action
        bpy.ops.object.retarget_action_to_range_custom()

        if context.scene.retarget_action.play and not context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()


        return {'FINISHED'}
    
class ActionRenameSimple(bpy.types.Operator):
    """Rename Current Action"""
    bl_idname = "object.retarget_rename_action_simple"
    bl_label = "Retarget Action Rename"
    bl_options = {'REGISTER', 'UNDO'}

    new_name: StringProperty(default="", name="Renamed to")

    @classmethod
    def poll(cls, context):
        ob = ops.get_ob_or_armature(context, context.active_object)
        if not ob:
            return False
        if ob.type != 'ARMATURE':
            return False
        if not ob.animation_data:
            return False
        if not ob.animation_data.action:
            return False

        return True

    def execute(self, context):
        ob = ops.get_ob_or_armature(context, context.active_object)
        action = ob.animation_data.action
        if self.new_name and action:
            action.name = self.new_name

        # remove candidate from other actions
        for other_action in bpy.data.actions:
            if other_action == action:
                continue
            idx = other_action.retarget_name_candidates.find(self.new_name)
            if idx > -1:
                other_action.retarget_name_candidates.remove(idx)
            if len(other_action.retarget_name_candidates) == 1:
                other_action.name = other_action.retarget_name_candidates[0].name

        action.retarget_name_candidates.clear()

        ops.update_action_list(context)
        
        return {'FINISHED'}
    

class VIEW3D_PT_retarget_rename_candidates(bpy.types.Panel):
    bl_label = "Action Name Candidates"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Retarget"
    bl_idname = "VIEW3D_PT_retarget_rename_candidates"

    @classmethod
    def poll(cls, context):
        if context.mode not in ['POSE', 'OBJECT']:
            return False

        try:
            next(a for a in bpy.data.actions if len(a.retarget_name_candidates) > 1)
        except StopIteration:
            return False

        return True

    def draw(self, context):
        layout = self.layout

        to_rename = [a for a in bpy.data.actions if len(a.retarget_name_candidates) > 1]

        row = layout.row()
        row.operator(ActionMakeActive.bl_idname, text="Next of {} actions to rename".format(len(to_rename)))

        ob = ops.get_ob_or_armature(context, context.active_object)
        action = ob and ob.animation_data and ob.animation_data.action
        if not action:
            return

        row = layout.row()
        row.label(text=action.name)

        for candidate in action.retarget_name_candidates:

            # if candidate.name in bpy.data.actions:
            #     # that name has been taken
            #     continue

            row = layout.row()
            op = row.operator(ActionRenameSimple.bl_idname, text=candidate.name)
            op.new_name = candidate.name


class VIEW3D_PT_retarget_rename_advanced(bpy.types.Panel):
    bl_label = "Advanced Options"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = VIEW3D_PT_retarget_rename_candidates.bl_idname

    @classmethod
    def poll(cls, context):
        if context.mode not in ['POSE', 'OBJECT']:
            return False

        to_rename = [a for a in bpy.data.actions if len(a.retarget_name_candidates) > 1]
        return len(to_rename) > 0

    def draw(self, context):
        row = self.layout.row()
        row.operator(ActionRemoveRenameData.bl_idname, text="Remove Rename Data")

#---------

class AddPresetArmatureRetarget(AddPresetBase, Operator):
    """Add a Bone Retarget Preset"""
    bl_idname = "object.retarget_armature_preset_add"
    bl_label = "Retarget Preset (select a armature)"
    preset_menu = "VIEW3D_MT_retarget_presets"

    # variable used for all preset values
    preset_defines = [
        "skeleton = bpy.context.object.data.retarget_retarget"
    ]

    # properties to store in the preset
    preset_values = [
        "skeleton.face",

        "skeleton.spine",
        "skeleton.right_arm",
        "skeleton.left_arm",
        "skeleton.right_leg",
        "skeleton.left_leg",

        "skeleton.left_fingers",
        "skeleton.right_fingers",

        "skeleton.right_arm_ik",
        "skeleton.left_arm_ik",

        "skeleton.right_leg_ik",
        "skeleton.left_leg_ik",

        "skeleton.deform_preset",
        "skeleton.root",
        "skeleton.other_bone",
    ]

    preset_subdir = preset_handler.PRESETS_SUBDIR

    def execute(self, context):

        o = support.get_ob_pined_or_not(context)
        if not o or o.type != 'ARMATURE':
            return {'FINISHED'}
        context.view_layer.objects.active = o
        super().execute(context)
        return {'FINISHED'}

class GuessRetarget(Operator):
    bl_idname = "object.retarget_guess"
    bl_label = "Guess Settings"
    bl_options = {'REGISTER', 'UNDO'}

    selected: BoolProperty(name="selected", default=False)

    skip_deform: BoolProperty(name="Skip Deform Bones",
                              description="Bones that deform the mesh",
                               default=False)
    has_shape: BoolProperty(name="Only Control Shapes",
                            description="Bones that have a custom display",
                            default=False)
    visible: BoolProperty(name="Visible",
                            description="Only visible bone",
                            default=False)

    starwith:StringProperty(name = "Start With", description="Bone Name Start With This Value", options = {'SKIP_SAVE'},
                            default="")
    
    dontstarwith:StringProperty(name = "Don't Start With", description="Bone Name Don't Start With This Value (separate with a comma)", options = {'SKIP_SAVE'},
                            default="")
    
    dontcontain:StringProperty(name = "Don't contain", description="Bone Name Don't contain This Value  (separate with a comma)", options = {'SKIP_SAVE'},
                            default="")

    @classmethod
    def poll(cls, context):
        ob = support.get_ob_pined_or_not(context)
        if not ob:
            return False
        if ob.type != 'ARMATURE':
            return False

        return True
    
    def execute(self, context):

        current_m = context.mode

        retarget_setting = context.scene.retarget_setting
        if retarget_setting.pin:
            armatures = [support.get_ob_pined_or_not(context)]
        else:
            armatures = ops.get_selected_obs(context)

        if self.dontstarwith:
            donts = self.dontstarwith.split(",")
        else:
            donts = []

        lowercase_list = [s.lower() for s in donts if s]

        if self.dontcontain:
            dontc = self.dontcontain.split(",")
        else:
            dontc = []

        dontcontain_list = [s.lower() for s in dontc if s]

        startwith = self.starwith.lower()

        for ob in armatures:

            if ob.type != 'ARMATURE':
                continue

            context.view_layer.objects.active = ob
            bpy.ops.object.mode_set(mode='POSE')

            preset_handler.guess(ob, startwith, lowercase_list, dontcontain_list, self.selected, self.skip_deform, self.has_shape, self.visible)

        bpy.ops.object.mode_set(mode= current_m)
        return {'FINISHED'}


class ClearArmatureRetarget(Operator):
    """Clean Only Bone Mapped In Body Section"""
    bl_idname = "object.retarget_armature_clear"
    bl_label = "Clear Retarget Settings"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = support.get_ob_pined_or_not(context)
        if not ob:
            return False
        if ob.type != 'ARMATURE':
            return False

        return True

    def execute(self, context):

        retarget_setting = context.scene.retarget_setting
        if retarget_setting.pin:
            armatures = [support.get_ob_pined_or_not(context)]
        else:
            armatures = ops.get_selected_obs(context)
        for ob in armatures:

            if ob.type != 'ARMATURE':
                continue

            skeleton = ob.data.retarget_retarget
            for setting in (skeleton.right_arm, skeleton.left_arm, skeleton.spine, skeleton.right_leg,
                            skeleton.left_leg, skeleton.right_arm_ik, skeleton.left_arm_ik,
                            skeleton.right_leg_ik, skeleton.left_leg_ik,
                            skeleton.face,
                            ):
                for k in setting.keys():
                    if k == 'name':
                        continue
                    try:
                        setattr(setting, k, '')
                    except TypeError:
                        continue

            for settings in (skeleton.right_fingers, skeleton.left_fingers):
                for setting in [getattr(settings, k) for k in settings.keys() if k != 'name']:

                    try:
                        for k in setting.keys():
                            if k == 'name':
                                continue
                            setattr(setting, k, '')
                    except AttributeError:
                        continue

            skeleton.root = ''
            skeleton.deform_preset = '--'

        return {'FINISHED'}


class SetToActiveBone(Operator):
    """Set adjacent UI entry to active bone"""
    bl_idname = "object.retarget_set_to_active_bone"
    bl_label = "Set Retarget value to active bone"

    attr_name: StringProperty(default="", options={'SKIP_SAVE'})
    sub_attr_name: StringProperty(default="", options={'SKIP_SAVE'})
    slot_name: StringProperty(default="", options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        if context.mode  == 'EDIT_ARMATURE':
            return False
        return True

    def execute(self, context):
        current_m = context.mode
        
        if not self.attr_name or not  context.active_pose_bone:
            bpy.ops.object.mode_set(mode= current_m)
            return {'FINISHED'}
        
        ob = support.get_ob_pined_or_not(context)
        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='POSE')

        skeleton = ob.data.retarget_retarget

        if not self.slot_name:
            if self.attr_name == 'root':
                setattr(skeleton, 'root', context.active_pose_bone.name)

            bpy.ops.object.mode_set(mode= current_m)
            return {'FINISHED'}

        try:
            rig_grp = getattr(skeleton, self.attr_name)
        except AttributeError:
            # TODO: warning
            bpy.ops.object.mode_set(mode= current_m)
            return {'FINISHED'}
        else:
            if self.sub_attr_name:
                rig_grp = getattr(rig_grp, self.sub_attr_name)
                
            setattr(rig_grp, self.slot_name, context.active_pose_bone.name)

        
        bpy.ops.object.mode_set(mode= current_m)
        return {'FINISHED'}


class MirrorSettings(Operator):
    """Mirror Settings to the other side"""
    bl_idname = "object.retarget_settings_mirror"
    bl_label = "Mirror Skeleton Mapping"
    bl_options = {'REGISTER', 'UNDO'}

    src_setting: StringProperty(default="", options={'SKIP_SAVE'})
    trg_setting: StringProperty(default="", options={'SKIP_SAVE'})

    use_name: BoolProperty(name="Use Name",
                                description= "Use the Name of the bone to quickly find other bone",
                                default= True)
    
    use_tolerance: BoolProperty(name="Use Tolerance",
                                default= False)

    tolerance: FloatProperty(default=0.0001)

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, 'src_setting')

        row = column.row()
        row.prop(self, 'trg_setting')

        row = column.row()
        row.prop(self, 'use_name')

        row = column.row()
        row.prop(self, 'use_tolerance')

        row = column.row()
        row.prop(self, 'tolerance')
        row.enabled = self.use_tolerance

    @classmethod
    def poll(cls, context):
        ob = support.get_ob_pined_or_not(context)
        if not ob:
            return False
        if ob.type != 'ARMATURE':
            return False
        if not ob.data.retarget_retarget:
            return False

        return True

    def _is_mirrored_vec(self, trg_head, src_head):
        epsilon = self.tolerance
        # if abs(trg_head.x + src_head.x) > epsilon:
        #     return False
        if abs(trg_head.y - src_head.y) > epsilon:
            return False
        return abs(trg_head.z - src_head.z) <= epsilon
    
    def _is_mirrored(self, src_bone, trg_bone):
        if not self._is_mirrored_vec(src_bone.head_local, trg_bone.head_local):
            return False
        if not self._is_mirrored_vec(src_bone.tail_local, trg_bone.tail_local):
            return False
        
        return True

    def find_mirrored(self, arm_data, bone):
        # TODO: should be in bone_utils
        # DONE: should select best among mirror candidates

        lookup_name = bone_utils.lrl_strip(bone)
        return next((b for b in arm_data.bones if (
                            bone != b
                            and (self.use_name and lookup_name == bone_utils.lrl_strip(b) or not self.use_name)
                            and (self.use_tolerance and self._is_mirrored(bone, b) or not self.use_tolerance)
                        )
                    ), None)

    def execute(self, context):
        ob = support.get_ob_pined_or_not(context)
        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        context.view_layer.objects.active = ob
        current_m = context.mode
        bpy.ops.object.mode_set(mode='POSE')

        if not self.src_setting:
            bpy.ops.object.mode_set(mode= current_m)
            return {'FINISHED'}
        if not self.trg_setting:
            bpy.ops.object.mode_set(mode= current_m)
            return {'FINISHED'}

        skeleton = ob.data.retarget_retarget

        try:
            src_grp = getattr(skeleton, self.src_setting)
        except AttributeError:
            # TODO: warning
            bpy.ops.object.mode_set(mode= current_m)
            return {'FINISHED'}
        
        try:
            trg_grp = getattr(skeleton, self.trg_setting)
        except AttributeError:
            # TODO: warning
            bpy.ops.object.mode_set(mode= current_m)
            return {'FINISHED'}

        arm_data = ob.data
        if 'fingers' in self.trg_setting:
            for finger_name in ('thumb', 'index', 'middle', 'ring', 'pinky'):
                for attr_name in ('a', 'b', 'c'):
                    bone_name = getattr(getattr(src_grp, finger_name), attr_name)
                    if not bone_name:
                        m_bone = None
                    else:
                        m_bone = self.find_mirrored(arm_data,
                                                    arm_data.bones[bone_name])
                    if  m_bone:
                        setattr(getattr(trg_grp, finger_name), attr_name, m_bone.name)
                    # else:
                    #     setattr(getattr(trg_grp, finger_name), attr_name, "")

            bpy.ops.object.mode_set(mode= current_m)
            return {'FINISHED'}

        for k, v in src_grp.items():

            if k == "name":
                continue

            if not v:
                bone = None
            else:
                try:
                    bone = arm_data.bones[v]
                except KeyError:
                    bone = None

            if bone:
                m_bone = self.find_mirrored(arm_data, bone)
            else:
                m_bone = None

            if m_bone:
                setattr(trg_grp, k, m_bone.name)
            # else:
            #     setattr(trg_grp, k, "")

        bpy.ops.object.mode_set(mode= current_m)
        return {'FINISHED'}


class SetPresetArmatureRetarget(Operator):
    """Apply a Bone Retarget Preset"""
    bl_idname = "object.expy_kit_armature_preset_apply"
    bl_label = "Apply Bone Retarget Preset"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE'},
    )
    menu_idname: StringProperty(
        name="Menu ID Name",
        description="ID name of the menu this was called from",
        options={'SKIP_SAVE'},
    )

    def execute(self, context):
        ob = support.get_ob_pined_or_not(context)
        if not ob:
            return {'FINISHED'}

        if ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        from os.path import basename, splitext
        filepath = self.filepath

        # change the menu title to the most recently chosen option
        preset_class = VIEW3D_MT_retarget_presets
        preset_class.bl_label = bpy.path.display_name(basename(filepath), title_case=False)

        ext = splitext(filepath)[1].lower()

        if ext not in {".py", ".xml"}:
            self.report({'ERROR'}, "Unknown file type: %r" % ext)
            return {'CANCELLED'}
        
        retarget_setting = context.scene.retarget_setting
        if retarget_setting.pin:
            armatures = [support.get_ob_pined_or_not(context)]
        else:
            armatures = ops.get_selected_obs(context)
        for src_object in armatures:

            if src_object.type != 'ARMATURE':
                continue
            context.view_layer.objects.active = src_object
            settings = src_object.data.retarget_retarget

            #reset retarget setting
            preset_handler.reset_setting(settings)

            if hasattr(preset_class, "reset_cb"):
                preset_class.reset_cb(context)

            if ext == ".py":
                try:
                    bpy.utils.execfile(filepath)
                except Exception as ex:
                    self.report({'ERROR'}, "Failed to set the preset: " + repr(ex))

            elif ext == ".xml":
                import rna_xml
                rna_xml.xml_file_run(context,
                                    filepath,
                                    preset_class.preset_xml_map)

            if hasattr(preset_class, "post_cb"):
                preset_class.post_cb(context)

            preset_handler.validate_preset(src_object.data, find=True)

            preset_handler.reset_preset_names(settings)

        return {'FINISHED'}
    
class VIEW3D_MT_retarget_presets(Menu):
    bl_label = "Retarget Presets"
    preset_subdir = AddPresetArmatureRetarget.preset_subdir
    #preset_operator = "script.execute_preset"
    preset_operator = SetPresetArmatureRetarget.bl_idname

    draw = Menu.draw_preset


class BindFromPanelSelection(Operator):
    """Constrain to armature selected in panel"""
    bl_idname = "object.retarget_bind_from_panel"
    bl_label = "Bind Armatures"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = support.get_ob_pined_or_not(context)
        return context.mode != 'EDIT_ARMATURE' and context.scene.retarget_bind_to and ob != context.scene.retarget_bind_to and ob.type == 'ARMATURE'
    
    def execute(self, context: Context):

        current_m = context.mode
        o = support.get_ob_pined_or_not(context)

        obs = ops.get_selected_obs(context)

        if not o in obs:
            obs.append(o)

        for ob in obs:
            if not ob.hide_viewport:
                ob.select_set(ob == o)
       
        if not context.scene.retarget_bind_to.hide_viewport and context.scene.retarget_bind_to.name in context.view_layer.objects:
            context.scene.retarget_bind_to.select_set(True)

        if len(obs) < 2:
            self.report({'WARNING'}, "A object is hidden")
            return {'FINISHED'}
        
        context.view_layer.objects.active = context.scene.retarget_bind_to

        if context.scene.retarget_bind_to.animation_data and context.scene.retarget_bind_to.animation_data.action:
            # TODO: this should be in the constrain operator
            bpy.ops.object.retarget_action_to_range()

        bpy.ops.object.mode_set(mode= current_m)
        
        bpy.ops.armature.retarget_constrain_to_armature('INVOKE_DEFAULT', force_dialog=True)

        return {'FINISHED'}


class VIEW3D_PT_Preset(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Retarget"
    bl_label = "Preset"
    bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout
        column = layout.column()

        ob = support.get_ob_pined_or_not(context)
        if not ob or ob.type != 'ARMATURE':
            return
        
        #test if its local
        if ob.library is not None:
            column.label(text=f"make '{ob.name}' local to change its setting", icon='ERROR')
            column.separator()

        retarget_setting = context.scene.retarget_setting

        setting = ob.data.retarget_retarget
        skeleton = preset_handler.get_settings_skel(setting)
        number_bone = len(skeleton.bone_names())

        row = column.row()
        row.alignment = "CENTER"
        row.label(text = ob.name, translate=False, icon='ARMATURE_DATA')
        row.label(text = f'{number_bone} Bone(s) Mapped')
        icon = 'PINNED' if retarget_setting.pin else 'UNPINNED'
        row.prop(retarget_setting, "pin", text='', icon=icon)

        row.operator(support.Armature_OT_copy_setting.bl_idname, text='', icon='COPYDOWN')
        row.operator(support.Armature_OT_paste_setting.bl_idname, text='', icon='PASTEDOWN')
        row.operator(support.Armature_OT_reset_setting.bl_idname, text='', icon='TRASH')

        split = layout.split(factor=0.75)
        split.menu(VIEW3D_MT_retarget_presets.__name__, text=VIEW3D_MT_retarget_presets.bl_label)
        row = split.row(align=True)
        row.operator(AddPresetArmatureRetarget.bl_idname, text="+")
        row.operator(AddPresetArmatureRetarget.bl_idname, text="-").remove_active = True


class VIEW3D_PT_BindPanel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Retarget"
    bl_label = "Bind To"
    bl_parent_id = 'VIEW3D_PT_Preset'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.mode  != 'EDIT_ARMATURE'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, 'retarget_bind_to', text="")

        layout.operator(BindFromPanelSelection.bl_idname)

class VIEW3D_PT_Body(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Retarget"
    bl_label = "Body"
    bl_parent_id = 'VIEW3D_PT_Preset'
    bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout

class RetargetBasePanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'VIEW3D_PT_Body'

    @classmethod
    def poll(cls, context):
        return context.mode != 'EDIT_ARMATURE'

    def sided_rows(self, ob, limbs, bone_names, suffix=""):
        split = self.layout.split()

        labels = None
        side = 'right'
        for group in limbs:
            attr_tokens = [side, group.name]
            attr_suffix = suffix.strip(' ').lower()
            if attr_suffix:
                attr_tokens.append(attr_suffix)

            attr_name = '_'.join(attr_tokens)
            
            col = split.column()
            row = col.row()
            if not labels:
                row.label(text=side.title())
                labels = split.column()
                row = labels.row()

                mirror_props = row.operator(MirrorSettings.bl_idname, text="<--")
                mirror_props.trg_setting = attr_name

                mirror_props_2 = row.operator(MirrorSettings.bl_idname, text="-->")
                mirror_props_2.src_setting = attr_name
                side = 'left'
            else:
                mirror_props.src_setting = attr_name
                mirror_props_2.trg_setting = attr_name
                row.label(text=side.title())

            for k in bone_names:
                bsplit = col.split(factor=0.85)
                bsplit.prop_search(group, k, ob.data, "bones", text="")

                props = bsplit.operator(SetToActiveBone.bl_idname, text="<-")
                props.attr_name = attr_name
                props.slot_name = k

        for k in bone_names:
            row = labels.row()
            row.label(text=(k + suffix).title())


class VIEW3D_PT_retarget_retarget_face(RetargetBasePanel, Panel):
    bl_label = "Face"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ob = support.get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return
        layout = self.layout

        if not context.active_object or ob.type != 'ARMATURE':
            return
        
        skeleton = ob.data.retarget_retarget

        bsplit = layout.split(factor=0.85)
        bsplit.prop_search(skeleton.face, "jaw", ob.data, "bones", text="Jaw")
        props = bsplit.operator(SetToActiveBone.bl_idname, text="<-")
        props.attr_name = 'face'
        props.slot_name = 'jaw'

        split = layout.split()
        col = split.column()
        col.label(text="Right")

        bsplit = col.split(factor=0.85)
        col = bsplit.column()
        col.prop_search(skeleton.face, "right_eye", ob.data, "bones", text="")
        col.prop_search(skeleton.face, "right_upLid", ob.data, "bones", text="")

        col = bsplit.column()
        eye_props = col.operator(SetToActiveBone.bl_idname, text="<-")
        eye_props.attr_name = 'face'
        eye_props.slot_name = 'right_eye'

        eye_props = col.operator(SetToActiveBone.bl_idname, text="<-")
        eye_props.attr_name = 'face'
        eye_props.slot_name = 'right_upLid'

        col = split.column()
        col.label(text="")
        col.label(text="Eye")
        col.label(text="Up Lid")

        col = split.column()
        col.label(text="Left")

        bsplit = col.split(factor=0.85)
        col = bsplit.column()
        col.prop_search(skeleton.face, "left_eye", ob.data, "bones", text="")
        col.prop_search(skeleton.face, "left_upLid", ob.data, "bones", text="")

        col = bsplit.column()
        eye_props = col.operator(SetToActiveBone.bl_idname, text="<-")
        eye_props.attr_name = 'face'
        eye_props.slot_name = 'left_eye'

        eye_props = col.operator(SetToActiveBone.bl_idname, text="<-")
        eye_props.attr_name = 'face'
        eye_props.slot_name = 'left_upLid'

        row = layout.row()
        row.prop(skeleton.face, "super_copy", text="As Rigify Super Copy")


class VIEW3D_PT_retarget_retarget_fingers(RetargetBasePanel, Panel):
    bl_label = "Fingers"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ob = support.get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return
        
        layout = self.layout

        if not ob or ob.type != 'ARMATURE':
            return
        
        skeleton = ob.data.retarget_retarget
        
        sides = "right", "left"
        split = layout.split()
        finger_bones = ('a', 'b', 'c')
        fingers = ('thumb', 'index', 'middle', 'ring', 'pinky')
        m_props = []
        for side, group in zip(sides, [skeleton.right_fingers, skeleton.left_fingers]):
            col = split.column()
            m_props.append(col.operator(MirrorSettings.bl_idname, text="<--" if side == 'right' else "-->"))

            for k in fingers:
                if k == 'name':  # skip Property Group name
                    continue
                row = col.row()
                row.label(text=" ".join((side, k)).title())
                finger = getattr(group, k)
                for slot in finger_bones:
                    bsplit = col.split(factor=0.85)
                    bsplit.prop_search(finger, slot, ob.data, "bones", text="")
                    
                    f_props = bsplit.operator(SetToActiveBone.bl_idname, text="<-")
                    f_props.attr_name = '_'.join([side, group.name])
                    f_props.sub_attr_name = k
                    f_props.slot_name = slot

        m_props[0].trg_setting = "right_fingers"
        m_props[0].src_setting = "left_fingers"

        m_props[1].trg_setting = "left_fingers"
        m_props[1].src_setting = "right_fingers"


class VIEW3D_PT_retarget_retarget_arms_IK(RetargetBasePanel, Panel):
    bl_label = "Arms IK"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ob = support.get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return
        layout = self.layout

        try:

            skeleton = ob.data.retarget_retarget
            arm_bones = ('arm', 'hand')
            #arm_bones = ('shoulder', 'arm', 'forearm', 'hand')

            self.sided_rows(ob, (skeleton.right_arm_ik, skeleton.left_arm_ik), arm_bones, suffix=" IK")
        except AttributeError:
            pass

class VIEW3D_PT_retarget_retarget_arms(RetargetBasePanel, Panel):
    bl_label = "Arms"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ob = support.get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return
        layout = self.layout

        try:

            skeleton = ob.data.retarget_retarget

            row = layout.row()
            row.prop(context.scene.retarget_setting, "twist_on", text="Display Twist Bones")
            
            if context.scene.retarget_setting.twist_on:
                arm_bones = ('shoulder', 'arm', 'arm_twist', 'arm_twist_02', 'forearm', 'forearm_twist', 'forearm_twist_02', 'hand')
            else:
                arm_bones = ('shoulder', 'arm', 'forearm', 'hand')

            self.sided_rows(ob, (skeleton.right_arm, skeleton.left_arm), arm_bones)
        except AttributeError:
            pass

class VIEW3D_PT_retarget_retarget_spine(RetargetBasePanel, Panel):
    bl_label = "Spine"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ob = support.get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return
        layout = self.layout

        try:

            skeleton = ob.data.retarget_retarget

            for slot in ('head', 'neck', 'spine2', 'spine1', 'spine', 'hips'):
                split = layout.split(factor=0.85)
                split.prop_search(skeleton.spine, slot, ob.data, "bones", text="Chest" if slot == 'spine2' else slot.title())
                props = split.operator(SetToActiveBone.bl_idname, text="<-")
                props.attr_name = 'spine'
                props.slot_name = slot
        except AttributeError:
            pass

class VIEW3D_PT_retarget_retarget_leg_IK(RetargetBasePanel, Panel):
    bl_label = "Legs IK"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ob = support.get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return
        
        try:

            skeleton = ob.data.retarget_retarget
            
            leg_bones = ('upleg', 'foot', 'toe', 'foot_spin', 'foot_heel')
            #leg_bones = ('upleg', 'leg', 'foot', 'toe', 'foot_spin', 'foot_heel')
            self.sided_rows(ob, (skeleton.right_leg_ik, skeleton.left_leg_ik), leg_bones, suffix=" IK")
        except AttributeError:
            pass

class VIEW3D_PT_retarget_retarget_leg(RetargetBasePanel, Panel):
    bl_label = "Legs"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ob = support.get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return

        try:

            skeleton = ob.data.retarget_retarget

            row = self.layout.row(align=True)
            row.prop(context.scene.retarget_setting, "twist_on", text="Display Twist Bones")

            if context.scene.retarget_setting.twist_on:
                leg_bones = ('upleg', 'upleg_twist', 'upleg_twist_02', 'leg', 'leg_twist', 'leg_twist_02', 'foot', 'toe')
            else:
                leg_bones = ('upleg', 'leg', 'foot', 'toe')

            self.sided_rows(ob, (skeleton.right_leg, skeleton.left_leg), leg_bones)
        except AttributeError:
            pass

class VIEW3D_PT_retarget_retarget_root(RetargetBasePanel, Panel):
    bl_label = "Root"

    def draw(self, context):
        ob = support.get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return
        
        layout = self.layout

        try:

            skeleton = ob.data.retarget_retarget

            split = layout.split(factor=0.85)
            split.prop_search(skeleton, 'root', ob.data, "bones", text="Root")
            s_props = split.operator(SetToActiveBone.bl_idname, text="<-")
            s_props.attr_name = 'root'
            s_props.sub_attr_name = ''

            layout.separator()
            row = layout.row()
            row.prop(skeleton, 'deform_preset')

            row = layout.row()
            row.operator(GuessRetarget.bl_idname, text="Guess Settings", icon='SHADERFX')

            row = layout.row()
            row.operator(ClearArmatureRetarget.bl_idname, text="Clear All", icon='PANEL_CLOSE')

        except AttributeError:
            pass
class VIEW3D_UL_Other_bone_list(UIList):

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        items_sorted = bpy.types.UI_UL_list.sort_items_by_name(items, "name")

        
        retarget_setting = context.scene.retarget_setting

        if retarget_setting.sort_bone_name:
            items_sorted = bpy.types.UI_UL_list.sort_items_by_name(items, "bone_name")

        if retarget_setting.sort_limb:
            items_sorted = bpy.types.UI_UL_list.sort_items_by_name(items, "limb")

        filtered = [self.bitflag_filter_item] * len(items)
        for i, item in enumerate(items):

            if not support.correct_bones(item, context):
                filtered[i] &= ~self.bitflag_filter_item

        support.filter_name = ''
        support.use_filter_invert = False
        return filtered, items_sorted


    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align=True)

        row.prop(item, "name", text="",emboss=False, icon='GROUP_BONE')

        ob = support.get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return

        retarget_setting = context.scene.retarget_setting

        if retarget_setting.show_bone_name:
            row.prop_search(item, "bone_name", ob.data, "bones", text='')

        subrow = row.row()
        subrow.alignment = "RIGHT"

        if retarget_setting.show_eye_dropper:
            subrow.prop(item, "eye_dropper", text='', emboss=False, icon = "RESTRICT_SELECT_OFF")

        if retarget_setting.show_ik:
            subrow.prop(item, "ik", toggle=True)
            if item.ik:
                subrow.prop_search(item, "target", ob.data, "bones", text='')
        
        if retarget_setting.show_loc:
            subrow.prop(item, "loc", toggle=True)
        
        if retarget_setting.show_limb:
            subrow.prop(item, "limb", text='' , icon='TAG', emboss=False)
        
        if retarget_setting.show_hidden:
            if item.is_hidden:
                subrow.prop(item, "is_hidden", text='' , icon='HIDE_ON', emboss=False)
            else:
                subrow.prop(item, "is_hidden", text='' , icon='HIDE_OFF', emboss=False)

        if item.is_selected:
            row.prop(item, "is_selected", text="", icon='CHECKBOX_HLT', emboss=False)
        else:
            row.prop(item, "is_selected", text="", icon='CHECKBOX_DEHLT', emboss=False)

        support.filter_name = self.filter_name
        support.use_filter_invert = self.use_filter_invert


class VIEW3D_PT_other_bone_panel(Panel):
    bl_label = "Other Bone"
    bl_idname = "VIEW3D_PT_retarget_other_bone_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'VIEW3D_PT_Preset'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.mode != 'EDIT_ARMATURE'
    
    def draw(self, context):
        layout = self.layout
        column = layout.column()

        retarget_setting = context.scene.retarget_setting

        #title
        ob = support.get_ob_pined_or_not(context)

        number_bone = len(support.get_view_bone(context))
        number_selected = len(support.get_selected_bone(context))
        icon_F='NONE'

        if any((
            retarget_setting.filt_bone,
            retarget_setting.filt_limb,
            retarget_setting.filt_with_limb,
            retarget_setting.filt_not_limb,
            retarget_setting.filt_ik,
            retarget_setting.filt_not_ik,
            retarget_setting.filt_loc,
            retarget_setting.filt_not_loc,
            retarget_setting.filt_with_bone_name,
            retarget_setting.filt_With_not_bone_name,
            retarget_setting.filt_hidden,
            retarget_setting.filt_no_hidden,
            retarget_setting.filt_selected,
            retarget_setting.filt_not_selected,
            support.filter_name,
        )):
            icon_F = 'FILTER'

        row = column.row()
        row.alignment = "CENTER"
        row.label(text = f'{number_bone} Bone(s)', icon=icon_F)
        row.label(text = f'{number_selected} Selected')
        
        if not ob or ob.type != 'ARMATURE':
            return
    
        skeleton = ob.data.retarget_retarget

        row = column.row()
        row.template_list("VIEW3D_UL_Other_bone_list", "", skeleton, "other_bone", skeleton, "other_bone_id")

        #side view
        if retarget_setting.side_view:
            col = row.column(align=True)
            col.menu(support.VIEW3D_PT_retarget_add_bone.bl_idname, text='', icon='ADD')
            col.separator()
            col.operator(support.Armature_OT_select_all_armature.bl_idname, text='', icon='CHECKBOX_HLT')
            col.operator(support.Armature_OT_deselect_all_armature.bl_idname, text='', icon='CHECKBOX_DEHLT')
            col.operator(support.Armature_OT_inverse_selection.bl_idname, text='', icon='ARROW_LEFTRIGHT')
            col.operator(support.Armature_OT_select_select_bone.bl_idname, text='', icon='BONE_DATA')
            col.operator(support.Armature_OT_op_select_bone.bl_idname, text='', icon='CON_ARMATURE')
            col.separator()
            col.operator(support.VIEW3D_PT_retarget_view_setting_bone.bl_idname, text='', icon='RESTRICT_VIEW_OFF')
            col.operator(support.VIEW3D_PT_retarget_filter_bone.bl_idname, text='', icon='FILTER')
            col.operator(support.VIEW3D_PT_retarget_sort_bone.bl_idname, text='', icon='SORTALPHA')

            col.separator()
            col.menu(support.VIEW3D_PT_retarget_select_bone.bl_idname, text='', icon='CHECKMARK')
            col.menu(support.VIEW3D_PT_retarget_ops_bone.bl_idname, text='', icon='TOOL_SETTINGS')

        #view setting
        row = column.row()
        if retarget_setting.expand_list_view:
            row.prop(retarget_setting, "expand_list_view", icon='DOWNARROW_HLT')
            column.separator()

            #Show
            row = column.row()
            row.alignment = "CENTER"

            row.prop(retarget_setting, "show_bone_name", text='', icon='BONE_DATA')
            row.prop(retarget_setting, "show_eye_dropper", text='', icon='RESTRICT_SELECT_OFF')
            row.prop(retarget_setting, "show_ik", toggle=True)
            row.prop(retarget_setting, "show_loc", toggle=True)
            row.prop(retarget_setting, "show_limb", text='', icon='TAG')
            row.prop(retarget_setting, "show_hidden", text='', icon='HIDE_OFF')
            row.prop(retarget_setting, "side_view", text='', icon='UV_ISLANDSEL')

            #sort by
            row = column.row()
            row.label(text = 'Sort By', icon='SORTALPHA')

            row = column.row()
            row.alignment = "CENTER"
            row.prop(retarget_setting, "sort_bone_name", text="", icon='BONE_DATA')
            row.prop(retarget_setting, "sort_limb", text="", icon='TAG')
            #filter

            row = column.row()
            row.label(text = 'Filter', icon='FILTER')

            row = column.row()
            row.prop(retarget_setting, "filt_bone", icon='BONE_DATA')
            if retarget_setting.filt_bone:
                row = column.row()
                row.prop(retarget_setting, "filt_bone_name")

            row = column.row()
            row.prop(retarget_setting, "filt_limb", icon='TAG')
            if retarget_setting.filt_limb:
                row = column.row()
                row.prop(retarget_setting, "filt_limb_search_option", text="", icon="SYNTAX_ON")
                if retarget_setting.filt_limb_search_option:
                    row.prop(retarget_setting, "filt_limb_name")
                else:
                    row.prop(retarget_setting, "filt_limb_name_")
            
            column.separator()
            row = column.row()
            row.alignment = "CENTER"

            row.prop(retarget_setting, "filt_with_limb", text="", icon='RESTRICT_COLOR_OFF')
            row.prop(retarget_setting, "filt_not_limb", text="", icon='RESTRICT_COLOR_ON')
            
            row.prop(retarget_setting, "filt_not_ik", icon='CHECKBOX_HLT')
            row.prop(retarget_setting, "filt_ik", icon='CHECKBOX_DEHLT')

            row.prop(retarget_setting, "filt_not_loc", icon='CHECKBOX_HLT')
            row.prop(retarget_setting, "filt_loc", icon='CHECKBOX_DEHLT')

            row.prop(retarget_setting, "filt_With_not_bone_name", text="", icon='CON_ARMATURE')
            row.prop(retarget_setting, "filt_with_bone_name", text="", icon='ARMATURE_DATA')

            row.prop(retarget_setting, "filt_no_hidden", text="", icon='HIDE_OFF')
            row.prop(retarget_setting, "filt_hidden", text="", icon='HIDE_ON')

            row.prop(retarget_setting, "filt_not_selected", text="", icon='CHECKBOX_HLT')
            row.prop(retarget_setting, "filt_selected", text="", icon='CHECKBOX_DEHLT')

        else:
            row.prop(retarget_setting, "expand_list_view", icon='RIGHTARROW')

        #operation/select
        row = column.row()
        row.menu(support.VIEW3D_PT_retarget_select_bone.bl_idname, icon='CHECKMARK')

        row.menu(support.VIEW3D_PT_retarget_ops_bone.bl_idname, icon='TOOL_SETTINGS')



def poll_armature_bind_to(self, object):
    ob = support.get_ob_pined_or_not(bpy.context)
    return object != ob and object.type == 'ARMATURE' 


classes = (
     OP_ActivateRetargetTab,
     GuessRetarget,
	 ClearArmatureRetarget,
	 VIEW3D_MT_retarget_presets,
     SetPresetArmatureRetarget,
	 AddPresetArmatureRetarget,
	 SetToActiveBone,
	 MirrorSettings,
	 BindingsMenu,
	 ConvertMenu,
	 AnimMenu,
     Rigging,

	 BindFromPanelSelection,
     VIEW3D_PT_Preset,
	 VIEW3D_PT_BindPanel,
     VIEW3D_PT_Body,
	 VIEW3D_PT_retarget_retarget_face,
	 VIEW3D_PT_retarget_retarget_fingers,
	 VIEW3D_PT_retarget_retarget_arms,
	 VIEW3D_PT_retarget_retarget_arms_IK,
	 VIEW3D_PT_retarget_retarget_leg,
	 VIEW3D_PT_retarget_retarget_leg_IK,
	 VIEW3D_PT_retarget_retarget_spine,
	 VIEW3D_PT_retarget_retarget_root,

     VIEW3D_MT_PIE_Retarget,

     VIEW3D_PT_retarget_nla_range_option,

     VIEW3D_UL_Other_bone_list,
     VIEW3D_PT_other_bone_panel,
)

classes_candidate = (
    ActionRenameSimple,
    ActionMakeActive,
    ActionRemoveRenameData,
    VIEW3D_PT_retarget_rename_candidates,
    VIEW3D_PT_retarget_rename_advanced,
)
def register_classes_c():
    for cls in classes_candidate:
        bpy.utils.register_class(cls)
def unregister_classes_c():
     for cls in reversed(classes_candidate):
        bpy.utils.unregister_class(cls)

def register_classes():
    bpy.types.Scene.retarget_bind_to = bpy.props.PointerProperty(type=bpy.types.Object,
                                                                name="Bind To",
                                                                poll=poll_armature_bind_to,
                                                                description="This armature will drive another one.")
    bpy.types.Scene.retarget_active_track = BoolProperty(name="Only Active Track", 
                                                         description="Scene range only to the active track",
                                                         default=False)                                                     
    bpy.types.Scene.retarget_active_strip = BoolProperty(name="Only Active Strip",
                                                          description="Scene range only to the active strip",
                                                          default=False) 

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_pose_context_menu.append(pose_context_options)
    bpy.types.VIEW3D_MT_object_context_menu.append(pose_context_options)
    bpy.types.VIEW3D_MT_armature_context_menu.append(armature_context_options)
    # bpy.types.DOPESHEET_HT_header.append(action_header_buttons)
    # bpy.types.GRAPH_HT_header.append(action_header_buttons)
    # bpy.types.NLA_MT_editor_menus.append(action_nla_header_buttons)


def unregister_classes():

    bpy.types.VIEW3D_MT_pose_context_menu.remove(pose_context_options)
    bpy.types.VIEW3D_MT_object_context_menu.remove(pose_context_options)
    bpy.types.VIEW3D_MT_armature_context_menu.remove(armature_context_options)
    # bpy.types.DOPESHEET_HT_header.remove(action_header_buttons)
    # bpy.types.GRAPH_HT_header.remove(action_header_buttons)
    # bpy.types.NLA_MT_editor_menus.remove(action_nla_header_buttons)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.retarget_bind_to
    del bpy.types.Scene.retarget_active_track
    del bpy.types.Scene.retarget_active_strip

