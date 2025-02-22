from app.database.import_data.import_fos import import_fos
from app.database.import_data.import_programs import import_all_programs



def start_import():
    import_fos()
    import_all_programs()