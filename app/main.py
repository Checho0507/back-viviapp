from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, datetime
from typing import List
import pytz
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud  # tu módulo con funciones CRUD
from app import models  # tus modelos de SQLAlchemy

import logging

# Crear la app
app = FastAPI(title="Pedidos API", version="1.0")

# Configurar CORS para el frontend en Vite
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de logging
logger = logging.getLogger("uvicorn.access")

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response

# =====================
# MODELOS (Schemas)
# =====================
class PedidoCreate(BaseModel):
    distribuidor: str
    valor: float
    fecha: date
    descripcion: str | None = None

class PedidoOut(PedidoCreate):
    id: int

class ResumenDia(BaseModel):
    fecha: date
    total_pedidos: int
    total_valor: float

# =====================
# ENDPOINTS DE PEDIDOS
# =====================

@app.post("/pedidos", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def crear_pedido(pedido: PedidoCreate, db: Session = Depends(get_db)):
    return crud.crear_pedido(db, pedido)

@app.get("/pedidos")
def listar_pedidos(db: Session = Depends(get_db)):
    pedidos = db.query(models.Pedido).all()
    return pedidos

@app.get("/pedidos/resumen", response_model=ResumenDia)
def resumen_dia(fecha: date, db: Session = Depends(get_db)):
    return crud.resumen_pedidos_dia(db, fecha)

# =====================
# ENDPOINTS DE REPORTES (ejemplo)
# =====================

@app.get("/reportes/todos_pedidos", response_model=List[PedidoOut])
def todos_los_pedidos(db: Session = Depends(get_db)):
    return crud.listar_todos_pedidos(db)

@app.delete("/pedidos/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    db.delete(pedido)
    db.commit()
    return {"detail": "Pedido eliminado exitosamente"}

@app.get("/pedidos/resumen")
def resumen_pedidos(db: Session = Depends(get_db)):
    # Zona horaria de Colombia
    tz = pytz.timezone("America/Bogota")
    hoy = datetime.now(tz).date()

    pedidos = db.query(models.Pedido).all()
    
    total_pedidos = len(pedidos)
    total_hoy = sum(p.valor for p in pedidos if p.fecha == hoy)
    total_general = sum(p.valor for p in pedidos)

    return {
        "total_pedidos": total_pedidos,
        "total_hoy": total_hoy,
        "total_general": total_general
    }
