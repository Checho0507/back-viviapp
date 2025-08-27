from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, condecimal, field_validator
from datetime import date, datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.database import get_db
from app import crud, models, schemas
import logging
import json
import os
from fastapi.responses import FileResponse
import pandas as pd

PAGADOS_FILE = "pagados.json"

# Asegurar que el archivo exista
if not os.path.exists(PAGADOS_FILE):
    with open(PAGADOS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)


# =====================
# CONFIGURACIÓN DE LA APP
# =====================
app = FastAPI(title="Pedidos API", version="1.0")

# CORS
origins = [
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

    @field_validator('fecha')
    @classmethod
    def validate_fecha(cls, v):
        """
        Asegura que la fecha recibida se interprete correctamente como fecha de Colombia.
        """
        if isinstance(v, str):
            # Si viene como string, parsearlo como fecha
            try:
                parsed_date = datetime.strptime(v, '%Y-%m-%d').date()
                logger.info(f"Fecha parseada desde string: {parsed_date}")
                return parsed_date
            except ValueError:
                raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD")
        elif isinstance(v, date):
            logger.info(f"Fecha recibida como date: {v}")
            return v
        else:
            raise ValueError("La fecha debe ser un string en formato YYYY-MM-DD o un objeto date")


class PedidoOut(PedidoCreate):
    id: int


class ResumenDia(BaseModel):
    fecha: date
    total: condecimal(max_digits=12, decimal_places=2)  # type: ignore
    cantidad: int


# =====================
# HELPERS
# =====================
def fecha_colombia() -> date:
    """Devuelve la fecha actual en Colombia (UTC-5)."""
    ahora_utc = datetime.now(timezone.utc)
    colombia_time = ahora_utc - timedelta(hours=5)
    return colombia_time.date()


def datetime_colombia() -> datetime:
    """Devuelve el datetime actual en Colombia (UTC-5)."""
    ahora_utc = datetime.now(timezone.utc)
    return ahora_utc - timedelta(hours=5)


def get_colombia_day_range(fecha_colombia: date) -> tuple[datetime, datetime]:
    """
    Retorna el rango de datetime para un día específico en horario de Colombia.
    Convierte las 00:00:00 y 23:59:59 de Colombia a UTC para comparar con la BD.
    """
    # Inicio del día en Colombia (00:00:00)
    inicio_dia_colombia = datetime.combine(fecha_colombia, datetime.min.time())
    # Final del día en Colombia (23:59:59.999999)
    final_dia_colombia = datetime.combine(fecha_colombia, datetime.max.time())
    
    # Convertir a UTC: Colombia es UTC-5, por lo que sumamos 5 horas para obtener UTC
    inicio_dia_utc = inicio_dia_colombia + timedelta(hours=5)
    final_dia_utc = final_dia_colombia + timedelta(hours=5)
    
    return inicio_dia_utc, final_dia_utc


# =====================
# ENDPOINTS
# =====================
@app.post("/pedidos", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def crear_pedido(pedido: PedidoCreate, db: Session = Depends(get_db)):
    # Log para debugging
    logger.info(f"Creando pedido con fecha Colombia: {pedido.fecha}")
    
    # Crear el pedido directamente con la fecha como está (date, no datetime)
    # No necesitamos conversiones de zona horaria para fechas simples
    pedido_creado = crud.crear_pedido(db, pedido)
    
    logger.info(f"Pedido creado con fecha: {pedido_creado.fecha}")
    
    return pedido_creado


@app.get("/pedidos", response_model=List[PedidoOut])
def listar_pedidos(db: Session = Depends(get_db)):
    pedidos = db.query(models.Pedido).all()
    
    # Convertir a la estructura de respuesta
    pedidos_response = []
    for pedido in pedidos:
        # Asegurar que la fecha sea de tipo date
        if isinstance(pedido.fecha, datetime):
            # Si por alguna razón está como datetime, extraer solo la fecha
            fecha_final = pedido.fecha.date()
        else:
            # Si ya es date, usarla directamente
            fecha_final = pedido.fecha
            
        pedido_dict = {
            "id": pedido.id,
            "distribuidor": pedido.distribuidor,
            "valor": pedido.valor,
            "descripcion": pedido.descripcion,
            "fecha": fecha_final
        }
        
        pedidos_response.append(PedidoOut(**pedido_dict))
    
    return pedidos_response


@app.get("/pedidos/resumen-dia", response_model=ResumenDia)
def resumen_dia(fecha: date, db: Session = Depends(get_db)):
    logger.info(f"Consultando resumen para fecha: {fecha}")
    
    # Si las fechas en BD son de tipo date, hacer comparación directa
    # Si son datetime, usar el rango de datetime
    try:
        # Intentar primero comparación directa con date
        total_val, count_val = db.query(
            func.coalesce(func.sum(models.Pedido.valor), 0),
            func.count(models.Pedido.id),
        ).filter(
            models.Pedido.fecha == fecha
        ).one()
        
        logger.info(f"Consulta directa por fecha exitosa: total={total_val}, count={count_val}")
        
    except Exception as e:
        # Si falla, usar el rango de datetime para compatibilidad
        logger.info(f"Consulta directa falló, usando rango datetime: {e}")
        inicio_dia, final_dia = get_colombia_day_range(fecha)
        
        total_val, count_val = db.query(
            func.coalesce(func.sum(models.Pedido.valor), 0),
            func.count(models.Pedido.id),
        ).filter(
            and_(
                models.Pedido.fecha >= inicio_dia,
                models.Pedido.fecha <= final_dia
            )
        ).one()

    return ResumenDia(
        fecha=fecha,
        total=total_val,
        cantidad=count_val
    )


@app.get("/pedidos/resumen-general")
def resumen_pedidos(db: Session = Depends(get_db)):
    from decimal import Decimal

    # Obtener la fecha actual de Colombia
    hoy_colombia = fecha_colombia()
    
    # Total de pedidos
    total_pedidos = db.query(func.count(models.Pedido.id)).scalar() or 0

    # Total de hoy - intentar comparación directa primero
    try:
        total_hoy = db.query(
            func.coalesce(func.sum(models.Pedido.valor), Decimal('0.00'))
        ).filter(
            models.Pedido.fecha == hoy_colombia
        ).scalar()
        
        logger.info(f"Consulta directa para hoy exitosa: {total_hoy}")
        
    except Exception as e:
        # Si falla, usar rango datetime
        logger.info(f"Consulta directa para hoy falló, usando rango: {e}")
        inicio_hoy, final_hoy = get_colombia_day_range(hoy_colombia)
        
        total_hoy = db.query(
            func.coalesce(func.sum(models.Pedido.valor), Decimal('0.00'))
        ).filter(
            and_(
                models.Pedido.fecha >= inicio_hoy,
                models.Pedido.fecha <= final_hoy
            )
        ).scalar()

    # Total general
    total_general = db.query(
        func.coalesce(func.sum(models.Pedido.valor), Decimal('0.00'))
    ).scalar()

    logger.info(f"Fecha Colombia hoy: {hoy_colombia}")
    logger.info(f"Total hoy calculado: {total_hoy}")

    return {
        "total_pedidos": total_pedidos,
        "total_hoy": float(total_hoy) if total_hoy else 0.0,
        "total_general": float(total_general) if total_general else 0.0,
        "fecha_colombia": hoy_colombia.isoformat()
    }


@app.delete("/pedidos/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    db.delete(pedido)
    db.commit()
    return {"detail": "Pedido eliminado exitosamente"}


# =====================
# PAGADOS
# =====================
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

        # Convertir a Excel
        excel_file = "pagados.xlsx"
        df = pd.DataFrame(pagados)
        df.to_excel(excel_file, index=False)

        # Retornar archivo para descarga
        return FileResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="pagados.xlsx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando: {str(e)}")