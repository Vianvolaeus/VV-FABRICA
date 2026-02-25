import bpy
from bpy.types import Panel
from ... import ui_conventions as ui


# ¦ ¦ ¦ PANELS
class VV_FABRICA_PT_cameras(Panel):
    bl_idname = "VV_FABRICA_PT_cameras"
    bl_label = "Cameras"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VV-FABRICA"

    def draw_header(self, context):
        self.layout.label(icon='CAMERA_DATA')

    def draw(self, context):
        layout = self.layout

        cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
        active_cam = context.scene.camera
        group_box = ui.section_box(layout)
        ui.section_box(group_box, title="Viewport Cameras", icon='CAMERA_DATA')

        data_box = group_box.box()
        active_box = data_box.box()
        if active_cam:
            active_box.label(text=f"Active: {active_cam.name}")
        else:
            active_box.label(text="No active camera")
        count_box = data_box.box()
        count_box.label(text=f"Scene cameras: {len(cameras)}")

        actions_box = group_box.box()
        ui.draw_primary_operator(
            actions_box,
            "vv_fabrica.cameras_add_viewport_camera",
            icon='CAMERA_DATA',
        )

        row = actions_box.row(align=True)
        row.enabled = len(cameras) > 0
        row.operator("vv_fabrica.cameras_switch_previous", text="Prev", icon='TRIA_LEFT')
        row.operator("vv_fabrica.cameras_switch_next", text="Next >", icon='NONE')


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_PT_cameras,
]
