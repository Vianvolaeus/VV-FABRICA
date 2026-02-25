import bpy


# ¦ ¦ ¦ MENUS
class VV_FABRICA_MT_vrc_analysis(bpy.types.Menu):
    bl_label = "VRC Analysis"
    bl_idname = "VV_FABRICA_MT_vrc_analysis"

    def draw(self, context):
        layout = self.layout
        layout.operator("vv_fabrica.vrc_analysis_analyse", icon='VIEWZOOM')


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_MT_vrc_analysis,
]
