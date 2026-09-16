import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.ods_service import get_ods_areas_formatted

print(get_ods_areas_formatted())
