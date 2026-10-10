# ====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ======================= END GPL LICENSE BLOCK ========================


bl_info = {
    "name": "Retarget",
    "version": (1, 0, 0),
    "author": "KBS DEV",
    "blender": (5, 0, 0),
    "description": "Tools for Character Rig Conversion",
    "category": "Rigging",
}


from . import operators
from . import support
from . import ui
from . import preferences
from . import preset_handler
from . import properties
from .anim_aide import anim
from .action import action
from .rigging import surface as rig_op
#from .physics import physics__init__

def register():
    #set the rename candidate first
    ui.register_classes_c()
    action.register_classes()
    properties.register_classes()
    preferences.register_classes()
    operators.register_classes()
    support.register_classes()
    ui.register_classes()

    preset_handler.install_presets()

    #-- animaide

    anim.register_classes()

   
    preferences.add_key_manager_panel()
    preferences.add_anim_offset_header()

    preferences.add_anim_offset_panel()

    #update tab
    preferences.update_action_manager(None,None)
    preferences.update_preset(None,None)


    #-- rigging
    rig_op.register()
   

    #--- physics
    #physics__init__.register_classes()


def unregister():

    #--- physics
    #physics__init__.unregister_classes()

    #-- rigging
    rig_op.unregister()

    #-- animaide
    anim.unregister_classes()

    preferences.remove_key_manager_panel()

    preferences.remove_anim_offset_panel()

    preferences.remove_anim_offset_header()

    #-----
    ui.unregister_classes()
    support.unregister_classes()
    operators.unregister_classes()
    preferences.unregister_classes()
    properties.unregister_classes()
    action.unregister_classes()
    ui.unregister_classes_c()
