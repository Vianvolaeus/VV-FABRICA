"""
VV-FABRICA MODULE REGISTRY

HANDLES DISCOVERY, REGISTRATION, AND LIFECYCLE MANAGEMENT OF ADDON MODULES.
EACH MODULE IN `modules/` EXPORTS A `MODULE_INFO` DICT AND HELPER FUNCTIONS.
THE REGISTRY SCANS FOR THESE, MANAGES ENABLE/DISABLE STATE VIA PREFERENCES,
AND HANDLES BLENDER CLASS REGISTRATION/UNREGISTRATION.
"""

import importlib
import pkgutil
import bpy


# ¦ ¦ ¦ HELPERS
# ¦ INTERNAL STATE
_discovered_modules = {}  # ¦ {MODULE_ID: MODULE_REFERENCE}
_registered_modules = set()  # ¦ SET OF CURRENTLY REGISTERED MODULE_IDS


def _module_sort_key(module_info):
    """SORT MODULES BY OPTIONAL `ui_order`, THEN `name`, THEN `id`."""
    return (
        module_info.get("ui_order", 100),
        module_info.get("name", ""),
        module_info.get("id", ""),
    )


# ¦ ¦ ¦ REGISTRY FUNCTIONS
def discover_modules():
    """SCAN THE `modules/` PACKAGE AND IMPORT EACH SUBMODULE.

    POPULATES `_discovered_modules` WITH {`id`: `module_ref`} FROM EACH
    MODULE'S `MODULE_INFO` DICT.
    """
    global _discovered_modules
    _discovered_modules = {}

    from . import modules as modules_pkg

    for importer, modname, ispkg in pkgutil.iter_modules(modules_pkg.__path__):
        if not ispkg:
            continue
        try:
            module = importlib.import_module(f".modules.{modname}", package=__package__)
            if hasattr(module, "MODULE_INFO"):
                module_id = module.MODULE_INFO["id"]
                _discovered_modules[module_id] = module
                print(f"[VV-FABRICA] Discovered module: {module_id}")
            else:
                print(f"[VV-FABRICA] Skipping {modname}: no MODULE_INFO")
        except Exception as e:
            print(f"[VV-FABRICA] Error importing module {modname}: {e}")


def get_all_modules():
    """RETURN LIST OF `MODULE_INFO` DICTS FOR ALL DISCOVERED MODULES."""
    modules = [mod.MODULE_INFO for mod in _discovered_modules.values()]
    modules.sort(key=_module_sort_key)
    return modules


def get_module(module_id):
    """RETURN THE MODULE REFERENCE FOR A GIVEN `module_id`, OR NONE."""
    return _discovered_modules.get(module_id)


def get_enabled_module_ids():
    """RETURN SET OF CURRENTLY REGISTERED MODULE IDS."""
    return set(_registered_modules)


def get_enabled_modules():
    """RETURN ENABLED MODULE REFERENCES IN UI SORT ORDER."""
    modules = [mod for module_id, mod in _discovered_modules.items() if module_id in _registered_modules]
    modules.sort(key=lambda mod: _module_sort_key(mod.MODULE_INFO))
    return modules


def register_module(module_id):
    """REGISTER ALL BLENDER CLASSES AND SCENE PROPERTIES FOR A MODULE."""
    if module_id in _registered_modules:
        return

    module = _discovered_modules.get(module_id)
    if module is None:
        print(f"[VV-FABRICA] Cannot register unknown module: {module_id}")
        return

    try:
        # Register classes (operators, panels, menus)
        if hasattr(module, "get_classes"):
            for cls in module.get_classes():
                bpy.utils.register_class(cls)

        # Register scene properties
        if hasattr(module, "get_scene_properties"):
            for prop_name, (prop_type, prop_kwargs) in module.get_scene_properties().items():
                setattr(bpy.types.Scene, prop_name, prop_type(**prop_kwargs))

        _registered_modules.add(module_id)
        print(f"[VV-FABRICA] Registered module: {module_id}")

    except Exception as e:
        print(f"[VV-FABRICA] Error registering module {module_id}: {e}")


def unregister_module(module_id):
    """UNREGISTER ALL BLENDER CLASSES AND SCENE PROPERTIES FOR A MODULE."""
    if module_id not in _registered_modules:
        return

    module = _discovered_modules.get(module_id)
    if module is None:
        return

    try:
        # Unregister scene properties
        if hasattr(module, "get_scene_properties"):
            for prop_name in module.get_scene_properties().keys():
                if hasattr(bpy.types.Scene, prop_name):
                    delattr(bpy.types.Scene, prop_name)

        # Unregister classes in reverse order
        if hasattr(module, "get_classes"):
            for cls in reversed(module.get_classes()):
                try:
                    bpy.utils.unregister_class(cls)
                except RuntimeError:
                    pass  # Class may not be registered

        _registered_modules.discard(module_id)
        print(f"[VV-FABRICA] Unregistered module: {module_id}")

    except Exception as e:
        print(f"[VV-FABRICA] Error unregistering module {module_id}: {e}")


def register_all_enabled(preferences):
    """REGISTER ALL MODULES THAT ARE ENABLED IN PREFERENCES."""
    for module_info in get_all_modules():
        module_id = module_info["id"]
        prop_name = f"module_{module_id}"
        if getattr(preferences, prop_name, False):
            register_module(module_id)


def unregister_all():
    """UNREGISTER ALL CURRENTLY REGISTERED MODULES."""
    for module_id in list(_registered_modules):
        unregister_module(module_id)
