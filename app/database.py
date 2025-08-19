from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .settings import settings

# URL de la base de datos desde .env
DATABASE_URL = settings.database_url

# Configuración del motor
engine_kwargs = {
    "pool_pre_ping": True,  # Revisa conexión antes de usarla
    "future": True  # Activa modo SQLAlchemy 2.x
}
connect_args = {}

# Ajuste especial si usas SQLite en desarrollo
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Crear motor SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_size=5,       # Ajuste conservador para Render
    max_overflow=10,   # Conexiones extra en picos
    pool_timeout=30,   # Tiempo máximo antes de error
    **engine_kwargs
)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Base para modelos
Base = declarative_base()

# Dependencia para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
