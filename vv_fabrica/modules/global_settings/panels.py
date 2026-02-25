import os
import json

import bpy
import bpy.utils.previews
from bpy.types import Panel
from ... import ui_conventions as ui
from ... import registry
from ... import preferences as addon_preferences

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


# ¦ ¦ ¦ HELPERS
_DOCS_LINKS = [
    ("Release Repository", "https://github.com/Vianvolaeus/VV-FABRICA"),
    ("Bug Reports", "https://github.com/Vianvolaeus/VV-FABRICA/issues"),
]

_PLATFORM_PLACEHOLDER_LINKS = [
    ("Platform 1", "https://github.com/Vianvolaeus/VV-FABRICA"),
    ("Platform 2", "https://github.com/Vianvolaeus/VV-FABRICA"),
    ("Platform 3", "https://github.com/Vianvolaeus/VV-FABRICA"),
]

_LOGO_FILE_NAME = "FABRICA-LOGO.png"
_LOGO_PREVIEW_KEY = "fabrica_logo_banner"
_AUTHOR_ICON_FILE_NAME = "VV-ICON.png"
_AUTHOR_ICON_PREVIEW_KEY = "fabrica_author_vv_icon"
_HEADER_SPLIT_FACTOR = 0.50
_LOGO_SCALE = 5.2
# ¦ KEEP RIGHT-SIDE ROWS VISUALLY BALANCED WITH THE SQUARE LOGO PREVIEW CELL.
_RIGHT_CELL_SCALE_Y = max(1.10, round((_LOGO_SCALE / 4.0) - 0.04, 2))
_AUTHOR_URL = "https://vianvolae.us"
_logo_preview_collection = None
_logo_icon_id = 0
_logo_load_failed = False
_logo_mtime = None
_author_icon_id = 0
_author_icon_load_failed = False
_manifest_version = "?"
_manifest_package_id = "vv_fabrica"
_manifest_mtime = None
_remote_index_cache = {}


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


def _addon_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def _logo_path():
    return os.path.join(_addon_root(), "assets", "icons", _LOGO_FILE_NAME)


def _manifest_path():
    return os.path.join(_addon_root(), "blender_manifest.toml")


def _author_icon_path():
    return os.path.join(_addon_root(), "assets", "icons", _AUTHOR_ICON_FILE_NAME)


def _read_manifest_package_and_version(manifest_path):
    if not os.path.exists(manifest_path):
        return "", ""

    try:
        package_id = ""
        version = ""
        if tomllib is not None:
            with open(manifest_path, "rb") as manifest_file:
                manifest_data = tomllib.load(manifest_file)
                package_id = str(manifest_data.get("id", "")).strip()
                version = str(manifest_data.get("version", "")).strip()
        else:
            with open(manifest_path, "r", encoding="utf-8") as manifest_file:
                for line in manifest_file:
                    stripped = line.strip()
                    if stripped.startswith("id"):
                        _, value = stripped.split("=", 1)
                        package_id = value.strip().strip('"').strip("'")
                    elif stripped.startswith("version"):
                        _, value = stripped.split("=", 1)
                        version = value.strip().strip('"').strip("'")
        return package_id, version
    except Exception as exc:
        print(f"[VV-FABRICA:global_settings] Could not read manifest '{manifest_path}': {exc}")
        return "", ""


def _read_remote_repo_versions(index_path):
    if not os.path.exists(index_path):
        return None

    try:
        current_mtime = os.path.getmtime(index_path)
        cached = _remote_index_cache.get(index_path)
        if cached is not None and cached[0] == current_mtime:
            return cached[1]

        with open(index_path, "r", encoding="utf-8") as index_file:
            index_data = json.load(index_file)

        version_map = {}
        for item in index_data.get("data", []):
            if not isinstance(item, dict):
                continue
            package_id = item.get("id")
            version = item.get("version")
            if isinstance(package_id, str) and package_id:
                version_map[package_id] = str(version) if version is not None else ""

        _remote_index_cache[index_path] = (current_mtime, version_map)
        return version_map
    except Exception as exc:
        print(f"[VV-FABRICA:global_settings] Could not read remote index '{index_path}': {exc}")
        _remote_index_cache.pop(index_path, None)
        return None


def _clear_logo_preview():
    global _logo_preview_collection, _logo_icon_id, _logo_load_failed, _logo_mtime
    global _author_icon_id, _author_icon_load_failed
    if _logo_preview_collection is not None:
        bpy.utils.previews.remove(_logo_preview_collection)
    _logo_preview_collection = None
    _logo_icon_id = 0
    _logo_load_failed = False
    _logo_mtime = None
    _author_icon_id = 0
    _author_icon_load_failed = False


def _get_logo_icon_id():
    global _logo_preview_collection, _logo_icon_id, _logo_load_failed, _logo_mtime

    icon_path = _logo_path()
    if not os.path.exists(icon_path):
        _clear_logo_preview()
        return 0

    try:
        current_mtime = os.path.getmtime(icon_path)
        if _logo_icon_id and _logo_mtime == current_mtime and not _logo_load_failed:
            return _logo_icon_id

        # Source file changed (or first load): rebuild preview so re-exports show up.
        if _logo_preview_collection is not None:
            bpy.utils.previews.remove(_logo_preview_collection)
            _logo_preview_collection = None

        if _logo_preview_collection is None:
            _logo_preview_collection = bpy.utils.previews.new()
        thumb = _logo_preview_collection.load(_LOGO_PREVIEW_KEY, icon_path, 'IMAGE')
        _logo_icon_id = thumb.icon_id
        _logo_mtime = current_mtime
        _logo_load_failed = False
        return _logo_icon_id
    except Exception as exc:
        _logo_load_failed = True
        _logo_icon_id = 0
        print(f"[VV-FABRICA:global_settings] Could not load FABRICA logo: {exc}")
        return 0


def _get_author_icon_id():
    global _logo_preview_collection, _author_icon_id, _author_icon_load_failed

    icon_path = _author_icon_path()
    if not os.path.exists(icon_path):
        _author_icon_id = 0
        return 0

    if _logo_preview_collection is not None and _author_icon_id and not _author_icon_load_failed:
        return _author_icon_id

    try:
        if _logo_preview_collection is None:
            _logo_preview_collection = bpy.utils.previews.new()
        if _AUTHOR_ICON_PREVIEW_KEY not in _logo_preview_collection:
            thumb = _logo_preview_collection.load(_AUTHOR_ICON_PREVIEW_KEY, icon_path, 'IMAGE')
        else:
            thumb = _logo_preview_collection[_AUTHOR_ICON_PREVIEW_KEY]
        _author_icon_id = thumb.icon_id
        _author_icon_load_failed = False
        return _author_icon_id
    except Exception as exc:
        _author_icon_load_failed = True
        _author_icon_id = 0
        print(f"[VV-FABRICA:global_settings] Could not load author icon: {exc}")
        return 0


def _get_extension_version():
    global _manifest_version, _manifest_package_id, _manifest_mtime

    manifest_path = _manifest_path()
    if not os.path.exists(manifest_path):
        return "?"

    try:
        current_mtime = os.path.getmtime(manifest_path)
        if _manifest_mtime == current_mtime:
            return _manifest_version

        parsed_package_id, parsed_version = _read_manifest_package_and_version(manifest_path)
        if not parsed_package_id:
            parsed_package_id = "vv_fabrica"
        if not parsed_version:
            parsed_version = "?"

        _manifest_version = parsed_version or "?"
        _manifest_package_id = parsed_package_id
        _manifest_mtime = current_mtime
        return _manifest_version
    except Exception as exc:
        print(f"[VV-FABRICA:global_settings] Could not read manifest version: {exc}")
        return "?"


def _get_extension_package_id():
    _get_extension_version()
    return _manifest_package_id or "vv_fabrica"


def _get_extension_update_status(context):
    package_id = _get_extension_package_id()
    found_local_install = False
    found_remote_status = False

    try:
        repos = context.preferences.extensions.repos
    except Exception:
        repos = []

    for repo in repos:
        try:
            if not getattr(repo, "enabled", False):
                continue

            repo_directory = getattr(repo, "directory", "")
            if not repo_directory:
                continue

            local_manifest_path = os.path.join(repo_directory, package_id, "blender_manifest.toml")
            local_package_id, local_version = _read_manifest_package_and_version(local_manifest_path)
            if not local_version:
                continue
            if local_package_id and local_package_id != package_id:
                continue

            found_local_install = True

            if not getattr(repo, "use_remote_url", False):
                continue
            if not getattr(repo, "remote_url", ""):
                continue

            index_path = os.path.join(repo_directory, ".blender_ext", "index.json")
            version_map = _read_remote_repo_versions(index_path)
            if version_map is None:
                continue

            remote_version = version_map.get(package_id)
            if not remote_version:
                continue

            found_remote_status = True
            if str(remote_version) != str(local_version):
                return ("Out of date", 'ERROR')
        except Exception as exc:
            print(f"[VV-FABRICA:global_settings] Could not evaluate FABRICA update status: {exc}")
            continue

    if found_remote_status:
        return ("Up to date", 'CHECKMARK')
    if found_local_install:
        return ("No remote status", 'QUESTION')
        return ("Status unavailable", 'QUESTION')


# ¦ ¦ ¦ PANELS
class VV_FABRICA_PT_global_settings(Panel):
    bl_idname = "VV_FABRICA_PT_global_settings"
    bl_label = "FABRICA"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VV-FABRICA"
    bl_order = -1000

    def draw_header(self, context):
        self.layout.label(icon='PREFERENCES')

    @classmethod
    def unregister(cls):
        _clear_logo_preview()

    def draw(self, context):
        layout = self.layout
        prefs = addon_preferences.get_addon_preferences(context)

        group_box = ui.section_box(layout)
        split = group_box.split(factor=_HEADER_SPLIT_FACTOR, align=True)
        logo_box = split.box()
        right_box = split.box()

        logo_icon_id = _get_logo_icon_id()
        logo_row = logo_box.row(align=True)
        logo_row.alignment = 'CENTER'
        if logo_icon_id:
            logo_row.template_icon(icon_value=logo_icon_id, scale=_LOGO_SCALE)
        else:
            logo_row.label(text="FABRICA", icon='PREFERENCES')

        tabs_col = right_box.column(align=True)

        tabs_cell = tabs_col.box()
        tab_row = tabs_cell.row(align=True)
        tab_row.alignment = 'CENTER'
        tab_row.scale_y = _RIGHT_CELL_SCALE_Y
        if prefs and hasattr(prefs, "global_settings_tab"):
            tab_row.prop(prefs, "global_settings_tab", expand=True, icon_only=True)
        else:
            tab_row.label(text="Tabs", icon='PREFERENCES')

        version_cell = tabs_col.box()
        version_row = version_cell.row(align=True)
        version_row.alignment = 'CENTER'
        version_row.scale_y = _RIGHT_CELL_SCALE_Y
        version_row.label(text=f"v{_get_extension_version()}")

        update_text, update_icon = _get_extension_update_status(context)
        update_cell = tabs_col.box()
        update_row = update_cell.row(align=True)
        update_row.alignment = 'CENTER'
        update_row.scale_y = _RIGHT_CELL_SCALE_Y
        update_row.label(text=update_text, icon=update_icon)

        author_cell = group_box.box()
        author_row = author_cell.row(align=True)
        author_row.alignment = 'CENTER'
        author_icon_id = _get_author_icon_id()
        if author_icon_id:
            author_op = author_row.operator(
                "vv_fabrica.global_settings_open_url",
                text="by VIANVOLAEUS",
                icon_value=author_icon_id,
                emboss=False,
            )
        else:
            author_op = author_row.operator(
                "vv_fabrica.global_settings_open_url",
                text="by VIANVOLAEUS",
                icon='URL',
                emboss=False,
            )
        author_op.url = _AUTHOR_URL

        if prefs is None:
            fallback_box = group_box.box()
            fallback_box.label(text="Global settings unavailable: addon preferences not found.", icon='ERROR')
            return

        active_tab = getattr(prefs, "global_settings_tab", "MODULES")
        if active_tab == "MODULES":
            modules_box = group_box.box()
            modules_open = _draw_disclosure_toggle(
                modules_box,
                prefs,
                "global_settings_show_module_settings",
                "Module Settings",
            )
            if not modules_open:
                return

            module_info_by_id = _enabled_module_info_by_id()
            enabled_module_ids = list(module_info_by_id.keys())

            if enabled_module_ids and hasattr(prefs, "global_settings_module_settings_target"):
                selected_module_id = getattr(prefs, "global_settings_module_settings_target", "")
                if selected_module_id not in enabled_module_ids:
                    selected_module_id = enabled_module_ids[0]
                    try:
                        prefs.global_settings_module_settings_target = selected_module_id
                    except Exception as exc:
                        print(
                            "[VV-FABRICA:global_settings] Could not update "
                            f"module settings target: {exc}"
                        )

                selector_box = modules_box.box()
                selector_row = selector_box.row(align=True)
                selector_row.alignment = 'CENTER'
                selector_row.prop(prefs, "global_settings_module_settings_target", expand=True, icon_only=True)
            else:
                selected_module_id = "none"
                selector_box = modules_box.box()
                selector_box.label(text="No enabled modules with settings", icon='INFO')

            settings_box = modules_box.box()
            if selected_module_id == "cameras":
                details_open = _draw_disclosure_toggle(
                    settings_box,
                    prefs,
                    "global_settings_show_module_settings_details",
                    "Viewport Cameras",
                )
                if details_open:
                    details_box = settings_box.box()
                    if hasattr(prefs, "cameras_dof_aperture_fstop"):
                        details_box.prop(prefs, "cameras_dof_aperture_fstop", text="DoF Aperture F-Stop")
                    else:
                        details_box.label(text="Cameras setting unavailable", icon='ERROR')
            elif selected_module_id in module_info_by_id:
                module_name = module_info_by_id[selected_module_id].get("name", selected_module_id)
                details_open = _draw_disclosure_toggle(
                    settings_box,
                    prefs,
                    "global_settings_show_module_settings_details",
                    module_name,
                )
                if details_open:
                    details_box = settings_box.box()
                    details_box.label(text=f"{module_name}: no settings exposed yet", icon='INFO')
            else:
                settings_box.label(text="Enable a module to configure its settings", icon='INFO')

        elif active_tab == "HELP":
            help_box = group_box.box()
            if _draw_disclosure_toggle(help_box, prefs, "global_settings_show_quick_help", "Quick Links"):
                links_box = help_box.box()
                for link_text, link_url in _DOCS_LINKS:
                    op = links_box.operator("vv_fabrica.global_settings_open_url", text=link_text, icon='URL')
                    op.url = link_url

            if _draw_disclosure_toggle(help_box, prefs, "global_settings_show_platform_links", "Released On"):
                platform_box = help_box.box()
                platform_row = platform_box.row(align=True)
                for platform_text, platform_url in _PLATFORM_PLACEHOLDER_LINKS:
                    op = platform_row.operator("vv_fabrica.global_settings_open_url", text=platform_text, icon='URL')
                    op.url = platform_url

        elif active_tab == "INFO":
            info_box = group_box.box()
            info_box.label(text="VV-FABRICA", icon='INFO')
            info_box.label(text="Global control panel is toggleable as its own module.")


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_PT_global_settings,
]
