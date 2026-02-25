import bpy
import json
from bpy.types import Operator


def analyze_selected_objects():
    """COLLECT STATISTICS FROM SELECTED OBJECTS. USES `bpy` — LIVES IN OPERATORS, NOT CORE."""
    statistics = {
        'triangles': 0,
        'texture_memory': 0,
        'skinned_meshes': 0,
        'meshes': 0,
        'material_slots': 0,
        'bones': 0,
    }

    texture_memory_usage = {}

    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            depsgraph = bpy.context.evaluated_depsgraph_get()
            temp_obj = obj.evaluated_get(depsgraph)
            temp_mesh = bpy.data.meshes.new_from_object(temp_obj)

            triangles = sum(len(p.vertices) - 2 for p in temp_mesh.polygons)
            statistics['triangles'] += triangles

            bpy.data.meshes.remove(temp_mesh)
            statistics['material_slots'] += len(obj.material_slots)

            if any(mod for mod in obj.modifiers if mod.type == 'ARMATURE'):
                statistics['skinned_meshes'] += 1
            else:
                statistics['meshes'] += 1

            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    for node in mat_slot.material.node_tree.nodes:
                        if node.type == "TEX_IMAGE":
                            img = node.image
                            if img:
                                if img not in texture_memory_usage:
                                    texture_memory_usage[img] = img.size[0] * img.size[1] * 4 // 4

        elif obj.type == 'ARMATURE':
            statistics['bones'] += len(obj.data.bones)

    statistics['texture_memory'] = sum(texture_memory_usage.values())
    return statistics


class VVFabrica_OT_vrc_analysis_analyse(Operator):
    bl_idname = "vv_fabrica.vrc_analysis_analyse"
    bl_label = "VRC Analyse"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        if not context.selected_objects:
            self.report({"WARNING"}, "[VV-FABRICA] No objects selected for analysis")
            return {"CANCELLED"}

        context.area.tag_redraw()
        result = analyze_selected_objects()
        context.scene["VRC_Analysis_Results"] = json.dumps(result)
        context.area.tag_redraw()
        self.report({"INFO"}, "[VV-FABRICA] VRC analysis complete")
        return {"FINISHED"}


classes = [
    VVFabrica_OT_vrc_analysis_analyse,
]
