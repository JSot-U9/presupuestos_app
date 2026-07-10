from database.connection import get_session
from models.presupuesto import Presupuesto

with get_session() as s:
    s.query(Presupuesto).delete()
    s.commit()
    print("Presupuestos eliminados")
