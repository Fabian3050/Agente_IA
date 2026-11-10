import openpyxl
import os
from typing import List, Dict

AREAS_PATH = os.path.join(os.path.dirname(__file__), "..", "areas", "Areas_ODS.xlsx")

def get_ods_areas() -> List[Dict[str, str]]:
    """Lee el archivo Excel de áreas ODS y devuelve una lista de diccionarios {codigo, area, descripcion}."""
    wb = openpyxl.load_workbook(AREAS_PATH)
    sheet = wb.active
    areas = []
    
    # Los datos comienzan en la fila 5
    for row in sheet.iter_rows(min_row=5, values_only=True):
        codigo = row[0]
        area = row[1]
        descripcion = row[2]
        
        # Validamos que al menos tenga el código y el área
        if codigo and area:
            try:
                # Nos aseguramos de que el código sea un número (ej: ignoramos notas a pie de página)
                cod_int = int(float(codigo))
                areas.append({
                    "codigo": str(cod_int), 
                    "area": str(area).strip(),
                    "descripcion": str(descripcion).strip() if descripcion else ""
                })
            except (ValueError, TypeError):
                continue
            
    return areas

def get_ods_areas_formatted() -> str:
    """Devuelve las áreas formateadas como texto para incluir en el prompt del LLM."""
    areas = get_ods_areas()
    return "\n".join([f"- ODS {item['codigo']} ({item['area']}): {item['descripcion']}" for item in areas])
