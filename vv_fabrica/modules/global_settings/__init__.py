"""GLOBAL SETTINGS MODULE — TOP-LEVEL UI CONTROLS AND QUICK HELP ACTIONS."""


MODULE_INFO = {
    "id": "global_settings",
    "name": "FABRICA",
    "description": "Global UI controls and quick help",
    "default_enabled": True,
    "icon": "PREFERENCES",
    "ui_order": 0,
}


def get_classes():
    from . import operators, panels, menus
    return operators.classes + panels.classes + menus.classes


def get_scene_properties():
    return {}


def get_menu_class():
    from . import menus
    return menus.VV_FABRICA_MT_global_settings
