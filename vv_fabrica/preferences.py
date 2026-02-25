"""
VV-FABRICA ADDON PREFERENCES

PROVIDES THE PREFERENCES PANEL WITH MODULE TOGGLE SWITCHES.
MODULE TOGGLES ARE DYNAMICALLY CREATED BASED ON DISCOVERED MODULES.
"""

import json
import os
from datetime import datetime

import bpy
from . import registry


# ¦ ¦ ¦ HELPERS
_SETTINGS_FILE_NAME = "vv_fabrica_settings.json"
_SETTINGS_SCHEMA_VERSION = 1
_suspend_preference_updates = False
_last_settings_error = ""


def _clear_last_settings_error():
    global _last_settings_error
    _last_settings_error = ""


def _set_last_settings_error(message):
    global _last_settings_error
    _last_settings_error = str(message)
    print(f"[VV-FABRICA:preferences] {_last_settings_error}")


def get_last_settings_error():
    return _last_settings_error or "Unknown settings error"


def get_addon_preferences(context=None):
    """RETURN VV-FABRICA `AddonPreferences` INSTANCE, OR NONE IF UNAVAILABLE."""
    ctx = context or bpy.context
    if ctx is None:
        _set_last_settings_error("No Blender context available for addon preferences lookup")
        return None
    addons = getattr(getattr(ctx, "preferences", None), "addons", None)
    if addons is None:
        _set_last_settings_error("Context has no preferences/addons collection")
        return None

    package_name = __package__ or "vv_fabrica"
    package_suffix = package_name.split(".")[-1]
    candidate_keys = [package_name, package_suffix, "vv_fabrica"]

    for key in candidate_keys:
        addon_entry = addons.get(key)
        if addon_entry is not None and getattr(addon_entry, "preferences", None) is not None:
            _clear_last_settings_error()
            return addon_entry.preferences

    for addon_key, addon_entry in addons.items():
        if addon_key == package_suffix or addon_key.endswith(f".{package_suffix}"):
            prefs = getattr(addon_entry, "preferences", None)
            if prefs is not None:
                _clear_last_settings_error()
                return prefs

    for addon_entry in addons.values():
        prefs = getattr(addon_entry, "preferences", None)
        if prefs is None:
            continue
        if hasattr(prefs, "auto_save_addon_settings") and hasattr(prefs, "global_settings_tab"):
            _clear_last_settings_error()
            return prefs

    available_keys = ", ".join(sorted([str(key) for key in addons.keys()]))
    _set_last_settings_error(
        "Could not resolve VV-FABRICA AddonPreferences entry. "
        f"Searched package='{package_name}', suffix='{package_suffix}'. "
        f"Available addon keys: {available_keys}"
    )
    return None


def _settings_file_path():
    config_dir = bpy.utils.user_resource("CONFIG", path="", create=True)
    if not config_dir:
        config_dir = bpy.app.tempdir or ""
    return os.path.join(config_dir, _SETTINGS_FILE_NAME)


def _iter_persisted_setting_keys(prefs):
    static_keys = [
        "auto_save_addon_settings",
        "global_settings_tab",
        "global_settings_show_module_settings",
        "global_settings_show_module_settings_details",
        "global_settings_show_quick_help",
        "global_settings_show_platform_links",
        "global_settings_module_settings_target",
        "cameras_dof_aperture_fstop",
    ]
    for key in static_keys:
        if hasattr(prefs, key):
            yield key

    for module_info in registry.get_all_modules():
        key = f"module_{module_info['id']}"
        if hasattr(prefs, key):
            yield key


def _serialize_settings(prefs):
    data = {
        "schema_version": _SETTINGS_SCHEMA_VERSION,
        "settings": {},
    }
    for key in _iter_persisted_setting_keys(prefs):
        data["settings"][key] = getattr(prefs, key)
    return data


def _json_safe_value(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, set):
        return sorted([_json_safe_value(item) for item in value], key=lambda item: str(item))
    return str(value)


def _quarantine_invalid_settings_file(path):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    quarantined_path = f"{path}.invalid-{timestamp}"
    try:
        os.replace(path, quarantined_path)
        return quarantined_path
    except Exception as exc:
        _set_last_settings_error(
            f"Settings file is invalid and could not be quarantined ('{path}'): {exc}"
        )
        return None


def save_internal_settings(context=None):
    prefs = get_addon_preferences(context)
    if prefs is None:
        if not _last_settings_error:
            _set_last_settings_error("Addon preferences were not available")
        return False
    try:
        path = _settings_file_path()
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        data = _serialize_settings(prefs)
        safe_data = {
            "schema_version": data.get("schema_version", _SETTINGS_SCHEMA_VERSION),
            "settings": {},
        }
        for key, value in data.get("settings", {}).items():
            safe_data["settings"][key] = _json_safe_value(value)
        temp_path = f"{path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as settings_file:
            json.dump(safe_data, settings_file, indent=2, sort_keys=True)
        os.replace(temp_path, path)
        _clear_last_settings_error()
        return True
    except Exception as exc:
        _set_last_settings_error(f"Could not save internal settings to '{path}': {exc}")
        try:
            temp_path = f"{path}.tmp"
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
        return False


def _load_settings_payload():
    path = _settings_file_path()
    if not os.path.exists(path):
        _set_last_settings_error(f"Settings file was not found at '{path}'")
        return None
    try:
        with open(path, "r", encoding="utf-8") as settings_file:
            data = json.load(settings_file)
        if not isinstance(data, dict):
            _set_last_settings_error(f"Settings file is not a JSON object: '{path}'")
            return None
        _clear_last_settings_error()
        return data
    except Exception as exc:
        quarantined_path = _quarantine_invalid_settings_file(path)
        if quarantined_path:
            _set_last_settings_error(
                f"Could not load internal settings from '{path}': {exc}. "
                f"Invalid file was moved to '{quarantined_path}'"
            )
        else:
            _set_last_settings_error(f"Could not load internal settings from '{path}': {exc}")
        return None


def _sync_module_registration_from_preferences(prefs):
    desired_enabled_ids = set()
    for module_info in registry.get_all_modules():
        module_id = module_info["id"]
        prop_name = f"module_{module_id}"
        if getattr(prefs, prop_name, False):
            desired_enabled_ids.add(module_id)

    current_enabled_ids = registry.get_enabled_module_ids()
    to_disable = sorted(current_enabled_ids - desired_enabled_ids)
    to_enable = sorted(desired_enabled_ids - current_enabled_ids)

    for module_id in to_disable:
        registry.unregister_module(module_id)
    for module_id in to_enable:
        registry.register_module(module_id)
    _rebuild_top_menu()


def _with_suspended_updates(fn):
    global _suspend_preference_updates
    _suspend_preference_updates = True
    try:
        return fn()
    finally:
        _suspend_preference_updates = False


def _apply_persisted_settings(prefs, payload, sync_modules=True):
    settings = payload.get("settings", {}) if isinstance(payload, dict) else {}
    if not isinstance(settings, dict):
        _set_last_settings_error("Persisted payload is missing a valid 'settings' object")
        return False

    deferred_module_settings_target = settings.get("global_settings_module_settings_target")

    def _apply():
        for key in _iter_persisted_setting_keys(prefs):
            if key not in settings:
                continue
            if key == "global_settings_module_settings_target":
                continue
            try:
                setattr(prefs, key, settings[key])
            except Exception as exc:
                print(f"[VV-FABRICA:preferences] Could not apply setting '{key}': {exc}")

    _with_suspended_updates(_apply)
    if sync_modules:
        _sync_module_registration_from_preferences(prefs)
    if deferred_module_settings_target is not None and hasattr(
        prefs, "global_settings_module_settings_target"
    ):
        available_target_ids = {item[0] for item in _module_settings_items(None, None)}
        if deferred_module_settings_target in available_target_ids:
            def _apply_deferred_target():
                try:
                    prefs.global_settings_module_settings_target = deferred_module_settings_target
                except Exception as exc:
                    print(
                        "[VV-FABRICA:preferences] Could not apply setting "
                        f"'global_settings_module_settings_target': {exc}"
                    )

            _with_suspended_updates(_apply_deferred_target)
    _clear_last_settings_error()
    return True


def load_internal_settings(context=None, sync_modules=True):
    prefs = get_addon_preferences(context)
    if prefs is None:
        if not _last_settings_error:
            _set_last_settings_error("Addon preferences were not available")
        return False
    payload = _load_settings_payload()
    if payload is None:
        return False
    return _apply_persisted_settings(prefs, payload, sync_modules=sync_modules)


def reset_internal_settings_to_defaults(context=None):
    prefs = get_addon_preferences(context)
    if prefs is None:
        if not _last_settings_error:
            _set_last_settings_error("Addon preferences were not available")
        return False

    def _reset():
        for key in _iter_persisted_setting_keys(prefs):
            try:
                prop = prefs.bl_rna.properties.get(key)
                if prop is None:
                    continue
                setattr(prefs, key, prop.default)
            except Exception as exc:
                print(f"[VV-FABRICA:preferences] Could not reset setting '{key}': {exc}")

    _with_suspended_updates(_reset)
    _sync_module_registration_from_preferences(prefs)
    if save_internal_settings(context):
        _clear_last_settings_error()
        return True
    return False


def _settings_update(self, _context):
    """PERSIST SETTINGS WHEN AUTO-SAVE IS ENABLED."""
    if _suspend_preference_updates:
        return
    if getattr(self, "auto_save_addon_settings", False):
        save_internal_settings()


def _make_module_toggle_update(module_id):
    """CREATE AN UPDATE CALLBACK FOR A MODULE TOGGLE PROPERTY."""
    def update(self, context):
        if _suspend_preference_updates:
            return
        prop_name = f"module_{module_id}"
        enabled = getattr(self, prop_name, False)
        if enabled:
            registry.register_module(module_id)
        else:
            registry.unregister_module(module_id)
        # Rebuild the top menu to reflect enabled/disabled modules
        _rebuild_top_menu()
        _settings_update(self, context)
    return update


def _rebuild_top_menu():
    """FORCE REDRAW OF ALL VIEW_3D AREAS TO UPDATE MENUS."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()


def _module_settings_items(_self, _context):
    items = []
    index = 0
    for module in registry.get_enabled_modules():
        module_info = getattr(module, "MODULE_INFO", {})
        module_id = module_info.get("id", "")
        if not module_id or module_id == "global_settings":
            continue
        module_name = module_info.get("name", module_id)
        module_icon = module_info.get("icon", "NONE")
        items.append((module_id, module_name, f"{module_name} settings", module_icon, index))
        index += 1

    if not items:
        items.append(("none", "No Modules", "No enabled modules with settings", "INFO", 0))
    return items


def _enabled_module_info_by_id():
    module_info_by_id = {}
    for module in registry.get_enabled_modules():
        module_info = getattr(module, "MODULE_INFO", {})
        module_id = module_info.get("id", "")
        if not module_id or module_id == "global_settings":
            continue
        module_info_by_id[module_id] = module_info
    return module_info_by_id


def _draw_disclosure_toggle(layout, data, prop_name, text):
    expanded = bool(getattr(data, prop_name, False))
    icon = 'TRIA_DOWN' if expanded else 'TRIA_RIGHT'
    row = layout.row(align=True)
    if hasattr(data, prop_name):
        row.prop(data, prop_name, text=text, icon=icon, emboss=False)
    else:
        row.label(text=text, icon=icon)
    return expanded


def _has_rna_property(data, prop_name):
    try:
        return bool(getattr(data, "bl_rna", None) and prop_name in data.bl_rna.properties)
    except Exception:
        return False


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _draw_module_toggle_row(layout, module_info, prefs, context=None):
    module_id = module_info.get("id", "")
    prop_name = f"module_{module_id}"
    module_name = module_info.get("name", module_id)
    module_description = module_info.get("description", "")
    module_icon = module_info.get("icon", "NONE")

    row = layout.row(align=True)
    row.use_property_split = False
    row.use_property_decorate = False
    row.alignment = 'EXPAND'

    # Blender UI has no strict min/max width constraints, so we approximate them
    # by deriving split factors from panel width and clamping the range.
    region_width = 0.0
    if context is not None:
        region = getattr(context, "region", None)
        region_width = float(getattr(region, "width", 0.0) or 0.0)

    checkbox_factor = 0.07
    name_factor = 0.30
    if region_width > 0.0:
        checkbox_target_px = 34.0
        checkbox_factor = _clamp(checkbox_target_px / region_width, 0.05, 0.08)
        remaining_factor = max(1.0 - checkbox_factor, 0.01)
        name_target_px = 180.0
        name_factor = _clamp(name_target_px / (region_width * remaining_factor), 0.24, 0.38)

    split = row.split(factor=checkbox_factor, align=True)
    checkbox_box = split.box()
    text_split = split.split(factor=name_factor, align=True)
    name_box = text_split.box()
    description_box = text_split.box()

    if _has_rna_property(prefs, prop_name):
        is_enabled = bool(getattr(prefs, prop_name, False))
        toggle_icon = 'CHECKBOX_HLT' if is_enabled else 'CHECKBOX_DEHLT'
        toggle_row = checkbox_box.row(align=True)
        toggle_row.alignment = 'LEFT'
        toggle_row.scale_y = 1.1
        toggle_op = toggle_row.operator(
            "vv_fabrica.preferences_toggle_module",
            text="",
            icon=toggle_icon,
            emboss=False,
        )
        toggle_op.module_id = module_id

        name_row = name_box.row(align=True)
        name_row.alignment = 'LEFT'
        name_row.scale_y = 1.1
        name_row.label(text=module_name, icon=module_icon)

        description_row = description_box.row(align=True)
        description_row.alignment = 'LEFT'
        description_row.scale_y = 1.1
        description_row.label(text=module_description)
    else:
        name_row = name_box.row(align=True)
        name_row.alignment = 'LEFT'
        name_row.scale_y = 1.1
        name_row.label(text=module_name, icon=module_icon)
        description_row = description_box.row(align=True)
        description_row.alignment = 'LEFT'
        description_row.scale_y = 1.1
        description_row.label(text="Property not found", icon='ERROR')


# ¦ ¦ ¦ OPERATORS
class VVFabrica_OT_preferences_save_settings(bpy.types.Operator):
    bl_idname = "vv_fabrica.preferences_save_settings"
    bl_label = "Save Settings"
    bl_description = "Save VV-FABRICA internal settings to disk"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        if save_internal_settings(context):
            self.report({"INFO"}, "[VV-FABRICA] Settings saved")
            return {"FINISHED"}
        self.report({"ERROR"}, f"[VV-FABRICA] Could not save settings: {get_last_settings_error()}")
        return {"CANCELLED"}


class VVFabrica_OT_preferences_load_settings(bpy.types.Operator):
    bl_idname = "vv_fabrica.preferences_load_settings"
    bl_label = "Load Settings"
    bl_description = "Load VV-FABRICA internal settings from disk"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        settings_path = _settings_file_path()
        if not os.path.exists(settings_path):
            self.report({"WARNING"}, f"[VV-FABRICA] No saved settings file found at: {settings_path}")
            return {"CANCELLED"}
        if load_internal_settings(context):
            self.report({"INFO"}, "[VV-FABRICA] Settings loaded")
            return {"FINISHED"}
        self.report({"ERROR"}, f"[VV-FABRICA] Could not load settings: {get_last_settings_error()}")
        return {"CANCELLED"}


class VVFabrica_OT_preferences_reset_settings(bpy.types.Operator):
    bl_idname = "vv_fabrica.preferences_reset_settings"
    bl_label = "Reset Settings"
    bl_description = "Reset VV-FABRICA settings to defaults and save them"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        if reset_internal_settings_to_defaults(context):
            self.report({"INFO"}, "[VV-FABRICA] Settings reset to defaults")
            return {"FINISHED"}
        self.report({"ERROR"}, f"[VV-FABRICA] Could not reset settings: {get_last_settings_error()}")
        return {"CANCELLED"}


class VVFabrica_OT_preferences_toggle_module(bpy.types.Operator):
    bl_idname = "vv_fabrica.preferences_toggle_module"
    bl_label = "Toggle Module"
    bl_description = "Enable or disable a VV-FABRICA module"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    module_id: bpy.props.StringProperty(name="Module ID")

    def execute(self, context):
        prefs = get_addon_preferences(context)
        if prefs is None:
            self.report({"ERROR"}, f"[VV-FABRICA] Could not toggle module: {get_last_settings_error()}")
            return {"CANCELLED"}

        prop_name = f"module_{self.module_id}"
        if not _has_rna_property(prefs, prop_name):
            self.report({"ERROR"}, f"[VV-FABRICA] Module toggle property not found: {prop_name}")
            return {"CANCELLED"}

        currently_enabled = bool(getattr(prefs, prop_name, False))
        try:
            setattr(prefs, prop_name, not currently_enabled)
        except Exception as exc:
            self.report({"ERROR"}, f"[VV-FABRICA] Could not toggle module '{self.module_id}': {exc}")
            return {"CANCELLED"}

        new_state = "enabled" if not currently_enabled else "disabled"
        self.report({"INFO"}, f"[VV-FABRICA] Module {self.module_id} {new_state}")
        return {"FINISHED"}


# ¦ ¦ ¦ PREFERENCES CLASS
class VVFabricaPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    auto_save_addon_settings: bpy.props.BoolProperty(
        name="Auto-Save VV-FABRICA Settings",
        description=(
            "Automatically save VV-FABRICA internal settings to disk when settings change"
        ),
        default=True,
        update=_settings_update,
    )

    global_settings_tab: bpy.props.EnumProperty(
        name="FABRICA Tab",
        description="Global settings panel tab",
        items=[
            ("MODULES", "Modules", "Module settings", "PREFERENCES", 0),
            ("HELP", "Help", "Help links", "QUESTION", 1),
            ("INFO", "Info", "Version and status", "INFO", 2),
        ],
        default="MODULES",
        update=_settings_update,
    )

    global_settings_show_module_settings: bpy.props.BoolProperty(
        name="Show Module Settings",
        description="Expand/collapse Module Settings section",
        default=True,
        update=_settings_update,
    )

    global_settings_show_module_settings_details: bpy.props.BoolProperty(
        name="Show Selected Module Settings",
        description="Expand/collapse selected module settings details",
        default=True,
        update=_settings_update,
    )

    global_settings_show_quick_help: bpy.props.BoolProperty(
        name="Show Quick Help",
        description="Expand/collapse quick help links",
        default=True,
        update=_settings_update,
    )

    global_settings_show_platform_links: bpy.props.BoolProperty(
        name="Show Platform Links",
        description="Expand/collapse platform links",
        default=True,
        update=_settings_update,
    )

    global_settings_module_settings_target: bpy.props.EnumProperty(
        name="Module Settings Target",
        description="Choose which enabled module settings to display",
        items=_module_settings_items,
        update=_settings_update,
    )

    cameras_dof_aperture_fstop: bpy.props.FloatProperty(
        name="DoF Aperture F-Stop",
        description="Default Depth of Field aperture f-stop for new Viewport Cameras",
        default=1.2,
        min=0.1,
        soft_max=64.0,
        precision=2,
        update=_settings_update,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        all_modules = registry.get_all_modules()
        enabled_modules = []
        disabled_modules = []
        for module_info in all_modules:
            module_id = module_info.get("id", "")
            if not module_id:
                continue
            prop_name = f"module_{module_id}"
            if getattr(self, prop_name, False):
                enabled_modules.append(module_info)
            else:
                disabled_modules.append(module_info)

        # Active Modules
        box = layout.box()
        box.use_property_split = False
        box.use_property_decorate = False
        box.label(text="Active Modules", icon='PACKAGE')
        box.label(text="Uncheck a module to unload it.")

        if not enabled_modules:
            row = box.row()
            row.label(text="No active modules", icon='INFO')

        for module_info in enabled_modules:
            _draw_module_toggle_row(box, module_info, self, context)

        # Inactive Modules
        box = layout.box()
        box.use_property_split = False
        box.use_property_decorate = False
        box.label(text="Inactive Modules", icon='TIME')
        box.label(text="Check a module to load it.")

        if not disabled_modules:
            row = box.row()
            row.label(text="No inactive modules", icon='CHECKMARK')

        for module_info in disabled_modules:
            _draw_module_toggle_row(box, module_info, self, context)

        # Module Settings (parity with Global Settings panel behavior)
        settings_box = layout.box()
        modules_open = _draw_disclosure_toggle(
            settings_box,
            self,
            "global_settings_show_module_settings",
            "Module Settings",
        )
        if modules_open:
            module_info_by_id = _enabled_module_info_by_id()
            enabled_module_ids = list(module_info_by_id.keys())

            if enabled_module_ids and hasattr(self, "global_settings_module_settings_target"):
                selected_module_id = getattr(self, "global_settings_module_settings_target", "")
                if selected_module_id not in enabled_module_ids:
                    selected_module_id = enabled_module_ids[0]
                    try:
                        self.global_settings_module_settings_target = selected_module_id
                    except Exception as exc:
                        print(f"[VV-FABRICA:preferences] Could not update module settings target: {exc}")

                selector_box = settings_box.box()
                selector_row = selector_box.row(align=True)
                selector_row.alignment = 'CENTER'
                selector_row.prop(self, "global_settings_module_settings_target", expand=True, icon_only=True)
            else:
                selected_module_id = "none"
                empty_box = settings_box.box()
                empty_box.label(text="No enabled modules with settings", icon='INFO')

            module_details_box = settings_box.box()
            if selected_module_id == "cameras":
                details_open = _draw_disclosure_toggle(
                    module_details_box,
                    self,
                    "global_settings_show_module_settings_details",
                    "Viewport Cameras",
                )
                if details_open:
                    details_content_box = module_details_box.box()
                    details_content_box.prop(self, "cameras_dof_aperture_fstop", text="DoF Aperture F-Stop")
            elif selected_module_id in module_info_by_id:
                module_name = module_info_by_id[selected_module_id].get("name", selected_module_id)
                details_open = _draw_disclosure_toggle(
                    module_details_box,
                    self,
                    "global_settings_show_module_settings_details",
                    module_name,
                )
                if details_open:
                    details_content_box = module_details_box.box()
                    details_content_box.label(text=f"{module_name}: no settings exposed yet", icon='INFO')
            else:
                module_details_box.label(text="Enable a module to configure its settings", icon='INFO')

        persistence_box = layout.box()
        persistence_box.label(text="Persistence (Internal File)", icon='PREFERENCES')
        persistence_box.prop(self, "auto_save_addon_settings")
        button_row = persistence_box.row(align=True)
        button_row.operator("vv_fabrica.preferences_save_settings", icon='FILE_TICK')
        button_row.operator("vv_fabrica.preferences_load_settings", icon='FILE_REFRESH')
        button_row.operator("vv_fabrica.preferences_reset_settings", icon='LOOP_BACK')
        persistence_box.label(text=f"File: {_settings_file_path()}")
        persistence_box.label(
            text="Settings are stored in VV-FABRICA's internal JSON file."
        )
        persistence_box.label(
            text="This does not require Blender's global Auto-Save Preferences."
        )


def register_module_properties():
    """DYNAMICALLY ADD `BoolProperty` FOR EACH DISCOVERED MODULE TO PREFERENCES.

    MUST BE CALLED AFTER `registry.discover_modules()` AND BEFORE
    REGISTERING `VVFabricaPreferences`.
    """
    annotations = getattr(VVFabricaPreferences, "__annotations__", None)
    if annotations is None:
        annotations = {}
        setattr(VVFabricaPreferences, "__annotations__", annotations)

    for module_info in registry.get_all_modules():
        module_id = module_info["id"]
        prop_name = f"module_{module_id}"
        default = module_info.get("default_enabled", True)

        prop = bpy.props.BoolProperty(
            name=module_info["name"],
            description=f"Enable/disable the {module_info['name']} module",
            default=default,
            update=_make_module_toggle_update(module_id),
        )

        annotations[prop_name] = prop


# ¦ ¦ ¦ REGISTRATION
classes = [
    VVFabrica_OT_preferences_save_settings,
    VVFabrica_OT_preferences_load_settings,
    VVFabrica_OT_preferences_reset_settings,
    VVFabrica_OT_preferences_toggle_module,
    VVFabricaPreferences,
]


def register():
    register_module_properties()
    for cls in classes:
        bpy.utils.register_class(cls)
    # ¦ BEST-EFFORT RESTORE OF INTERNAL SETTINGS BEFORE MODULE ENABLE SYNC RUNS.
    if not load_internal_settings(sync_modules=False):
        print("[VV-FABRICA:preferences] No persisted settings loaded (using defaults)")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
