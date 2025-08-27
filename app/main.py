from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, condecimal
from datetime import date, datetime
from typing import List
import pytz
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud, models
import logging
import json
import os
from fastapi.responses import FileResponse
import pandas as pd

PAGADOS_FILE = "pagados.json"

# =====================
# CONFIGURACIÓN GLOBAL
# =====================

# Asegurar que el archivo exista
if not os.path.exists(PAGADOS_FILE):
    with open(PAGADOS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)

# Leer la zona horaria desde variable de entorno
APP_TZ = os.getenv("APP_TZ", "America/Bogota")  # Valor por defecto si no existe
try:
    tz = pytz.timezone(APP_TZ)
except pytz.UnknownTimeZoneError:
    tz = pytz.timezone("America/Bogota")  # fallback

# =====================
# CONFIGURACIÓN DE LA APP
# =====================
app = FastAPI(title="Pedidos API", version="1.0")

# CORS (leer también de entorno si quieres)
origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
    "https://back-viviapp.onrender.com",
    "https://front-viviapp.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging independiente para evitar errores de uvicorn.access
logger = logging.getLogger("pedidos_logger")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Middleware para logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request received: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response sent: {request.method} {request.url} - Status: {response.status_code}")
    return response

# =====================
# MODELOS (Schemas)
# =====================
class PedidoCreate(BaseModel):
    distribuidor: str
    valor: condecimal(max_digits=10, decimal_places=2)  # type: ignore
    fecha: date
    descripcion: str | None = None

class PedidoOut(PedidoCreate):
    id: int

class ResumenDia(BaseModel):
    fecha: date
    total: condecimal(max_digits=12, decimal_places=2)  # type: ignore
    cantidad: int

# =====================
# ENDPOINTS
# =====================
@app.post("/pedidos", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def crear_pedido(pedido: PedidoCreate, db: Session = Depends(get_db)):
    return crud.crear_pedido(db, pedido)

@app.get("/pedidos", response_model=List[PedidoOut])
def listar_pedidos(db: Session = Depends(get_db)):
    return db.query(models.Pedido).all()

@app.get("/pedidos/resumen-dia", response_model=ResumenDia)
def resumen_dia(fecha: date, db: Session = Depends(get_db)):
    return crud.resumen_pedidos_dia(db, fecha)

@app.get("/pedidos/resumen-general")
def resumen_pedidos(db: Session = Depends(get_db)):
    from sqlalchemy import func
    from decimal import Decimal
    
    hoy = datetime.now(tz).date()
    
    # Usar SQL para hacer los cálculos (más eficiente y seguro)
    total_pedidos = db.query(func.count(models.Pedido.id)).scalar() or 0
    
    total_hoy = db.query(
        func.coalesce(func.sum(models.Pedido.valor), Decimal('0.00'))
    ).filter(models.Pedido.fecha == hoy).scalar()
    
    total_general = db.query(
        func.coalesce(func.sum(models.Pedido.valor), Decimal('0.00'))
    ).scalar()

    return {
        "total_pedidos": total_pedidos,
        "total_hoy": float(total_hoy),
        "total_general": float(total_general)
    }

@app.delete("/pedidos/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    db.delete(pedido)
    db.commit()
    return {"detail": "Pedido eliminado exitosamente"}

def load_pagados():
    if os.path.exists(PAGADOS_FILE):
        try:
            with open(PAGADOS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    return []  # Si hay algo raro, devolvemos lista vacía
        except json.JSONDecodeError:
            return []
    return []

def save_pagados(pagados):
    with open(PAGADOS_FILE, "w", encoding="utf-8") as f:
        json.dump(pagados, f, ensure_ascii=False, indent=2)

@app.post("/pagados/agregar")
async def agregar_pagado(pedido: dict):
    try:
        pagados = load_pagados()
        pagados.append(pedido)
        save_pagados(pagados)
        return {"message": "Pagado agregado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando pagado: {str(e)}")

@app.get("/pagados/exportar")
async def exportar_pagados():
    try:
        pagados = load_pagados()
        if not pagados:
            raise HTTPException(status_code=404, detail="No hay pedidos pagados")

        excel_file = "pagados.xlsx"
        df = pd.DataFrame(pagados)
        df.to_excel(excel_file, index=False)

        return FileResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="pagados.xlsx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando: {str(e)}")
