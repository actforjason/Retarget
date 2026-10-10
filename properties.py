import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty
from bpy.props import PointerProperty
from bpy.props import BoolProperty
from bpy.props import EnumProperty
from bpy.props import IntProperty
from bpy.props import CollectionProperty

from . import preset_handler, support
from .action import ops

class RetargetBase(PropertyGroup):
    def has_settings(self):
        for k, v in self.items():
            if k in ['name', 'super_copy']:
                continue
            if v:
                return True
        return False


class RetargetSpine(RetargetBase):
    head: StringProperty(name="head")
    neck: StringProperty(name="neck")
    spine2: StringProperty(name="spine2")
    spine1: StringProperty(name="spine1")
    spine: StringProperty(name="spine")
    hips: StringProperty(name="hips")


class RetargetArm(RetargetBase):
    shoulder: StringProperty(name="shoulder")
    arm: StringProperty(name="arm")
    arm_twist: StringProperty(name="arm_twist")
    arm_twist_02: StringProperty(name="arm_twist_02")
    forearm: StringProperty(name="forearm")
    forearm_twist: StringProperty(name="forearm_twist")
    forearm_twist_02: StringProperty(name="forearm_twist_02")
    hand: StringProperty(name="hand")

    name: StringProperty(default='arm')


class RetargetLeg(RetargetBase):
    upleg: StringProperty(name="upleg")
    upleg_twist: StringProperty(name="upleg_twist")
    upleg_twist_02: StringProperty(name="upleg_twist_02")
    leg: StringProperty(name="leg")
    leg_twist: StringProperty(name="leg_twist")
    leg_twist_02: StringProperty(name="leg_twist_02")
    foot: StringProperty(name="foot")
    toe: StringProperty(name="toe")

    foot_spin: StringProperty(name="foot_spin")
    foot_heel: StringProperty(name="foot_heel")

    name: StringProperty(default='leg')


class RetargetFinger(RetargetBase):
    meta: StringProperty(name="meta")
    a: StringProperty(name="A")
    b: StringProperty(name="B")
    c: StringProperty(name="C")


class RetargetFingers(PropertyGroup):
    thumb: PointerProperty(type=RetargetFinger)
    index: PointerProperty(type=RetargetFinger)
    middle: PointerProperty(type=RetargetFinger)
    ring: PointerProperty(type=RetargetFinger)
    pinky: PointerProperty(type=RetargetFinger)

    name: StringProperty(default='fingers')

    def has_settings(self):
        for setting in (self.thumb, self.index, self.middle, self.ring, self.pinky):
            if setting.has_settings():
                return True

        return False


class RetargetFaceSimple(RetargetBase):
    jaw: StringProperty(name="jaw")
    left_eye: StringProperty(name="left_eye")
    right_eye: StringProperty(name="right_eye")

    left_upLid: StringProperty(name="left_upLid")
    right_upLid: StringProperty(name="right_upLid")

    super_copy: BoolProperty(default=True)

def update_bone_name(self, context):
    ob = support.get_ob_pined_or_not(context)
    if not ob or ob.type != 'ARMATURE':
        return 
    
    if context.active_pose_bone and context.active_pose_bone.name in ob.data.bones:
        if self.bone_name and self.ik and not self.target:
            self.target = context.active_pose_bone.name
        else:
            self.bone_name = context.active_pose_bone.name

def update_pin(self, context):

    if self.pin:
        ob = ops.get_ob_or_armature(context, context.active_object)

        if not ob or ob.type != 'ARMATURE':
            return
        
        self.pin_armature = ob
    else:
        self.pin_armature = None

class OtherBoneItem(PropertyGroup):
    name: StringProperty(name= "Bone ID")
    bone_name: StringProperty(name= "Bone Name")
    eye_dropper: BoolProperty(name= "Set the active bone name", default=False, update=update_bone_name)
    ik: BoolProperty(name= "IK", 
                     description="Set the IK property to this bone",
                     default=False)
    
    target: StringProperty(name= "Target", description="Arm Ik or Pole Target")

    loc: BoolProperty(name= "LOC", 
                      description="Add Location Constraint to this Bone",
                      default=False)

    limb: StringProperty(name= "Limb")

    is_hidden: BoolProperty(name="",description="Hidden Mark", default=False)

    is_selected: BoolProperty(name="", description="Select Bone", default=False)

class RetargetSettings(PropertyGroup):
    face: PointerProperty(type=RetargetFaceSimple)
    spine: PointerProperty(type=RetargetSpine)

    left_arm: PointerProperty(type=RetargetArm)
    left_arm_ik: PointerProperty(type=RetargetArm)
    left_fingers: PointerProperty(type=RetargetFingers)

    right_arm: PointerProperty(type=RetargetArm)
    right_arm_ik: PointerProperty(type=RetargetArm)
    right_fingers: PointerProperty(type=RetargetFingers)

    left_leg: PointerProperty(type=RetargetLeg)
    left_leg_ik: PointerProperty(type=RetargetLeg)
    right_leg: PointerProperty(type=RetargetLeg)
    right_leg_ik: PointerProperty(type=RetargetLeg)

    root: StringProperty(name="root")

    def has_settings(self):
        for setting in (self.face, self.spine, self.left_arm, self.left_arm_ik, self.left_fingers,
                        self.right_arm, self.right_arm_ik, self.right_fingers,
                        self.left_leg, self.left_leg_ik, self.right_leg, self.right_leg_ik):
            if setting.has_settings():
                return True
            
        if self.other_bone:
            return True

        if self.root:
            return True

        return False

    # deform_preset: EnumProperty(items=preset_handler.iterate_presets,
    #                             name="Deformation Bones")

    deform_preset: StringProperty(name="Deformation Bones", search=preset_handler.iterate_presets_search,
                    default="--")
    
    other_bone: CollectionProperty(type=OtherBoneItem)

    other_bone_id: IntProperty(name="Index", default=0)

class RetargetSettingsVariable(PropertyGroup):
    twist_on: BoolProperty(default=False)

    pin: BoolProperty(name= "Pin the armature", default=False, update=update_pin)
    pin_armature: PointerProperty(type=bpy.types.Object)
    tmp_setting: PointerProperty(type=RetargetSettings)


    expand_list_view: BoolProperty(name= "View Setting", default=False)

    show_bone_name: BoolProperty(name= "Show Bone Name", default=True)
    
    show_eye_dropper: BoolProperty(name= "Show Eye Dropper", default=True)

    show_ik: BoolProperty(name= "IK", 
                          description="Show IK Setting",
                          default=False)
    
    show_loc: BoolProperty(name= "LOC", 
                           description="Show Location Setting",
                           default=False)

    show_limb: BoolProperty(name= "Show Limb",default=False)

    show_hidden: BoolProperty(name= "Show The Hidden Mark", default=False)

    side_view: BoolProperty(name= "Side View", default=True)
    
    #sort by
    sort_bone_name: BoolProperty(name= "Sort By Bone Name", default=False)
    sort_limb: BoolProperty(name= "Sort By Limb", default=False)

    #filter
    filt_bone: BoolProperty(name= "Filter By Bone Name", default=False)
    filt_bone_name: StringProperty(name="Name",description= "Enter the Bone Name (comma is the separator)", default="")

    filt_limb: BoolProperty(name= "Filter By Limb", default=False)
    filt_limb_search_option: BoolProperty(name="Suggestion",default=True)
    filt_limb_name: StringProperty(name="Name",description= "Enter the Limb Name", default="",  search=support.get_all_limb)
    filt_limb_name_: StringProperty(name="Name",description= "Enter the Limb Name (comma is the separator)", default="")

    filt_with_limb: BoolProperty(name= "Hide bone With No Limb", default=False)
    filt_not_limb: BoolProperty(name= "Hide bone With Limb", default=False)

    filt_ik: BoolProperty(name= "IK", description= "Hide No IK Bone", default=False)
    filt_not_ik: BoolProperty(name= "IK", description= "Hide IK Bone", default=False)

    filt_loc: BoolProperty(name= "LOC", description= "Hide No LOC Bone", default=False)
    filt_not_loc: BoolProperty(name= "LOC", description= "Hide LOC Bone", default=False)

    filt_with_bone_name: BoolProperty(name= "Bone Name", description= "Hide item with No Bone Name", default=False)
    filt_With_not_bone_name: BoolProperty(name= "TRACK", description= "Hide item with Bone Name", default=False)

    filt_hidden: BoolProperty(name= "Hide bone with Hidden Mark ON", default=False)
    filt_no_hidden: BoolProperty(name= "Hide bone with Hidden Mark OFF", default=False)

    filt_selected: BoolProperty(name= "Hide bone No Selected", default=False)
    filt_not_selected: BoolProperty(name= "Hide bone Selected", default=False)

classes = (
    RetargetSpine,
    RetargetArm,
    RetargetLeg,
    RetargetFinger,
    RetargetFingers,
    RetargetFaceSimple,
    OtherBoneItem,
    RetargetSettings,
    RetargetSettingsVariable,
)

def register_classes():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Armature.retarget_retarget = PointerProperty(type=RetargetSettings)
    bpy.types.Scene.retarget_setting = PointerProperty(type=RetargetSettingsVariable)

def unregister_classes():
    del bpy.types.Scene.retarget_setting
    del bpy.types.Armature.retarget_retarget

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
