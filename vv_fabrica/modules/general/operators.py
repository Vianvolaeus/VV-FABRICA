import bpy
from bpy.types import Operator


# ¦ ¦ ¦ HELPERS

def rename_data_blocks(obj):
    data_block = getattr(obj, "data", None)
    if data_block is None:
        return False
    data_block.name = obj.name
    return True


# ¦ ¦ ¦ OPERATORS: DATA MANAGEMENT

class VVFabrica_OT_general_rename_data_blocks(Operator):
    bl_idname = "vv_fabrica.general_rename_data_blocks"
    bl_label = "Object Name Data Block Rename"
    bl_description = "Rename the data blocks of the selected objects based on their Object's name"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        if not context.selected_objects:
            self.report({"ERROR"}, "[VV-FABRICA] No selected objects")
            return {"CANCELLED"}

        renamed_count = 0
        skipped_count = 0
        failed = []
        for obj in context.selected_objects:
            try:
                if rename_data_blocks(obj):
                    renamed_count += 1
                else:
                    skipped_count += 1
            except Exception as exc:
                failed.append(obj.name)
                print(f"[VV-FABRICA:general] Failed datablock rename for '{obj.name}': {exc}")

        if failed:
            self.report(
                {"WARNING"},
                f"[VV-FABRICA] Renamed data blocks on {renamed_count} object(s); failed on {len(failed)} object(s)",
            )
        elif renamed_count == 0:
            self.report({"WARNING"}, "[VV-FABRICA] No selected objects had a datablock to rename")
        elif skipped_count:
            self.report(
                {"INFO"},
                f"[VV-FABRICA] Renamed data blocks on {renamed_count} object(s); skipped {skipped_count} object(s)",
            )
        else:
            self.report({"INFO"}, f"[VV-FABRICA] Renamed data blocks on {renamed_count} object(s)")
        return {"FINISHED"}


# ¦ ¦ ¦ OPERATORS: VIEWPORT

class VVFabrica_OT_general_vp_wireframe(Operator):
    bl_idname = "vv_fabrica.general_vp_wireframe"
    bl_label = "Viewport Wireframe"
    bl_description = "Toggles global wireframe in the viewport."
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        toggled_areas = 0
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_wireframes = not space.overlay.show_wireframes
                        toggled_areas += 1
        self.report({"INFO"}, f"[VV-FABRICA] Toggled viewport wireframe in {toggled_areas} 3D view area(s)")
        return {"FINISHED"}


# ¦ ¦ ¦ REGISTRATION

classes = [
    VVFabrica_OT_general_rename_data_blocks,
    VVFabrica_OT_general_vp_wireframe,
]
