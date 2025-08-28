from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import date

from . import models, schemas

from datetime import timedelta
from decimal import Decimal

# Crear pedido
def crear_pedido(db: Session, data: schemas.PedidoCreate) -> models.Pedido:
    pedido = models.Pedido(
        distribuidor=data.distribuidor.strip(),
        fecha=data.fecha + timedelta(days=1),  # ✅ Sumamos un día
        valor=Decimal(data.valor),  # Asegura que sea Decimal para la DB
        descripcion=data.descripcion.strip() if data.descripcion else None
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido

# Listar pedidos por fecha
def listar_pedidos_por_fecha(db: Session, fecha: date) -> List[models.Pedido]:
    stmt = (
        select(models.Pedido)
        .where(models.Pedido.fecha == fecha)
        .order_by(models.Pedido.id.desc())
    )
    return list(db.scalars(stmt).all())

from sqlalchemy import select, func
from datetime import date

def resumen_pedidos_dia(db: Session, fecha: date) -> schemas.ResumenDia:
    # Total y cantidad (forzamos comparación por fecha sin hora)
    total_stmt = (
        select(
            func.coalesce(func.sum(models.Pedido.valor), 0),
            func.count(models.Pedido.id),
        )
        .where(func.date(models.Pedido.fecha) == fecha)
    )
    total_val, count_val = db.execute(total_stmt).one()

    # Agrupado por distribuidor (también filtramos por fecha sin hora)
    dist_stmt = (
        select(
            models.Pedido.distribuidor,
            func.coalesce(func.sum(models.Pedido.valor), 0),
            func.count(models.Pedido.id),
        )
        .where(func.date(models.Pedido.fecha) == fecha)
        .group_by(models.Pedido.distribuidor)
        .order_by(models.Pedido.distribuidor)
    )

    por_distribuidor = [
        schemas.ResumenDistribuidor(distribuidor=d, total=t, cantidad=c)
        for d, t, c in db.execute(dist_stmt).all()
    ]

    return schemas.ResumenDia(
        fecha=fecha,
        total=total_val,
        cantidad=count_val,
        por_distribuidor=por_distribuidor,
    )
