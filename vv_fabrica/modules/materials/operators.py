import bpy
from bpy.types import Operator


# ¦ ¦ ¦ HELPERS


# ¦ ¦ ¦ OPERATORS: CLEANUP

class VVFabrica_OT_materials_remove_unused(Operator):
    bl_idname = "vv_fabrica.materials_remove_unused"
    bl_label = "Remove Unused Materials"
    bl_description = "Remove materials that aren't being used by any vertex on objects."
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    warning_shown = False

    def remove_unused_materials(self, obj):
        used_materials = set()
        for poly in obj.data.polygons:
            used_materials.add(poly.material_index)

        removed_count = 0
        for i, mat_slot in reversed(list(enumerate(obj.material_slots))):
            if i not in used_materials:
                obj.active_material_index = i
                with bpy.context.temp_override(object=obj):
                    bpy.ops.object.material_slot_remove()
                removed_count += 1
        return removed_count

    def execute(self, context):
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not mesh_objects:
            self.report({"WARNING"}, "[VV-FABRICA] No mesh objects selected")
            return {"CANCELLED"}

        total_removed = 0
        for obj in mesh_objects:
            total_removed += self.remove_unused_materials(obj)

        if total_removed == 0:
            self.report({"INFO"}, "[VV-FABRICA] No unused materials to remove")
        else:
            self.report({"INFO"}, f"[VV-FABRICA] {total_removed} unused material(s) removed")
        return {"FINISHED"}

    def invoke(self, context, event):
        self.warning_shown = True
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        if self.warning_shown:
            layout = self.layout
            col = layout.column()
            col.label(text="Removing materials that aren't being used by any vertex on objects.")
            col.label(text="If you would like to retain the materials in the Blender file,")
            col.label(text="consider adding a Fake User (Shield Icon) to them first.")


# ¦ ¦ ¦ OPERATORS: TEXTURES

class VVFabrica_OT_materials_reload_textures(Operator):
    bl_idname = "vv_fabrica.materials_reload_textures"
    bl_label = "Reload Textures of Selected"
    bl_description = "Reload all textures in materials of the selected objects."
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        if not context.selected_objects:
            self.report({"WARNING"}, "[VV-FABRICA] No objects selected")
            return {"CANCELLED"}

        reloaded_count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            for mat_slot in obj.material_slots:
                if mat_slot.material is None:
                    continue
                if mat_slot.material.node_tree is None:
                    continue
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image is not None:
                        node.image.reload()
                        reloaded_count += 1

        if reloaded_count == 0:
            self.report({"WARNING"}, "[VV-FABRICA] No textures found to reload on selected objects")
        else:
            self.report({"INFO"}, f"[VV-FABRICA] {reloaded_count} texture(s) reloaded")
        return {"FINISHED"}


# ¦ ¦ ¦ REGISTRATION

classes = [
    VVFabrica_OT_materials_remove_unused,
    VVFabrica_OT_materials_reload_textures,
]
