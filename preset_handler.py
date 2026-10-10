
import os
import shutil

import bpy
from .rig_mapping.bone_mapping import HumanFingers, HumanSpine, HumanLeg, HumanArm, HumanSkeleton, SimpleFace
from .action import ops
from . import bone_utils

PRESETS_SUBDIR = os.path.join("retarget", "humanoid")

def get_retarget_dir():
    
    presets_dir = os.path.join("presets", PRESETS_SUBDIR)
    retarget_dir = bpy.utils.user_resource('SCRIPTS', path= presets_dir, create=True)
    
    return retarget_dir


def install_presets():
    retarget_dir = get_retarget_dir()

    extensions_path = os.path.join(os.path.dirname(__file__))

    bundled_dir = os.path.join(extensions_path, "rig_mapping", "presets")

    for f in os.listdir(bundled_dir):
        shutil.copy2(os.path.join(bundled_dir, f), retarget_dir)


def iterate_presets_with_current(scene, context):
    """CallBack for Enum Property. Must take scene, context arguments"""

    yield '--', "--", "None"  # first menu entry, doesn't do anything
    yield "--Current--", "-- Current Settings --", "Use Bones set in Retarget Retarget Panel"

    for f in os.listdir(get_retarget_dir()):
        if not f.endswith('.py'):
            continue
        yield f, os.path.splitext(f)[0].title(), ""


def iterate_presets(scene, context):
    """CallBack for Enum Property. Must take scene, context arguments"""

    yield '--', "--", "None"  # first menu entry, doesn't do anything

    for f in os.listdir(get_retarget_dir()):
        if not f.endswith('.py'):
            continue
        yield f, os.path.splitext(f)[0].title(), ""

def iterate_presets_search(self, context, edit_text):
    """CallBack for Enum Property. Must take scene, context arguments"""

    yield ('--', "--") # first menu entry, doesn't do anything

    for f in os.listdir(get_retarget_dir()):
        if not f.endswith('.py'):
            continue
        yield (f, os.path.splitext(f)[0].title())

def findPreset(ob):
    best_preset = "--"
    number_bone = 0
    
    settings = ob.data.retarget_retarget

    for f in os.listdir(get_retarget_dir()):
        if not f.endswith('.py'):
            continue

        skeleton = get_preset_skel(f, settings)

        if not skeleton or not skeleton.has_settings():
            continue

        if len(skeleton.bone_names()) == len(ob.data.bones):
            reset_setting(settings)
            return f

        if best_preset == "--" and number_bone == 0:
            best_preset = f
            number_bone = len(skeleton.bone_names())
        
        elif number_bone < len(skeleton.bone_names()):
            best_preset = f
            number_bone = len(skeleton.bone_names())

    reset_setting(settings)
    return best_preset


def get_settings_skel(settings):
    mapping = HumanSkeleton(preset=settings)
    return mapping

def guessBone(name, attrlist, ik, l, r, number, bones, starwith, dontstarwith, dontcontain, selected, skip_deform, has_shape, visible, used, exclude = []):

    if name != "":
        v = name
        if ":" in name:
            v = name.split(":")[-1]

        for bone in bones:
            if v.lower() in bone.name.lower():
                return bone.name
           
    for attr in attrlist:
        if 'eye' in attr.lower():
            attr = 'eye'
        
       
        for bone in bones:

            if selected and not bone.select:
                continue

            if skip_deform and bone.bone.use_deform:
                continue

            if has_shape and not bool(bone.custom_shape):
                continue

            if visible and not bone_utils.visible_bone(bone):
                continue

            #used
            if bone.name in used:
                continue
            
            #exclude
            if exclude:
                in_exclude = False
                for ex in exclude:
                    if ex.lower() in bone.name.lower():
                        in_exclude = True
                        break
                if in_exclude:
                    continue

            #start with
            if starwith and not bone.name.lower().startswith(starwith):
                continue
            
            #dont start with
            cont = True
            for d in dontstarwith:
                if d and bone.name.lower().startswith(d):
                    cont = False
                    break

            if not cont:
                continue
            
            #dont contain
            for d in dontcontain:
                if d and d in bone.name.lower():
                    cont = False
                    break

            if not cont:
                continue

            #------

            if attr.lower() in bone.name.lower() and ((ik and "ik" in bone.name.lower() and attr.lower()) or (not ik)):

                #handle twist bone
                if ("twist" in bone.name.lower() or "tweak" in bone.name.lower()) and (not "twist" in attr.lower() and not "tweak" in attr.lower()):
                    continue

                if r:

                    if bone_utils.bone_left_or_right(bone.name.lower()):
                        continue
                    # if ".l" in bone.name.lower():
                    #     continue
                    # if not ".r" in bone.name.lower():
                    #     if not "right" in bone.name.lower():
                    #         if not "rgt" in bone.name.lower():
                    #             if not "_r_" in bone.name.lower():
                    #                 if not "_r" in bone.name.lower() or "_ring" in bone.name.lower()  or "_roll" in bone.name.lower() :
                    #                     if not " r" in bone.name.lower():
                    #                         if not "r_" in bone.name.lower():
                    #                             continue
                if l:
                    if not bone_utils.bone_left_or_right(bone.name.lower()):
                        continue
                    
                    # if ".r" in bone.name.lower():
                    #     continue
                    # if not ".l" in bone.name.lower():
                    #     if not "left" in bone.name.lower():
                    #         if not "lft" in bone.name.lower():
                    #             if not "_l_" in bone.name.lower():
                    #                 if not "_l" in bone.name.lower():
                    #                     if not " l" in bone.name.lower():
                    #                         if not "l_" in bone.name.lower():
                    #                             continue
                #finger
                if number != "0":
                    if not number in bone.name.lower():
                        continue

                used.append(bone.name)
                
                return bone.name
        
    return ""

def guess(armature, starwith, dontstarwith, dontcontain, selected, skip_deform, has_shape, visible,separator=':'):
    settings = armature.data.retarget_retarget

    if not armature.data.bones:
        return
    
    a_name = armature.data.bones[0].name

    prefix = ""
    if separator in a_name:
        prefix = a_name.rsplit(separator, 1)[0]
        prefix += separator

    used = []

    exclude = []
    #root bone
    v = getattr(settings, "root", "")
    with_prefix = prefix + v
    try:
        setattr(settings, "root" , with_prefix if with_prefix in armature.data.bones \
        else guessBone(v, ["c_pos","root","master"], False, False, False, "0", armature.pose.bones, starwith, dontstarwith, dontcontain, selected, skip_deform, has_shape, visible, used))
    except:
        pass
    #---

    for group in ('spine', 'left_arm', 'left_arm_ik', 'right_arm', 'right_arm_ik',
                    'right_leg', 'right_leg_ik', 'left_leg', 'left_leg_ik', 'face'):

        trg_setting = getattr(settings, group)

        for k in sorted(dir(trg_setting)):

            if k.startswith("__") or k in ["bl_rna", "type", "name"]:
                continue

            # coherence

            if (k == "foot_heel" or k == "foot_spin") and not "ik" in group:
                continue
        
            if "twist" in k and "ik" in group:
                continue

            if (k == "forearm" or k == "shoulder") and "ik" in group:
                continue

            if k == "leg" and "ik" in group:
                continue
            
            exclude.clear()

            #---------

            try:
                v = getattr(trg_setting, k)
                if v not in armature.data.bones:
                    with_prefix = prefix + v
                    l = bool("left" in group)
                    r = bool("right" in group)
                    if group == "face":
                        l = bool("left" in k)
                        r = bool("right" in k)

                    attrlist = []
                    
                    if k == "shoulder":
                        attrlist.append("clavicle")
                        attrlist.append("collarbone")
                        attrlist.append("collar")
                    if "twist" in k:
                        attrlist.append(k.replace("twist", "tweak"))
                    if k == "arm":
                        attrlist.append("upper_arm")
                        attrlist.append("upperarm")
                        exclude.append("forearm")
                    if k == "forearm":
                        attrlist.append("lower_arm")
                        attrlist.append("lowerarm")
                    if k == "hand":
                        attrlist.append("palm")
                    if k == "spine2":
                        attrlist.append("spine_03")
                        attrlist.append("spine_fk.003")
                        attrlist.append("upperchest")
                        attrlist.append("chest")
                        attrlist.append("ribcage")
                    if k == "spine1":
                        attrlist.append("spine_02")
                        attrlist.append("spine_fk.002")
                        attrlist.append("chest")
                    if k == "spine":
                        attrlist.append("waist")
                        attrlist.append("spine_01")
                        attrlist.append("spine_fk.001")
                    if k == "hips":
                        attrlist.append("torso")
                        attrlist.append("pelvis")
                        attrlist.append("master")
                        attrlist.append("hip")
                    if k == "upleg":
                        attrlist.append("thigh")
                        attrlist.append("upperleg")
                        attrlist.append(k)
                        attrlist.append("leg")
                    if k == "leg":
                        attrlist.append("lowerleg")
                        attrlist.append("shin")
                        attrlist.append("calf")
                        attrlist.append("_leg")
                        attrlist.append("leg_")
                        exclude.append("upleg")
                    if k == "foot_spin":
                        attrlist.append("foot_01")
                        attrlist.append("spin")
                        exclude.append("spine")
                    if k == "foot_heel":
                        attrlist.append("footroll")
                        attrlist.append("Cursor")
                        attrlist.append("heel")

                    attrlist.append(k)

                    ik = bool("ik" in group and k != "foot_spin" and k != "foot_heel")

                    setattr(trg_setting, k, with_prefix if with_prefix in armature.data.bones \
                    else guessBone(v, attrlist, ik, l, r, "0", armature.pose.bones, starwith, dontstarwith, dontcontain, selected, skip_deform, has_shape, visible, used, exclude))
            
            except TypeError:
                continue

    #finger_bones = 'meta', 'a', 'b', 'c'
    finger_bones = 'a', 'b', 'c'
    for trg_grp in settings.left_fingers, settings.right_fingers:
        
        for k, trg_finger in trg_grp.items():
            if k == 'name':  # skip Property Group name
                continue
            i = 1
            for slot in finger_bones:
                bone_name = trg_finger.get(slot)
                if not bone_name or bone_name not in armature.data.bones:
                    if not bone_name:
                        bone_name = ""
                    with_prefix = prefix + bone_name
                    
                    l = bool(trg_grp == settings.left_fingers)
                    r = bool(trg_grp == settings.right_fingers)

                    attrlist = []
                    attrlist.append(k)
                    if k == "pinky":
                        attrlist.append("little")
                    trg_finger[slot] = with_prefix if with_prefix in armature.data.bones \
                        else guessBone(bone_name, attrlist, False, l, r, str(i), armature.pose.bones, starwith, dontstarwith, dontcontain, selected, skip_deform, has_shape, visible, used)
                    bpy.context.view_layer.update()
                i += 1


def findBone(name, bones, find = False, used = []):

    if name != "":

        v = name
        if find:
            v = name.lower()
        if ":" in name:
            v = v.split(":")[-1]

        for bone in bones:
            if find and bone.name in used:
                continue
            bone_name = bone.name.lower() if find else bone.name
            if v in bone_name:
                used.append(bone.name)
                return bone.name
            
        if find:
           for bone in bones:
                if bone.name in used:
                    continue
                bone_name = bone.name.lower().split(":")[-1]
                if bone_name in v:
                    used.append(bone.name)
                    return bone.name
    return ""

def validate_preset(armature_data, separator=':', find = False):
    settings = armature_data.retarget_retarget

    if not armature_data.bones:
        return
    
    used = []
    a_name = armature_data.bones[0].name

    prefix = ""
    if separator in a_name:
        prefix = a_name.rsplit(separator, 1)[0]
        prefix += separator

    #root bone
    v = getattr(settings, "root", "")
    with_prefix = prefix + v
    if with_prefix in armature_data.bones:
        used.append(with_prefix)
    try:
        setattr(settings, "root" , with_prefix if with_prefix in armature_data.bones else findBone(v, armature_data.bones, find, used))
    except:
        pass
    #---

    for group in ('spine', 'left_arm', 'left_arm_ik', 'right_arm', 'right_arm_ik',
                    'right_leg', 'right_leg_ik', 'left_leg', 'left_leg_ik', 'face'):

        trg_setting = getattr(settings, group)

        for k in sorted(dir(trg_setting)):

            if k.startswith("__") or k in ["bl_rna", "type", "name"]:
                continue
            
            try:
                v = getattr(trg_setting, k)

                if v in armature_data.bones:
                    used.append(v)
                elif with_prefix in armature_data.bones:
                    used.append(with_prefix)

                if v not in armature_data.bones:
                    with_prefix = prefix + v
                    setattr(trg_setting, k, with_prefix if with_prefix in armature_data.bones else findBone(v, armature_data.bones, find, used))
                   
            except TypeError:
                continue

    finger_bones = 'meta', 'a', 'b', 'c'
    for trg_grp in settings.left_fingers, settings.right_fingers:
        for k, trg_finger in trg_grp.items():
            if k == 'name':  # skip Property Group name
                continue
           
            for slot in finger_bones:
                bone_name = trg_finger.get(slot)

                if bone_name and bone_name in armature_data.bones:
                    used.append(bone_name)
                elif with_prefix in armature_data.bones:
                    used.append(with_prefix)

                if bone_name and bone_name not in armature_data.bones:
                    with_prefix = prefix + bone_name
                    trg_finger[slot] = with_prefix if with_prefix in armature_data.bones else findBone(bone_name, armature_data.bones, find, used)
                    
    
    for item in settings.other_bone:

        if item.bone_name and item.bone_name in armature_data.bones:
            used.append(item.bone_name)
        if item.target and item.target in armature_data.bones:
            used.append(item.target)

        if item.bone_name and not item.bone_name in armature_data.bones:
            item.bone_name = findBone(item.bone_name, armature_data.bones, find, used)
        
        if item.target and not item.target in armature_data.bones:
            item.target = findBone(item.target, armature_data.bones, find, used)
        
           
def reset_setting(skeleton):
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

    skeleton.other_bone.clear()

def get_preset_from_file(filename, settings):

   
    list_value = dict()
    list_other_bone = []
    try:
        
        with open(filename, 'r') as file:
            
            for line in file:

                if not ("import bpy" in line.strip() or "data.retarget_retarget" in line.strip() or line.strip() == ""):
                    
                    line_str = line.strip()
                    sp = line_str.split(" = ")
                    if len(sp) == 2:
                        value_test = sp[1].rsplit("'")

                        if 'skeleton.' in sp[0]:
                            if len(value_test) > 2:
                            
                                key = sp[0].removeprefix('skeleton.')
                                value = value_test[1]
                                if key and value:
                                    list_value[key] = value
                        else:
                            #other bone
                            if "skeleton.other_bone.add()" in sp[1]:
                                pass

                            else:  
                                it = sp[0].split(".")
                                if len(it) == 2: 
                                
                                    list_other_bone.append((it[1], sp[1].replace("'","")))
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return PresetSkeleton()
    except Exception as e:
        print(f"An error occurred: {e}")
        return PresetSkeleton()
    
    
    if not list_value and not list_other_bone:
        return PresetSkeleton()
  
    skeleton = settings
    if not settings:
        skeleton = PresetSkeleton()
    #reset retarget setting
    else:
        reset_setting(skeleton)

    try:
        setattr(skeleton, "root" , list_value["root"])
    except:
        pass

    try:
        setattr(skeleton, "deform_preset" , list_value["deform_preset"])
    except:
        pass

    for group in ('spine', 'left_arm', 'left_arm_ik', 'right_arm', 'right_arm_ik',
                    'right_leg', 'right_leg_ik', 'left_leg', 'left_leg_ik', 'face'):

        trg_setting = getattr(skeleton, group)
        for k in sorted(dir(trg_setting)):

            if not k:
                continue
            if k.startswith("__") or k in ["bl_rna", "type", "name"]:
                continue
            try:
                if not 'super_copy' in k:
                    setattr(trg_setting, k, list_value[group + "." + k])

            except:
                continue

  

    for group in ('thumb', 'index', 'middle', 'ring', 'pinky'):

        trg_setting = getattr(skeleton.left_fingers, group)
        for k in sorted(dir(trg_setting)):
            if not k:
                continue
            if k.startswith("__") or k in ["bl_rna", "type", "name"]:
                continue
            try:
                setattr(trg_setting, k, list_value["left_fingers." + group + "." + k])
            except:
                continue

        trg_setting = getattr(skeleton.right_fingers, group)
        for k in sorted(dir(trg_setting)):
            if not k:
                continue
            if k.startswith("__") or k in ["bl_rna", "type", "name"]:
                continue
            try:
                setattr(trg_setting, k, list_value["right_fingers." + group + "." + k])
            except:
                continue

        #other bone

        if settings:
            name = ""
            bone_name = ""
            bone_name_ = False
            eye_dropper = False
            ik = ""
            target = ""
            target_ = False
            loc = ""
            limb = ""
            limb_ = False
            is_hidden = ""
            is_selected = ""
            for k, v in list_other_bone:
                    
                if k == "name":
                    name = v

                if k == "bone_name":
                    bone_name = v
                    bone_name_ = True

                if k == "eye_dropper":
                    eye_dropper = True

                if k == "ik":
                    ik = v

                if k == "target":
                    target = v
                    target_ = True

                if k == "loc":
                    loc = v

                if k == "limb":
                    limb = v
                    limb_ = True

                if k == "is_hidden":
                    is_hidden = v

                if k == "is_selected":
                    is_selected = v

                if name and bone_name_ and eye_dropper and ik and target_ and loc and limb_ and is_hidden and is_selected:

                    for it in skeleton.other_bone:
                        if name == it.name:
                            name = ""
                            bone_name = ""
                            bone_name_ = False
                            eye_dropper = False
                            ik = ""
                            target = ""
                            target_ = False
                            loc = ""
                            limb = ""
                            limb_ = False
                            is_hidden = ""
                            is_selected = ""
                            break

                    if name and bone_name_ and eye_dropper and ik and target_ and loc and limb_ and is_hidden and is_selected:
                        item = skeleton.other_bone.add()
                        item.name = name
                        item.bone_name = bone_name
                        item.ik = False if ik == "False" else True
                        item.target = target
                        item.loc = False if loc == "False" else True
                        item.limb = limb
                        item.is_hidden = False if is_hidden == "False" else True
                        item.is_selected = False if is_selected == "False" else True

                        name = ""
                        bone_name = ""
                        bone_name_ = False
                        eye_dropper = False
                        ik = ""
                        target = ""
                        target_ = False
                        loc = ""
                        limb = ""
                        limb_ = False
                        is_hidden = ""
                        is_selected = ""
        else:

            key = ""
            value = ""
            for k, v in list_other_bone:

                if k == "name":
                    key = v

                if k == "bone_name":
                    value = v

                if key and value:

                    skeleton.other_bone[key] = value
                    key = ""
                    value = ""
    
    return skeleton

    
def set_preset_skel(preset, context, validate=True, find = True):
    
    if not preset:
        return
    if not preset.endswith(".py"):
        return

    preset_path = os.path.join(get_retarget_dir(), preset)
    if not os.path.isfile(preset_path):
        return
    ob = ops.get_ob_or_armature(context, context.active_object)
    skeleton = ob.data.retarget_retarget

    get_preset_from_file(preset_path, skeleton)

    if validate:
        validate_preset(skeleton.id_data, find = find)

    mapping = get_settings_skel(skeleton)
    return mapping

def get_preset_skel(preset, settings=None, validate=True):
    if not preset:
        return
    if not preset.endswith(".py"):
        return

    preset_path = os.path.join(get_retarget_dir(), preset)
    if not os.path.isfile(preset_path):
        return
    
    defaut_s = get_preset_from_file(preset_path, settings)

    skeleton = settings if settings else defaut_s

    if settings and validate:
        validate_preset(settings.id_data)

    mapping = HumanSkeleton(preset=skeleton)
    del skeleton
    
    return mapping


def reset_preset_names(settings):
    "Reset preset names used by scripts"
    settings.right_arm.name = 'arm'
    settings.left_arm.name = 'arm'

    settings.right_leg.name = 'leg'
    settings.left_leg.name = 'leg'

    settings.right_fingers.name = 'fingers'
    settings.left_fingers.name = 'fingers'


class PresetFinger:
    def __init__(self):
        self.a = ""
        self.b = ""
        self.c = ""
        self.meta = ""


class PresetSkeleton:
    def __init__(self):
        self.face = SimpleFace()
        self.spine = HumanSpine()

        self.left_arm = HumanArm()
        self.left_arm_ik = HumanArm()
        self.right_arm = HumanArm()
        self.right_arm_ik = HumanArm()

        self.right_leg = HumanLeg()
        self.right_leg_ik = HumanLeg()
        self.left_leg = HumanLeg()
        self.left_leg_ik = HumanLeg()

        self.left_fingers = HumanFingers(thumb=PresetFinger(), index=PresetFinger(), middle=PresetFinger(), ring=PresetFinger(), pinky=PresetFinger())
        self.right_fingers = HumanFingers(thumb=PresetFinger(), index=PresetFinger(), middle=PresetFinger(), ring=PresetFinger(), pinky=PresetFinger())
        self.root = ""

        self.deform_preset = "--"

        self.other_bone = dict()

    def copy(self, settings):

        try:
            setattr(self, "root" , getattr(settings, "root"))
        except:
            pass

        try:
            setattr(self, "deform_preset" , getattr(settings, "deform_preset"))
        except:
            pass

        for group in ('spine', 'left_arm', 'left_arm_ik', 'right_arm', 'right_arm_ik',
                      'right_leg', 'right_leg_ik', 'left_leg', 'left_leg_ik', 'face'):
            
            setting = getattr(self, group)
            trg_setting = getattr(settings, group)

            for k in setting.keys():
                setattr(setting, k, getattr(trg_setting, k))

        finger_bones = 'a', 'b', 'c', 'meta'
        for group, trg_grp in zip((self.left_fingers, self.right_fingers),
                                  (settings.left_fingers, settings.right_fingers)):
            for k in group.keys():
                if k == 'name':  # skip Property Group name
                    continue

                finger = getattr(group, k)
                trg_finger = getattr(trg_grp, k)

                for i, slot in enumerate(finger_bones):
                    # preset/settings compatibility: a,b,c against [0], [1], [2]
                    try:
                        setattr(finger, slot, getattr(trg_finger, slot))
                    except AttributeError:
                        setattr(finger, slot, trg_finger[i])

        if hasattr(settings,"other_bone_id"):
            for item in settings.other_bone:
                if item.name and item.bone_name:
                    self.other_bone[item.name] = item.bone_name
        else:
            self.other_bone = settings.other_bone.copy()