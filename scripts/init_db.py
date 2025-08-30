from sqlalchemy import inspect, text
from app.db import engine, Base
import app.models  

def is_postgres(url: str) -> bool:
    return url.startswith("postgresql")

def main():
    # Crea tablas
    Base.metadata.create_all(bind=engine)

    # Lista tablas
    insp = inspect(engine)
    try:
        with engine.connect() as conn:
            try:
                schema = conn.execute(text("select current_schema()")).scalar()
            except Exception:
                schema = None
    except Exception:
        schema = None

    if schema:
        print("current_schema:", schema)
    else:
        print("current_schema: (no disponible o no es Postgres)")

    print("tables:", insp.get_table_names())

if __name__ == "__main__":
    main()
