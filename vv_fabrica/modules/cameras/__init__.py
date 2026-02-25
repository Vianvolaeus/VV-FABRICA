"""CAMERAS MODULE — VIEWPORT CAMERA, CAMERA SWITCHING."""


MODULE_INFO = {
    "id": "cameras",
    "name": "Cameras",
    "description": "Viewport camera, camera switching",
    "default_enabled": True,
    "icon": "CAMERA_DATA",
}


def get_classes():
    from . import operators, panels, menus
    return operators.classes + panels.classes + menus.classes


def get_scene_properties():
    return {}


def get_menu_class():
    from . import menus
    return menus.VV_FABRICA_MT_cameras
