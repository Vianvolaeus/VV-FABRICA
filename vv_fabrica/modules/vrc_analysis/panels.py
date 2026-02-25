import bpy
import json
import re
from bpy.types import Panel
from .core.analysis import performance_rank, performance_warning
from ... import ui_conventions as ui


# ¦ ¦ ¦ HELPERS
# ¦ RANK NAME TO PROGRESS FACTOR (0.0 = WORST, 1.0 = BEST).
_RANK_FACTORS = {
    "Excellent": 1.0,
    "Good": 0.75,
    "Medium": 0.5,
    "Poor": 0.25,
    "Very Poor": 0.05,
}


def _format_bytes(byte_count):
    """FORMAT BYTE COUNT AS HUMAN-READABLE MB STRING."""
    return f"{byte_count / (1024 * 1024):.2f} MB"


def _format_number(n):
    """FORMAT INTEGER WITH THOUSANDS SEPARATORS."""
    return f"{n:,}"


# ¦ ¦ ¦ PANELS
class VV_FABRICA_PT_vrc_analysis(Panel):
    bl_idname = "VV_FABRICA_PT_vrc_analysis"
    bl_label = "VRC Analysis"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VV-FABRICA"

    def draw_header(self, context):
        self.layout.label(icon='GRAPH')

    def draw(self, context):
        layout = self.layout

        group_box = ui.section_box(layout)

        # ¦ PRIMARY ACTION AT TOP
        ui.draw_primary_operator(
            group_box,
            "vv_fabrica.vrc_analysis_analyse",
            icon='VIEWZOOM'
        )

        results = None
        if "VRC_Analysis_Results" in context.scene:
            results_str = context.scene["VRC_Analysis_Results"]
            results = json.loads(results_str)

        if results:
            # ¦ PERFORMANCE RANK WITH PROGRESS BAR
            rank = performance_rank(results)
            factor = _RANK_FACTORS.get(rank, 0.0)

            results_section = ui.section_box(group_box, title="Results", icon='INFO')

            rank_box = results_section.box()
            rank_box.progress(factor=factor, type='BAR', text=f"Performance Rank: {rank}")

            # ¦ FORMATTED STATISTICS
            stats_box = results_section.box()
            col = stats_box.column(align=True)
            col.label(text=f"Polygons (Tris): {_format_number(results['triangles'])} / 70,000")
            col.label(text=f"Texture Memory: {_format_bytes(results['texture_memory'])}")
            col.label(text=f"Skinned Meshes: {results['skinned_meshes']}")
            col.label(text=f"Meshes: {results['meshes']}")
            col.label(text=f"Material Slots: {results['material_slots']}")
            col.label(text=f"Bones: {_format_number(results['bones'])}")

            # ¦ WARNINGS
            warnings = performance_warning(results)
            if warnings:
                warnings_section = ui.section_box(group_box, title="Warnings", icon='ERROR')
                for warning in warnings:
                    warning_box = ui.section_box(warnings_section, alert=True)
                    lines = re.split(r'(?<=[.!,] )', warning)
                    for line in lines:
                        if line:
                            warning_box.label(text=line)
        else:
            info_box = group_box.box()
            info_box.enabled = False
            info_box.label(text="No analysis data available", icon='INFO')

            alert_box = ui.section_box(group_box, alert=True)
            alert_box.label(text="First analysis may take a moment", icon='TIME')


# ¦ ¦ ¦ REGISTRATION
classes = [
    VV_FABRICA_PT_vrc_analysis,
]
