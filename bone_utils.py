import bpy
from mathutils import Vector
from mathutils import Matrix
from mathutils import Quaternion
from bpy_extras import anim_utils
from math import pi
from .action import ops
#retarget bones suffix
cp_suffix = '_RET'
const_type = ['COPY_LOCATION', 'LIMIT_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'LOCKED_TRACK', 'FLOOR', 'DAMPED_TRACK']


def is_pose_bone_all_locked(pose_bone) -> bool:
    """Return True if all pose_bone's transform channels are locked"""
    if not all(pose_bone.lock_location):
        return False
    if not all(pose_bone.lock_scale):
        return False
    if not all(pose_bone.lock_rotation):
        return False
    
    return True


def vec_roll_to_mat3_normalized(nor, roll):
    THETA_SAFE = 1.0e-5  # theta above this value are always safe to use
    THETA_CRITICAL = 1.0e-9  # above this is safe under certain conditions

    assert nor.magnitude - 1.0 < 0.01

    x = nor.x
    y = nor.y
    z = nor.z

    theta = 1.0 + y
    theta_alt = x * x + z * z

    # When theta is close to zero (nor is aligned close to negative Y Axis),
    # we have to check we do have non-null X/Z components as well.
    # Also, due to float precision errors, nor can be (0.0, -0.99999994, 0.0) which results
    # in theta being close to zero. This will cause problems when theta is used as divisor.

    bMatrix = Matrix().to_3x3()

    if theta > THETA_SAFE or ((bool(x) | bool(z)) and theta > THETA_CRITICAL):
        # nor is *not* aligned to negative Y-axis (0,-1,0).
        # We got these values for free... so be happy with it... ;)

        bMatrix[0][1] = -x
        bMatrix[1][0] = x
        bMatrix[1][1] = y
        bMatrix[1][2] = z
        bMatrix[2][1] = -z

        if theta > THETA_SAFE:
            # nor differs significantly from negative Y axis (0,-1,0): apply the general case. */
            bMatrix[0][0] = 1 - x * x / theta
            bMatrix[2][2] = 1 - z * z / theta
            bMatrix[2][0] = bMatrix[0][2] = -x * z / theta
        else:
            # nor is close to negative Y axis (0,-1,0): apply the special case. */
            bMatrix[0][0] = (x + z) * (x - z) / -theta_alt
            bMatrix[2][2] = -bMatrix[0][0]
            bMatrix[2][0] = bMatrix[0][2] = 2.0 * x * z / theta_alt
    else:
        # nor is very close to negative Y axis (0,-1,0): use simple symmetry by Z axis. */
        bMatrix.identity()
        bMatrix[0][0] = bMatrix[1][1] = -1.0

    # Make Roll matrix */
    quat = Quaternion(nor, roll)
    rMatrix = quat.to_matrix()

    # Combine and output result */
    return rMatrix @ bMatrix


def ebone_roll_to_vector(bone, align_axis, axis_only=False):
    align_axis.normalize()
    assert abs(align_axis.magnitude - 1.0) < 1.0e-5
    nor = bone.tail - bone.head
    nor.normalize()

    d = nor.dot(align_axis)
    if d == 1.0:
        return 0.0

    # project the new_up_axis along the normal */
    vec = align_axis.project(nor)
    align_axis_proj = align_axis - vec

    mat = vec_roll_to_mat3_normalized(nor, 0.0)
    if axis_only:
        try:
            if align_axis_proj.angle(mat[2]) > pi / 2:
                align_axis_proj.negate()
        except ValueError:
            return bone.roll

    try:
        roll = align_axis_proj.angle(mat[2])
    except ValueError:
        return bone.roll

    vec = mat[2].cross(align_axis_proj)
    if vec.dot(nor) < 0.0:
        return -roll

    return roll

def copy_modifier_properties(source_mod, dest_mod):
    """
    Copies properties from a source modifier to a destination modifier.
    
    :param source_mod: The original modifier (bpy.types.Modifier).
    :param dest_mod: The new modifier (bpy.types.Modifier).
    """
    for attr_name in sorted(dir(source_mod)):
        # Skip internal, read-only, or non-applicable properties
        if attr_name.startswith("__") or attr_name in ["bl_rna", "type", "name"]:
            continue
        
        try:
            # Check if the property is not read-only before attempting to set
            if not source_mod.is_property_readonly(attr_name):
                setattr(dest_mod, attr_name, getattr(source_mod, attr_name))
        except Exception:
            # Some properties might raise exceptions even if not "readonly"
            pass

def copy_bone_constraints(bone_a, bone_b):
    """Copy all bone constraints from bone_A to bone_b and sets their writable attributes.
       Doesn't delete constraints that already exist
    """
    for constr_a in bone_a.constraints:
        constr_b = bone_b.constraints.new(constr_a.type)

        for c_attr in dir(constr_b):
            if c_attr.startswith("_"):
                continue
            try:
                setattr(constr_b, c_attr, getattr(constr_a, c_attr))
            except AttributeError:
                continue


def copy_bone_to_arm(src_ob, trg_ob, bone_name, suffix=cp_suffix):
    """Create a new bone in trg_ob with the same head/tail as bone with the given name"""
    try:
        src_bone = src_ob.data.bones[bone_name]
    except KeyError:
        return

    new_name = bone_name+suffix
    
    try:
        new_bone = trg_ob.data.edit_bones[new_name]
    except KeyError:
        new_bone = trg_ob.data.edit_bones.new(new_name)

    new_bone.head = src_bone.head_local
    new_bone.tail = src_bone.tail_local

    return new_bone.name


def copy_bone(ob, bone_name, assign_name='', constraints=False, deform_bone='SAME'):
    """ Makes a copy of the given bone in the given armature object.
        Returns the resulting bone's name.

        NOTE: taken from rigify module utils.py, added the contraints option and stripped the part about rna properties
    """
    if bone_name not in ob.data.edit_bones:
        raise Exception("copy_bone(): bone '%s' not found, cannot copy it" % bone_name)

    if assign_name == '':
        assign_name = bone_name
    # Copy the edit bone
    edit_bone_1 = ob.data.edit_bones[bone_name]
    edit_bone_2 = ob.data.edit_bones.new(assign_name)

    bone_name_1 = bone_name
    bone_name_2 = edit_bone_2.name

    edit_bone_2.parent = edit_bone_1.parent
    edit_bone_2.use_connect = edit_bone_1.use_connect

    # Copy edit bone attributes
    try:
        edit_bone_2.layers = list(edit_bone_1.layers)
    except AttributeError:
        for collection in edit_bone_1.collections:
            collection.assign(edit_bone_2)

    edit_bone_2.head = Vector(edit_bone_1.head)
    edit_bone_2.tail = Vector(edit_bone_1.tail)
    edit_bone_2.roll = edit_bone_1.roll

    edit_bone_2.use_inherit_rotation = edit_bone_1.use_inherit_rotation
    try:
        edit_bone_2.use_inherit_scale = edit_bone_1.use_inherit_scale
    except AttributeError:
        edit_bone_2.inherit_scale = edit_bone_1.inherit_scale
    edit_bone_2.use_local_location = edit_bone_1.use_local_location

    if deform_bone == 'SAME':
        edit_bone_2.use_deform = edit_bone_1.use_deform
    else:
        edit_bone_2.use_deform = deform_bone
    edit_bone_2.bbone_segments = edit_bone_1.bbone_segments
    edit_bone_2.bbone_custom_handle_start = edit_bone_1.bbone_custom_handle_start
    edit_bone_2.bbone_custom_handle_end = edit_bone_1.bbone_custom_handle_end

    # ITD- bones go to MCH layer
    try:
        edit_bone_2.layers[30] = True
    except AttributeError:
        try:
            MCH_coll = ob.data.collections['MCH']
        except KeyError:
            MCH_coll = ob.data.collections.new('MCH')
        else:
            MCH_coll.assign(edit_bone_2)
    else:
        edit_bone_2.layers[31] = False
        for i in range(30):
            edit_bone_2.layers[i] = False

    ob.update_from_editmode()

    # Get the pose bones
    pose_bone_1 = ob.pose.bones[bone_name_1]
    pose_bone_2 = ob.pose.bones[bone_name_2]

    # Copy pose bone attributes
    pose_bone_2.rotation_mode = pose_bone_1.rotation_mode
    pose_bone_2.rotation_axis_angle = tuple(pose_bone_1.rotation_axis_angle)
    pose_bone_2.rotation_euler = tuple(pose_bone_1.rotation_euler)
    pose_bone_2.rotation_quaternion = tuple(pose_bone_1.rotation_quaternion)

    pose_bone_2.lock_location = tuple(pose_bone_1.lock_location)
    pose_bone_2.lock_scale = tuple(pose_bone_1.lock_scale)
    pose_bone_2.lock_rotation = tuple(pose_bone_1.lock_rotation)
    pose_bone_2.lock_rotation_w = pose_bone_1.lock_rotation_w
    pose_bone_2.lock_rotations_4d = pose_bone_1.lock_rotations_4d

    if constraints:
        copy_bone_constraints(pose_bone_1, pose_bone_2)

    return bone_name_2


def remove_bone_constraints(pbone):
    for constr in reversed(pbone.constraints):
        pbone.constraints.remove(constr)


def remove_all_bone_constraints(ob):
    for pbone in ob.pose.bones:
        remove_bone_constraints(pbone)


def get_constrained_controls(armature_object: bpy.types.Object, unselect=False, use_deform=False) -> list[bpy.types.PoseBone]:
    for pb in armature_object.pose.bones:
        if pb.bone.use_deform and not use_deform:  # FIXME: ik controls might have use_deform just to be exported for games
            if unselect:
                pb.select = False
            continue

        if len(pb.constraints) == 0:
            if unselect:
                pb.select = False
            continue
    
        yield pb


def get_armature_bone(ob, bone_name):
    """Return the Armature Bone with given bone_name, None if not found"""
    return ob.data.bones.get(bone_name, None)


def get_edit_bone(ob, bone_name):
    """Return the Edit Bone with given bone name, None if not found"""
    return ob.data.edit_bones.get(bone_name, None)


def is_def_bone(ob, bone_name):
    """Return True if the bone with given name is a deforming bone,
       False if it isn't, None if the bone is not found"""
    bone = get_armature_bone(ob, bone_name)

    if not bone:
        return

    return bone.use_deform


def find_def_parent(ob, org_bone):
    """Return the first DEF- bone that is suitable as parent bone of given ORG- bone"""
    org_par = org_bone.parent
    if not org_par:
        return

    if org_par.name.startswith("MCH-"):  # MCH bones risk to be named after the bone we have started with
        return find_def_parent(ob, org_par)

    par_def_name = "DEF-{0}".format(org_par.name[4:])
    try:
        par_def = ob.pose.bones[par_def_name]
        return par_def
    except KeyError:
        return find_def_parent(ob, org_par)


def get_deform_root_name(ob):
    """Get the name of first deform bone with no deform parent

    :param ob:
    :return:
    """
    # TODO
    return 'DEF-spine'


def get_deform_hips_name(ob, bone_name=None):
    """Starting from the root, get the first bone with more than one child

    :param ob: the armature object
    :param bone_name:
    :return: name of deform hips bone
    """
    if not bone_name:
        bone_name = get_deform_root_name(ob)

    try:
        bone = ob.data.edit_bones[bone_name]
    except KeyError:
        return

    if len(bone.children) > 1:
        return bone_name

    return get_deform_hips_name(ob, bone.children[0].name)


def set_inherit_scale(ob, inherit_mode='FIX_SHEAR'):
    for bone in ob.data.edit_bones:
        if not bone.use_deform:
            continue

        bone.inherit_scale = inherit_mode


def copy_chain(ob, first, last_excluded=None, flip_bones=False):
    """Copy a chain of bones, return name of last copied bone"""
    bone = first
    bone_name = ''

    prev_itd_bone = None
    while bone != last_excluded:
        bone_name = bone.name
        itd_name = bone_name.replace("DEF-", "ITD-")
        try:
            itd_bone = ob.data.edit_bones[itd_name]
        except KeyError:
            itd_name = copy_bone(ob, bone_name, assign_name=itd_name, constraints=True, deform_bone=False)
            itd_bone = ob.data.edit_bones[itd_name]

        itd_bone.use_deform = False
        itd_bone.parent = prev_itd_bone
        prev_itd_bone = itd_bone

        cp_name = copy_bone(ob, bone_name, assign_name=bone_name.replace("DEF-", "CP-"), constraints=False,
                            deform_bone=False)
        cp_bone = ob.data.edit_bones[cp_name]
        cp_bone.use_deform = False

        cp_bone.parent = None

        if flip_bones:
            flip_bone(cp_bone)

        pbone = ob.pose.bones[bone_name]
        remove_bone_constraints(pbone)
        cp_loc = pbone.constraints.new('COPY_LOCATION')
        cp_rot = pbone.constraints.new('COPY_ROTATION')
        cp_scale = pbone.constraints.new('COPY_SCALE')
        for constr in (cp_loc, cp_rot, cp_scale):
            constr.target = ob
            constr.subtarget = cp_name

        cp_bone.parent = itd_bone

        # ITD- bones go to MCH layer
        for new_bone in (itd_bone, cp_bone):
            try:
                new_bone.layers[30] = True
            except AttributeError:
                #TODO: use collections
                break

            new_bone.layers[31] = False
            for i in range(30):
                new_bone.layers[i] = False

        if not bone.children:
            break
        bone = bone.children[0]

    return bone_name


def flip_bone(bone):
    bone.head, bone.tail = bone.tail.copy(), bone.head.copy()


def find_tail_root(ob, tail_start_name='DEF-tail.001'):
    try:
        tail_bone = get_edit_bone(ob, tail_start_name)
    except KeyError:
        return

    if not tail_bone:
        return

    while tail_bone.parent and is_def_bone(ob, tail_bone.parent.name):
        tail_bone = tail_bone.parent

    return tail_bone.name


def fix_tail_direction(ob):
    """Make the hips the actual root and parent the tail to it (Rigify tails are the other way around"""
    def_root_name = get_deform_root_name(ob)
    def_hips_name = get_deform_hips_name(ob, def_root_name)

    if not def_hips_name:
        return

    if def_root_name == def_hips_name:

        def_root_name = find_tail_root(ob)
        if not def_root_name:
            print("cannot figure root/hips, not fixing, tail")
            return def_hips_name

    def_root_edit = get_edit_bone(ob, def_root_name)
    def_hips_edit = get_edit_bone(ob, def_hips_name)

    tail_next_name = copy_chain(ob, def_root_edit, def_hips_edit, flip_bones=True)
    def_tail_next = get_edit_bone(ob, tail_next_name)
    def_tail_previous = def_hips_edit

    def_hips_edit.parent = None
    def_root_edit.parent = def_hips_edit

    while def_tail_next:
        if def_tail_next == def_hips_edit:
            break
        previous_parent = def_tail_next.parent

        def_tail_next.parent = None
        # flip bone
        flip_bone(def_tail_next)
        def_tail_next.parent = def_tail_previous
        if def_tail_previous is not def_hips_edit:
            def_tail_next.use_connect = True

        def_tail_previous = def_tail_next
        def_tail_next = previous_parent

    return def_hips_name


def copytransform_to_copylocrot(ob):
    for pbone in ob.pose.bones:
        if not ob.data.bones[pbone.name].use_deform:
            continue

        to_remove = []
        for constr in pbone.constraints:
            if constr.type == 'COPY_TRANSFORM':
                to_remove.append(constr)
                for cp_constr in (pbone.constraints.new('COPY_ROTATION'), pbone.constraints.new('COPY_LOCATION')):
                    cp_constr.target = constr.ob
                    cp_constr.subtarget = constr.subtarget
            elif constr.type == 'STRETCH_TO':
                constr.mute = True

        for constr in to_remove:
            pbone.constraints.remove(constr)


def limit_spine_scale(ob):
    for pbone in ob.pose.bones:
        if not ob.data.bones[pbone.name].use_deform:
            continue

        if not pbone.name.startswith('DEF-spine'):
            continue

        constr = pbone.constraints.new('LIMIT_SCALE')

        constr.min_x = 1
        constr.min_y = 1
        constr.min_z = 1

        constr.max_x = 1
        constr.max_y = 1
        constr.max_z = 1

        constr.use_min_x = True
        constr.use_min_y = True
        constr.use_min_z = True

        constr.use_max_x = True
        constr.use_max_y = True
        constr.use_max_z = True

        constr.owner_space = 'LOCAL'


def gamefriendly_hierarchy(ob, fix_tail=True, limit_scale=False):
    """Changes Rigify (0.5) rigs to a single root deformation hierarchy.
    Create ITD- (InTermeDiate) bones in the process"""
    assert (ob.mode == 'EDIT')

    bone_names = list((b.name for b in ob.data.bones if is_def_bone(ob, b.name)))
    new_bone_names = []  # collect newly added bone names so that they can be edited later in Object Mode

    def_root_name = get_deform_root_name(ob)
    num_reparents = 0

    # we want deforming bone (i.e. the ones on layer 29) to have deforming bone parents
    for bone_name in bone_names:
        if bone_name == def_root_name:
            continue

        if not ob.pose.bones[bone_name].parent:
            # root bones are fine
            continue
        if is_def_bone(ob, ob.pose.bones[bone_name].parent.name):
            continue

        # Intermediate Bone
        itd_name = bone_name.replace("DEF-", "ITD-")
        itd_name = itd_name.replace("MCH-", "ITD-")
        if not itd_name.startswith("ITD-"):
            itd_name = "ITD-" + itd_name
        try:
            ob.data.edit_bones[itd_name]
        except KeyError:
            itd_name = copy_bone(ob, bone_name, assign_name=itd_name, constraints=True,
                                 deform_bone=False)
            new_bone_names.append(itd_name)

        # DEF- bone will now follow the ITD- bone
        pbone = ob.pose.bones[bone_name]
        remove_bone_constraints(pbone)
        for cp_constr in (pbone.constraints.new('COPY_LOCATION'),
                          pbone.constraints.new('COPY_ROTATION'),
                          pbone.constraints.new('COPY_SCALE')):
            cp_constr.target = ob
            cp_constr.subtarget = itd_name

        # Look for a DEF- bone that would be a good parent. Unlike DEF- bones, ORG- bones retain the
        # hierarchy from the metarig, so we are going to reproduce the ORG- hierarchy
        if bone_name.startswith('DEF-eye'):
            org_name = "ORG-eye." + bone_name[-1]
        else:
            org_name = "ORG-{0}".format(bone_name[4:])

        try:
            org_bone = ob.pose.bones[org_name]
        except KeyError:
            print("WARNING: 'ORG-' bone not found ({0})", org_name)
            continue
        else:
            def_par = find_def_parent(ob, org_bone)
            if not def_par:
                print("WARNING: Parent not found for {0}".format(bone_name))
                # as a last resort, look for a DEF- bone with the same name but a lower number
                # (i.e. try to parent DEF-tongue.002 to DEF-tongue.001)
                if bone_name[-4] == "." and bone_name[-3:].isdigit():
                    try:
                        bname, number = bone_name.rsplit(".")
                    except ValueError:
                        print("No valid numbering for {0}".format(bone_name))
                        continue

                    number = int(number)
                    if number > 1:
                        def_par_name = "{0}.{1:03d}".format(bname, number - 1)
                        print("Trying to use {0}".format(def_par_name))
                        try:
                            def_par = ob.pose.bones[def_par_name]
                        except KeyError:
                            print("No suitable DEF- parent for {0}".format(bone_name))
                            continue
                    else:
                        continue
                else:
                    continue

        ebone = get_edit_bone(ob, bone_name)
        ebone_par = get_edit_bone(ob, def_par.name)
        ebone.parent = ebone_par
        num_reparents += 1

    if fix_tail:
        # FIXME: these bones will not be added to num_reparents
        try:
            new_root_name = fix_tail_direction(ob)
        except IndexError:
            fix_tail = False
        else:
            if new_root_name:
                def_root_name = new_root_name

    if limit_scale:
        limit_spine_scale(ob)

    try:
        ob.data.edit_bones[def_root_name].parent = ob.data.edit_bones['root']
    except KeyError:
        print("WARNING: DEF hierarchy root was not parented to root bone")

    return num_reparents


def iterate_rigged_obs(armature_object, context):
    for ob in context.scene.objects:
        if ob.type != 'MESH':
            continue
        if not ob.modifiers:
            continue
        for modifier in [mod for mod in ob.modifiers if mod.type == 'ARMATURE']:
            if modifier.object == armature_object:
                yield ob
                break


def get_group_verts(obj, vertex_group, threshold=0.1):
    group_idx = obj.vertex_groups[vertex_group].index
    weighted_verts = []

    for i, v in enumerate(obj.data.vertices):
        try:
            g = next(g for g in v.groups if g.group == group_idx)
        except StopIteration:
            continue

        if g.weight < threshold:
            continue

        weighted_verts.append(i)

    return weighted_verts


def align_to_closer_axis(src_bone, trg_bone):
    src_rot = src_bone.matrix_local.to_3x3().inverted()
    src_x_axis = src_rot[0]
    src_y_axis = src_rot[1]
    src_z_axis = src_rot[2]

    bone_direction = trg_bone.parent.vector.normalized()
    dot_x = abs(bone_direction.dot(src_x_axis))
    dot_y = abs(bone_direction.dot(src_y_axis))
    dot_z = abs(bone_direction.dot(src_z_axis))

    matching_dot = max(dot_x, dot_y, dot_z)
    if matching_dot == dot_x:
        closer_axis = src_x_axis
    elif matching_dot == dot_y:
        closer_axis = src_y_axis
    else:
        closer_axis = src_z_axis

    offset = closer_axis * src_bone.length
    if closer_axis.dot(bone_direction) < 0:
        offset *= -1

    trg_bone.tail = trg_bone.head + offset


def closest_bone_axis(bone, mat, direction):
    """Return bone axis which is closest to direction"""
    xyz = bone.x_axis, bone.y_axis, bone.z_axis
    xyz = [(mat @ x).normalized() for x in xyz]

    dot_prods = [abs(direction.dot(x)) for x in xyz]

    return xyz[dot_prods.index(max(dot_prods))]


def relative_direction(start_bone, end_bone, mat):
    direction = end_bone.matrix_local.translation.copy()
    direction -= start_bone.matrix_local.translation

    direction = mat @ direction
    return direction.normalized()


def relative_pose_direction(start_pose_bone, end_pose_bone, mat):
    direction = end_pose_bone.matrix.translation.copy()
    direction -= start_pose_bone.matrix.translation

    direction = mat @ direction
    return direction.normalized()


def lrl_strip(bone): # bone: str, Bone, PoseBone, EditBone
    """Returns Left/Right agnostic name of the bone. Lower case."""
    if not bone:
        return ""
    name = (bone if type(bone) is str else bone.name).lower()
    for _ in (".r", ".l", "right", "left", "rgt", "lft", "_l_", "_l", "l_", "_r_", "_r", "r_", " r", " l", "r ", "l ", "r", "l", "右", "左"):
        _new = name.replace(_, "")
        name = _new or name
    return name

def bone_left_or_right(bone):
    # true mean that is a left bone
    if not bone:
        return True
    
    name = (bone if type(bone) is str else bone.name).lower()
    if ":" in name:
        name = name.split(":")[-1]
    key = ""

    for _ in (".l", "left", "lft", "_l_", "_l", "l_", " l", "l ", "左"):
        if _ in name:
            key = _
            break

    if not key:
        for _ in (".r", "right", "rgt", "_r_", "_r", "r_", " r", "r ", "右"):
            if _ in name:
                key = _
                break
            
    if not key:
        for _ in ("l", "r"):
            if _ in name:
                if name.startswith(_):
                    key = _
                    break
                if name.endswith(_):
                    key = _
                    break
                break
    
    left = (".l", "left", "lft", "_l_", "_l", "l_", " l", "l ", "l", "左")

    return bool(key in left)
    
def bone_left_name(right):
    if not right:
        return ""
    
    right_left = {
        ".R": ".L",
        ".r": ".l",
        "right": "left",
        "RIGHT": "LEFT",
        "Right": "Left",
        "_R_": "_L_",
        "_R": "_L",
        "R_": "L_",
        "_r_": "_l_",
        "_r": "_l",
        "r_": "l_",
        " R": " L",
        " r": " l",
        "R ": "L ",
        "r ": "l ",
        "R": "L",
        "r": "l",
        "右": "左",
    }
    
    name = (right if type(right) is str else right.name)
    if ":" in name:
        name = name.split(":")[-1]
    left = ""

    for r, l in right_left.items():

        if r in name:
            if name.startswith(r):
                left = l + name.removeprefix(r)
                break
            if name.endswith(r):
                left = name.removesuffix(r) + l
                break
            
            left = name.replace(r, l)
            break

    return left
    
def bone_right_name(left):
    if not left:
        return ""
    
    right_left = {
        ".R": ".L",
        ".r": ".l",
        "right": "left",
        "RIGHT": "LEFT",
        "Right": "Left",
        "_R_": "_L_",
        "_R": "_L",
        "R_": "L_",
        "_r_": "_l_",
        "_r": "_l",
        "r_": "l_",
        " R": " L",
        " r": " l",
        "R ": "L ",
        "r ": "l ",
        "R": "L",
        "r": "l",
        "右": "左",
    }
    
    name = (left if type(left) is str else left.name)
    if ":" in name:
        name = name.split(":")[-1]

    right = ""

    for r, l in right_left.items():

        if l in name:
            if name.startswith(l):
                right = r + name.removeprefix(l)
                break
            if name.endswith(l):
                right = name.removesuffix(l) + r
                break

            right = name.replace(l, r)
            break

    return right





def get_rest_z_axes(obj, context):
    """returns {pbone.name : z_axis} for obj's rest pose"""
    axes = {}
    old_mode = obj.data.pose_position
    if old_mode != 'REST':
        obj.data.pose_position = 'REST'
        if bpy.app.version < (2, 80):
            context.scene.update()
        else:
            context.view_layer.update()
    for pb in obj.pose.bones:
        axes[pb.name] = pb.z_axis
    if old_mode != 'REST':
        obj.data.pose_position = old_mode
        if bpy.app.version < (2, 80):
            context.scene.update()
        else:
            context.view_layer.update()
    return axes

def visible_bone(bone):

    if bone.hide:
        return False

    if bone.bone.hide:
        return False
    
    visible = True
    for col in bone.bone.collections:
        if col.is_visible_effectively:
            return True
        else:
            visible = False

    return visible


def get_trg_iterate(self, context, edit_text):

    iterate = list()
    iterate.append(("All", "All Target"))

    armatures = context.selected_objects
    
    for ob in armatures:

        if ob.type != 'ARMATURE':
            continue

        trg_list = get_trg_ob(ob)

        if trg_list:
            for trg in trg_list:
                iterate.append((trg.name, trg.name))

    return iterate

def get_trg_iterate_all(self, context, edit_text):


    iterate = list()
    iterate.append(("All", "All Target"))

    armatures = context.selected_objects

    for ob in armatures:

        if ob.type != 'ARMATURE':
            continue
    
        target_list = list()

        for pb in get_constrained_controls(armature_object=ob, use_deform=True):
            for constr in pb.constraints:

                try:
                    target = constr.target
                except AttributeError:
                    continue

                if constr.target and not constr.target in target_list:
                    target_list.append(constr.target)

        if target_list:
            for trg in target_list:
                iterate.append((trg.name, trg.name))

    return iterate

def get_trg_ob(ob: bpy.types.Object , all = False, suffix = cp_suffix):
       
    target_list = list()

    for pb in get_constrained_controls(armature_object=ob, use_deform=True):
        for constr in pb.constraints:
            try:
                target = constr.target
            except AttributeError:
                continue

            if all:
                if constr.target and not constr.target in target_list:
                    target_list.append(constr.target)

            elif suffix in constr.name:

                if constr.target and not constr.target in target_list:
                    target_list.append(constr.target)

    return target_list

def get_all_limb(self, context, edit_text):
    limbs = []
    limbs.append(('--', "--"))

    o = ops.get_ob_or_armature(context, context.active_object)
    obj = None

    #find source rig
    for ob in ops.get_selected_obs(context):
        if ob != o and ob.type == 'ARMATURE':
            obj = ob
            break

    if not obj or obj.type != 'ARMATURE':
        return limbs
    
    skeleton = obj.data.retarget_retarget

    if skeleton.spine.head or skeleton.spine.neck:
        limbs.append(('head', "Head"))
        
    if skeleton.spine.has_settings():
        limbs.append(('spine', "Spine "))
    
    if skeleton.right_arm.shoulder:
        limbs.append(('RightShoulder', "Right Shoulder"))

    if skeleton.left_arm.shoulder:
        limbs.append(('LeftShoulder', "Left Shoulder"))

    if skeleton.right_arm.has_settings():
        limbs.append(('right_arm', "Right Arm"))

    if skeleton.left_arm.has_settings():
        limbs.append(('left_arm', "Left Arm"))
    
    if skeleton.left_fingers.has_settings():
        limbs.append(('left_fingers', "Left Fingers"))

    if skeleton.right_fingers.has_settings():
        limbs.append(('right_fingers', "Right Fingers"))

    if skeleton.right_leg.upleg or skeleton.right_leg.leg:
        limbs.append(('right_leg', "Right Leg"))

    if skeleton.left_leg.upleg or skeleton.left_leg.leg:
        limbs.append(('left_leg', "Left Leg"))

    if skeleton.right_leg.foot or skeleton.right_leg.toe:
        limbs.append(('right_foot', "Right Foot"))

    if skeleton.left_leg.foot or skeleton.left_leg.toe:
        limbs.append(('left_foot', "Left Foot"))

    if skeleton.right_arm_ik.has_settings():
        limbs.append(('right_arm_ik', "Right Arm IK"))

    if skeleton.left_arm_ik.has_settings():
        limbs.append(('left_arm_ik', "Left Arm IK"))

    if skeleton.right_leg_ik.has_settings():
        limbs.append(('right_leg_ik', "Right Leg IK"))

    if skeleton.left_leg_ik.has_settings():
        limbs.append(('left_leg_ik', "Left Leg IK"))

    if skeleton.spine.hips:
        limbs.append(('hips', "Hips"))

    if not skeleton.other_bone:
        return limbs

    for item in skeleton.other_bone:
        if item.limb and not (item.limb, item.limb) in limbs:
            limbs.append((item.limb, item.limb))
    
    return limbs

def get_limb_other_bone(src_settings):
    limbs = []
    for item in src_settings.other_bone:
        if item.limb and not item.limb in limbs:
            limbs.append(item.limb)
    
    return limbs

# matrix bone for apply constrainst
def get_ob_matrix(ob, mat):
        parent = ob.parent
        matrix = mat
        if parent:
            return parent.matrix_world.inverted_safe() @ matrix
        else:
            return matrix.copy() 
        
def get_bone_matrix(bone, mat):
        

    bmat = mat
    
    for child_of_cns in reversed(bone.constraints):

        if child_of_cns.type not in ['CHILD_OF', 'ARMATURE']:
            continue
        
        # for CHILD_OF constraint
        elif child_of_cns.type == 'CHILD_OF' and getattr(child_of_cns, "target", None):

            if child_of_cns.target.type != 'ARMATURE':
                continue
            # Child Of constraints are preserved after baking
            # need to compensate the matrix with the Child Of transformation
            
            if child_of_cns:
                if child_of_cns.subtarget:
                    if child_of_cns.influence == 1.0 and not child_of_cns.mute:
                        subtarget_bone = child_of_cns.target.pose.bones.get(
                            child_of_cns.subtarget
                        )
                        if subtarget_bone:

                            bmat = (
                                subtarget_bone.matrix_channel.copy().inverted() @ bmat
                            )
                            break
                        else:
                            print(
                                f"Subtarget bone not found: {child_of_cns.subtarget}"  # noqa: E501
                            )
            else:
                print(f"No Child Of constraint found for {bone.name}")

        # for ARMATURE constrainst

        elif child_of_cns.type == 'ARMATURE' and getattr(child_of_cns, "targets", None):

            if child_of_cns.influence != 1 or child_of_cns.mute:
                continue

            subtarget = None

            for target in child_of_cns.targets:

                if target.target.type != 'ARMATURE':
                    continue

                if target and target.subtarget and target.weight == 1:
                    subtarget = target.target.pose.bones.get(target.subtarget)
                    break
            if subtarget:
                bmat = (
                            subtarget.matrix_channel.copy().inverted() @ bmat
                        )
                break
    
    return bmat


#baking action -----------------



def has_slotted_actions():
    """Check if Blender supports slotted actions (4.4+)"""
    return bpy.app.version >= (4, 4, 0)

def is_pose_bone_selected(pbone):
    if pbone is None:
        return False

    try:
        if hasattr(pbone, "bone") and pbone.bone is not None and hasattr(
            pbone.bone, "select"
        ):
            return bool(pbone.bone.select)
        if hasattr(pbone, "select"):
            return bool(pbone.select)
        arm_obj = getattr(pbone, "id_data", None)
        arm_data = getattr(arm_obj, "data", None)
        if arm_data is not None and hasattr(arm_data, "bones"):
            b = arm_data.bones.get(pbone.name)
            if b is not None and hasattr(b, "select"):
                return bool(b.select)
    except Exception:
        return False

    return False


class ArpBlenderVersion:
    _string = bpy.app.version_string
    blender_v = bpy.app.version
    _float = blender_v[0] * 100 + blender_v[1] + blender_v[2] * 0.01
    # _char = bpy.app.version_string

blender_version = ArpBlenderVersion()

def assign_action_to_animdata(anim_data, action, target_datablock=None):
    """
    Assign an action to animation data, handling slot assignment for 4.4+.

    Args:
        anim_data: bpy.types.AnimData
        action: bpy.types.Action
        target_datablock: The data-block being animated (slot assign)  # noqa: E501

    Returns:
        bool: True if successful
    """
    if anim_data is None or action is None:
        return False

    # Assign the action (works in all versions)
    anim_data.action = action

    # Blender 4.4+: explicitly assign an Action Slot if auto-assignment didn't happen
    if has_slotted_actions():
        # Official pattern: use anim_data.action_slot and action_suitable_slots
        if hasattr(anim_data, "action_slot"):
            try:
                if anim_data.action_slot is None:
                    suitable = getattr(anim_data, "action_suitable_slots", None)
                    if suitable and len(suitable) > 0:
                        # Direct assignment of the slot object
                        anim_data.action_slot = suitable[0]
                    else:
                        # Fallback: ensure a slot by creating/ensuring an FCurve for this datablock  # noqa: E501
                        # This API will also create the layer/strip/slot and assign it as needed  # noqa: E501
                        if target_datablock is not None and hasattr(
                            action, "fcurve_ensure_for_datablock"
                        ):
                            try:
                                # Use a representative data path for the datablock type
                                data_path = "location"
                                if (
                                    hasattr(target_datablock, "pose")
                                    and hasattr(target_datablock.pose, "bones")
                                    and len(target_datablock.pose.bones) > 0
                                ):
                                    first_bone_name = target_datablock.pose.bones[
                                        0
                                    ].name
                                    data_path = f'pose.bones["{first_bone_name}"].rotation_euler'  # noqa: E501
                                action.fcurve_ensure_for_datablock(
                                    target_datablock, data_path, index=0
                                )
                            except Exception:
                                pass
            except Exception:
                pass

    return True


def get_action_fcurves(action):
    if not action:
        return []
    
    channelbag = None
    for slot in action.slots:

        if slot.target_id_type != 'OBJECT':
            continue

        channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
        if not channelbag:
            if len(action.layers) == 0:
                action.layers.new("layer0")
            if len(action.layers[0].strips) == 0:
                action.layers[0].strips.new(type='KEYFRAME')
            channelbag = action.layers[0].strips[0].channelbag(slot, ensure=True)

        return channelbag.fcurves 
        
    return []

def ensure_fcurve_exists(action, datablock, data_path, index=0):
    """
    Ensure an F-Curve exists on an action for a specific data-block property.
    Compatible with legacy, slotted, and layered actions.

    Args:
        action: bpy.types.Action
        datablock: The data-block being animated
        data_path: Property data path (e.g., "location")
        index: Array index for the property

    Returns:
        bpy.types.FCurve or None
    """
    if action is None:
        return None

    # In 4.4+, use the convenience function if available
    if has_slotted_actions() and hasattr(action, "fcurve_ensure_for_datablock"):
        try:
            return action.fcurve_ensure_for_datablock(datablock, data_path, index=index)
        except Exception:
            pass

    # Blender 5.0+: action.fcurves is removed, use layered action API
    if bpy.app.version >= (5, 0, 0):
        # Get fcurves collection from layered action
        fcurves = get_action_fcurves(action)
        if fcurves:
            # Try to find existing fcurve
            for fc in fcurves:
                if fc.data_path == data_path and fc.array_index == index:
                    return fc
            # Create new fcurve if collection supports it
            if hasattr(fcurves, "new"):
                try:
                    return fcurves.new(data_path, index=index)
                except Exception:
                    pass
        return None

    # Fallback to legacy API (Blender < 5.0)
    if hasattr(action, "fcurves"):
        fcurve = action.fcurves.find(data_path, index=index)
        if fcurve is None:
            fcurve = action.fcurves.new(data_path, index=index)
        return fcurve

    return None

def bake_anim(
    frame_start=0,
    frame_end=10,
    only_selected=False,
    bake_bones=False,
    bake_object=False,
    use_current_action=False,
    suffix = cp_suffix,
    step = 1,
    interpolation = 'LINEAR',
    handle_type = 'AUTO_CLAMPED',
    inverse = False,
):
    scn = bpy.context.scene
    obj_data = []
    bones_data = []
    armature = ops.get_ob_or_armature(bpy.context, bpy.context.active_object)
    
    if armature.type != 'ARMATURE':
        return

    def get_bones_matrix():
        matrix = {}
        for pbone in armature.pose.bones:
            if only_selected and not is_pose_bone_selected(pbone):
                continue

            bmat = pbone.matrix.copy()
            
            for child_of_cns in reversed(pbone.constraints):

                if child_of_cns.type not in ['CHILD_OF', 'ARMATURE']:
                    continue
               
                # for CHILD_OF constraint
                elif child_of_cns.type == 'CHILD_OF' and getattr(child_of_cns, "target", None):

                    if suffix in child_of_cns.name:
                        continue

                    if child_of_cns.target.type != 'ARMATURE':
                        continue


                    # Child Of constraints are preserved after baking
                    # need to compensate the matrix with the Child Of transformation
                    
                    if child_of_cns:
                        if child_of_cns.subtarget:
                            if child_of_cns.influence == 1.0 and not child_of_cns.mute:
                                subtarget_bone = child_of_cns.target.pose.bones.get(
                                    child_of_cns.subtarget
                                )
                                if subtarget_bone:

                                    bmat = (
                                        subtarget_bone.matrix_channel.copy().inverted() @ bmat
                                    )
                                    break
                                else:
                                    print(
                                        f"Subtarget bone not found: {child_of_cns.subtarget}"  # noqa: E501
                                    )
                    else:
                        print(f"No Child Of constraint found for {pbone.name}")

                # for ARMATURE constrainst

                elif child_of_cns.type == 'ARMATURE' and getattr(child_of_cns, "targets", None):

                    if child_of_cns.influence != 1 or child_of_cns.mute:
                        continue

                    if suffix in child_of_cns.name:
                        continue

                    subtarget = None

                    for target in child_of_cns.targets:

                        if target.target.type != 'ARMATURE':
                            continue

                        if target and target.subtarget and target.weight == 1:
                            subtarget = target.target.pose.bones.get(target.subtarget)
                            break
                    if subtarget:
                        bmat = (
                                    subtarget.matrix_channel.copy().inverted() @ bmat
                                )
                        break

            matrix[pbone.name] = armature.convert_space(
                pose_bone=pbone, matrix=bmat, from_space="POSE", to_space="LOCAL"
            )

        return matrix

    def get_obj_matrix():
        parent = armature.parent
        matrix = armature.matrix_world.copy()
        if parent:
            return parent.matrix_world.copy().inverted_safe() @ matrix
        else:
            return matrix.copy()

    # store matrices
    current_frame = scn.frame_current
    list_inv = []
    i = 0
    step = int(abs(step))

    if inverse:
        from itertools import chain
        list_inv.extend(chain(reversed(range(int(frame_start), int(frame_end + step)))))
    

    for f in range(int(frame_start), int(frame_end + step), step):
        tmp = f
            
        #inverse
        if inverse:
            try:
                tmp = list_inv[i]
            except:
                tmp = list_inv[-1]

        scn.frame_set(tmp)
        bpy.context.view_layer.update()

        i += step

        if bake_bones:
            bones_data.append((f, get_bones_matrix()))
        if bake_object:
            obj_data.append((f, get_obj_matrix()))

    # set new action (compatible with both legacy and slotted actions)
    if use_current_action and armature.animation_data and armature.animation_data.action:
        action = armature.animation_data.action
    else:
        action = bpy.data.actions.new("Action")
        anim_data = armature.animation_data_create()
        assign_action_to_animdata(anim_data, action, armature)

    def store_keyframe(bn, prop_type, fc_array_index, fra, val):
        fc_data_path = 'pose.bones["' + bn + '"].' + prop_type
        fc_key = (fc_data_path, fc_array_index)
        if not keyframes.get(fc_key):
            keyframes[fc_key] = []
        keyframes[fc_key].extend((fra, val))

    # set transforms and store keyframes
    if bake_bones:
        for pb in armature.pose.bones:
            if only_selected and not is_pose_bone_selected(pb):
                continue
            
            euler_prev = None
            quat_prev = None
            keyframes = {}

            for f, matrix in bones_data:
                pb.matrix_basis = matrix[pb.name].copy()

                for arr_idx, value in enumerate(pb.location):
                    store_keyframe(pb.name, "location", arr_idx, f, value)

                rotation_mode = pb.rotation_mode

                if rotation_mode == "QUATERNION":
                    if quat_prev is not None:
                        quat = pb.rotation_quaternion.copy()
                        quat.make_compatible(quat_prev)
                        pb.rotation_quaternion = quat
                        quat_prev = quat
                        del quat
                    else:
                        quat_prev = pb.rotation_quaternion.copy()

                    for arr_idx, value in enumerate(pb.rotation_quaternion):
                        store_keyframe(
                            pb.name, "rotation_quaternion", arr_idx, f, value
                        )

                elif rotation_mode == "AXIS_ANGLE":
                    for arr_idx, value in enumerate(pb.rotation_axis_angle):
                        store_keyframe(
                            pb.name, "rotation_axis_angle", arr_idx, f, value
                        )

                else:  # euler, XYZ, ZXY etc
                    if euler_prev is not None:
                        euler = pb.rotation_euler.copy()
                        euler.make_compatible(euler_prev)
                        pb.rotation_euler = euler
                        euler_prev = euler
                        del euler
                    else:
                        euler_prev = pb.rotation_euler.copy()

                    for arr_idx, value in enumerate(pb.rotation_euler):
                        store_keyframe(pb.name, "rotation_euler", arr_idx, f, value)

                for arr_idx, value in enumerate(pb.scale):
                    store_keyframe(pb.name, "scale", arr_idx, f, value)

            # Add keyframes (use ensure API so 4.4+ creates slot/layer/strip)
            for fc_key, key_values in keyframes.items():
                data_path, index = fc_key
                fcurve = ensure_fcurve_exists(
                    action, armature, data_path, index=index
                )
                # ensure the fcurve is grouped under the bone name (harmless if already set)  # noqa: E501
                try:
                    if fcurve.group is None or fcurve.group.name != pb.name:
                        slot = armature.animation_data.action_slot
                        channelbag = anim_utils.action_get_channelbag_for_slot(action,slot)
                        if channelbag:
                            grp = channelbag.groups.get(pb.name) or channelbag.groups.new(pb.name)
                            fcurve.group = grp
                except Exception:
                    pass

                num_keys = len(key_values) // 2
                fcurve.keyframe_points.add(num_keys)
                fcurve.keyframe_points.foreach_set("co", key_values)


    if bake_object:
        euler_prev = None
        quat_prev = None

        for f, matrix in obj_data:
            name = "Object Transforms"
            armature.matrix_basis = matrix

            armature.keyframe_insert("location", index=-1, frame=f, group=name)

            rotation_mode = armature.rotation_mode
            if rotation_mode == "QUATERNION":
                if quat_prev is not None:
                    quat = armature.rotation_quaternion.copy()
                    quat.make_compatible(quat_prev)
                    armature.rotation_quaternion = quat
                    quat_prev = quat
                    del quat
                else:
                    quat_prev = armature.rotation_quaternion.copy()
                armature.keyframe_insert(
                    "rotation_quaternion", index=-1, frame=f, group=name
                )
            elif rotation_mode == "AXIS_ANGLE":
                armature.keyframe_insert(
                    "rotation_axis_angle", index=-1, frame=f, group=name
                )
            else:  # euler, XYZ, ZXY etc
                if euler_prev is not None:
                    euler = armature.rotation_euler.copy()
                    euler.make_compatible(euler_prev)
                    armature.rotation_euler = euler
                    euler_prev = euler
                    del euler
                else:
                    euler_prev = armature.rotation_euler.copy()
                armature.keyframe_insert(
                    "rotation_euler", index=-1, frame=f, group=name
                )

            armature.keyframe_insert("scale", index=-1, frame=f, group=name)

    # restore current frame
    scn.frame_set(current_frame)

    #last clean up
    slot = armature.animation_data.action_slot
    channelbag = anim_utils.action_get_channelbag_for_slot(action,slot)
    if channelbag:
        del_fc = []
        for fcurve in channelbag.fcurves:
            if not fcurve.group and not fcurve.keyframe_points:
                del_fc.append(fcurve)
            
            for kf in fcurve.keyframe_points:
                kf.interpolation = interpolation
                if interpolation == 'BEZIER':
                    kf.handle_left_type = handle_type
                    kf.handle_left_type = handle_type

            fcurve.keyframe_points.sort()
            fcurve.keyframe_points.handles_recalc()
            fcurve.keyframe_points.deduplicate()

            fcurve.update()

        for fcurve in reversed(del_fc):
            channelbag.fcurves.remove(fcurve)


    # Blender 4.4+: Ensure the newly created action has its slot assigned
    try:
        if has_slotted_actions() and armature.animation_data:
            anim_data = armature.animation_data
            if hasattr(anim_data, "action_slot") and anim_data.action_slot is None:
                suitable = getattr(anim_data, "action_suitable_slots", None)
                if suitable and len(suitable) > 0:
                    anim_data.action_slot = suitable[0]
    except Exception:
        pass
