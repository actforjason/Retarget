
import bpy
import blf

from bpy.props import BoolProperty
from bpy.props import IntProperty
from bpy.props import StringProperty
from bpy.props import PointerProperty
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty
from mathutils import Matrix
from . import ops

def play_action(self, context):
    #stop playing
    if not self.play and context.screen.is_animation_playing:
        bpy.ops.screen.animation_play()
    if self.play and not context.screen.is_animation_playing:
        bpy.ops.screen.animation_play()

message_text = None 
def add_message(message):

    global message_text

    def draw_text_callback(info):
        font_id = 0
        blf.position(font_id, 5, 80, 0)
        blf.size(font_id, 30)
        blf.color(font_id, 1, 1, 1, .5)
        blf.draw(font_id, info)

    if message_text is None:
        # set_bar_color(0.5, 0.3, 0.2, 1)
        message_text = bpy.types.SpaceView3D.draw_handler_add(
            draw_text_callback, (message,),
            'WINDOW', 'POST_PIXEL')

def remove_message():
    global message_text

    if message_text:
        bpy.types.SpaceView3D.draw_handler_remove(message_text, 'WINDOW')
    message_text = None

def message_unlink(self, context):
    if self.unlink and self.auto_switch:
        add_message("Auto Unlink Activated")
    else:
        remove_message()


def update_ob_action(self, context):

    #updates every time you pick action in the list
    ob = context.active_object

    if not ob:
        return
    
    #show the message (unlink stat)
    message_unlink(self, context)
    
    scene = context.scene

    if scene.retarget_action.link:
        
        ob = ops.get_ob_or_armature(context, ob)

        if not ob.animation_data:
            ob.animation_data_create()

        ret = scene.retarget_action_list[scene.retarget_action.action_index]

        #reset Transform for new animation no needed
        #ob.location = (0,0,0)
        
        ob.animation_data.action = ret.action_ptr

        if not ob.animation_data.action_slot:
            for slot in ret.action_ptr.slots:
                if ops.validate_slot(ret.action_ptr, slot, ob.path_resolve, armature= bool(ob.type == "'ARMATURE'")):
                    ob.animation_data.action_slot = slot
                    break

        if scene.retarget_action.play and not context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()

        if scene.retarget_action.action_range:
            bpy.ops.object.retarget_action_to_range_custom()
        


def update_list(self, context):
    ops.update_action_list(context)

def armature_mode_update(self, context):
    ob = context.active_object

    if ob and hasattr(ob, 'animation_data') and ob.animation_data and ob.animation_data.action:
        ob.animation_data.action = None

    ob = ops.get_ob_or_armature(context, ob)
                
    if ob and hasattr(ob, 'animation_data') and ob.animation_data and ob.animation_data.action:
        ob.animation_data.action = None

    ops.update_action_list(context)

class ActionVariable(PropertyGroup):

    #list index
    action_index: IntProperty(name="Index", default=0, update = update_ob_action)

    #list of mode
    
    only_compatible: BoolProperty(name= "Compatible Actions", update=update_list,
                                  description="Only display compatible action with the active object",
                                  default=False)

    armature_mode: BoolProperty(name= "Armature Mode", 
                                description="Armature Mode (Try to Find An Armature When we Select A Object)", update = armature_mode_update,
                                default=True)
    
    object_mode: BoolProperty(name= "Oject Mode", 
                                description="Object List (Only Show Action Added To the Active Object)", update = update_list,
                                default=False)
    #library setting
    library_mode: BoolProperty(name= "Library Mode", 
                                description="Action In Asset Browser", update = update_list,
                                default=False)
    library_index: IntProperty(name="Index", default=0)

    show_file: BoolProperty(name= "Show The Blend File", default=False)
    show_folder: BoolProperty(name= "Show The Folder", default=False)

    filt_folder: BoolProperty(name= "Filter By Folder", default=False)
    filt_folder_name: StringProperty(name="Name",description= "Enter the Folder Name", default="")

    filt_file: BoolProperty(name= "Filter By File", default=False)
    filt_file_name: StringProperty(name="Name",description= "Enter the File Name", default="")
    
    sort_by_folder: BoolProperty(name= "Sort By Folder", default=False)
    sort_by_file: BoolProperty(name= "Sort By File", default=False)
    
    #sort by
    sort_by_frame: BoolProperty(name= "Sort By Frame", default=False)
    sort_by_tag: BoolProperty(name= "Sort By Tag", default=False)
    
    #-------------------
    #Action play

    link: BoolProperty(name= "Auto Link", 
                         description="Link Action Selected To Active Object",
                         default=True)
    
    play: BoolProperty(name= "PLAY", 
                        description="Play selected Action", update = play_action,
                        default=False)
    
    action_range: BoolProperty(name= "Action Range to Scene",
                               description="Set Playback range to current action Start/End",
                               default=True)
    
    auto_switch: BoolProperty(name= "Auto Refresh", 
                              description="Refresh The Action List When We Select A New Object",
                              default=True, update = ops.handle_object_update)
    
    unlink: BoolProperty(name= "Auto Unlink", update = message_unlink,
                         description="Unlink Action On Previous Object(s) When We Select A New One (Warning: Can break orther thing so disable it when its not needed)",
                         default=False)
    
    #--------------------------
    #view setting

    expand_list_view: BoolProperty(name= "View Setting", default=False)
    show_hidden: BoolProperty(name= "Show The Hidden Mark", default=False)
    show_fake_user: BoolProperty(name= "Show The Fake User", default=True)
    show_library: BoolProperty(name= "Show The Library", default=False)
    show_local: BoolProperty(name= "Show The Local Statut", default=False)
    show_users: BoolProperty(name= "Show The Number of Users", default=False)
    show_frame: BoolProperty(name= "Show The Number of Frame", default=False)
    show_tag: BoolProperty(name= "Show The Tag", default=False)
    show_push_to_nla: BoolProperty(name= "Show Push To NLA", default=False)

    align: BoolProperty(name= "Align View", default=False)
    side_view: BoolProperty(name= "Side View", default=True)

    #filter tag
    filt_with_tag: BoolProperty(name= "Hide Action With No Tag", default=False, update=update_list)
    filt_not_tag: BoolProperty(name= "Hide Action With Tag", default=False, update=update_list)

    #deep tag finding
    filt_tag: BoolProperty(name= "Filter By Tag", default=False, update=update_list)
    filt_tag_prefix: BoolProperty(name= "Prefix", default=False, update=update_list)
    filt_tag_contain: BoolProperty(name= "Containt", default=True, update=update_list)
    filt_tag_suffix: BoolProperty(name= "Suffix", default=False, update=update_list)
    filt_tag_search_option: BoolProperty(name="Suggestion",default=True)
    filt_tag_name: StringProperty(name="Name",description= "Enter the tag Name (comma is the separator)", default="", update=update_list,search=ops.get_all_tag)
    filt_tag_name_: StringProperty(name="Name",description= "Enter the tag Name (comma is the separator)", default="", update=update_list)
    filt_tag_invert: BoolProperty(name="Invert",description= "Invert The Filter", default=False, update=update_list)
    filt_tag_show_all_filter: BoolProperty(name="Show All Tag", default=False)
    filt_tag_show_all_filter_line: IntProperty(name="Number By Line", default=3, min=1)

    #filter
    filt_hidden: BoolProperty(name= "Hide Action with Hidden Mark ON", default=False, update=update_list)
    filt_no_hidden: BoolProperty(name= "Hide Action with Hidden Mark OFF", default=False, update=update_list)
    filt_armature: BoolProperty(name= "Hide No Armature Action", default=False, update=update_list)
    filt_not_armature: BoolProperty(name= "Hide Armature Action", default=False, update=update_list)
    filt_fake_user: BoolProperty(name= "Hide Action With Not Fake User", default=False, update=update_list)
    filt_not_fake_user: BoolProperty(name= "Hide Action With Fake User", default=False, update=update_list)
    filt_library: BoolProperty(name= "Hide Action Not Present in Library", default=False, update=update_list)
    filt_not_library: BoolProperty(name= "Hide Action in Library", default=False, update=update_list)
    filt_selected: BoolProperty(name= "Hide Action No Selected", default=False, update=update_list)
    filt_not_selected: BoolProperty(name= "Hide Action Selected", default=False, update=update_list)
    #----------


#------------------------------------------
def asset_update(self, context):
    if self.action_ptr:
        if self.asset_mark and self.action_ptr.asset_data is None:
            self.action_ptr.asset_mark()
            if self.tag:
                self.action_ptr.asset_data.tags.new(self.tag, skip_if_exists=True)

        if not self.asset_mark and self.action_ptr.asset_data is not None:
            self.action_ptr.asset_clear()

def local_update(self, context):
    if self.action_ptr:
        if self.local and self.action_ptr.library:
            self.action_ptr.make_local()

def nla_update(self, context):
    if context.scene.retarget_action.library_mode or not self.action_ptr:
            return
    
    ob = context.active_object
    ob = ops.get_ob_or_armature(context, ob)

    if ob:
        if ob.animation_data is None:
            ob.animation_data_create()

        nla_tracks = ob.animation_data.nla_tracks

        new_track = nla_tracks.new()
        new_track.name = self.action_ptr.name
        start_frame = int(self.action_ptr.frame_range[0])
        strip = new_track.strips.new(self.action_ptr.name, start_frame, self.action_ptr)



def action_select(self, context):
    if self.action_ptr:
        self.action_ptr.retarget_act.is_selected = self.is_selected

def action_tag(self, context):
    if self.action_ptr:
        self.action_ptr.retarget_act.tag = self.tag

def action_is_hidden(self, context):
    if self.action_ptr:
        self.action_ptr.retarget_act.is_hidden = self.is_hidden

def update_action_name(self, context):
    if self.action_ptr:
        self.action_ptr.name = self.name

# action_list attr
class ActionListItem(PropertyGroup):
    name: StringProperty(update=update_action_name)
    action_ptr: PointerProperty(type=bpy.types.Action)
    asset_mark: BoolProperty(name="",description="Asset library", default=False, update=asset_update)
    local: BoolProperty(name="Local", description="Local Action", default=False, update=local_update)
    push_to_nla: BoolProperty(name="Push Down To NLA", description="Push Down To NLA", default=False, update=nla_update)
    tag: StringProperty(name="Tag", description="Tag Action", default="", update=action_tag)
    frame: IntProperty(name="Frame", description="Number Of Frame Of Action")
    is_hidden: BoolProperty(name="",description="Hidden Mark", default=False, update=action_is_hidden)
    is_selected: BoolProperty(name="",description="Select Action", default=False, update=action_select)


#library setting
class ActionListLibraryItem(PropertyGroup):
    name: StringProperty()
    file: StringProperty(name="Blend File", description="Folder", default="")
    folder: StringProperty(name="Folder", description="Folder", default="")
    tag: StringProperty(name="Tag", description="Tag Action", default="")
    is_hidden: BoolProperty(name="",description="Hidden Mark", default=False)
    is_selected: BoolProperty(name="",description="Select Action", default=False)

    
#action attr
class ActionAttr(PropertyGroup):
    tag: StringProperty(name="Tag", description="Tag Action", default="")
    is_hidden: BoolProperty(name="",description="Hidden Mark", default=False)
    is_selected: BoolProperty(name="",description="Select Action", default=False)

class ObjectAttr(PropertyGroup):
    action_ptr: PointerProperty(type=bpy.types.Action)
# --- Enregistrement ---
classes = (
    ActionVariable,
    ActionListItem,
    ActionListLibraryItem,
    ActionAttr,
    ObjectAttr,
)

def register_classes():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Propriétés attachées à la scène
    bpy.types.Scene.retarget_action_list = CollectionProperty(type=ActionListItem)
    bpy.types.Scene.retarget_action_library = CollectionProperty(type=ActionListLibraryItem)
    bpy.types.Scene.retarget_action = PointerProperty(type=ActionVariable)
    bpy.types.Action.retarget_act = PointerProperty(type=ActionAttr)
    bpy.types.Object.retarget_object_list = CollectionProperty(type=ObjectAttr)

def unregister_classes():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.retarget_action_list
    del bpy.types.Scene.retarget_action_library
    del bpy.types.Scene.retarget_action
    del bpy.types.Action.retarget_act
    del bpy.types.Object.retarget_object_list
