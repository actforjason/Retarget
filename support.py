import bpy
from bpy.types import Operator, Menu, Panel
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty, EnumProperty
from bpy_extras import anim_utils
from .action import ops
from. import preset_handler, bone_utils

#op -----------------------
filter_name = ""
use_filter_invert = False

class Armature_OT_add_bone(Operator):
    bl_idname = "object.retarget_armature_add_armature"
    bl_label = "Add a New Bone"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):

        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return  {'FINISHED'}
        
        skeleton = ob.data.retarget_retarget
        item = skeleton.other_bone.add()

        #find unique name
        name = "bone"
        i = 1
        while True:
            find = False
            for it in skeleton.other_bone:
                if it.name == name:
                    name = "bone."+str(i)
                    i = i + 1
                    find = True
            if not find:
                break

        item.name = name

        #set the focus
        for i, it in enumerate(skeleton.other_bone):
            if it.name == item.name:
                skeleton.other_bone_id = i
                break
        
        return {'FINISHED'}
    
class Armature_OT_add_other_bone(Operator):
    """Add Bone Of the Armature"""
    bl_idname = "object.retarget_armature_add_other_bone"
    bl_label = "Add Other Bone"
    bl_options = {'REGISTER', 'UNDO'}

    no_mapped: BoolProperty(name="No Mapped", 
                            description="Add Bone That are not Mapped",
                            default=True)

    selected: BoolProperty(name="selected", default=False)

    only_animated_Bone: BoolProperty(name="Only Animated Bone",
                               default=False)

    skip_deform: BoolProperty(name="Skip Deform Bones",
                              description="Bones that deform the mesh",
                               default=False)
    has_shape: BoolProperty(name="Only Control Shapes",
                            description="Bones that have a custom display",
                            default=False)
    visible: BoolProperty(name="Visible",
                            description="Only visible bone",
                            default=False)

    def execute(self, context):

        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        action = None
        channelbag = None

        if ob.animation_data and ob.animation_data.action:
            action = ob.animation_data.action
            channelbag = anim_utils.action_get_channelbag_for_slot(action, ob.animation_data.action_slot)

        if self.only_animated_Bone and not (action and channelbag):
            return {'FINISHED'}
        
        setting = ob.data.retarget_retarget
        
        skeleton = preset_handler.get_settings_skel(setting)

        mapped = skeleton.bone_names()

        for bone in ob.pose.bones:

            if self.no_mapped and bone.name in mapped:
                continue

            if self.selected and not bone.select:
                continue

            if self.only_animated_Bone and (not channelbag or bone.name not in channelbag.groups):
                continue

            if self.skip_deform and bone.bone.use_deform:
                continue

            if self.has_shape and not bool(bone.custom_shape):
                continue

            if self.visible and not bone_utils.visible_bone(bone):
                continue

            name = bone.name.split(":")[-1]
            find = False

            for item in setting.other_bone:
                if item.name == name:
                    find = True
                    break
                
            if find:
                continue

            item_bone = setting.other_bone.add()
            item_bone.name = bone.name.split(":")[-1]
            item_bone.bone_name = bone.name
        
        return {'FINISHED'}


class Armature_OT_copy_setting(Operator):
    """Copy The Setting of The Armature"""
    bl_idname = "object.retarget_armature_copy_setting"
    bl_label = "Copy The Setting"
    bl_options = {'REGISTER', 'UNDO'}

    only_other_bone: BoolProperty(name="Copy Only Other Bone", default=False)

    @classmethod
    def poll(cls, context):

        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return False
        
        return True
    
    def execute(self, context):
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        retarget_setting = context.scene.retarget_setting
        
        trg_setting = ob.data.retarget_retarget
        src_setting = retarget_setting.tmp_setting

        #reset the setting
        preset_handler.reset_setting(src_setting)

        if not self.only_other_bone:

            src_setting.root = trg_setting.root
            src_setting.deform_preset = trg_setting.deform_preset

            for group in ('spine', 'left_arm', 'left_arm_ik', 'right_arm', 'right_arm_ik',
                        'right_leg', 'right_leg_ik', 'left_leg', 'left_leg_ik', 'face'):

                trg_group = getattr(trg_setting, group)
                scr_group = getattr(src_setting, group)


                for k in trg_group.keys():

                    if k.startswith("__") or k in ["bl_rna", "type", "name"]:
                        continue
                    
                    try:
                        v = getattr(trg_group, k)
                        setattr(scr_group, k, v)
                    except TypeError:
                        continue
            
            for group in ('thumb', 'index', 'middle', 'ring', 'pinky'):

                trg_group = getattr(trg_setting.left_fingers, group)
                scr_group = getattr(src_setting.left_fingers, group)
                for k in trg_group.keys():
                    if not k:
                        continue
                    if k.startswith("__") or k in ["bl_rna", "type", "name"]:
                        continue
                    try:
                        v = getattr(trg_group, k)
                        setattr(scr_group, k, v)
                    except:
                        continue

                trg_group = getattr(trg_setting.right_fingers, group)
                scr_group = getattr(src_setting.right_fingers, group)
                for k in trg_group.keys():
                    if not k:
                        continue
                    if k.startswith("__") or k in ["bl_rna", "type", "name"]:
                        continue
                    try:
                        v = getattr(trg_group, k)
                        setattr(scr_group, k, v)
                    except:
                        continue

        for item in trg_setting.other_bone:
             
            item_bone = src_setting.other_bone.add()
            item_bone.name = item.name
            item_bone.bone_name = item.bone_name
            item_bone.ik = item.ik
            item_bone.target = item.target
            item_bone.loc = item.loc
            item_bone.limb = item.limb
            item_bone.is_hidden = item.is_hidden
            item_bone.is_selected = item.is_selected
        
        return {'FINISHED'}

class Armature_OT_paste_setting(Operator):
    """Paste The Setting On selected Armature(s)"""
    bl_idname = "object.retarget_armature_paste_setting"
    bl_label = "Paste The Setting"
    bl_options = {'REGISTER', 'UNDO'}

    overwrite_Setting: BoolProperty(name="Overwrite Other Bone Setting", default=True)

    @classmethod
    def poll(cls, context):


        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return False
        
        retarget_setting = context.scene.retarget_setting

        if not retarget_setting.tmp_setting.has_settings():
            return False
        
        return True
    
    def execute(self, context):
        o = get_ob_pined_or_not(context)

        if not o or o.type != 'ARMATURE':
            return {'FINISHED'}
        
        retarget_setting = context.scene.retarget_setting
        if not retarget_setting.tmp_setting.has_settings():
            return {'FINISHED'}
        
        if retarget_setting.pin:
            armatures = [get_ob_pined_or_not(context)]
        else:
            armatures = ops.get_selected_obs(context)

        for ob in armatures:

            if not ob or ob.type != 'ARMATURE':
                continue
        
            trg_setting = retarget_setting.tmp_setting
            src_setting = ob.data.retarget_retarget

            #reset the setting

            if trg_setting.root and not src_setting.root:
                src_setting.root = trg_setting.root

            if trg_setting.deform_preset and not src_setting.deform_preset:
                src_setting.deform_preset = trg_setting.deform_preset

            for group in ('spine', 'left_arm', 'left_arm_ik', 'right_arm', 'right_arm_ik',
                        'right_leg', 'right_leg_ik', 'left_leg', 'left_leg_ik', 'face'):

                trg_group = getattr(trg_setting, group)
                scr_group = getattr(src_setting, group)


                for k in trg_group.keys():

                    if k.startswith("__") or k in ["bl_rna", "type", "name"]:
                        continue
                    
                    try:
                        v_s = getattr(scr_group, k)

                        if v_s:
                            continue

                        v = getattr(trg_group, k)

                        if not v:
                            continue

                        setattr(scr_group, k, v)
                    except TypeError:
                        continue
            
            for group in ('thumb', 'index', 'middle', 'ring', 'pinky'):

                trg_group = getattr(trg_setting.left_fingers, group)
                scr_group = getattr(src_setting.left_fingers, group)
                for k in trg_group.keys():
                    if not k:
                        continue
                    if k.startswith("__") or k in ["bl_rna", "type", "name"]:
                        continue
                    try:
                        v_s = getattr(scr_group, k)

                        if v_s:
                            continue

                        v = getattr(trg_group, k)

                        if not v:
                            continue

                        setattr(scr_group, k, v)
                    except:
                        continue

                trg_group = getattr(trg_setting.right_fingers, group)
                scr_group = getattr(src_setting.right_fingers, group)
                for k in trg_group.keys():
                    if not k:
                        continue
                    if k.startswith("__") or k in ["bl_rna", "type", "name"]:
                        continue
                    try:
                        v_s = getattr(scr_group, k)

                        if v_s:
                            continue

                        v = getattr(trg_group, k)

                        if not v:
                            continue

                        setattr(scr_group, k, v)
                    except:
                        continue

            for item in trg_setting.other_bone:
                find = False
                for it in src_setting.other_bone:
                    if it.name == item.name:
                        if self.overwrite_Setting:
                            it.ik = item.ik
                            it.target = item.target
                            it.loc = item.loc
                            it.limb = item.limb
                            it.is_hidden = item.is_hidden
                            it.is_selected = item.is_selected
                        find = True
                        break

                if find:
                    continue
                
                item_bone = src_setting.other_bone.add()
                item_bone.name = item.name
                item_bone.bone_name = item.bone_name
                item_bone.ik = item.ik
                item_bone.target = item.target
                item_bone.loc = item.loc
                item_bone.limb = item.limb
                item_bone.is_hidden = item.is_hidden
                item_bone.is_selected = item.is_selected
            
            preset_handler.validate_preset(ob.data, find=True)

        return {'FINISHED'}
    

class Armature_OT_reset_setting(Operator):
    bl_idname = "object.retarget_armature_reset_setting"
    bl_label = "Clear All Setting"
    bl_options = {'REGISTER', 'UNDO'}

    selected: BoolProperty(name="selected", default=False)

    @classmethod
    def poll(cls, context):

        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return False
        return True
    
    def execute(self, context):

        if self.selected:
            for ob in ops.get_selected_obs(context):
                if not ob or ob.type != 'ARMATURE':
                    continue

                setting = ob.data.retarget_retarget
                preset_handler.reset_setting(setting)
                
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        setting = ob.data.retarget_retarget

        preset_handler.reset_setting(setting)
        return {'FINISHED'}
#select 
def correct_bones(item, context):
    global filter_name
    global use_filter_invert

    if not ((filter_name.lower() in item.name.lower() and not use_filter_invert)
            or (filter_name.lower() not in item.name.lower() and use_filter_invert)):
            return False
    
    retarget_setting = context.scene.retarget_setting
    
    if retarget_setting.filt_bone:
        name = retarget_setting.filt_bone_name.lower()
        names = name.split(",")

        valid = True
        for limb in names:

            if not limb:
                continue
            
            valid = True

            if not limb in item.bone_name.lower():
                valid = False

            if valid:
                break

        if not valid:
            return False

    if retarget_setting.filt_limb:
        name = retarget_setting.filt_limb_name.lower() if retarget_setting.filt_limb_search_option else retarget_setting.filt_limb_name_.lower()
        limbs = name.split(",")

        valid = True
        for limb in limbs:

            if not limb:
                continue

            valid = True

            if not limb in item.limb.lower():
                valid = False

            if valid:
                break

        if not valid:
            return False
    
    if retarget_setting.filt_with_limb:
        if not item.limb:
            return False
    
    if retarget_setting.filt_not_limb:
        if item.limb:
            return False
    
    if retarget_setting.filt_ik:
        if not item.ik:
            return False
    
    if retarget_setting.filt_not_ik:
        if item.ik:
            return False
    
    if retarget_setting.filt_loc:
        if not item.loc:
            return False
    
    if retarget_setting.filt_not_loc:
        if item.loc:
            return False
    
    if retarget_setting.filt_with_bone_name:
        if not item.bone_name:
            return False
    
    if retarget_setting.filt_With_not_bone_name:
        if item.bone_name:
            return False
    
    if retarget_setting.filt_hidden:
        if item.is_hidden:
            return False
    
    if retarget_setting.filt_no_hidden:
        if not item.is_hidden:
            return False
    
    if retarget_setting.filt_selected:
        if not item.is_selected:
            return False
    
    if retarget_setting.filt_not_selected:
        if item.is_selected:
            return False

    return True
def get_ob_pined_or_not(context):

    retarget_setting = context.scene.retarget_setting

    if retarget_setting.pin:
        ob = retarget_setting.pin_armature

        if ob.hide_get(view_layer=context.view_layer):
            ob = None
        
    else:
        ob = ops.get_ob_or_armature(context, context.active_object)
    return ob

def get_view_bone(context):
    global filter_name
    global use_filter_invert 

    bones = []
    ob = get_ob_pined_or_not(context)

    if not ob or ob.type != 'ARMATURE':
        return bones
    
    skeleton = ob.data.retarget_retarget

    for item in skeleton.other_bone:
        if not correct_bones(item, context):
            continue
        bones.append(item)
    return bones

def get_all_limb(self, context, edit_text):
    limbs = []
    ob = get_ob_pined_or_not(context)

    if not ob or ob.type != 'ARMATURE':
        return limbs
    
    skeleton = ob.data.retarget_retarget

    for item in skeleton.other_bone:
        if item.limb and not (item.limb, item.limb) in limbs:
            limbs.append((item.limb, item.limb))
    return limbs

class Armature_OT_select_name(Operator):
    """Select by Name"""
    bl_idname = "object.retarget_armature_select_by_name"
    bl_label = "Select By Name"
    bl_options = {'REGISTER', 'UNDO'}

    bone_attr: EnumProperty(items=[
        ('property', "ID", "Bone ID"),
        ('bone_name', "Bone Name", "Bone Name"),
        ('limb', "Limb", "Limb")
         ],
        name="",
        default='bone_name')
    
    search_option: BoolProperty(name="Suggestion",default=True)
    name_: StringProperty(name="Name",search=get_all_limb,
                          description= "Enter the Name (comma is the separator)",
                          default="")

    invert: BoolProperty(name="Invert",default=False)
    name: StringProperty(name="Name",
                         description= "Enter the Name (comma is the separator)",
                         default="")
    prefix: BoolProperty(name="Prefix",default=False)
    contain: BoolProperty(name="Contain",default=False)
    equals: BoolProperty(name="Equal",default=True)
    suffix: BoolProperty(name="Suffix",default=False)

    @classmethod
    def poll(cls, context):
        return len(get_view_bone(context)) > 0

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "bone_attr", toggle=True)

        row = column.row()
        row.prop(self, "prefix", toggle=True)
        row.prop(self, "contain", toggle=True)
        row.prop(self, "equals", toggle=True)
        row.prop(self, "suffix", toggle=True)
        row = column.row()

        if self.bone_attr == 'limb':
            row.prop(self, "search_option", text="", icon="SYNTAX_ON")
            if self.search_option:
                row.prop(self, "name_")
            else:
                row.prop(self, "name")
        else:
            row.prop(self, "name")
        row.prop(self, "invert", text="",icon='ARROW_LEFTRIGHT')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        bone_list = get_view_bone(context)
       
        for item in bone_list:
            if any((self.prefix,self.contain,self.equals,self.suffix)):
                #valid
                name = self.name
                valid = True
                tags = self.name.lower().split(",")
                action_tag = ''
                if self.bone_attr == 'bone_name':
                    action_tag = item.bone_name.lower()
                elif self.bone_attr == 'property':
                    action_tag = item.name.lower()
                elif self.bone_attr == 'limb':
                    action_tag = item.limb.lower()
                    tags = self.name_.lower().split(",") if self.search_option else self.name.lower().split(",")
                    name = self.name_ if self.search_option else self.name
                #find it
                if name:
                    for tag in tags:

                        if not tag:
                            continue
                        
                        if not self.invert:
                            valid = True

                        if not self.invert:

                            if self.prefix and not action_tag.startswith(tag):
                                valid = False
                            
                            if self.contain and not tag in action_tag:
                                valid = False

                            if self.equals and tag != action_tag:
                                valid = False

                            if self.suffix and not action_tag.endswith(tag):
                                valid = False
                        
                        else:

                            if self.prefix and action_tag.startswith(tag):
                                valid = False
                            
                            if self.contain and tag in action_tag:
                                valid = False
                            
                            if self.equals and tag == action_tag:
                                valid = False
                        
                            if self.suffix and action_tag.endswith(tag):
                                valid = False

                        if not self.invert and valid:
                            break
                else:
                    if not self.invert:
                        if self.equals and action_tag:
                            valid = False
                    else:
                        if self.equals and not action_tag:
                            valid = False

                if valid:
                    item.is_selected = True
            
        return {'FINISHED'}
    
class Armature_OT_select_by_ik(Operator):
    bl_idname = "object.retarget_select_by_ik"
    bl_label = "Select By IK"
    bl_options = {'REGISTER', 'UNDO'}

    ik: BoolProperty(name="IK", default=False)

    @classmethod
    def poll(cls, context):
        return len(get_view_bone(context)) > 0
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        bone_list = get_view_bone(context)

        for item in bone_list:
            if item.ik == self.ik:
                item.is_selected = True

        return {'FINISHED'}
    
class Armature_OT_select_by_loc(Operator):
    bl_idname = "object.retarget_select_by_loc"
    bl_label = "Select By LOC"
    bl_options = {'REGISTER', 'UNDO'}

    loc: BoolProperty(name="LOC", default=False)

    @classmethod
    def poll(cls, context):
        return len(get_view_bone(context)) > 0
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        bone_list = get_view_bone(context)

        for item in bone_list:
            if item.loc == self.loc:
                item.is_selected = True

        return {'FINISHED'}

class Armature_OT_select_by_hidden(Operator):
    bl_idname = "object.retarget_select_by_hidden"
    bl_label = "Select By The Hidden Mark"
    bl_options = {'REGISTER', 'UNDO'}

    is_hidden: BoolProperty(name="Hidden Mark", default=False)

    def draw(self, context):

        layout = self.layout
        column = layout.column()

        row = column.row()
        if self.is_hidden:
            row.prop(self, 'is_hidden', text="", icon='HIDE_ON', emboss=False)
        else:
            row.prop(self, 'is_hidden', text="", icon='HIDE_OFF', emboss=False)

    @classmethod
    def poll(cls, context):
        return len(get_view_bone(context)) > 0
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        for item in get_view_bone(context):
            if item.is_hidden == self.is_hidden:
                item.is_selected = True

        return {'FINISHED'}

class Armature_OT_select_select_bone(Operator):
    bl_idname = "object.retarget_armature_select_select_bone"
    bl_label = "Select Selected Bone(s)"
    bl_options = {'REGISTER', 'UNDO'}

    deselected: BoolProperty(name="Deselect", 
                             description="Deselect other Bone on the List",
                             default=True)

    @classmethod
    def poll(cls, context):
        ob = get_ob_pined_or_not(context)
        if not ob or ob.type != 'ARMATURE':
            return False
        skeleton = ob.data.retarget_retarget
        return bool(skeleton.other_bone)

    def execute(self, context):
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        skeleton = ob.data.retarget_retarget
        bone_list = skeleton.other_bone
        
        #deselect
        if self.deselected:
            for item in bone_list:
                item.is_selected = False

        obs = ops.get_selected_obs(context)

        for o in obs:
            if not o or o.type != 'ARMATURE':
                continue

            bone_names = []

            if ob == o:
                for bone in ob.pose.bones:
                    
                    if not bone.select:
                        continue
                    bone_names.append(bone.name)

                if bone_names:
                    for item in bone_list:
                        if item.bone_name not in bone_names:
                            continue
                        item.is_selected = True
            else:
                for bone in o.pose.bones:
                    if not bone.select:
                        continue
                    bone_names.append(bone.name.split(":")[-1])

                if bone_names:
                    for item in bone_list:
                        if item.name not in bone_names:
                            continue
                        item.is_selected = True

        #set the focus
        for i, item in enumerate(skeleton.other_bone):
                if item.is_selected:
                    skeleton.other_bone_id = i
                    break

        return {'FINISHED'}

class Armature_OT_inverse_selection(Operator):
    bl_idname = "object.retarget_armature_inverse_selection"
    bl_label = "Inverse Selection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_bone(context)) > 0

    def execute(self, context):
        bone_list = get_view_bone(context)
        for item in bone_list:
            item.is_selected = not item.is_selected
        return {'FINISHED'}

class Armature_OT_deselect_all_armature(Operator):
    bl_idname = "object.retarget_armature_deselect_all_armature"
    bl_label = "Deselect All Bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_bone(context)) > 0

    def execute(self, context):
        bone_list = get_view_bone(context)
        for item in bone_list:
            item.is_selected = False
        return {'FINISHED'}

class Armature_OT_select_all_armature(Operator):
    bl_idname = "object.retarget_armature_select_all_armature"
    bl_label = "Select All Bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_bone(context)) > 0

    def execute(self, context):
        bone_list = get_view_bone(context)
        for item in bone_list:
            item.is_selected = True
        return {'FINISHED'}
    
# operation
def get_selected_bone(context):
    items = []
    ob = get_ob_pined_or_not(context)

    if not ob or ob.type != 'ARMATURE':
        return items
    
    skeleton = ob.data.retarget_retarget

    for item in skeleton.other_bone:

        if not correct_bones(item, context):
            continue

        if item.is_selected:
            items.append(item)

    return items
  
#ops.

class Armature_OT_add_prefix_suffix_name(Operator):
    """Add Prefix or Suffix on The ID Of Selected Bone(s)"""
    bl_idname = "object.retarget_armature_add_prefix_suffix_name"
    bl_label = "Add Prefix or Suffix On ID"
    bl_options = {'REGISTER', 'UNDO'}

    prefix: StringProperty(name="prefix",default="")
    suffix: StringProperty(name="suffix",default="")
    replace: StringProperty(name="replace",default="")
    with_this: StringProperty(name="with",default="")

    @classmethod
    def poll(cls, context):
        return len(get_selected_bone(context)) > 0

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "prefix")
        row = column.row()
        row.prop(self, "replace")
        row = column.row()
        row.prop(self, "with_this")
        row = column.row()
        row.prop(self, "suffix")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        bones = get_selected_bone(context)
        for item in bones:
            item.name = self.prefix + item.name.replace(self.replace, self.with_this) + self.suffix
        
        return {'FINISHED'}
    
class Armature_OT_mirror_select_bone(Operator):
    """Mirror Setting of the Selected Bone(s)"""
    bl_idname = "object.retarget_mirror_select_bone"
    bl_label = "Mirror Setting"
    bl_options = {'REGISTER', 'UNDO'}

    all_bone: BoolProperty(name="All Bone", 
                               description="Mirror of All Bone",
                               default=False)

    def find_mirror_bone(self, name, ob):
        strip = bone_utils.lrl_strip(name)
        for bone in ob.pose.bones:
            if name != bone.name and strip == bone_utils.lrl_strip(bone.name):
                return bone.name
        return ""
    
    def find_mirror_id(self, name, skeleton):
        strip = bone_utils.lrl_strip(name)
        for item in skeleton.other_bone:
            if item.name != name and strip == bone_utils.lrl_strip(item.name):
                return item.name
        return ""
    
    def execute(self, context):
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        skeleton = ob.data.retarget_retarget
        
        left_right = dict()

        if self.all_bone:
            items = []
            for it in skeleton.other_bone:
                items.append(it)
            selected_item = items
        else:
            selected_item = get_selected_bone(context)
        
        for item in selected_item:

            # test if is not a mirror bone
            if not item.bone_name or not self.find_mirror_bone(item.bone_name, ob):
                continue
            if item.name in left_right.keys() or item.name in left_right.values():
                continue

            if bone_utils.bone_left_or_right(item.name):
                find = self.find_mirror_id(item.name, skeleton)
                if not find:
                    find = bone_utils.bone_right_name(item.name)

            else:
                find = self.find_mirror_id(item.name, skeleton)
                if not find:
                    find = bone_utils.bone_left_name(item.name)
            
            if find and find not in left_right.values() and find not in left_right.keys():
                if bone_utils.bone_left_or_right(find):
                    left_right[find] = item.name
                else:
                    left_right[item.name] = find

        for l, r in left_right.items():
            l_item = None
            r_item = None

            for item in skeleton.other_bone:

                if item.name == l:
                    l_item = item

                if item.name == r:
                    r_item = item

                if l_item and r_item:
                    break

            if (l_item and l_item.bone_name) or (r_item and r_item.bone_name):

                if l_item and not r_item:
                    r_item = skeleton.other_bone.add()
                    r_item.name = bone_utils.bone_right_name(l_item.name)
                    r_item.bone_name = self.find_mirror_bone(l_item.bone_name, ob)
                    if not r_item.bone_name in ob.pose.bones:
                        r_item.bone_name = ""
                    else:
                        r_item.target = self.find_mirror_bone(l_item.target, ob)
                        r_item.ik = l_item.ik
                        r_item.loc = l_item.loc
                        r_item.limb = l_item.limb

                elif r_item and not l_item:
                    l_item = skeleton.other_bone.add()
                    l_item.name = bone_utils.bone_left_name(r_item.name)
                    l_item.bone_name = self.find_mirror_bone(r_item.bone_name, ob)
                    if not l_item.bone_name in ob.pose.bones:
                        l_item.bone_name = ""
                    else:
                        l_item.target = self.find_mirror_bone(r_item.target, ob)
                        l_item.ik = r_item.ik
                        l_item.loc = r_item.loc
                        l_item.limb = r_item.limb

                elif r_item and l_item:
                    if r_item.bone_name and not l_item.bone_name:
                        l_item.bone_name = self.find_mirror_bone(r_item.bone_name, ob)
                        if not l_item.bone_name in ob.pose.bones:
                            l_item.bone_name = ""
                        else:
                            l_item.target = self.find_mirror_bone(r_item.target, ob)
                            l_item.ik = r_item.ik
                            l_item.loc = r_item.loc
                            l_item.limb = r_item.limb

                    elif not r_item.bone_name and l_item.bone_name:
                        r_item.bone_name = self.find_mirror_bone(l_item.bone_name, ob)
                        if not r_item.bone_name in ob.pose.bones:
                            r_item.bone_name = ""
                        else:
                            r_item.target = self.find_mirror_bone(l_item.target, ob)
                            r_item.ik = l_item.ik
                            r_item.loc = l_item.loc
                            r_item.limb = l_item.limb

                    if r_item.limb and not l_item.limb:
                        l_item.limb = bone_utils.bone_left_name(r_item.limb)

                    elif not r_item.limb and l_item.limb:
                        r_item.limb = bone_utils.bone_right_name(l_item.limb)

                    if r_item.ik != l_item.ik:
                        if r_item in selected_item:
                            l_item.target = self.find_mirror_bone(r_item.target, ob)
                            l_item.ik = r_item.ik
                        else:
                            r_item.target = self.find_mirror_bone(l_item.target, ob)
                            r_item.ik = l_item.ik

                    if not r_item.target or not l_item.target:
                        if r_item in selected_item and r_item.target:
                            l_item.target = self.find_mirror_bone(r_item.target, ob)
                        elif l_item in selected_item and l_item.target:
                            r_item.target = self.find_mirror_bone(l_item.target, ob)

                    if r_item.loc != l_item.loc:
                        if r_item in selected_item:
                            l_item.loc = r_item.loc
                        else:
                            r_item.loc = l_item.loc
        return {'FINISHED'}

class Armature_OT_op_batch_bone_name(Operator):
    """Select 2 Armatures and Pin one"""
    bl_idname = "object.retarget_op_batch_bone_name"
    bl_label = "Batch Mapping"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):

        retarget_setting = context.scene.retarget_setting

        if not retarget_setting.pin:
            return False
        
        if len(ops.get_selected_obs(context)) < 2:
            return False
        
        i = 0
        for ob in ops.get_selected_obs(context):
            if ob.type == 'ARMATURE':
                i = i + 1
            if i >= 2:
                return True
        return False
    
    ob = None
    other_ob = None
    
    def invoke(self, context, event):
        self.ob = get_ob_pined_or_not(context)
        if not self.ob or self.ob.type != 'ARMATURE':
            return {'CANCELLED'}
        
        self.other_ob = None
        for o in ops.get_selected_obs(context):
            if o.type == 'ARMATURE' and o != self.ob:
                self.other_ob = o
                break

        if not self.other_ob or self.other_ob.type != 'ARMATURE':
            return {'CANCELLED'}
        
        self.ob.select_set(True, view_layer = context.view_layer)
        self.other_ob.select_set(True, view_layer = context.view_layer)
        
        context.view_layer.objects.active = self.ob
        bpy.ops.object.mode_set(mode='POSE')
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    #bone of other armature
    other_bone = ''
    map_one_time = True

    def modal(self, context, event):

        if not self.ob or not self.other_ob:
            return {'FINISHED'}

        if context.mode != 'POSE':
            context.view_layer.objects.active = self.ob
            bpy.ops.object.mode_set(mode='POSE')


        info = "Confirm: (Enter/Space),   Cancel: (Esc),    Erase: (Rclick/Delete),   Map One Time: (A) "+ str(self.map_one_time)
        info = info + "    Select Mapped Bone: (S),    Mirror: (M),    Set Bone Name: (Click),    Set IK: (I),    Set LOC: (L)"
        if self.other_bone:
            info = info + "  Bind   { "+ self.other_bone +" }   to ....."

        context.area.header_text_set(info)

        # Allow navigation
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'LEFT_ALT', 'LEFTMOUSE', 'R', 'G'}:
            return {'PASS_THROUGH'}
        
        context.area.tag_redraw()

        if event.type in {'RET', 'SPACE', 'NUMPAD_ENTER'}:
            context.area.header_text_set(None)
            return {'FINISHED'}
        
        if event.type in {'ESC'}:
            context.area.header_text_set(None)
            return {'CANCELLED'}
        
        if event.type in {'A'} and event.value == 'PRESS':
            self.map_one_time = not self.map_one_time

        if event.type in {'S'} and event.value == 'PRESS':
            skeleton = self.ob.data.retarget_retarget
            for item in skeleton.other_bone:
                if item.name and item.bone_name and item.name in self.other_ob.pose.bones:
                    self.other_ob.pose.bones[item.name].select = True

                if item.bone_name in self.ob.pose.bones:
                    self.ob.pose.bones[item.bone_name].select = True
        
        if event.type in {'M'} and event.value == 'PRESS':
            bpy.ops.object.retarget_mirror_select_bone(all_bone=True)

        if event.type in {'I'} and event.value == 'PRESS':
            skeleton = self.ob.data.retarget_retarget
            try:
                item = skeleton.other_bone[skeleton.other_bone_id]
                item.ik = not item.ik

            except:
                pass

        if event.type in {'L'} and event.value == 'PRESS':
            skeleton = self.ob.data.retarget_retarget
            try:
                item = skeleton.other_bone[skeleton.other_bone_id]
                item.loc = not item.loc

            except:
                pass
        
        if self.other_bone and event.type in ('BACK_SPACE', 'DEL', 'RIGHTMOUSE') and event.value == 'PRESS':
            self.other_bone = ''
            if context.active_pose_bone.name in self.other_ob.data.bones:
                self.other_ob.data.bones.active = None

        elif not self.other_bone and event.type in ('BACK_SPACE', 'DEL', 'RIGHTMOUSE') and event.value == 'PRESS':
            skeleton = self.ob.data.retarget_retarget
            try:
                it = skeleton.other_bone[skeleton.other_bone_id]
                if it:
                    if it.ik and it.target:
                        it.target = ''
                    else:
                        it.bone_name = ''
            except:
                pass

        elif context.active_pose_bone:

            if context.active_pose_bone.name in self.other_ob.data.bones:

                self.other_bone = context.active_pose_bone.name
                find = False

                #set the focus (in because of prefix)
                skeleton = self.ob.data.retarget_retarget
                for i, item in enumerate(skeleton.other_bone):
                    other_bone = self.other_bone.split(":")[-1]
                    if item.name == other_bone:
                        skeleton.other_bone_id = i
                        find = True
                        break
                
                if not find:
                    self.other_bone = ''

            elif self.other_bone and context.active_pose_bone.name in self.ob.data.bones:
                pinned_bone = context.active_pose_bone.name
                
                find = False
                skeleton = self.ob.data.retarget_retarget
                #check if bone is already mapped
                for item in skeleton.other_bone:
                    if item.bone_name == pinned_bone or (item.ik and item.target == pinned_bone):
                        find = True
                        break
                
                if find and self.map_one_time:
                    return {'RUNNING_MODAL'}

                for item in skeleton.other_bone:
                    other_bone = self.other_bone.split(":")[-1]
                    if item.name == other_bone:
                        if item.bone_name and item.ik and not item.target:
                            item.target = pinned_bone
                        else:
                            item.bone_name = pinned_bone

                        self.other_bone = ''
                        break

            else:
                pinned_bone = context.active_pose_bone.name

                skeleton = self.ob.data.retarget_retarget
                it = None
                for i, item in enumerate(skeleton.other_bone):
                    if item.bone_name == pinned_bone:
                        skeleton.other_bone_id = i
                        it = item
                        break

        return {'RUNNING_MODAL'}

class Armature_OT_op_select_bone(Operator):
    """Select bone corresponding On Armature"""
    bl_idname = "object.retarget_op_select_bone"
    bl_label = "Select Bone"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_selected_bone(context)) > 0
   
    def execute(self, context):
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        obs = ops.get_selected_obs(context)

        for o in obs:
            if not o or o.type != 'ARMATURE':
                continue
        
            if o == ob:
                for item in get_selected_bone(context):
                    if item.bone_name in ob.pose.bones:
                        bone = ob.pose.bones[item.bone_name]
                        bone.select = True
            elif o.pose.bones:
                bone_names = dict()
                for bone in o.pose.bones:
                    if  bone.select:
                        continue
                    bone_names[bone.name.split(":")[-1]] = bone.name

                
                for item in get_selected_bone(context):
                    if item.name in bone_names.keys():
                        bone = o.pose.bones[bone_names[item.name]]
                        bone.select = True

        return {'FINISHED'}
    
class Armature_OT_set_ik(Operator):
    """Set The IK on Selected Bone(s)"""
    bl_idname = "object.retarget_set_ik"
    bl_label = "Set The IK"
    bl_options = {'REGISTER', 'UNDO'}

    ik: BoolProperty(name="IK", default=False)

    @classmethod
    def poll(cls, context):
        return len(get_selected_bone(context)) > 0
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        for item in get_selected_bone(context):
            item.ik = self.ik

        return {'FINISHED'}

class Armature_OT_set_loc(Operator):
    """Set The LOC (Location Constraint) on Selected Bone(s)"""
    bl_idname = "object.retarget_set_loc"
    bl_label = "Set The LOC"
    bl_options = {'REGISTER', 'UNDO'}

    loc: BoolProperty(name="LOC", default=False)

    @classmethod
    def poll(cls, context):
        return len(get_selected_bone(context)) > 0
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        for item in get_selected_bone(context):
            item.loc = self.loc

        return {'FINISHED'}

class Armature_OT_set_hidden(Operator):
    """Set The Damped Track of the Selected Bone(s)"""
    bl_idname = "object.retarget_set_hidden"
    bl_label = "Set The Hidden Mark"
    bl_options = {'REGISTER', 'UNDO'}

    is_hidden: BoolProperty(name="Hidden Mark", default=False)

    def draw(self, context):

        layout = self.layout
        column = layout.column()

        row = column.row()
        if self.is_hidden:
            row.prop(self, 'is_hidden', text="", icon='HIDE_ON', emboss=False)
        else:
            row.prop(self, 'is_hidden', text="", icon='HIDE_OFF', emboss=False)

    @classmethod
    def poll(cls, context):
        return len(get_selected_bone(context)) > 0
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        for item in get_selected_bone(context):
            item.is_hidden = self.is_hidden

        return {'FINISHED'}

class Armature_OT_add_prefix_suffix_limb(Operator):
    """Add Prefix or Suffix on The Limb Of Selected Bone(s)"""
    bl_idname = "object.retarget_armature_add_prefix_suffix_limb"
    bl_label = "Add Prefix or Suffix On Limb"
    bl_options = {'REGISTER', 'UNDO'}

    prefix: StringProperty(name="prefix",default="")
    suffix: StringProperty(name="suffix",default="")
    replace: StringProperty(name="replace",default="")
    with_this: StringProperty(name="with",default="")

    @classmethod
    def poll(cls, context):
        return len(get_selected_bone(context)) > 0

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "prefix")
        row = column.row()
        row.prop(self, "replace")
        row = column.row()
        row.prop(self, "with_this")
        row = column.row()
        row.prop(self, "suffix")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        bones = get_selected_bone(context)
        for item in bones:
            item.limb = self.prefix + item.limb.replace(self.replace, self.with_this) + self.suffix
        
        return {'FINISHED'}
    
class Armature_OT_set_limb(Operator):
    """Add Set The Limb Of Selected Bone(s)"""
    bl_idname = "object.retarget_armature_set_limb"
    bl_label = "Set A Limb"
    bl_options = {'REGISTER', 'UNDO'}

    search_option: BoolProperty(name="Suggestion",default=True)

    name: StringProperty(name="Limb",default="", 
                         description= "Enter the Limb Name (comma is the separator)",
                         search=get_all_limb)
    name_: StringProperty(name="Limb",
                          description= "Enter the Limb Name (comma is the separator)",
                          default="")
    
    @classmethod
    def poll(cls, context):
        return len(get_selected_bone(context)) > 0

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "search_option", text="", icon="SYNTAX_ON")
        if self.search_option:
            row.prop(self, "name")
        else:
            row.prop(self, "name_")
       

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        limb = self.name if self.search_option else self.name_
        bone_list = get_selected_bone(context)
        for item in bone_list:
            item.limb = limb
        return {'FINISHED'}

class Armature_OT_duplicate_bone_item(Operator):
    """Duplicate Selected Bone Item"""
    bl_idname = "object.retarget_armature_duplicate_bone_item"
    bl_label = "Duplicate Selected Bone Item"
    bl_options = {'REGISTER', 'UNDO'}

    prefix: StringProperty(name="Property prefix",default="")
    suffix: StringProperty(name="Property suffix",default="")
    replace: StringProperty(name="replace",default="")
    with_this: StringProperty(name="with",default="")

    @classmethod
    def poll(cls, context):
        return len(get_selected_bone(context)) > 0

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "prefix")
        row = column.row()
        row.prop(self, "replace")
        row = column.row()
        row.prop(self, "with_this")
        row = column.row()
        row.prop(self, "suffix")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return
        
        skeleton = ob.data.retarget_retarget

        bones = get_selected_bone(context)

        for item in bones:
            it = skeleton.other_bone.add()
            it.name = self.prefix + item.name.replace(self.replace, self.with_this) + self.suffix
            it.bone_name = item.bone_name
            it.ik = item.ik
            it.loc = item.loc
            it.limb = item.limb
        
        return {'FINISHED'}
    
class Armature_OT_remove_bone_name(Operator):
    """Remove Bone name of the Selected Bone(s)"""
    bl_idname = "object.retarget_remove_bone_name"
    bl_label = "Remove Bone Name"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_selected_bone(context)) > 0
    
    def execute(self, context):
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        for item in get_selected_bone(context):
            item.bone_name = ""

        return {'FINISHED'}

class Armature_OT_clean_selected(Operator):
    """Remove Selected Bones(s) On the List"""
    bl_idname = "object.retarget_clean_selected_bone"
    bl_label = "Clean Selected Bone(S)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_selected_bone(context)) > 0
    
    def execute(self, context):
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        skeleton = ob.data.retarget_retarget

        for item in reversed(get_selected_bone(context)):
            for i, it in enumerate(skeleton.other_bone):
                if item == it:
                    skeleton.other_bone.remove(i)
                    break

        return {'FINISHED'}

class Armature_OT_clean_bone_list(Operator):
    """Clean The Whole Bone List"""
    bl_idname = "object.retarget_clean_bone_list"
    bl_label = "Clean The Whole List"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = get_ob_pined_or_not(context)

        if not ob or ob.type != 'ARMATURE':
            return {'FINISHED'}
        
        skeleton = ob.data.retarget_retarget

        skeleton.other_bone.clear()

        return {'FINISHED'}

#menu ------------------------

class VIEW3D_PT_retarget_add_bone(Menu):
    bl_label = "Add a New Bone"
    bl_idname = "OBJECT_MT_retarget_add_bone"
    
    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(Armature_OT_add_bone.bl_idname)

        row = layout.row()
        row.operator(Armature_OT_add_other_bone.bl_idname)

class VIEW3D_PT_retarget_view_setting_bone(Operator):
    bl_label = "View Setting"
    bl_idname = "object.retarget_ops_view_setting_bone"
    bl_options = {'REGISTER', 'UNDO'}
    def draw(self, context):
        layout = self.layout
        retarget_setting = context.scene.retarget_setting

        row = layout.row()
        col = row.column(align=True)

        col.prop(retarget_setting, "show_bone_name", text='', icon='BONE_DATA')
        col.prop(retarget_setting, "show_eye_dropper", text='', icon='RESTRICT_SELECT_OFF')

        subcol = col.column()
        subcol.alignment = "RIGHT"
        subcol.prop(retarget_setting, "show_ik", toggle=True)
        
        subcol = col.column()
        subcol.alignment = "RIGHT"
        subcol.prop(retarget_setting, "show_loc", toggle=True)

        col.prop(retarget_setting, "show_limb", text='', icon='TAG')
        col.prop(retarget_setting, "show_hidden", text='', icon='HIDE_OFF')
        col.prop(retarget_setting, "side_view", text='', icon='UV_ISLANDSEL')

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)

    def execute(self, context):
        return {'FINISHED'}

class VIEW3D_PT_retarget_filter_bone(Operator):
    bl_label = "Filter"
    bl_idname = "object.retarget__ops_filter_bone"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        retarget_setting = context.scene.retarget_setting

        row = layout.row()
        col = row.column(align=True)

        col.prop(retarget_setting, "filt_with_limb", text="", icon='RESTRICT_COLOR_OFF')
        col.prop(retarget_setting, "filt_not_limb", text="", icon='RESTRICT_COLOR_ON')

        subcol = col.column()
        subcol.alignment = "RIGHT"
        subcol.prop(retarget_setting, "filt_not_ik", icon='CHECKBOX_HLT')
        subcol = col.column()
        subcol.alignment = "RIGHT"
        subcol.prop(retarget_setting, "filt_ik", icon='CHECKBOX_DEHLT')

        subcol = col.column()
        subcol.alignment = "RIGHT"
        subcol.prop(retarget_setting, "filt_not_loc", icon='CHECKBOX_HLT')
        subcol = col.column()
        subcol.alignment = "RIGHT"
        subcol.prop(retarget_setting, "filt_loc", icon='CHECKBOX_DEHLT')

        col.prop(retarget_setting, "filt_With_not_bone_name", text="", icon='CON_ARMATURE')
        col.prop(retarget_setting, "filt_with_bone_name", text="", icon='ARMATURE_DATA')

        col.prop(retarget_setting, "filt_not_selected", text="", icon='CHECKBOX_HLT')
        col.prop(retarget_setting, "filt_selected", text="", icon='CHECKBOX_DEHLT')

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)

    def execute(self, context):
        return {'FINISHED'}

class VIEW3D_PT_retarget_sort_bone(Operator):
    bl_label = "View Setting"
    bl_idname = "object.retarget_ops_sort_bone"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        retarget_setting = context.scene.retarget_setting

        row = layout.row()
        col = row.column(align=True)

        col.prop(retarget_setting, "sort_bone_name", text="", icon='BONE_DATA')
        col.prop(retarget_setting, "sort_limb", text="", icon='TAG')

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)

    def execute(self, context):
        return {'FINISHED'}

class VIEW3D_PT_retarget_select_bone(Menu):
    bl_label = "Select"
    bl_idname = "OBJECT_MT_retarget_select_bone_Menu"
    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(Armature_OT_select_name.bl_idname, icon='SORTALPHA')

        row = layout.row()
        row.operator(Armature_OT_select_by_ik.bl_idname)

        row = layout.row()
        row.operator(Armature_OT_select_by_loc.bl_idname)

        row = layout.row()
        row.operator(Armature_OT_select_by_hidden.bl_idname, icon='HIDE_OFF')

        row = layout.row()
        row.operator(Armature_OT_select_select_bone.bl_idname, icon='BONE_DATA')

        row = layout.row()
        row.operator(Armature_OT_inverse_selection.bl_idname, icon='ARROW_LEFTRIGHT')

        row = layout.row()
        row.operator(Armature_OT_deselect_all_armature.bl_idname, icon='CHECKBOX_DEHLT')

        row = layout.row()
        row.operator(Armature_OT_select_all_armature.bl_idname, icon='CHECKBOX_HLT')

class VIEW3D_PT_retarget_ops_bone(Menu):
    bl_label = "Operations"
    bl_idname = "OBJECT_MT_retarget_ops_select_bone_Menu"
    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.menu(VIEW3D_PT_retarget_add_bone.bl_idname, icon='ADD')

        row = layout.row()
        row.operator(Armature_OT_add_prefix_suffix_name.bl_idname, icon="SORTALPHA")

        row = layout.row()
        row.operator(Armature_OT_mirror_select_bone.bl_idname, icon="MOD_MIRROR")

        row = layout.row()
        row.operator(Armature_OT_op_batch_bone_name.bl_idname, icon="CON_ACTION")

        row = layout.row()
        row.operator(Armature_OT_op_select_bone.bl_idname, icon="CON_ARMATURE")

        row = layout.row()
        row.operator(Armature_OT_set_ik.bl_idname)

        row = layout.row()
        row.operator(Armature_OT_set_loc.bl_idname)

        row = layout.row()
        row.operator(Armature_OT_set_hidden.bl_idname, icon='HIDE_OFF')

        row = layout.row()
        row.operator(Armature_OT_add_prefix_suffix_limb.bl_idname, icon='TAG')

        row = layout.row()
        row.operator(Armature_OT_set_limb.bl_idname, icon='TAG')

        row = layout.row()
        row.operator(Armature_OT_duplicate_bone_item.bl_idname, icon='DUPLICATE')

        row = layout.row()
        row.operator(Armature_OT_remove_bone_name.bl_idname, icon='BONE_DATA')

        row = layout.row()
        row.operator(Armature_OT_clean_selected.bl_idname, icon='TRACKING_CLEAR_BACKWARDS')

        row = layout.row()
        row.operator(Armature_OT_clean_bone_list.bl_idname, icon='TRASH')

classes = (
    #add
    Armature_OT_add_bone,
    Armature_OT_add_other_bone,

    Armature_OT_copy_setting,
    Armature_OT_paste_setting,
    Armature_OT_reset_setting,

    #select
    Armature_OT_select_name,
    Armature_OT_select_by_ik,
    Armature_OT_select_by_loc,
    Armature_OT_select_by_hidden,
    Armature_OT_select_select_bone,
    Armature_OT_inverse_selection,
    Armature_OT_deselect_all_armature,
    Armature_OT_select_all_armature,

    #op
    Armature_OT_add_prefix_suffix_name,
    Armature_OT_mirror_select_bone,
    Armature_OT_op_batch_bone_name,
    Armature_OT_op_select_bone,
    Armature_OT_set_ik,
    Armature_OT_set_loc,
    Armature_OT_set_hidden,
    Armature_OT_add_prefix_suffix_limb,
    Armature_OT_set_limb,
    Armature_OT_duplicate_bone_item,
    Armature_OT_remove_bone_name,
    Armature_OT_clean_selected,
    Armature_OT_clean_bone_list,

    #menu
    VIEW3D_PT_retarget_view_setting_bone,
    VIEW3D_PT_retarget_filter_bone,
    VIEW3D_PT_retarget_sort_bone,

    VIEW3D_PT_retarget_add_bone,
    VIEW3D_PT_retarget_select_bone,
    VIEW3D_PT_retarget_ops_bone,
)


def register_classes():
     for cls in classes:
        bpy.utils.register_class(cls)

def unregister_classes():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)