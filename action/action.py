
from . import property,ops,ui,ui_menu


# --- Enregistrement ---

def register_classes():
    property.register_classes()
    ops.register_classes()
    ui_menu.register_classes()
    ui.register_classes()



def unregister_classes():
    ui.unregister_classes()
    ui_menu.unregister_classes()
    ops.unregister_classes()
    property.unregister_classes()
   