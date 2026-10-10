
import bpy
import uuid

from bpy.types import Operator
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty
from bpy_extras import anim_utils
from bpy.app.handlers import persistent
from mathutils import Matrix
from bpy_extras.io_utils import ImportHelper

from pathlib import Path
import os

filter_name = ""
use_filter_invert = False
use_filter_sort_reverse = False

def action_armature(action: bpy.types.Action):

    if not action:
        return False

    valid = False

    for slot in action.slots:

        if valid:
            break

        channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)

        if channelbag:

            for fc in channelbag.fcurves:
                data_path = fc.data_path
            
                if not "pose.bones" in data_path:
                    continue

                valid = True
                break
        
    return valid

def slot_armature(action: bpy.types.Action, slot):

    if not action:
        return False
    
    valid = False

    channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)

    if channelbag:

        for fc in channelbag.fcurves:
            data_path = fc.data_path
        
            if not "pose.bones" in data_path:
                continue

            valid = True
            break
        
    return valid

def validate_actions(action: bpy.types.Action, path_resolve: callable, armature = False):

    if not action:
        return False
    
    valid = False
    for slot in action.slots:

        if valid:
            break

        channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)

        if channelbag:
            for fc in channelbag.fcurves:
                data_path = fc.data_path
                
                if armature and not "pose.bones" in data_path:
                    continue
                try:
                    path_resolve(data_path)
                    valid = True
                    break
                except ValueError:
                    continue  # Invalid.
        
    return valid

def validate_slot(action, slot, path_resolve: callable, armature = False):

    if not action:
        return False
    
    valid = False

    channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)

    for fc in channelbag.fcurves:
        data_path = fc.data_path

        if armature and not "pose.bones" in data_path:
            continue
        try:
            path_resolve(data_path)
            valid = True
            break
        except ValueError:
            continue  # Invalid.
        
    return valid

def correct_library_action(scene, action_list):
    global filter_name
    global use_filter_invert

    if scene.retarget_action.library_mode:

        if not ((filter_name.lower() in action_list.name.lower() and not use_filter_invert)
            or (filter_name.lower() not in action_list.name.lower() and use_filter_invert)):
            return False
    
        if scene.retarget_action.filt_with_tag:
            if not action_list.tag:
                return False
            
        if scene.retarget_action.filt_not_tag:
            if action_list.tag:
                return False
            
        if scene.retarget_action.filt_hidden:
            if action_list.is_hidden:
                return False
        
        if scene.retarget_action.filt_no_hidden:
            if not action_list.is_hidden:
                return False
        
        #filter folder name
        if scene.retarget_action.filt_folder:
            if not scene.retarget_action.filt_folder_name.lower() in action_list.folder.lower():
                return False
        
        if scene.retarget_action.filt_file:
            if not scene.retarget_action.filt_file_name.lower() in action_list.file.lower():
                return False
            
        if scene.retarget_action.filt_selected:
            if not action_list.is_selected:
                return False
        
        if scene.retarget_action.filt_not_selected:
            if action_list.is_selected:
                return False
        
        #tag
        if scene.retarget_action.filt_tag:
            if any((scene.retarget_action.filt_tag_prefix,scene.retarget_action.filt_tag_contain,scene.retarget_action.filt_tag_suffix)):
                name = scene.retarget_action.filt_tag_name if scene.retarget_action.filt_tag_search_option else scene.retarget_action.filt_tag_name_
                if name:
                    #valid
                    valid = True
                    tags = name.lower().split(",")
                    action_tag = action_list.tag.lower()
                    #find it
                    for tag in tags:

                        if not tag:
                            continue
                        
                        if not scene.retarget_action.filt_tag_invert:
                            valid = True

                        if not scene.retarget_action.filt_tag_invert:

                            if scene.retarget_action.filt_tag_prefix and not action_tag.startswith(tag):
                                valid = False
                            
                            if scene.retarget_action.filt_tag_contain and not tag in action_tag:
                                valid = False

                            if scene.retarget_action.filt_tag_suffix and not action_tag.endswith(tag):
                                valid = False
                        
                        else:

                            if scene.retarget_action.filt_tag_prefix and action_tag.startswith(tag):
                                valid = False
                            
                            if scene.retarget_action.filt_tag_contain and tag in action_tag:
                                valid = False

                            if scene.retarget_action.filt_tag_suffix and action_tag.endswith(tag):
                                valid = False

                        if not scene.retarget_action.filt_tag_invert and valid:
                            break

                    if not valid:
                        return False
    return True

def number_of_action(context):
    scene = context.scene
    list_actions = []
    if not scene.retarget_action.library_mode:
        list_actions = context.scene.retarget_action_list
    else:
        list_actions =  scene.retarget_action_library

    num = len(list_actions)
    return num

def number_selected(context):
    global filter_name
    global use_filter_invert

    scene = context.scene
    list_actions = []
    if not scene.retarget_action.library_mode:
        list_actions = context.scene.retarget_action_list
    else:
        list_actions =  scene.retarget_action_library

    num = 0
    for action_list in list_actions:

        if not correct_library_action(scene,action_list):
            continue    

        if action_list.is_selected and ((filter_name.lower() in action_list.name.lower() and not use_filter_invert)
            or (filter_name.lower() not in action_list.name.lower() and use_filter_invert)):
            num += 1
    return num
           


def get_only_selected_action_list(context):
    global filter_name
    global use_filter_invert

    actions = []
    scene = context.scene

    list_actions = scene.retarget_action_list

    for action_list in list_actions:
        
        if action_list.is_selected and ((filter_name.lower() in action_list.name.lower() and not use_filter_invert)
            or (filter_name.lower() not in action_list.name.lower() and use_filter_invert)):
            actions.append(action_list)

    return actions

def get_selected_action_list(context):
    global filter_name
    global use_filter_invert

    actions = []
    scene = context.scene

    list_actions = []
    if not scene.retarget_action.library_mode:
        list_actions = scene.retarget_action_list
    else:
        list_actions =  scene.retarget_action_library

    for action_list in list_actions:
        if not correct_library_action(scene,action_list):
            continue
        if action_list.is_selected and ((filter_name.lower() in action_list.name.lower() and not use_filter_invert)
            or (filter_name.lower() not in action_list.name.lower() and use_filter_invert)):
            actions.append(action_list)

    return actions

def get_view_action_list(context):
    global filter_name
    global use_filter_invert

    actions = []
    scene = context.scene
    list_actions = []
    if not scene.retarget_action.library_mode:
        list_actions = context.scene.retarget_action_list
    else:
        list_actions =  scene.retarget_action_library
           
    for action_list in list_actions:
        if not correct_library_action(scene,action_list):
            continue
        if ((filter_name.lower() in action_list.name.lower() and not use_filter_invert)
            or (filter_name.lower() not in action_list.name.lower() and use_filter_invert)):
            actions.append(action_list)

    return actions

def get_list_context(context):
    scene = context.scene
    list_actions = []
    if not scene.retarget_action.library_mode:
        list_actions = scene.retarget_action_list
    else:
        list_actions =  scene.retarget_action_library

    return list_actions

#diseable it beacuse the search option is forcefull
def get_all_tag(self, context, edit_text):
    tags = []
    scene = context.scene

    if not scene.retarget_action.library_mode:
        for action in bpy.data.actions:
            if action and action.retarget_act.tag:
                if action.retarget_act.tag and not (action.retarget_act.tag,action.retarget_act.tag) in tags:
                    tags.append((action.retarget_act.tag,action.retarget_act.tag))
    else:
        for item in scene.retarget_action_library:
            if item and item.tag and item.tag:
                if item.tag and not (item.tag,item.tag) in tags:
                    tags.append((item.tag, item.tag))
    return tags

last_selected_objects = []

@persistent
def handle_object_selection_change(scene):
    global last_selected_objects
    
    current_selected_objects = get_selected_obs(bpy.context)
    
    # Check if the current selection is different from the last selection
    if current_selected_objects != last_selected_objects:
        # Unlink
        if scene.retarget_action.auto_switch and scene.retarget_action.unlink:
            for ob in last_selected_objects:
                try:

                    if ob and hasattr(ob, 'animation_data') and ob.animation_data and ob.animation_data.action:
                        ob.animation_data.action = None
                except:
                    pass

        object_changed()
        
        # Update the last selection state
        last_selected_objects = current_selected_objects

def object_changed():
    context = bpy.context
    scene = bpy.context.scene
    if context.active_object is not None:
        if scene.retarget_action.auto_switch:
           update_action_list(context)

def get_ob_or_armature(context, ob):
    if context.scene.retarget_action.armature_mode:
            #find armature
            if ob and ob.type != 'ARMATURE':
                if hasattr(ob, 'modifiers'):
                    for mod in ob.modifiers:
                        if mod.type == 'ARMATURE' and mod.object and not mod.object.hide_get(view_layer=context.view_layer):
                            ob = mod.object
            if ob and ob.type != 'ARMATURE':
                find_arm = ob
                while find_arm.parent:
                    find_arm = find_arm.parent
                    if find_arm.type == 'ARMATURE':
                        break
                if find_arm and find_arm.type == 'ARMATURE' and not find_arm.hide_get(view_layer=context.view_layer):
                    ob = find_arm
    return ob

def get_selected_obs(context):
    obs = list(context.selected_objects)

    #sometime the active object is not selected

    active_ob = context.active_object
    if active_ob and not active_ob in obs:
        obs.append(active_ob)

    valid_obs = []
    if context.scene.retarget_action.armature_mode:
        #find armature
        for ob in obs:
            tmp = get_ob_or_armature(context, ob)
            if not tmp in valid_obs:
                valid_obs.append(tmp)
    else:
        valid_obs = obs
        
    return valid_obs

def is_action_in_ob_list(ob, action):

    if ob.retarget_object_list:
        for ob_action in ob.retarget_object_list:
            if ob_action.action_ptr == action:
                return True
    return False

def is_action_in_library_list(name, folder, file, context):
    scene = context.scene
    if scene.retarget_action_library:
        for item in scene.retarget_action_library:
            if item.name == name and item.folder == folder and item.file == file:
                return True
    return False

#library Action
def action_external(context):
    action_ext = dict()
    prefs = context.preferences
    filepaths = prefs.filepaths
    asset_libraries = filepaths.asset_libraries

    for asset_library in asset_libraries:
        library_name = asset_library.name
        library_path = Path(asset_library.path)
        #print(f"\n--- Checking Library: '{library_name}' ---")

        # Find all .blend files within the library path
        directory = bpy.data.filepath
        blend_files = [fp for fp in library_path.glob("**/*.blend") if fp.is_file() and str(fp) != directory]

        for blend_file in blend_files:
            #print(f"  Checking file: {blend_file.name}")
            # Temporarily load the contents of the blend file, filtering for assets only
            with bpy.data.libraries.load(str(blend_file), assets_only=True) as (file_contents, _):
                # The file_contents object contains lists of names for different asset types
                #print(f"    Object Assets found: {file_contents.objects}")
                #print(f"    Material Assets found: {file_contents.materials}")
                #print(f"    Collection Assets found: {file_contents.collections}")
                if file_contents.actions:
                    #print(f"  In file: {blend_file.name}")
                    for action_name in file_contents.actions:
                        action_ext[action_name] = (str(blend_file), blend_file.name)

    return action_ext


def append_action(filepath, action_names, link_action=False):
    """
    Appends a specific action by name from an external .blend file.

    :param filepath: The full path to the source .blend file.
    :param action_name: The name of the action data-block to append.
    """
    
    # Define the path to the "Action" data-block directory within the .blend file

    directory = bpy.data.filepath
    if filepath == directory:
        return
    
    # Use bpy.data.libraries.load to access the data in the source file
    # The 'link=False' argument ensures the data is appended (copied) not linked
    try:
        with bpy.data.libraries.load(filepath, link=link_action) as (data_from, data_to):
            # Specify the name of the action to be appended
            actions = []
            for action_name in action_names:

                if action_name in data_from.actions:
                    actions.append(action_name)
            if actions:
                data_to.actions = actions
              
    except:
        pass

#-------
#$update object list
def update_ob_list(ob):
    if ob.retarget_object_list:
        to_del = []
        for ob_action in ob.retarget_object_list:
            if not ob_action.action_ptr:
                to_del.append(ob_action)
        if to_del:
            for ob_action in reversed(to_del):
                for i, ob_act in enumerate(ob.retarget_object_list):
                    if ob_act == ob_action:
                        ob.retarget_object_list.remove(i)
                        break


def update_action_list(context):

    scene = context.scene

    global filter_name
    global use_filter_invert

    filter_name = ""
    use_filter_invert = False
    
    #clean list
    if scene.retarget_action_list:
        scene.retarget_action_list.clear()

    ob = context.active_object
    #compatible mode
    if scene.retarget_action.only_compatible:
        if not ob:
            return
        
    #armature mode
    if ob:
        ob = get_ob_or_armature(context, ob)
        #update ob list
        update_ob_list(ob)
        
    for act in bpy.data.actions:

        #only compatible
        if scene.retarget_action.only_compatible:
            if not validate_actions(act, ob.path_resolve, armature= bool(ob.type == 'ARMATURE')):
                continue

        #object mode
        if scene.retarget_action.object_mode:
            if not ob:
                return
            if not ob.retarget_object_list:
                return
            find = False
            for item_ob in ob.retarget_object_list:
                if act == item_ob.action_ptr:
                    find = True
                    break
                
            if not find:
                continue
                
        
        #filter tag
        if scene.retarget_action.filt_tag:
            if any((scene.retarget_action.filt_tag_prefix,scene.retarget_action.filt_tag_contain,scene.retarget_action.filt_tag_suffix)):
                name = scene.retarget_action.filt_tag_name if scene.retarget_action.filt_tag_search_option else scene.retarget_action.filt_tag_name_
                if name:
                    #valid
                    valid = True
                    tags = name.lower().split(",")
                    action_tag = act.retarget_act.tag.lower()
                    #find it
                    for tag in tags:

                        if not tag:
                            continue
                        
                        if not scene.retarget_action.filt_tag_invert:
                            valid = True

                        if not scene.retarget_action.filt_tag_invert:

                            if scene.retarget_action.filt_tag_prefix and not action_tag.startswith(tag):
                                valid = False
                            
                            if scene.retarget_action.filt_tag_contain and not tag in action_tag:
                                valid = False

                            if scene.retarget_action.filt_tag_suffix and not action_tag.endswith(tag):
                                valid = False
                        
                        else:

                            if scene.retarget_action.filt_tag_prefix and action_tag.startswith(tag):
                                valid = False
                            
                            if scene.retarget_action.filt_tag_contain and tag in action_tag:
                                valid = False

                            if scene.retarget_action.filt_tag_suffix and action_tag.endswith(tag):
                                valid = False

                        if not scene.retarget_action.filt_tag_invert and valid:
                            break

                    if not valid:
                        continue

        #filter
        if scene.retarget_action.filt_with_tag:
            if not act.retarget_act.tag:
                continue
            
        if scene.retarget_action.filt_not_tag:
            if act.retarget_act.tag:
                continue
            
        if scene.retarget_action.filt_hidden:
            if act.retarget_act.is_hidden:
                continue

        if scene.retarget_action.filt_no_hidden:
            if not act.retarget_act.is_hidden:
                continue

        if scene.retarget_action.filt_armature:
            if not action_armature(act):
                continue

        if scene.retarget_action.filt_not_armature:
            if action_armature(act):
                continue

        if scene.retarget_action.filt_fake_user:
            if not act.use_fake_user:
                continue
        
        if scene.retarget_action.filt_not_fake_user:
            if act.use_fake_user:
                continue
        
        if scene.retarget_action.filt_library:
            if act.asset_data is None:
                continue
        
        if scene.retarget_action.filt_not_library:
            if act.asset_data is not None:
                continue
        
        if scene.retarget_action.filt_selected:
            if not act.retarget_act.is_selected:
                continue
        
        if scene.retarget_action.filt_not_selected:
            if act.retarget_act.is_selected:
                continue
        #---------

        item = scene.retarget_action_list.add()
        item.name = act.name
        item.asset_mark = act.asset_data is not None
        item.tag = act.retarget_act.tag

        fr_start, fr_end = act.frame_range
        frame = int(abs(fr_end - fr_start))
        if fr_start != 0 or fr_end != 0:
            frame += 1
        item.frame = frame

        item.is_hidden = act.retarget_act.is_hidden
        item.is_selected = act.retarget_act.is_selected

        item.action_ptr = act

# Mode list
class ACTION_OT_refresh_list(Operator):
    """Show All Actions"""
    bl_idname = "object.retarget_action_refresh_list"
    bl_label = "All Actions"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.retarget_action.only_compatible = False
        context.scene.retarget_action.object_mode = False

        return {'FINISHED'}
    

#library
class ACTION_OT_refresh_by_selected_library(Operator):
    """Add Selected Action In The Library"""
    bl_idname = "object.retarget_action_by_selected_library_path"
    bl_label = "Add Selected Action"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        action_ext = dict()

        asset_browser_area = next((a for a in context.screen.areas if a.ui_type == 'ASSETS'), None)

        if asset_browser_area:

            # 2. Use a temporary context override to access 'selected_assets' from that area
            with bpy.context.temp_override(area=asset_browser_area):

                if bpy.context.selected_assets:

                    for asset in bpy.context.selected_assets:

                        if asset.id_type != "ACTION":
                            continue
                        
                        #full_library_path=="" mean that the asset is in the current file
                        if not asset.full_library_path:
                            continue

                        name = os.path.basename(asset.full_library_path)

                        val = [asset.full_library_path, name]
                        
                        # 3. Access tags through the asset's metadata
                        if asset.metadata.tags:
                            val.append(asset.metadata.tags[0].name)

                        action_ext[asset.name] = val

        else:
            self.report({'WARNING'}, "Please open an Asset Browser editor first And Select Actions")
            return {'FINISHED'}

        scene = context.scene

        added = 0

        for action_name, directory in action_ext.items():

            if is_action_in_library_list(action_name, directory[0], directory[1], context):
                continue

            added += 1
            item = scene.retarget_action_library.add()
            item.name = action_name
            item.folder = directory[0]
            item.file = directory[1]
            
            if len(directory) > 2:
                item.tag = directory[2]

        self.report({'INFO'}, f" [{added}] Action(s) found")
        
        return {'FINISHED'}

class ACTION_OT_refresh_library_path(Operator):
    """Add Action by Library"""
    bl_idname = "object.retarget_action_refresh_library_path"
    bl_label = "Scan by Library"
    bl_options = {'REGISTER', 'UNDO'}

    folder: StringProperty(name="Library",default="")

    def draw(self, context):
        layout = self.layout
        column = layout.column()
        
        prefs = context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries

        row = column.row()
        row.label(text = 'Select The Library')

        row = column.row()
        row.prop_search(self, 'folder',
                            filepaths,
                            "asset_libraries")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        if not self.folder:
            return {'FINISHED'}
        
        action_ext = dict()
        prefs = context.preferences
        filepaths = prefs.filepaths
        asset_libraries = filepaths.asset_libraries

        asset_library = None

        for asset in asset_libraries:
            if asset.name == self.folder:
                asset_library = asset

        if not asset_library:
            return {'FINISHED'}
        library_name = asset_library.name
        library_path = Path(asset_library.path)
        print(f"\n--- Checking Library: '{library_name}' ---")

        # Find all .blend files within the library path
        directory = bpy.data.filepath
        blend_files = [fp for fp in library_path.glob("**/*.blend") if fp.is_file() and str(fp) != directory]

        for blend_file in blend_files:
            print(f"  Checking file: {blend_file.name}")
            # Temporarily load the contents of the blend file, filtering for assets only
            with bpy.data.libraries.load(str(blend_file), assets_only=True) as (file_contents, _):
                # The file_contents object contains lists of names for different asset types
                #print(f"    Object Assets found: {file_contents.objects}")
                #print(f"    Material Assets found: {file_contents.materials}")
                #print(f"    Collection Assets found: {file_contents.collections}")
                if file_contents.actions:
                    #print(f"  In file: {blend_file.name}")
                    for action_name in file_contents.actions:
                        action_ext[action_name] = (str(blend_file), blend_file.name)

        scene = context.scene
        added = 0

        for action_name, directory in action_ext.items():

            if is_action_in_library_list(action_name, directory[0], directory[1], context):
                continue
            added += 1

            item = scene.retarget_action_library.add()
            item.name = action_name
            item.folder = directory[0]
            item.file = directory[1]

        self.report({'INFO'}, f" [{added}] Action(s) found")

        return {'FINISHED'}
    

class ACTION_OT_refresh_library(Operator):
    """Scan The Whole Library (Find Action In The Whole Asset Library)"""
    bl_idname = "object.retarget_action_refresh_library"
    bl_label = "Scan The Whole Library"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        column = layout.column()
        row = column.row()
        row.label(text = 'Are You Sure (It will Take some Time) ?')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        scene = context.scene
        if scene.retarget_action_library:
            scene.retarget_action_library.clear()
        action_ext = action_external(context)
        for action_name, directory in action_ext.items():
            item = scene.retarget_action_library.add()
            item.name = action_name
            item.folder = directory[0]
            item.file = directory[1]

        self.report({'INFO'}, f" [{len(action_ext)}] Action(s) found")
        
        return {'FINISHED'}
    
#list manager
class ACTION_OT_add_to_object(Operator):
    """Add Selected Action In Object(s) List"""
    bl_idname = "object.retarget_action_add_to_object"
    bl_label = "Add Selected Action(s) To Object(s) List"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

    def execute(self, context):
        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        active_ob = get_ob_or_armature(context,context.active_object)
        action_list = get_selected_action_list(context)
        for ob in get_selected_obs(context):

            #don't add in active object in object mode
            if context.scene.retarget_action.object_mode and active_ob == ob:
                continue

            for item in action_list:
                if is_action_in_ob_list(ob, item.action_ptr):
                    self.report({'INFO'}, f"action [{item.action_ptr.name}] is already in [{ob.name}] action list")
                    continue
                action = ob.retarget_object_list.add()
                action.action_ptr = item.action_ptr
        return {'FINISHED'}
    
class ACTION_OT_clean_selected(Operator):
    """Remove Selected Action(s) On the List (It will not delete the action)"""
    bl_idname = "object.clean_selected_action"
    bl_label = "Clean Selected Action(s)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

    def execute(self, context):
        
        scene = context.scene
        action_list = get_selected_action_list(context)
        items = get_list_context(context)

        #clean object list
        if scene.retarget_action.object_mode and not scene.retarget_action.library_mode:
            for ob in get_selected_obs(context): 
                if ob.retarget_object_list:
                    for item in action_list:
                        for i, item_ob in enumerate(ob.retarget_object_list):
                            if item.action_ptr == item_ob.action_ptr:
                                ob.retarget_object_list.remove(i)
                                break

        for item in reversed(action_list):
            
            for i, it in enumerate(items):
                if item == it:
                    items.remove(i)
                    break
        
        update_action_list(context)
        return {'FINISHED'}
    
class ACTION_OT_refresh_list_clean(Operator):
    """Clean The Whole Action List Of Selected Object (It will not delete Action)"""
    bl_idname = "object.retarget_action_refresh_clean_list"
    bl_label = "Clean The Whole List"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_selected_obs(context)) > 0

    def execute(self, context):
        scene = context.scene
        #clean object
        if scene.retarget_action.object_mode and not scene.retarget_action.library_mode:
            for ob in get_selected_obs(context): 
                if ob.retarget_object_list:
                    ob.retarget_object_list.clear()

        if not scene.retarget_action.library_mode:
            if context.scene.retarget_action_list:
                context.scene.retarget_action_list.clear()
        else:
            if scene.retarget_action_library:
                scene.retarget_action_library.clear()
        return {'FINISHED'}
    
class ACTION_OT_SelectUp(Operator):
    bl_idname = "object.retarget_action_select_up"
    bl_label = "Select Up"

    def execute(self, context):
        global use_filter_sort_reverse

        scene = context.scene
        items = get_view_action_list(context)
        items_a = scene.retarget_action_list
        
        current_index = scene.retarget_action.action_index

        try:
            if use_filter_sort_reverse:
                
                if current_index < len(items_a):
                    for i in range(current_index + 1, len(items_a)):
                        if i < len(items_a) and items_a[i] in items:
                            scene.retarget_action.action_index = i
                            return {'FINISHED'}
                    
                    scene.retarget_action.action_index = 0

                else:
                    scene.retarget_action.action_index = 0 # Wrap around to top if at bottom
                    
            else:
                if current_index > 0:
                    for i in range(current_index - 1, -1, -1):
                        if i > -1 and items_a[i] in items:
                            scene.retarget_action.action_index = i
                            return {'FINISHED'}
                    #scene.retarget_action.action_index = current_index - 1
                    scene.retarget_action.action_index = len(items_a) - 1
                else:
                    scene.retarget_action.action_index = len(items_a) - 1 # Wrap around to bottom if at top
        except:
            pass

        return {'FINISHED'}

class ACTION_OT_SelectDown(Operator):
    bl_idname = "object.retarget_action_select_down"
    bl_label = "Select Down"

    def execute(self, context):
        global use_filter_sort_reverse

        scene = context.scene
        items = get_view_action_list(context)
        items_a = scene.retarget_action_list

        current_index = scene.retarget_action.action_index

        try:

            if use_filter_sort_reverse:

                if current_index > 0:
                    for i in range(current_index - 1, -1, -1):
                        if i > -1 and items_a[i] in items:
                            scene.retarget_action.action_index = i
                            return {'FINISHED'}
                    #scene.retarget_action.action_index = current_index - 1
                    scene.retarget_action.action_index = len(items_a) - 1
                else:
                    scene.retarget_action.action_index = len(items_a) - 1
            else:
                if current_index < len(items_a):
                    for i in range(current_index + 1, len(items_a)):
                        if i < len(items_a) and items_a[i] in items:
                            scene.retarget_action.action_index = i
                            return {'FINISHED'}
                    
                    scene.retarget_action.action_index = 0

                else:
                    scene.retarget_action.action_index = 0 # Wrap around to top if at bottom
        except:
            pass

        return {'FINISHED'}
    
# ------------------------

#select--------------

class ACTION_OT_select_name(Operator):
    """Select by Name"""
    bl_idname = "object.retarget_action_select_by_name"
    bl_label = "Select By Name"
    bl_options = {'REGISTER', 'UNDO'}

    invert: BoolProperty(name="Invert",default=False)
    name: StringProperty(name="Name",
                          description= "Enter the Name (comma is the separator)",
                          default="")
    prefix: BoolProperty(name="Prefix",default=False)
    contain: BoolProperty(name="Contain",default=True)
    suffix: BoolProperty(name="Suffix",default=False)

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "prefix", toggle=True)
        row.prop(self, "contain", toggle=True)
        row.prop(self, "suffix", toggle=True)
        row = column.row()
        row.prop(self, "name")
        row.prop(self, "invert", text="",icon='ARROW_LEFTRIGHT')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        action_list = get_view_action_list(context)
       
        for item in action_list:
            if any((self.prefix,self.contain,self.suffix)):
                #valid
                valid = True
                tags = self.name.lower().split(",")
                action_tag = item.name.lower()
                #find it
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

                        if self.suffix and not action_tag.endswith(tag):
                            valid = False
                    
                    else:

                        if self.prefix and action_tag.startswith(tag):
                            valid = False
                        
                        if self.contain and tag in action_tag:
                            valid = False

                        if self.suffix and action_tag.endswith(tag):
                            valid = False

                    if not self.invert and valid:
                        break
                if valid:
                    item.is_selected = True
            
        return {'FINISHED'}

class ACTION_OT_select_tag(Operator):
    """Select by Tag"""
    bl_idname = "object.retarget_action_select_by_tag"
    bl_label = "Select By Tag"
    bl_options = {'REGISTER', 'UNDO'}

    invert: BoolProperty(name="Invert",default=False)

    search_option: BoolProperty(name="Suggestion",default=True)
    name: StringProperty(name="Tag",default="", 
                         description= "Enter the tag Name (comma is the separator)",
                         search=get_all_tag)
    name_: StringProperty(name="Tag",
                          description= "Enter the tag Name (comma is the separator)",
                          default="")

    prefix: BoolProperty(name="Prefix",default=False)
    contain: BoolProperty(name="Contain",default=True)
    suffix: BoolProperty(name="Suffix",default=False)

    show: BoolProperty(name="Show All Tag", default=False)
    number: IntProperty(name="Number by line", default=3, min=1)

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "prefix", toggle=True)
        row.prop(self, "contain", toggle=True)
        row.prop(self, "suffix", toggle=True)

        row = column.row()
        row.prop(self, "search_option", text="", icon="SYNTAX_ON")
        if self.search_option:
            row.prop(self, "name")
        else:
            row.prop(self, "name_")

        row.prop(self, "invert", text="",icon='ARROW_LEFTRIGHT')
        row = column.row()
        row.prop(self, "show", toggle=True)
        if self.show:
            row.prop(self, "number")
            tags = []
            scene = context.scene

            if not scene.retarget_action.library_mode:
                # use bpy.data.actions because i want to acces to all the tag
                for action in bpy.data.actions:
                    if action and action.retarget_act.tag and action.retarget_act.tag not in tags:
                        tags.append(action.retarget_act.tag)
            else:
                for item in scene.retarget_action_library:
                    if item and item.tag and item.tag not in tags:
                        tags.append(item.tag)
                
            if tags:
                i = 0
                row = column.split(factor= 1 / self.number, align=True)
                for tag in tags:
                    if i == self.number:
                        row = column.split(factor= 1 / self.number, align=True)
                        i = 0
                    
                    row.label(text=tag, icon='TAG', translate=False)
                    i += 1

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        action_list = get_view_action_list(context)
        name = self.name if self.search_option else self.name_

        for item in action_list:
            if any((self.prefix,self.contain,self.suffix)):
                #valid
                valid = True
                tags = name.lower().split(",")
                
                action_tag = item.tag.lower()
                #find it
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

                        if self.suffix and not action_tag.endswith(tag):
                            valid = False
                    
                    else:

                        if self.prefix and action_tag.startswith(tag):
                            valid = False
                        
                        if self.contain and tag in action_tag:
                            valid = False

                        if self.suffix and action_tag.endswith(tag):
                            valid = False

                    if not self.invert and valid:
                        break
                if valid:
                    item.is_selected = True
                
        return {'FINISHED'}
    
class ACTION_OT_select_no_tag(Operator):
    bl_idname = "object.retarget_action_select_no_tag"
    bl_label = "Select Action(s) with No Tag"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def execute(self, context):
        action_list = get_view_action_list(context)
        scene = context.scene
        for item in action_list:
            if not item.tag:
                item.is_selected = True
        return {'FINISHED'}

class ACTION_OT_select_time(Operator):
    """Select by Frame"""
    bl_idname = "object.retarget_action_select_by_time"
    bl_label = "Select By Frame"
    bl_options = {'REGISTER', 'UNDO'}


    greater: BoolProperty(name="Greater Than",default=False)
    greater_value: IntProperty(name="Value",default=0)
    smaller: BoolProperty(name="Smaller Than",default=False)
    smaller_value: IntProperty(name="Value",default=0)
    egal: BoolProperty(name="Equal",default=True)
    egal_value: IntProperty(name="Value",default=0)

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "smaller", toggle=True)
        row.prop(self, "egal", toggle=True)
        row.prop(self, "greater", toggle=True)
        row = column.row()
        row.prop(self, "smaller_value")
        row.prop(self, "egal_value")
        row.prop(self, "greater_value")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        action_list = get_view_action_list(context)

        for item in action_list:
            valid = False
            if self.egal and item.frame == self.egal_value:
                valid = True
            if self.smaller and item.frame < self.smaller_value:
                valid = True
            if self.greater and item.frame > self.greater_value:
                valid = True

            if valid:
                item.is_selected = True
        return {'FINISHED'}

class ACTION_OT_select_hidden_on(Operator):
    bl_idname = "object.retarget_action_select_hidden_on"
    bl_label = "Select Action(s) with Hidden On"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def execute(self, context):
        action_list = get_view_action_list(context)
        scene = context.scene
        for item in action_list:
            if item.is_hidden:
                item.is_selected = True
        return {'FINISHED'}
    
class ACTION_OT_select_hidden_off(Operator):
    bl_idname = "object.retarget_action_select_hidden_off"
    bl_label = "Select Action(s) with Hidden Off"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def execute(self, context):
        action_list = get_view_action_list(context)
        scene = context.scene
        for item in action_list:
            if not item.is_hidden:
                item.is_selected = True
        return {'FINISHED'}
    
class ACTION_OT_select_fake_user(Operator):
    bl_idname = "object.retarget_action_select_fake_user"
    bl_label = "Select Action(s) with Fake User"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def execute(self, context):
        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        action_list = get_view_action_list(context)
        for item in action_list:
            if item.action_ptr and item.action_ptr.use_fake_user:
                item.is_selected = True
        return {'FINISHED'}
    
class ACTION_OT_select_fake_user_off(Operator):
    bl_idname = "object.retarget_action_select_fake_user_off"
    bl_label = "Select Action(s) with Fake User Off"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def execute(self, context):
        action_list = get_view_action_list(context)
        for item in action_list:
            if item.action_ptr and not item.action_ptr.use_fake_user:
                item.is_selected = True
        return {'FINISHED'}
    
class ACTION_OT_select_armature_action(Operator):
    bl_idname = "object.retarget_action_select_armature_action"
    bl_label = "Select Armature Action(s)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def execute(self, context):
        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        action_list = get_view_action_list(context)
        for item in action_list:
            if action_armature(item.action_ptr):
                item.is_selected = True
        return {'FINISHED'}
    
class ACTION_OT_select_no_armature_action(Operator):
    bl_idname = "object.retarget_action_select_no_armature_action"
    bl_label = "Select No Armature Action(s)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def execute(self, context):
        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        action_list = get_view_action_list(context)
        for item in action_list:
            if not action_armature(item.action_ptr):
                item.is_selected = True
        return {'FINISHED'}
    
class ACTION_OT_select_compatible(Operator):
    bl_idname = "object.retarget_action_select_compatible"
    bl_label = "Select Compatible Action(s)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def execute(self, context):
        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        obs = get_selected_obs(context)
        action_list = get_view_action_list(context)
        for item in action_list:
            for ob in obs:
                if validate_actions(item.action_ptr, ob.path_resolve, armature= bool(ob.type == 'ARMATURE')):
                    item.is_selected = True
        return {'FINISHED'}
    
class ACTION_OT_select_ob_action(Operator):
    bl_idname = "object.retarget_action_select_action_ob"
    bl_label = "Select Action(s) in Object(s) List"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def execute(self, context):
        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        obs = get_selected_obs(context)
        action_list = get_view_action_list(context)
        for item in action_list:
            for ob in obs:
                if is_action_in_ob_list(ob, item.action_ptr):
                    item.is_selected = True
        return {'FINISHED'}

#time consuming on big scene
# class ACTION_OT_select_no_compatible(Operator):
#     """Select No Compatible Action (Useless Actions)"""
#     bl_idname = "object.retarget_action_no_compatible"
#     bl_label = "Select Useless Actions"
#     bl_options = {'REGISTER', 'UNDO'}

#     def execute(self, context):
#          if context.scene.retarget_action.library_mode:
#            return {'FINISHED'}
#         obs = bpy.data.objects
#         action_list = get_view_action_list(context)
#         for item in action_list:
#             select = True
#             for ob in obs:
#                 if validate_actions(item.action_ptr, ob.path_resolve, armature= bool(ob.type == 'ARMATURE')):
#                     select = False
#                     break

#             if not select:
#                 continue

#             item.is_selected = True


#         return {'FINISHED'}

class ACTION_OT_inverse_selection(Operator):
    bl_idname = "object.retarget_action_inverse_selection"
    bl_label = "Inverse Selection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def execute(self, context):
        action_list = get_view_action_list(context)
        for item in action_list:
            item.is_selected = not item.is_selected
        return {'FINISHED'}

class ACTION_OT_deselect_all_action(Operator):
    bl_idname = "object.retarget_action_deselect_all_action"
    bl_label = "Deselect All Actions"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def execute(self, context):
        action_list = get_view_action_list(context)
        for item in action_list:
            item.is_selected = False
        return {'FINISHED'}

class ACTION_OT_select_all_action(Operator):
    bl_idname = "object.retarget_action_select_all_action"
    bl_label = "Select All Actions"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_view_action_list(context)) > 0

    def execute(self, context):
        action_list = get_view_action_list(context)
        for item in action_list:
            item.is_selected = True
        return {'FINISHED'}
    
#--------------------

#library
    
class ACTION_OT_link_action(Operator):
    """Link Selected Action"""
    bl_idname = "object.retarget_action_link_action"
    bl_label = "Link Action(s)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

    def execute(self, context):
        if not context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        action_list = get_selected_action_list(context)

        folders = []
        folders_files = dict()

        for item in action_list:
            if not item.folder in folders:
                folders.append(item.folder)

        for folder in folders:
            files = []
            for item in action_list:
                if item.folder == folder:
                    files.append(item.name) 

            folders_files[folder] = files

        for folder, f in folders_files.items():
            append_action(folder, f, link_action=True)

        self.report({'INFO'}, f" [{len(action_list)}] Action(s) linked")

        return {'FINISHED'}

class ACTION_OT_append_action(Operator):
    """Append Selected Action"""
    bl_idname = "object.retarget_action_append_action"
    bl_label = "Append Action(s)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

    def execute(self, context):
        if not context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        action_list = get_selected_action_list(context)

        folders = []
        folders_files = dict()

        for item in action_list:
            if not item.folder in folders:
                folders.append(item.folder)

        for folder in folders:
            files = []
            for item in action_list:
                if item.folder == folder:
                    files.append(item.name) 

            folders_files[folder] = files

        for folder, f in folders_files.items():
            append_action(folder, f)

        self.report({'INFO'}, f" [{len(action_list)}] Action(s) added")

        return {'FINISHED'}
#----------
#oparation 

class ImportFbxFiles(Operator, ImportHelper):
    bl_idname = "object.retarget_action_import_fbx"
    bl_label = "Import Fbx"
    bl_description = "Import Fbx"
    bl_options = {'PRESET', 'UNDO'}

    directory: StringProperty(name="Folder Path", subtype='DIR_PATH')

    filename_ext = ".fbx"
    filter_glob: StringProperty(default="*.fbx", options={'HIDDEN'})

    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )

    animation: BoolProperty(name="Animation", 
                               description="Import Animation",
                               default=True)

    only_action: BoolProperty(name="Only Action", 
                               description="Delete All Objects and leave the actions",
                               default=False)
    
    only_one: BoolProperty(name="Only One Armature", 
                            description="Delete All Objects and only leave one Armature",
                            default=False)
    
    no_armature_action: BoolProperty(name="Delete Not Armature Action", 
                            description="Delete Action That didn't not affect a bone",
                            default=True)

    delete_Empty: BoolProperty(name="Delete Empty", 
                            default=True)

    automatic_bone_orientation: BoolProperty(name="Automatic bone orientation", 
                            default=True)

    ignore_leaf_bones: BoolProperty(name="Ignore Leaf Bones", 
                            default=True)

    apply_rotation: BoolProperty(name="Apply rotation of Armature", 
                            default=True)
    
    rename_armature: BoolProperty(name="Rename Armature", 
                               description="Rename Armature from fbx name",
                               default=True)
    
    rename_action: BoolProperty(name="Rename Action", 
                               description="Rename Actions from fbx name",
                               default=True)
    
    add_prefix_suffix: BoolProperty(name="Add Prefix/Suffix", 
                                    description="Add Prefix/Suffix in Action Name",
                                    default=False)
    prefix: StringProperty(name="prefix",default="")
    suffix: StringProperty(name="suffix",default="")
        
    search_option: BoolProperty(name="Suggestion",default=False)
    tag: StringProperty(name="Tag", default="", search=get_all_tag)
    tag_: StringProperty(name="Tag",default="")
    
    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "animation")
        column.separator()

        row = column.row()
        row.prop(self, "only_action")
        column.separator()

        row = column.row()
        row.prop(self, "only_one")
        row.enabled = not self.only_action
        column.separator()

        row = column.row()
        row.prop(self, "no_armature_action")
        column.separator()

        row = column.row()
        row.prop(self, "delete_Empty")
        column.separator()

        row = column.row()
        row.prop(self, "automatic_bone_orientation")
        column.separator()

        row = column.row()
        row.prop(self, "ignore_leaf_bones")
        column.separator()

        row = column.row()
        row.prop(self, "apply_rotation")
        column.separator()

        row = column.row()
        row.prop(self, "rename_armature")
        column.separator()

        row = column.row()
        row.prop(self, "rename_action")
        column.separator()

        row = column.row()
        row.prop(self, "add_prefix_suffix")
        column.separator()

        if self.add_prefix_suffix:
            
            row = column.row()
            row.prop(self, "prefix")

            row = column.row()
            row.prop(self, "suffix")
            column.separator()


        row = column.row()
        row.prop(self, "search_option", text="", icon="SYNTAX_ON")
        if self.search_option:
            row.prop(self, "tag", icon='TAG')
        else:
            row.prop(self, "tag_", icon='TAG')

    def execute(self, context):

        existing_mats = set(bpy.data.materials)
        existing_imgs = set(bpy.data.images)
        existing_arms = set(bpy.data.armatures)
        existing_meshs = set(bpy.data.meshes)
        old_actions = set(bpy.data.actions)
        
        first_ob = None
        for f in self.files:
        
            try:
                fbx_path = os.path.join(self.directory, f.name)
                action_name = os.path.splitext(f.name[:-3])[0]
                existing_objs = set(bpy.data.objects)
                
                bpy.ops.import_scene.fbx(filepath=fbx_path, automatic_bone_orientation=self.automatic_bone_orientation,
                                        use_anim=self.animation,ignore_leaf_bones=self.ignore_leaf_bones)
                
                imported_armature = None
                imported_ob = []

                for obj in bpy.data.objects:

                    if not obj:
                        continue

                    if obj not in existing_objs:

                        imported_ob.append(obj)

                        if obj.type == 'ARMATURE' and not imported_armature:
                            imported_armature = obj

                action = None
                if imported_armature and imported_armature.animation_data and imported_armature.animation_data.action:
                    action = imported_armature.animation_data.action

                    if self.rename_action:
                        action.name = action_name

                if self.apply_rotation:

                    for action in reversed(bpy.data.actions):                 
                        if action not in old_actions:
                            #delete rotation
                            if action and action_armature(action):
                                for slot in action.slots:

                                    if slot.target_id_type != 'OBJECT' or not slot_armature(action, slot):
                                        continue

                                    del_fc = []
                                    channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
                                    
                                    if channelbag:
                                        for fcurve in channelbag.fcurves:
                                            if fcurve.data_path in ["rotation_axis_angle", "rotation_quaternion", "rotation_euler"]:
                                                del_fc.append(fcurve)

                                        for fc in reversed(del_fc):
                                            channelbag.fcurves.remove(fc)

                if self.only_action:
                    for ob in reversed(imported_ob):
                        bpy.data.objects.remove(ob, do_unlink=True)

                    for arm in reversed(bpy.data.armatures):
                        if arm not in existing_arms:
                            bpy.data.armatures.remove(arm, do_unlink=True)
               
                if self.apply_rotation:
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.select_all(action='DESELECT')
                    for ob in imported_ob:
                        if ob:
                            context.view_layer.objects.active = ob
                            bpy.ops.object.select_pattern( pattern=ob.name, case_sensitive=True, extend=True)
                    try:
                        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
                    except:
                        pass

                if self.only_one and not self.only_action:
                    
                    if first_ob:
                        context.view_layer.objects.active = first_ob

                    if not first_ob and imported_armature:
                        first_ob = imported_armature

                    for ob in reversed(imported_ob):
                        if first_ob and ob == first_ob:
                            continue
                        bpy.data.objects.remove(ob, do_unlink=True)

                    for arm in reversed(bpy.data.armatures):

                        if first_ob and arm == first_ob.data:
                            continue

                        if arm not in existing_arms:
                            bpy.data.armatures.remove(arm, do_unlink=True)

                if self.delete_Empty:
                    #delete Empty
                    if not self.only_one and not self.only_action:
                        for ob in reversed(imported_ob):
                            if ob.type == 'EMPTY':
                                bpy.data.objects.remove(ob, do_unlink=True)


                if self.rename_armature and imported_armature:
                    imported_armature.name = action_name

            except:
                pass

        if self.only_action or self.only_one:

            for mat in reversed(bpy.data.materials):
                if mat not in existing_mats:
                    bpy.data.materials.remove(mat, do_unlink=True)

            for img in reversed(bpy.data.images):
                if img not in existing_imgs:
                    bpy.data.images.remove(img, do_unlink=True)

            for mesh in reversed(bpy.data.meshes):
                if mesh not in existing_meshs:
                    bpy.data.meshes.remove(mesh, do_unlink=True)

        if self.no_armature_action:
            for action in reversed(bpy.data.actions):                 
                 if action not in old_actions and not action_armature(action):
                    bpy.data.actions.remove(action, do_unlink=True)

        tag = self.tag if self.search_option else self.tag_
        for action in reversed(bpy.data.actions):                 
            if action not in old_actions:
                action.retarget_act.tag = tag

            if self.add_prefix_suffix:
                action.name = self.prefix + action.name + self.suffix

        update_action_list(context)

        return {'FINISHED'}
    
class ACTION_OT_add_action(Operator):
    "Add a New Action On Active Object(s)"
    bl_idname = "object.retarget_action_add_action"
    bl_label = "Add a New Action"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(name="Action Name",default="Action")
    slot_name: StringProperty(name="Slot Name", default="Slot")
    number_of_frame: IntProperty(name="Number of frame", default=30)
    use_fake_user: BoolProperty(name="Use Fake User", default=True)

    search_option: BoolProperty(name="Suggestion",default=True)
    tag: StringProperty(name="Tag", default="", search=get_all_tag)
    tag_: StringProperty(name="Tag",default="")

    action_by_object: BoolProperty(name="New Action By Objects",
                                   description= "Each Selected Objects will have his own Action",
                                     default=False)
    
    add_object_list: BoolProperty(name="Add In Object(s) List", default=True)

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "name", icon='ACTION')

        row = column.row()
        row.prop(self, "slot_name", icon='ACTION_SLOT')

        row = column.row()
        row.prop(self, "number_of_frame", icon='ACTION_SLOT')

        row = column.row()
        row.prop(self, "search_option", text="", icon="SYNTAX_ON")
        if self.search_option:
            row.prop(self, "tag", icon='TAG')
        else:
            row.prop(self, "tag_", icon='TAG')

        row = column.row()
        row.prop(self, "use_fake_user", icon='FAKE_USER_ON')

        obs = get_selected_obs(context)
        if obs:
            if len(obs) > 1:
                row = column.row()
                row.prop(self, "action_by_object", icon='PLUS')
            row = column.row()
            row.prop(self, "add_object_list", icon='OBJECT_DATA')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        obs = get_selected_obs(context)
        tag = self.tag if self.search_option else self.tag_
        slot = None       
        action = bpy.data.actions.new(self.name)
        action.use_fake_user = self.use_fake_user
        action.retarget_act.tag = tag

        if self.slot_name:
            slot = action.slots.new('OBJECT', self.slot_name)

        if obs:
            for ob in obs:
                if ob and hasattr(ob, 'animation_data') and ob.animation_data and ob.animation_data.action:
                    ob.animation_data.action = None
                
                if not ob.animation_data:
                    ob.animation_data_create()

                if len(obs) > 1 and self.action_by_object and not action:
                    action = bpy.data.actions.new(self.name)
                    action.use_fake_user = self.use_fake_user
                    action.retarget_act.tag = tag
                    

                    if self.slot_name:
                        slot = action.slots.new('OBJECT', self.slot_name)
                
                if len(obs) > 1 and self.action_by_object and action:
                    action.name = ob.name+"|"+action.name
                
                ob.animation_data.action = action
                ob.animation_data.action_slot = slot

                if self.add_object_list:
                    ob_action = ob.retarget_object_list.add()
                    ob_action.action_ptr = action

                if len(obs) > 1 and self.action_by_object:
                    action = None
        
        update_action_list(context)

        if action:

            #set focus
            scene = context.scene

            for i, it in enumerate(scene.retarget_action_list):
                if it.action_ptr == action:
                    scene.retarget_action.action_index = i
                    break

            scene.frame_start = 0
            scene.frame_end = self.number_of_frame
            scene.frame_set(0)

            try:
                bpy.ops.action.view_all()
            except RuntimeError:
                # we are not in a timeline context, let's look for one in the screen
                for window in context.window_manager.windows:
                    screen = window.screen
                    for area in screen.areas:
                        if area.type == 'DOPESHEET_EDITOR':
                            for region in area.regions:
                                if region.type == 'WINDOW':
                                    with context.temp_override(window=window,
                                                            area=area,
                                                            region=region):
                                        bpy.ops.action.view_all()
                                    break
                            break

        return {'FINISHED'}

class ACTION_OT_unassign_action(Operator):
    "Unlink Action On Selected Object(s)"
    bl_idname = "object.retarget_action_unassign_action"
    bl_label = "Unlink Action"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obs = get_selected_obs(context)
        for ob in obs:
            if ob and hasattr(ob, 'animation_data') and ob.animation_data and ob.animation_data.action:
                ob.animation_data.action = None
        return {'FINISHED'}
    
class ACTION_OT_reset_transform(Operator):
    """Reset Transform Of Selected Object(s)"""
    bl_idname = "object.retarget_action_reset_transform"
    bl_label = "Reset Transform"
    bl_options = {'REGISTER', 'UNDO'}

    position: BoolProperty(name="Position",
                                description="also reset the position of the object",
                                default=True)

    all_transform: BoolProperty(name="All Transform",
                                description="also reset the position, rotation and the scale of the object",
                                default=False)

    @classmethod
    def poll(cls, context):
        return len(get_selected_obs(context)) > 0

    def execute(self, context):
        obs = get_selected_obs(context)
        for ob in obs:

            if self.all_transform:
                ob.matrix_basis = Matrix()
            elif self.position:
                ob.location = [0,0,0]
            if ob.type == 'ARMATURE':
                for bone in ob.pose.bones:
                    bone.matrix_basis = Matrix()

        return {'FINISHED'}
    
class ACTION_OT_add_prefix_suffix(Operator):
    """Add Prefix or Suffix on Selected Action(s)"""
    bl_idname = "object.retarget_action_add_prefix_suffix"
    bl_label = "Add Prefix or Suffix to Action Name"
    bl_options = {'REGISTER', 'UNDO'}

    prefix: StringProperty(name="prefix",default="")
    suffix: StringProperty(name="suffix",default="")
    replace: StringProperty(name="replace",default="")
    with_this: StringProperty(name="with",default="")

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

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
        action_list = get_selected_action_list(context)
       
        for item in action_list:
            item.name = self.prefix + item.name.replace(self.replace, self.with_this) + self.suffix
        return {'FINISHED'}
    
#tag
class ACTION_OT_add_prefix_suffix_tag(Operator):
    """Add Prefix or Suffix on The Tag Of Selected Action(s)"""
    bl_idname = "object.retarget_action_add_prefix_suffix_tag"
    bl_label = "Add Prefix or Suffix On Tag"
    bl_options = {'REGISTER', 'UNDO'}

    prefix: StringProperty(name="prefix",default="")
    suffix: StringProperty(name="suffix",default="")
    replace: StringProperty(name="replace",default="")
    with_this: StringProperty(name="with",default="")

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

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
        action_list = get_selected_action_list(context)
        for item in action_list:
            item.tag = self.prefix + item.tag.replace(self.replace, self.with_this) + self.suffix
        
        return {'FINISHED'}
    
class ACTION_OT_set_tag(Operator):
    """Add Set The Tag Of Selected Action(s)"""
    bl_idname = "object.retarget_action_set_tag"
    bl_label = "Set A Tag"
    bl_options = {'REGISTER', 'UNDO'}

    search_option: BoolProperty(name="Suggestion",default=True)

    name: StringProperty(name="Tag",default="", 
                         description= "Enter the tag Name (comma is the separator)",
                         search=get_all_tag)
    name_: StringProperty(name="Tag",
                          description= "Enter the tag Name (comma is the separator)",
                          default="")
    
    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

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
        tag = self.name if self.search_option else self.name_
        action_list = get_selected_action_list(context)
        for item in action_list:
            item.tag = tag
        return {'FINISHED'}
    
#-------------------

class ACTION_OT_hidden_on(Operator):
    """Set Hidden Mark on Selected Action(s)"""
    bl_idname = "object.retarget_action_hidden_on"
    bl_label = "Hidden ON"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

    def execute(self, context):
        action_list = get_selected_action_list(context)
        for item in action_list:
            item.is_hidden = True

        return {'FINISHED'}

class ACTION_OT_hidden_off(Operator):
    """Set Hidden Mark on Selected Action(s)"""
    bl_idname = "object.retarget_action_hidden_off"
    bl_label = "Hidden OFF"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

    def execute(self, context):
        action_list = get_selected_action_list(context)
        for item in action_list:
            item.is_hidden = False

        return {'FINISHED'}
    
class ACTION_OT_clear_users(Operator):
    """Set Clear Users on Selected Action(s)"""
    bl_idname = "object.retarget_action_clear_users"
    bl_label = "Clear Users"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

    def execute(self, context):
        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        action_list = get_selected_action_list(context)
       
        for item in action_list:
            if item.action_ptr:
                item.action_ptr.user_clear()
                item.asset_mark = False

        return {'FINISHED'}

class ACTION_OT_use_fake_user(Operator):
    """Set Fake User on Selected Action(s)"""
    bl_idname = "object.retarget_action_use_fake_user"
    bl_label = "Set Fake User"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

    def execute(self, context):
        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        action_list = get_selected_action_list(context)
       
        for item in action_list:
            if item.action_ptr:
                item.action_ptr.use_fake_user = True

        return {'FINISHED'}

class ACTION_OT_not_fake_user(Operator):
    """Remove Fake User on Selected Action(s)"""
    bl_idname = "object.retarget_action_not_fake_user"
    bl_label = "Remove Fake User"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

    def execute(self, context):
        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        action_list = get_selected_action_list(context)
       
        for item in action_list:
            if item.action_ptr:
                item.action_ptr.use_fake_user = False

        return {'FINISHED'}
    
class ACTION_OT_add_library(Operator):
    """Add Selected Action(s) In the Library"""
    bl_idname = "object.retarget_action_add_library"
    bl_label = "Add To the Library"
    bl_options = {'REGISTER', 'UNDO'}

    default_tag: BoolProperty(name="Default Tag", default=True)

    search_option: BoolProperty(name="Suggestion",default=True)

    name: StringProperty(name="Tag",default="", 
                         description= "Enter the tag Name (comma is the separator)",
                         search=get_all_tag)
    name_: StringProperty(name="Tag",
                          description= "Enter the tag Name (comma is the separator)",
                          default="")
    
    clear: BoolProperty(name="Clear Previou(s) tag", default=True)

    new_catalog: BoolProperty(name="Catalog by Tag",
                              description= "Add a New Catalog for Each Tag", 
                              default=False)

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0
    
    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "default_tag")

        if not self.default_tag:
            row = column.row()
            row.prop(self, "search_option", text="", icon="SYNTAX_ON")
            if self.search_option:
                row.prop(self, "name")
            else:
                row.prop(self, "name_")

        row = column.row()
        row.prop(self, "clear")

        row = column.row()
        row.prop(self, "new_catalog")
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        tag = self.name if self.search_option else self.name_

        action_list = get_selected_action_list(context)
       
        for item in action_list:
            item.asset_mark = True

            if self.default_tag:
                tag = item.tag

            if self.clear and item.action_ptr and item.action_ptr.asset_data.tags:
                tags = item.action_ptr.asset_data.tags
                while tags:
                    tags.remove(tags[0])

            if tag and item.action_ptr:
                item.action_ptr.asset_data.tags.new(tag, skip_if_exists=True)

            if self.new_catalog and tag:

                asset_browser_area = next((a for a in context.screen.areas if a.ui_type == 'ASSETS'), None)

                if asset_browser_area:

                    # 2. Use a temporary context override to access 'selected_assets' from that area
                    with bpy.context.temp_override(area=asset_browser_area):

                        if context.space_data.params.asset_library_reference == "ALL":
                            self.report({'WARNING'}, "Please select a valid catalog")
                            continue

                        directory = context.space_data.params.directory

                        d = str(directory).split('\'')

                        directory = d[1]

                        if not bpy.data.filepath or os.path.basename(bpy.data.filepath) not in os.listdir(directory):
                            self.report({'WARNING'}, "Make sure that the current is in the active library")
                            continue

                        cats_file = os.path.join(str(directory), "blender_assets.cats.txt")

                        is_tag_here = False
                        id = ""

                        # Create the file with header if it doesn't exist
                        if not os.path.exists(cats_file):
                                with open(cats_file, "w") as f:
                                    f.write("VERSION 1\n")
                        else:           
                            cat = open(os.path.join(str(directory), "blender_assets.cats.txt"))
                            cats = cat.readlines()
                            cat.close()

                            #check if the tag is already there

                            for line in cats:
                                if line[0:1] == "#":
                                    continue
                                if line.strip() == "":
                                    continue
                                if line[0:7] == "VERSION":
                                    continue
                                data = line.split(":")
                                if len(data) > 1:
                                    if data[1] == tag:
                                        is_tag_here = True
                                        id = data[0] 

                        if not is_tag_here:

                            # Generate a unique ID
                            catalog_id = str(uuid.uuid4())
                            catalog_path = tag
                            catalog_name = tag

                            # Append the new catalog entry
                            with open(cats_file, "a") as f:
                                f.write(f"{catalog_id}:{catalog_path}:{catalog_name}\n")

                            id = catalog_id
                        
                        if id:
                            item.action_ptr.asset_data.catalog_id = id

        return {'FINISHED'}
    
class ACTION_OT_remove_library(Operator):
    """Remove Selected Action(s) In the Library"""
    bl_idname = "object.retarget_action_remove_library"
    bl_label = "Remove From the Library"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

    def execute(self, context):
        action_list = get_selected_action_list(context)
       
        for item in action_list:
            item.asset_mark = False

        return {'FINISHED'}
    
    
class ACTION_OT_local_action(Operator):
    """Make Selected Action(s) Local"""
    bl_idname = "object.retarget_action_local_action"
    bl_label = "Make Local"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

    def execute(self, context):
        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        action_list = get_selected_action_list(context)
       
        for item in action_list:

            if item.action_ptr and item.action_ptr.library:
                item.action_ptr.make_local()

        return {'FINISHED'}
    
class ACTION_OT_push_nla(Operator):
    """Push Selected Action(s) To NLA"""
    bl_idname = "object.retarget_action_push_nla"
    bl_label = "Push To NLA"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return number_selected(context) > 0

    def execute(self, context):
        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        action_list = get_selected_action_list(context)
        obs = get_selected_obs(context)
        for ob in obs:
            
            if ob.animation_data is None:
                ob.animation_data_create()

            nla_tracks = ob.animation_data.nla_tracks

            for item in action_list:
                new_track = nla_tracks.new()
                new_track.name = item.action_ptr.name
                start_frame = int(item.action_ptr.frame_range[0])
                strip = new_track.strips.new(item.action_ptr.name, start_frame, item.action_ptr)

            ob.animation_data.action = None

        return {'FINISHED'}
    

class ACTION_OT_clean_empty_nla(Operator):
    """Clear Empty NLA Track On Selected Object(s)"""
    bl_idname = "object.retarget_action_clean_empty_nla"
    bl_label = "Clear Empty NLA Track"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return len(get_selected_obs(context)) > 0

    def execute(self, context):
        obs = get_selected_obs(context)
        for obj in obs:

            # Check if the object has animation data
            if obj.animation_data and obj.animation_data.nla_tracks:
                # Create a list of tracks to delete (cannot delete while iterating over the collection)
                tracks_to_delete = []
                for track in obj.animation_data.nla_tracks:
                    # An "empty" track has no strips
                    if not track.strips:
                        tracks_to_delete.append(track)
                
                # Delete the empty tracks
                for track in reversed(tracks_to_delete):
                    obj.animation_data.nla_tracks.remove(track)
                    print(f"Removed empty NLA track from object: {obj.name}")

            # Optional: Also clear animation data entirely from objects with no tracks remaining
            for obj in bpy.context.scene.objects:
                if obj.animation_data and not obj.animation_data.nla_tracks and not obj.animation_data.action:
                    obj.animation_data_clear()
                    print(f"Cleared all animation data for object: {obj.name}")

        return {'FINISHED'}

class ACTION_OT_clean_all_nla(Operator):
    """Clear All NLA Track On Selected Object(s)"""
    bl_idname = "object.retarget_action_clean_all_nla"
    bl_label = "Clear All NLA Track"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_selected_obs(context)) > 0

    def execute(self, context):
        obs = get_selected_obs(context)
        for obj in obs:

            if obj and obj.animation_data:
                obj.animation_data_clear()

        return {'FINISHED'}
    
class ACTION_OT_duplic_active_action(Operator):
    """Duplicate Active Action(s)"""
    bl_idname = "object.retarget_action_duplic_active_action"
    bl_label = "Duplicate"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(name="Action Name",default="Action")
    use_fake_user: BoolProperty(name="Use Fake User", default=True)

    search_option: BoolProperty(name="Suggestion",default=True)
    tag: StringProperty(name="Tag", default="", search=get_all_tag)
    tag_: StringProperty(name="Tag",default="")

    add_object_list: BoolProperty(name="Add In Object(s) List", default=True)

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "name", icon='ACTION')

        row = column.row()
        row.prop(self, "search_option", text="", icon="SYNTAX_ON")
        if self.search_option:
            row.prop(self, "tag", icon='TAG')
        else:
            row.prop(self, "tag_", icon='TAG')

        row = column.row()
        row.prop(self, "use_fake_user", icon='FAKE_USER_ON')

        obs = get_selected_obs(context)
        if obs:
            row = column.row()
            row.prop(self, "add_object_list", icon='OBJECT_DATA')

    def invoke(self, context, event):

        ob = context.active_object
        ob = get_ob_or_armature(context, ob)
        if ob:
            action = ob.animation_data.action
            self.name = action.name
            self.tag = action.retarget_act.tag
            self.tag_ = action.retarget_act.tag


        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        
        ob = context.active_object
        ob = get_ob_or_armature(context, ob)
        dup = None

        if ob and hasattr(ob, 'animation_data') and ob.animation_data and ob.animation_data.action:
            action = ob.animation_data.action
            dup = action.copy()
            if dup:
                tag = self.tag if self.search_option else self.tag_
                dup.name = self.name
                dup.retarget_act.tag = tag
                dup.use_fake_user = self.use_fake_user

                #add in Object list
                if self.add_object_list:
                    ob_action = ob.retarget_object_list.add()
                    ob_action.action_ptr = dup

        update_action_list(context)
        if dup:
            #set focus
            scene = context.scene
            for i, it in enumerate(scene.retarget_action_list):
                if it.action_ptr == dup:
                    scene.retarget_action.action_index = i
                    break
        return {'FINISHED'}
    
class ACTION_OT_duplic_action(Operator):
    """Duplicate Selected Action(s)"""
    bl_idname = "object.retarget_action_duplic_action"
    bl_label = "Duplicate"
    bl_options = {'REGISTER', 'UNDO'}

    prefix: StringProperty(name="Action prefix",default="")
    suffix: StringProperty(name="Action suffix",default="")
    use_fake_user: BoolProperty(name="Use Fake User", default=True)

    search_option: BoolProperty(name="Suggestion",default=True)
    tag: StringProperty(name="Tag", default="", search=get_all_tag)
    tag_: StringProperty(name="Tag",default="")

    add_object_list: BoolProperty(name="Add In Object(s) List", default=True)

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "prefix", icon='ACTION')

        row = column.row()
        row.prop(self, "suffix", icon='ACTION')

        row = column.row()
        row.prop(self, "search_option", text="", icon="SYNTAX_ON")
        if self.search_option:
            row.prop(self, "tag", icon='TAG')
        else:
            row.prop(self, "tag_", icon='TAG')

        row = column.row()
        row.prop(self, "use_fake_user", icon='FAKE_USER_ON')

        obs = get_selected_obs(context)
        if obs:
            row = column.row()
            row.prop(self, "add_object_list", icon='OBJECT_DATA')

    def invoke(self, context, event):

        ob = context.active_object
        ob = get_ob_or_armature(context, ob)
        if ob:
            action = ob.animation_data.action
            self.tag = action.retarget_act.tag
            self.tag_ = action.retarget_act.tag


        return context.window_manager.invoke_props_dialog(self)

    @classmethod
    def poll(cls, context):
        if context.scene.retarget_action.library_mode:
            return False
        return number_selected(context) > 0

    def execute(self, context):

        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        
        action_list = get_selected_action_list(context)
        dup = None
        for item in action_list:

            if item.action_ptr:
                dup = action = item.action_ptr.copy()
                if dup:
                    tag = self.tag if self.search_option else self.tag_
                    dup.retarget_act.tag = tag
                    dup.use_fake_user = self.use_fake_user
                    dup.name = self.prefix + dup.name + self.suffix

                    action.retarget_act.is_selected = False
                    #add in Object list
                    if self.add_object_list:
                        ob = context.active_object
                        ob = get_ob_or_armature(context, ob)
                        if ob:
                            ob_action = ob.retarget_object_list.add()
                            ob_action.action_ptr = dup

        update_action_list(context)
    
        if dup:
            #set focus
            scene = context.scene
            for i, it in enumerate(scene.retarget_action_list):
                if it.action_ptr == dup:
                    scene.retarget_action.action_index = i
                    break
        return {'FINISHED'}
    
class ACTION_OT_del_action(Operator):
    """Delete Selected Action(s)"""
    bl_idname = "object.retarget_action_delc_action"
    bl_label = "Delete"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.scene.retarget_action.library_mode:
            return False
        return number_selected(context) > 0

    def draw(self, context):
        layout = self.layout
        column = layout.column()
        row = column.row()
        row.label(text = 'Are You Sure (This will remove them completely) ?')

    def invoke(self, context, event):
        
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if context.scene.retarget_action.library_mode:
            return {'FINISHED'}
        action_list = get_selected_action_list(context)
        scene = context.scene

        for item in action_list:

            if item.action_ptr:
                #delete also in object list 
                if context.scene.retarget_action.object_mode:
                    ob = context.active_object
                    ob = get_ob_or_armature(context, ob)

                    if ob and ob.retarget_object_list:
                        for i, ob_action in enumerate(ob.retarget_object_list):
                            if ob_action.action_ptr == item.action_ptr:
                                ob.retarget_object_list.remove(i)

                bpy.data.actions.remove(item.action_ptr, do_unlink=True)
          

        update_action_list(context)
        return {'FINISHED'}
#--------------
# action range custom

class ActionRangeToSceneCustom(Operator):
    """Set Playback range to current action Start/End"""
    bl_idname = "object.retarget_action_to_range_custom"
    bl_label = "Action Range to Scene"
    bl_description = "Match scene range with current action range"
    bl_options = {'REGISTER', 'UNDO'}

    _allowed_modes_ = ['POSE', 'OBJECT']

    @classmethod
    def poll(cls, context):
        obj = context.object

        if not obj:
            return False
        if obj.mode not in cls._allowed_modes_:
            return False
       
        return True

    def execute(self, context):
        ob = context.active_object
        ob = get_ob_or_armature(context, ob)

        if not ob:
            return {'FINISHED'}

        if not ob.animation_data:
            return {'FINISHED'}

        if not ob.animation_data.action:
            return {'FINISHED'}

        action_range = ob.animation_data.action.frame_range

        scn = context.scene
        scn.frame_start = int(action_range[0])
        scn.frame_end = int(action_range[1])
        scn.frame_set(int(action_range[0]))
        
        try:
            bpy.ops.action.view_all()
        except RuntimeError:
            # we are not in a timeline context, let's look for one in the screen
            for window in context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'DOPESHEET_EDITOR':
                        for region in area.regions:
                            if region.type == 'WINDOW':
                                with context.temp_override(window=window,
                                                           area=area,
                                                           region=region):
                                    bpy.ops.action.view_all()
                                break
                        break
        return {'FINISHED'}
#-------------
classes = (
    #mode
    ACTION_OT_refresh_list,

    #library scan
    ACTION_OT_refresh_by_selected_library,
    ACTION_OT_refresh_library_path,
    ACTION_OT_refresh_library,

    #list manager
    ACTION_OT_add_to_object,
    ACTION_OT_clean_selected,
    ACTION_OT_refresh_list_clean,

    ACTION_OT_SelectUp,
    ACTION_OT_SelectDown,

    #select
    ACTION_OT_select_name,
    ACTION_OT_select_tag,
    ACTION_OT_select_no_tag,
    ACTION_OT_select_time,
    ACTION_OT_select_hidden_on,
    ACTION_OT_select_hidden_off,
    ACTION_OT_select_fake_user,
    ACTION_OT_select_fake_user_off,
    ACTION_OT_select_compatible,
    ACTION_OT_select_ob_action,
    ACTION_OT_select_armature_action,
    ACTION_OT_select_no_armature_action,
    #library op
    ACTION_OT_link_action,
    ACTION_OT_append_action,
    #ACTION_OT_select_no_compatible,
    ACTION_OT_inverse_selection,
    ACTION_OT_deselect_all_action,
    ACTION_OT_select_all_action,
    #ops
    ImportFbxFiles,
    ACTION_OT_add_action,

    ACTION_OT_unassign_action,
    ACTION_OT_reset_transform,

    #prefix on name
    ACTION_OT_add_prefix_suffix,

    #tag
    ACTION_OT_add_prefix_suffix_tag,
    ACTION_OT_set_tag,

    ACTION_OT_hidden_on,
    ACTION_OT_hidden_off,
    ACTION_OT_clear_users,
    ACTION_OT_use_fake_user,
    ACTION_OT_not_fake_user,
    ACTION_OT_add_library,
    ACTION_OT_remove_library,
    ACTION_OT_local_action,
    #nla
    ACTION_OT_push_nla,
    ACTION_OT_clean_empty_nla,
    ACTION_OT_clean_all_nla,

    ACTION_OT_duplic_active_action,
    ACTION_OT_duplic_action,
    ACTION_OT_del_action,

    ActionRangeToSceneCustom,
)

def handle_object_update(self, context):
    scene = context.scene
    if scene.retarget_action.auto_switch:

        if not handle_object_selection_change in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(handle_object_selection_change)
    else:

        if handle_object_selection_change in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(handle_object_selection_change)


def register_classes():

    if not handle_object_selection_change in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(handle_object_selection_change)

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_classes():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    if handle_object_selection_change in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(handle_object_selection_change)
    
   