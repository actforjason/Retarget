
import bpy
from bpy.types import Operator, Menu, Panel
from . import ops


class VIEW3D_PT_retarget_select(Menu):
    bl_label = "Select"
    bl_idname = "OBJECT_MT_retarget_select_Menu"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.operator(ops.ACTION_OT_select_name.bl_idname, icon='SORTALPHA')
        row = layout.row()
        row.operator(ops.ACTION_OT_select_tag.bl_idname, icon='TAG')
        row = layout.row()
        row.operator(ops.ACTION_OT_select_no_tag.bl_idname, icon='TAG')

        if not scene.retarget_action.library_mode:
            row = layout.row()
            row.operator(ops.ACTION_OT_select_time.bl_idname, icon='TIME')

        row = layout.row()
        row.operator(ops.ACTION_OT_select_hidden_on.bl_idname, icon='HIDE_ON')
        row = layout.row()
        row.operator(ops.ACTION_OT_select_hidden_off.bl_idname, icon='HIDE_OFF')

        if not scene.retarget_action.library_mode:
            row = layout.row()
            row.operator(ops.ACTION_OT_select_fake_user.bl_idname, icon='FAKE_USER_ON')
            row = layout.row()
            row.operator(ops.ACTION_OT_select_fake_user_off.bl_idname, icon='FAKE_USER_OFF')
            row = layout.row()
            row.operator(ops.ACTION_OT_select_armature_action.bl_idname, icon='ARMATURE_DATA')
            row = layout.row()
            row.operator(ops.ACTION_OT_select_no_armature_action.bl_idname)
            row = layout.row()
            row.operator(ops.ACTION_OT_select_compatible.bl_idname)
            row = layout.row()
            row.operator(ops.ACTION_OT_select_ob_action.bl_idname, icon='OBJECT_DATA')
        # row = layout.row()
        # row.operator(ops.ACTION_OT_select_no_compatible.bl_idname)
        row = layout.row()
        row.operator(ops.ACTION_OT_inverse_selection.bl_idname, icon='ARROW_LEFTRIGHT')
        row = layout.row()
        row.operator(ops.ACTION_OT_deselect_all_action.bl_idname, icon='CHECKBOX_DEHLT')
        row = layout.row()
        row.operator(ops.ACTION_OT_select_all_action.bl_idname, icon='CHECKBOX_HLT')


class VIEW3D_PT_retarget_ops_select(Menu):
    bl_label = "Operations"
    bl_idname = "OBJECT_MT_retarget_ops_select_Menu"
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        if not scene.retarget_action.library_mode:
            row = layout.row()
            row.operator(ops.ACTION_OT_add_action.bl_idname, icon='ADD')

            row = layout.row()
            row.operator(ops.ACTION_OT_add_to_object.bl_idname, icon='OBJECT_DATA')

        row = layout.row()
        row.operator(ops.ACTION_OT_clean_selected.bl_idname, icon='TRACKING_CLEAR_BACKWARDS')

        row = layout.row()
        row.operator(ops.ACTION_OT_refresh_list_clean.bl_idname, icon='TRASH')
        layout.separator()

        row = layout.row()
        row.operator(ops.ACTION_OT_unassign_action.bl_idname, icon='PLUGIN')

        row = layout.row()
        row.operator(ops.ACTION_OT_reset_transform.bl_idname, icon='OUTLINER_OB_ARMATURE')

        layout.separator()

        if not scene.retarget_action.library_mode:
            row = layout.row()
            row.operator(ops.ACTION_OT_add_prefix_suffix.bl_idname, icon='SORTALPHA')

        layout.separator()

        row = layout.row()
        row.operator(ops.ImportFbxFiles.bl_idname)
        row = layout.row()
        row.operator_context = 'INVOKE_DEFAULT'
        row.operator("armature.retarget_rename_actions_fbx")

        layout.separator()

        row = layout.row()
        row.operator(ops.ACTION_OT_add_prefix_suffix_tag.bl_idname, icon='TAG')

        row = layout.row()
        row.operator(ops.ACTION_OT_set_tag.bl_idname, icon='TAG')

        row = layout.row()
        row.operator(ops.ACTION_OT_hidden_on.bl_idname, icon='HIDE_ON')

        row = layout.row()
        row.operator(ops.ACTION_OT_hidden_off.bl_idname, icon='HIDE_OFF')

        if not scene.retarget_action.library_mode:
            row = layout.row()
            row.operator(ops.ACTION_OT_clear_users.bl_idname, icon='RESTRICT_INSTANCED_ON')

            row = layout.row()
            row.operator(ops.ACTION_OT_use_fake_user.bl_idname, icon='FAKE_USER_ON')

            row = layout.row()
            row.operator(ops.ACTION_OT_not_fake_user.bl_idname, icon='FAKE_USER_OFF')

            row = layout.row()
            row.operator(ops.ACTION_OT_add_library.bl_idname, icon='ASSET_MANAGER')

            row = layout.row()
            row.operator(ops.ACTION_OT_remove_library.bl_idname, icon='FILE_TICK')

            layout.separator()

            row = layout.row()
            row.operator(ops.ACTION_OT_local_action.bl_idname, icon='APPEND_BLEND')

            layout.separator()

            row = layout.row()
            row.operator(ops.ACTION_OT_push_nla.bl_idname, icon='NLA_PUSHDOWN')
            row = layout.row()
            row.operator(ops.ACTION_OT_clean_empty_nla.bl_idname, icon='SEQ_SEQUENCER')
            row = layout.row()
            row.operator(ops.ACTION_OT_clean_all_nla.bl_idname)

            layout.separator()

            row = layout.row()
            row.operator(ops.ACTION_OT_duplic_action.bl_idname, icon='DUPLICATE')

            row = layout.row()
            row.operator(ops.ACTION_OT_del_action.bl_idname, icon='PANEL_CLOSE')

        else:
            layout.separator()

            row = layout.row()
            row.operator(ops.ACTION_OT_link_action.bl_idname, icon='LINK_BLEND')

            row = layout.row()
            row.operator(ops.ACTION_OT_append_action.bl_idname, icon='APPEND_BLEND')

class VIEW3D_PT_retarget_view_setting(Operator):
    bl_label = "View Setting"
    bl_idname = "object.retarget_ops_view_setting"
    bl_options = {'REGISTER', 'UNDO'}
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        col = row.column(align=True)
         #Show
        if not scene.retarget_action.library_mode:
            col.prop(scene.retarget_action, "show_users", text='', icon='COMMUNITY')
            col.prop(scene.retarget_action, "show_frame", text='', icon='TIME')

        if scene.retarget_action.library_mode:
            col.prop(scene.retarget_action, "show_folder", text='', icon='FILEBROWSER')
            col.prop(scene.retarget_action, "show_file", text='', icon='FILE_BLEND')
        
        col.prop(scene.retarget_action, "show_tag", text='', icon='TAG')

        if not scene.retarget_action.library_mode:
            col.prop(scene.retarget_action, "show_library", text='', icon='ASSET_MANAGER')
            col.prop(scene.retarget_action, "show_local", text='', icon='LINK_BLEND')
        col.prop(scene.retarget_action, "show_hidden", text='', icon='HIDE_OFF')
        
        if not scene.retarget_action.library_mode:
            col.prop(scene.retarget_action, "show_fake_user", text='', icon='FAKE_USER_ON')
        
        #align view
        col.prop(scene.retarget_action, "align", text='', icon='ALIGN_JUSTIFY')
        col.prop(scene.retarget_action, "side_view", text="", icon='UV_ISLANDSEL')

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)

    def execute(self, context):
        return {'FINISHED'}

class VIEW3D_PT_retarget_filter_setting(Operator):
    bl_label = "Filter"
    bl_idname = "object.retarget__ops_filter_setting"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        col = row.column(align=True)
        col.prop(scene.retarget_action, "filt_with_tag", text='', icon='RESTRICT_COLOR_OFF')
        col.prop(scene.retarget_action, "filt_not_tag", text='', icon='RESTRICT_COLOR_ON')
        col.prop(scene.retarget_action, "filt_hidden", text='', icon='HIDE_ON')
        col.prop(scene.retarget_action, "filt_no_hidden", text='', icon='HIDE_OFF')

        if not scene.retarget_action.library_mode:
            col.prop(scene.retarget_action, "filt_not_armature", text='', icon='ARMATURE_DATA')
            col.prop(scene.retarget_action, "filt_armature", text='', icon='ACTION')

            col.prop(scene.retarget_action, "filt_not_fake_user", text='', icon='FAKE_USER_ON')
            col.prop(scene.retarget_action, "filt_fake_user", text='', icon='FAKE_USER_OFF')

            col.prop(scene.retarget_action, "filt_not_library", text='', icon='ASSET_MANAGER')
            col.prop(scene.retarget_action, "filt_library", text='', icon='FILE_TICK')

        col.prop(scene.retarget_action, "filt_not_selected", text='', icon='CHECKBOX_HLT')
        col.prop(scene.retarget_action, "filt_selected", text='', icon='CHECKBOX_DEHLT')
    
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)

    def execute(self, context):
        return {'FINISHED'}

class VIEW3D_PT_retarget_sort_setting(Operator):
    bl_label = "View Setting"
    bl_idname = "object.retarget_ops_sort_setting"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        col = row.column(align=True)

        col.prop(scene.retarget_action, "sort_by_tag", text='', icon='TAG')
        if scene.retarget_action.library_mode:

            col.prop(scene.retarget_action, "sort_by_folder", text='', icon='FILEBROWSER')
            col.prop(scene.retarget_action, "sort_by_file", text='', icon='FILE_BLEND')
    
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)

    def execute(self, context):
        return {'FINISHED'}
classes = (
    VIEW3D_PT_retarget_select,
    VIEW3D_PT_retarget_ops_select,
    VIEW3D_PT_retarget_view_setting,
    VIEW3D_PT_retarget_filter_setting,
    VIEW3D_PT_retarget_sort_setting,
)


def register_classes():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister_classes():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
