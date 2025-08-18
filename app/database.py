from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .settings import settings

# URL de la base de datos desde .env
DATABASE_URL = settings.database_url

# Configuración del motor
engine_kwargs = {"pool_pre_ping": True}
connect_args = {}

# Ajuste especial si usas SQLite (ej. en desarrollo local)
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Crear motor SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_size=10,  # útil en producción
    max_overflow=20,  # conexiones adicionales si hay carga
    pool_timeout=30,  # espera antes de error por pool lleno
    **engine_kwargs
)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()


# Dependencia para inyección en FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
