import bpy


# ¦ ¦ ¦ MENUS
class VV_FABRICA_MT_global_settings(bpy.types.Menu):
    bl_label = "FABRICA"
    bl_idname = "VV_FABRICA_MT_global_settings"

    def draw(self, context):
        layout = self.layout
        docs_op = layout.operator("vv_fabrica.global_settings_open_url", text="Release Repository", icon='URL')
        docs_op.url = "https://github.com/Vianvolaeus/VV-FABRICA"
        issues_op = layout.operator("vv_fabrica.global_settings_open_url", text="Bug Reports", icon='URL')
        issues_op.url = "https://github.com/Vianvolaeus/VV-FABRICA/issues"


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_MT_global_settings,
]
