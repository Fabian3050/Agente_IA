import openpyxl
import os
from typing import List, Dict

AREAS_PATH = os.path.join(os.path.dirname(__file__), "..", "areas", "Areas_OCDE.xlsx")

def get_ocde_areas() -> List[Dict[str, str]]:
    """Lee el archivo Excel de áreas OCDE y devuelve una lista de diccionarios con la jerarquía."""
    wb = openpyxl.load_workbook(AREAS_PATH)
    sheet = wb.active
    areas = []
    
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row[0] and row[1]:
            areas.append({
                "id_area": str(row[0]),
                "nombre_area": str(row[1]),
                "id_subarea": str(row[2]) if len(row) > 2 and row[2] else "",
                "nombre_subarea": str(row[3]) if len(row) > 3 and row[3] else "",
                "id_disciplina": str(row[4]) if len(row) > 4 and row[4] else "",
                "nombre_disciplina": str(row[5]) if len(row) > 5 and row[5] else ""
            })
            
    return areas

def get_ocde_areas_formatted() -> str:
    """Devuelve las áreas formateadas como texto para incluir en el prompt del LLM."""
    areas = get_ocde_areas()
    lines = []
    for item in areas:
        line = f"- Área {item['id_area']} {item['nombre_area']}"
        if item['id_subarea'] and item['nombre_subarea']:
            line += f" > Subárea {item['id_subarea']} {item['nombre_subarea']}"
            if item['id_disciplina'] and item['nombre_disciplina']:
                line += f" > Disciplina {item['id_disciplina']} {item['nombre_disciplina']}"
        lines.append(line)
    
    # Remove duplicates in case the excel has multiple rows for same area/subarea
    unique_lines = list(dict.fromkeys(lines))
    return "\n".join(unique_lines)
