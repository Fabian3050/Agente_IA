import openpyxl
import os
from typing import List, Dict

AREAS_PATH = os.path.join(os.path.dirname(__file__), "..", "areas", "Areas_OCDE.xlsx")

def get_ocde_areas() -> List[Dict[str, str]]:
    """Lee el archivo Excel de áreas OCDE y devuelve una lista de diccionarios {codigo, descripcion}."""
    wb = openpyxl.load_workbook(AREAS_PATH)
    sheet = wb.active
    areas = []
    
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row[0] and row[1]:
            areas.append({"codigo": str(row[0]), "descripcion": str(row[1])})
            
    return areas

def get_ocde_areas_formatted() -> str:
    """Devuelve las áreas formateadas como texto para incluir en el prompt del LLM."""
    areas = get_ocde_areas()
    return "\n".join([f"- {item['codigo']}: {item['descripcion']}" for item in areas])
