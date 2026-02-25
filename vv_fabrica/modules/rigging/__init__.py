"""RIGGING MODULE — WEIGHT TRANSFER, BONE MERGING, BUTTON ATTACH."""

import bpy

MODULE_INFO = {
    "id": "rigging",
    "name": "Rigging",
    "description": "Weight transfer, bone merging, button attach",
    "default_enabled": True,
    "icon": "BONE_DATA",
}

def get_classes():
    from . import operators, panels, menus
    return operators.classes + panels.classes + menus.classes


def get_scene_properties():
    return {
        "vv_fabrica_source_object": (
            bpy.props.PointerProperty,
            {
                "name": "Source Object",
                "type": bpy.types.Object,
                "description": "Object to transfer vertex weights from",
            }
        ),
    }


def get_menu_class():
    from . import menus
    return menus.VV_FABRICA_MT_rigging
