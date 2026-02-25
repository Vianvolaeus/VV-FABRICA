import bpy


# ¦ ¦ ¦ MENUS
class VV_FABRICA_MT_mesh_ops(bpy.types.Menu):
    bl_label = "Mesh Operators"
    bl_idname = "VV_FABRICA_MT_mesh_ops"

    def draw(self, context):
        layout = self.layout
        layout.operator("vv_fabrica.mesh_ops_vis_geo_shape_key", icon='SHAPEKEY_DATA')
        layout.operator("vv_fabrica.mesh_ops_toggle_modifiers", icon='HIDE_OFF')


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_MT_mesh_ops,
]
