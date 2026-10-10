import bpy

from bpy.types import Panel
from bpy.types import UIList
from . import ops,ui_menu


# 2. L'interface de la liste (UIList)
class ACTION_UL_Library_select(UIList):

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        scene = context.scene
        sort = "name"
        if scene.retarget_action.sort_by_folder:
            sort = "folder"
        if scene.retarget_action.sort_by_file:
            sort = "file"
        if scene.retarget_action.sort_by_tag:
            sort = "tag"
        items_sorted = bpy.types.UI_UL_list.sort_items_by_name(items, sort)

        #filter_neworder = items_sorted(items, lambda i: len(getattr(i,sort)))
        # Initialize flags, then hide items based on custom property
        filtered = [self.bitflag_filter_item] * len(items)
        for i, item in enumerate(items):

            if not ops.correct_library_action(scene, item):
                filtered[i] &= ~self.bitflag_filter_item

        #reset filter  TODO find a better way
        ops.filter_name = ''
        ops.use_filter_invert = False
        return filtered, items_sorted
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        scene = context.scene
        row = layout.row(align=True)

        row.label(text=item.name, icon='ASSET_MANAGER')


        if scene.retarget_action.show_folder:
            row.label(text=item.folder, icon='FILEBROWSER')

        subrow = row
        if not scene.retarget_action.align:
            subrow = row.row()
            subrow.alignment = "RIGHT"

        if scene.retarget_action.show_file:
            subrow.label(text=item.file, icon='FILE_BLEND')

        if scene.retarget_action.show_tag:
            subrow.prop(item, "tag", text="",emboss=False, icon='TAG')
        
        if scene.retarget_action.show_hidden:
            if item.is_hidden:
                row.prop(item, "is_hidden", text="", icon='HIDE_ON', emboss=False)
            else:
                row.prop(item, "is_hidden", text="", icon='HIDE_OFF', emboss=False)

        if item.is_selected:
            row.prop(item, "is_selected", text="", icon='CHECKBOX_HLT', emboss=False)
        else:
            row.prop(item, "is_selected", text="", icon='CHECKBOX_DEHLT', emboss=False)

        ops.filter_name = self.filter_name
        ops.use_filter_invert = self.use_filter_invert

class ACTION_UL_multi_select(UIList):

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        scene = context.scene

        sort = "name"
       
       #TODO; fix this sort by int
        # if scene.retarget_action.sort_by_frame:
        #     #items_sorted =  bpy.types.UI_UL_list.sort_items_helper(items, lambda i: i.frame, True)
        #     sorted_items = sorted(items, key = lambda i: i.frame)
        #     items_sorted = []

        #     for s, item in enumerate(sorted_items)
        #     for sorted_item in sorted_items:
        #         i = 0
        #         for item in items:
        #             if item == sorted_item:
        #                 items_sorted.append(i)
        #                 break
        #             i += 1

        if scene.retarget_action.sort_by_tag:
            sort = "tag"
        
        items_sorted = bpy.types.UI_UL_list.sort_items_by_name(items, sort)
            
        #filter_neworder = items_sorted(items, lambda i: len(getattr(i,sort)))
        # Initialize flags, then hide items based on custom property
        filtered = [self.bitflag_filter_item] * len(items)
        for i, item in enumerate(items):
            if not ((ops.filter_name.lower() in item.name.lower() and not ops.use_filter_invert)
                or (ops.filter_name.lower() not in item.name.lower() and ops.use_filter_invert)):
                filtered[i] &= ~self.bitflag_filter_item

        #reset filter TODO find a better way
        ops.filter_name = ''
        ops.use_filter_invert = False
        return filtered, items_sorted
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        scene = context.scene
        row = layout.row(align=True)
        # if (scene.retarget_action.show_frame or scene.retarget_action.show_users) and item.action_ptr:
        #     row = layout.split(factor=0.6, align=True)
        # La case à cocher pour la multi-sélection
        # Le nom de l'action

        row.prop(item, "name", text="",emboss=False, icon='ACTION')
        
        subrow = row
        if not scene.retarget_action.align:
            subrow = row.row()
            subrow.alignment = "RIGHT"

        if scene.retarget_action.show_users and item.action_ptr:
            subrow.label(text = str(item.action_ptr.users), icon='COMMUNITY')

        if scene.retarget_action.show_frame and item.action_ptr:
            subrow.label(text=str(item.frame), icon='TIME')

        if scene.retarget_action.show_tag:
            subrow.prop(item, "tag", text="", emboss=False, icon='TAG')

        if scene.retarget_action.show_push_to_nla:
            subrow.prop(item, "push_to_nla", text="", icon='NLA_PUSHDOWN', emboss=False)

        if scene.retarget_action.show_library:
            if item.asset_mark:
                row.prop(item, "asset_mark", text="", icon='ASSET_MANAGER')
            else:
                row.prop(item, "asset_mark", text="", icon='FILE_TICK')

        if scene.retarget_action.show_local and item.action_ptr:
            if item.action_ptr.library:
                row.prop(item, "local", text="", icon='LINK_BLEND', emboss=False)
            else:
                row.prop(item, "local", text="", icon='APPEND_BLEND', emboss=False)

        if scene.retarget_action.show_hidden:
            if item.action_ptr.retarget_act.is_hidden:
                row.prop(item, "is_hidden", text="", icon='HIDE_ON', emboss=False)
            else:
                row.prop(item, "is_hidden", text="", icon='HIDE_OFF', emboss=False)

        if scene.retarget_action.show_fake_user and item.action_ptr:
            row.prop(item.action_ptr, "use_fake_user", text="")

        if item.is_selected:
            row.prop(item, "is_selected", text="", icon='CHECKBOX_HLT', emboss=False)
        else:
            row.prop(item, "is_selected", text="", icon='CHECKBOX_DEHLT', emboss=False)

        ops.filter_name = self.filter_name
        ops.use_filter_invert = self.use_filter_invert
        ops.use_filter_sort_reverse = self.use_filter_sort_reverse


# Action Manager panel
class VIEW3D_PT_multi_action_panel(Panel):
    bl_label = "Action Manager"
    bl_idname = "VIEW3D_PT_retarget_multi_action"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Retarget"

    def draw(self, context):
        layout = self.layout
        column = layout.column()
        scene = context.scene

        #title
        row = column.row()
        row.alignment = "CENTER"

        unlink_present = False
        ob = context.active_object
        obs  = ops.get_selected_obs(context)
        if ob:
            ob = ops.get_ob_or_armature(context, ob)

            ob_icon = 'OBJECT_DATA'
            if ob.type == 'ARMATURE':
                ob_icon = 'ARMATURE_DATA'

            selected_type = "Objects"
            if context.scene.retarget_action.armature_mode:
                selected_type = "Armatures"

            if len(obs) > 1:
                row.label(text = f"[{len(obs)} {selected_type}]", translate=False)
            row.label(text = ob.name, translate=False, icon=ob_icon)

            if ob and hasattr(ob, 'animation_data') and ob.animation_data and ob.animation_data.action:
                row.label(text = ob.animation_data.action.name, icon='ACTION')
                row.operator(ops.ACTION_OT_duplic_active_action.bl_idname, text='', icon='DUPLICATE')
                row.operator(ops.ACTION_OT_unassign_action.bl_idname, text='', icon='PLUGIN')
                unlink_present = True
        
        if not unlink_present:
            row.operator(ops.ACTION_OT_unassign_action.bl_idname, text='', icon='PLUGIN')

        if ob:
            number_action = len(ob.retarget_object_list)
            if number_action > 0:
                row.label(text = f'[{number_action} Action(s)]')

        number_action = len(ops.get_view_action_list(context))
        number_selected = ops.number_selected(context)
        icon_mode = "NONE"
        if scene.retarget_action.library_mode:
            mode_list = "Library"
            icon_mode = "ASSET_MANAGER"
        elif scene.retarget_action.only_compatible:
            mode_list = "Compatible"
            icon_mode = "CHECKMARK"
        else:
            mode_list = "All Action"
            icon_mode = "FILE_REFRESH"

        if not scene.retarget_action.library_mode:
            if scene.retarget_action.armature_mode:
                mode_list = mode_list + " | Armature"

            if scene.retarget_action.object_mode:
                mode_list = mode_list + " | Object"

        #subtitle
        #is threre actif filter
        icon_F='NONE'
        if scene.retarget_action.library_mode:
            if any(
                (scene.retarget_action.filt_tag,
                scene.retarget_action.filt_with_tag,
                scene.retarget_action.filt_not_tag,
                scene.retarget_action.filt_hidden,
                scene.retarget_action.filt_no_hidden,
                scene.retarget_action.filt_folder,
                scene.retarget_action.filt_file,
                scene.retarget_action.filt_selected,
                scene.retarget_action.filt_not_selected,
                ops.filter_name,
                )
                ):
                icon_F = 'FILTER'

        elif any(
                (scene.retarget_action.filt_tag,
                scene.retarget_action.filt_with_tag,
                scene.retarget_action.filt_not_tag,
                scene.retarget_action.filt_hidden,
                scene.retarget_action.filt_no_hidden,
                scene.retarget_action.filt_armature,
                scene.retarget_action.filt_not_armature,
                scene.retarget_action.filt_fake_user,
                scene.retarget_action.filt_not_fake_user,
                scene.retarget_action.filt_library,
                scene.retarget_action.filt_not_library,
                scene.retarget_action.filt_selected,
                scene.retarget_action.filt_not_selected,
                ops.filter_name,
                )
            ):
            icon_F = 'FILTER'

        row = column.row()
        row.alignment = "CENTER"
        row.label(text = f'{number_action} Action(s)', icon=icon_F)
        row.label(text = f'{number_selected} Selected')
        row.label(text = 'Mode: ' + mode_list, icon=icon_mode)


        # mode
        row = column.row()

        if not scene.retarget_action.library_mode:
            row.operator(ops.ACTION_OT_refresh_list.bl_idname, icon='FILE_REFRESH')
            row.prop(scene.retarget_action, "only_compatible", icon='CHECKMARK')
            row.prop(scene.retarget_action, "armature_mode", text="", icon='ARMATURE_DATA')
            row.prop(scene.retarget_action, "object_mode", text="", icon='OBJECT_DATA')

            row.prop(scene.retarget_action, "library_mode", text="", icon='ASSET_MANAGER')
        else:
            row.operator(ops.ACTION_OT_refresh_by_selected_library.bl_idname, icon='CHECKBOX_HLT')
            row.operator(ops.ACTION_OT_refresh_library_path.bl_idname, icon='FILE_REFRESH')
            row.operator(ops.ACTION_OT_refresh_library.bl_idname, icon='FILE_REFRESH')
            row.prop(scene.retarget_action, "library_mode", text="", icon='ASSET_MANAGER')

        # Affichage de la template_list
        if scene.retarget_action.library_mode:

            row = column.row()
            row.template_list("ACTION_UL_Library_select", "", scene, "retarget_action_library", scene.retarget_action, "library_index")
        else:
            row = column.row()
            row.template_list("ACTION_UL_multi_select", "", scene, "retarget_action_list", scene.retarget_action, "action_index")
        
        #side View
        if scene.retarget_action.side_view:
            col = row.column(align=True)

            if not scene.retarget_action.library_mode:
                col.operator(ops.ACTION_OT_add_action.bl_idname, text='', icon='ADD')
                col.separator()
                col.operator(ops.ACTION_OT_SelectUp.bl_idname, text='', icon='TRIA_UP')
                col.operator(ops.ACTION_OT_SelectDown.bl_idname, text='', icon='TRIA_DOWN')
                col.separator()

            col.operator(ops.ACTION_OT_select_all_action.bl_idname, text='', emboss=True, icon='CHECKBOX_HLT')
            col.operator(ops.ACTION_OT_deselect_all_action.bl_idname, text='', emboss=True, icon='CHECKBOX_DEHLT')
            col.operator(ops.ACTION_OT_inverse_selection.bl_idname, text='', emboss=True, icon='ARROW_LEFTRIGHT')
            col.separator()

            col.operator(ui_menu.VIEW3D_PT_retarget_view_setting.bl_idname, text='', icon='RESTRICT_VIEW_OFF')
            col.operator(ui_menu.VIEW3D_PT_retarget_filter_setting.bl_idname, text='', icon='FILTER')
            col.operator(ui_menu.VIEW3D_PT_retarget_sort_setting.bl_idname, text='', icon='SORTALPHA')
            col.separator()

            col.prop(scene.retarget_action,"link", text='', toggle=True, icon='LIBRARY_DATA_DIRECT')
            col.prop(scene.retarget_action,"play", text='', toggle=True, icon='PLAY')
            col.prop(scene.retarget_action,"action_range", text='', toggle=True, icon='PREVIEW_RANGE')
            col.prop(scene.retarget_action,"auto_switch", text='', toggle=True, icon='FILE_REFRESH')
        
            if scene.retarget_action.auto_switch:
                col.prop(scene.retarget_action,"unlink", text='', toggle=True, icon='PLUGIN')
            
            col.separator()
            col.menu(ui_menu.VIEW3D_PT_retarget_select.bl_idname, text='', icon='CHECKMARK')
            col.menu(ui_menu.VIEW3D_PT_retarget_ops_select.bl_idname, text='', icon='TOOL_SETTINGS')

        #view setting
        row = column.row()
        if scene.retarget_action.expand_list_view:
            row.prop(scene.retarget_action, "expand_list_view", icon='DOWNARROW_HLT', emboss=True)
            column.separator()

            #Show
            row = column.row()
            row.alignment = "CENTER"
            if not scene.retarget_action.library_mode:
                row.prop(scene.retarget_action, "show_users", text="", icon='COMMUNITY')
                row.prop(scene.retarget_action, "show_frame", text="", icon='TIME')
           
            if scene.retarget_action.library_mode:
                row.prop(scene.retarget_action, "show_folder", text="", icon='FILEBROWSER')
                row.prop(scene.retarget_action, "show_file", text="", icon='FILE_BLEND')
            
            row.prop(scene.retarget_action, "show_tag", text="", icon='TAG')

            if not scene.retarget_action.library_mode:
                row.prop(scene.retarget_action, "show_push_to_nla", text="", icon='NLA_PUSHDOWN')
                row.prop(scene.retarget_action, "show_library", text="", icon='ASSET_MANAGER')
                row.prop(scene.retarget_action, "show_local", text="", icon='LINK_BLEND')
            row.prop(scene.retarget_action, "show_hidden", text="", icon='HIDE_OFF')
            
            if not scene.retarget_action.library_mode:
                row.prop(scene.retarget_action, "show_fake_user", text="", icon='FAKE_USER_ON')
            
            #align view
            row.prop(scene.retarget_action, "align", text="", icon='ALIGN_JUSTIFY')
            row.prop(scene.retarget_action, "side_view", text="", icon='UV_ISLANDSEL')

            column.separator()

            #Sort BY
            row = column.row()
            row.label(text = 'Sort By', icon='SORTALPHA')

            row = column.row()
            row.alignment = "CENTER"
            row.prop(scene.retarget_action, "sort_by_tag", text="", icon='TAG')

            #Need to be fixed 
            # if not scene.retarget_action.library_mode:
            #     row.prop(scene.retarget_action, "sort_by_frame", text="", icon='TIME')

            if scene.retarget_action.library_mode:

                row.prop(scene.retarget_action, "sort_by_folder", text="", icon='FILEBROWSER')
                row.prop(scene.retarget_action, "sort_by_file", text="", icon='FILE_BLEND')

            column.separator()

            #filter
            row = column.row()
            row.label(text = 'Filter', icon='FILTER')
            
            #filter by tag
            row = column.row()
            row.prop(scene.retarget_action, "filt_tag", icon='TAG')
            
            if scene.retarget_action.filt_tag:
                row = column.row()
                row.prop(scene.retarget_action, "filt_tag_prefix", toggle=True)
                row.prop(scene.retarget_action, "filt_tag_contain", toggle=True)
                row.prop(scene.retarget_action, "filt_tag_suffix", toggle=True)

                row = column.row()
                row.prop(scene.retarget_action, "filt_tag_search_option", text="", icon="SYNTAX_ON")
                if scene.retarget_action.filt_tag_search_option:
                    row.prop(scene.retarget_action, "filt_tag_name")
                else:
                    row.prop(scene.retarget_action, "filt_tag_name_")

                row.prop(scene.retarget_action, "filt_tag_invert", text="",icon='ARROW_LEFTRIGHT')
                row = column.row()
                row.prop(scene.retarget_action, "filt_tag_show_all_filter", toggle=True)

                if scene.retarget_action.filt_tag_show_all_filter:

                    row.prop(scene.retarget_action, "filt_tag_show_all_filter_line", text="")

                    tags = []
                    if not scene.retarget_action.library_mode:
                        for action in bpy.data.actions:
                            if action and action.retarget_act.tag and action.retarget_act.tag not in tags:
                                tags.append(action.retarget_act.tag)
                    else:
                        for item in scene.retarget_action_library:
                            if item and item.tag and item.tag not in tags:
                                tags.append(item.tag)

                    if tags:
                        number = scene.retarget_action.filt_tag_show_all_filter_line
                        i = 0
                        row = column.split(factor= 1 / number, align=True)
                        for tag in tags:
                            if i == number:
                                row = column.split(factor= 1 / number, align=True)
                                i = 0
                            
                            row.label(text=tag, icon='TAG', translate=False)
                            i += 1

                column.separator()
            
            #filter library Folder,file
            if scene.retarget_action.library_mode:

                row = column.row()
                row.prop(scene.retarget_action, "filt_folder", icon='FILEBROWSER')
                if scene.retarget_action.filt_folder:
                    row = column.row()
                    row.prop(scene.retarget_action, "filt_folder_name")
                    column.separator()

                row = column.row()
                row.prop(scene.retarget_action, "filt_file", icon='FILE_BLEND')
                if scene.retarget_action.filt_file:
                    row = column.row()
                    row.prop(scene.retarget_action, "filt_file_name")

            #other filter
            column.separator()
            row = column.row()
            row.alignment = "CENTER"

            row.prop(scene.retarget_action, "filt_with_tag", text="", icon='RESTRICT_COLOR_OFF')
            row.prop(scene.retarget_action, "filt_not_tag", text="", icon='RESTRICT_COLOR_ON')

            row.prop(scene.retarget_action, "filt_hidden", text="", icon='HIDE_ON')
            row.prop(scene.retarget_action, "filt_no_hidden", text="", icon='HIDE_OFF')

            if not scene.retarget_action.library_mode:
                row.prop(scene.retarget_action, "filt_not_armature", text="", icon='ARMATURE_DATA')
                row.prop(scene.retarget_action, "filt_armature", text="", icon='ACTION')

                row.prop(scene.retarget_action, "filt_not_fake_user", text="", icon='FAKE_USER_ON')
                row.prop(scene.retarget_action, "filt_fake_user", text="", icon='FAKE_USER_OFF')

                row.prop(scene.retarget_action, "filt_not_library", text="", icon='ASSET_MANAGER')
                row.prop(scene.retarget_action, "filt_library", text="", icon='FILE_TICK')

            row.prop(scene.retarget_action, "filt_not_selected", text="", icon='CHECKBOX_HLT')
            row.prop(scene.retarget_action, "filt_selected", text="", icon='CHECKBOX_DEHLT')

        else:
            row.prop(scene.retarget_action, "expand_list_view", icon='RIGHTARROW', emboss=True)

        column.separator()

        #play
        row = column.row()
        row.prop(scene.retarget_action,"link", toggle=True, icon='LIBRARY_DATA_DIRECT')
        row.prop(scene.retarget_action,"play", toggle=True, icon='PLAY')
        row.prop(scene.retarget_action,"action_range", toggle=True, icon='PREVIEW_RANGE')

        row.prop(scene.retarget_action,"auto_switch", toggle=True, icon='FILE_REFRESH')
        
        if scene.retarget_action.auto_switch:
            row.prop(scene.retarget_action,"unlink", toggle=True, icon='PLUGIN')

        column.separator()

        #operation/select
        row = column.row()
        row.menu(ui_menu.VIEW3D_PT_retarget_select.bl_idname, icon='CHECKMARK')

        row.menu(ui_menu.VIEW3D_PT_retarget_ops_select.bl_idname, icon='TOOL_SETTINGS')

# --- Enregistrement ---
classes = (
    ACTION_UL_multi_select,
    ACTION_UL_Library_select,
    VIEW3D_PT_multi_action_panel,
)

def register_classes():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_classes():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
   