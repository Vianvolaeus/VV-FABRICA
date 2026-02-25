"""
VV-FABRICA — MODULAR TOOLKIT FOR CHARACTER AUTHORING AND 3D WORKFLOWS

A BLENDER EXTENSION BY VIANVOLAEUS.
MODULES CAN BE ENABLED/DISABLED INDIVIDUALLY VIA ADDON PREFERENCES.
"""

import bpy
from . import registry
from . import preferences


# ¦ ¦ ¦ MENUS
class VV_FABRICA_MT_main(bpy.types.Menu):
    bl_label = "VV-FABRICA"
    bl_idname = "VV_FABRICA_MT_main"

    def draw(self, context):
        layout = self.layout
        for module in registry.get_enabled_modules():
            if hasattr(module, "get_menu_class"):
                menu_cls = module.get_menu_class()
                if menu_cls is not None:
                    icon = module.MODULE_INFO.get("icon", "NONE")
                    layout.menu(menu_cls.bl_idname, icon=icon)


# ¦ ¦ ¦ HELPERS
def _draw_top_menu(self, context):
    self.layout.menu(VV_FABRICA_MT_main.bl_idname)


# ¦ ¦ ¦ REGISTRATION
def register():
    # ¦ DISCOVER ALL MODULES
    registry.discover_modules()

    # ¦ REGISTER PREFERENCES (CREATES DYNAMIC TOGGLE PROPERTIES)
    preferences.register()

    # ¦ REGISTER TOP MENU
    bpy.utils.register_class(VV_FABRICA_MT_main)
    bpy.types.TOPBAR_MT_editor_menus.append(_draw_top_menu)

    # ¦ REGISTER ENABLED MODULES BASED ON PREFERENCE STATE
    prefs = bpy.context.preferences.addons.get(__package__)
    if prefs:
        registry.register_all_enabled(prefs.preferences)
    else:
        # ¦ FIRST INSTALL — REGISTER MODULES WITH DEFAULT_ENABLED=TRUE
        for module_info in registry.get_all_modules():
            if module_info.get("default_enabled", True):
                registry.register_module(module_info["id"])

    print("[VV-FABRICA] Addon registered successfully")


def unregister():
    # ¦ UNREGISTER ALL MODULES
    registry.unregister_all()

    # ¦ REMOVE TOP MENU
    bpy.types.TOPBAR_MT_editor_menus.remove(_draw_top_menu)
    bpy.utils.unregister_class(VV_FABRICA_MT_main)

    # ¦ UNREGISTER PREFERENCES
    preferences.unregister()

    print("[VV-FABRICA] Addon unregistered")
