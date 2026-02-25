import bpy
from bpy.types import Operator


# ¦ ¦ ¦ HELPERS

_DEFAULT_URL = "https://github.com/Vianvolaeus/VV-FABRICA"


# ¦ ¦ ¦ OPERATORS: HELP

class VVFabrica_OT_global_settings_open_url(Operator):
    bl_idname = "vv_fabrica.global_settings_open_url"
    bl_label = "Open URL"
    bl_description = "Open a URL in your web browser"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    url: bpy.props.StringProperty(
        name="URL",
        description="URL to open",
        default=_DEFAULT_URL,
    )

    def execute(self, context):
        if not self.url:
            self.report({"ERROR"}, "[VV-FABRICA] No URL was provided")
            return {"CANCELLED"}
        try:
            bpy.ops.wm.url_open(url=self.url)
            self.report({"INFO"}, "[VV-FABRICA] Opened link")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, f"[VV-FABRICA] Could not open URL: {exc}")
            return {"CANCELLED"}


# ¦ ¦ ¦ REGISTRATION

classes = [
    VVFabrica_OT_global_settings_open_url,
]
