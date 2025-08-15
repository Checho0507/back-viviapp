from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import date
from decimal import Decimal

from . import models, schemas

# Crear pedido

def crear_pedido(db: Session, data: schemas.PedidoCreate) -> models.Pedido:
    pedido = models.Pedido(
        distribuidor=data.distribuidor.strip(),
        fecha=data.fecha,
        valor=Decimal(data.valor),  # asegura Decimal
        descripcion=data.descripcion.strip() if data.descripcion else None
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido

# Listar pedidos por fecha

def listar_pedidos_por_fecha(db: Session, fecha: date) -> list[models.Pedido]:
    stmt = (
        select(models.Pedido)
        .where(models.Pedido.fecha == fecha)
        .order_by(models.Pedido.id.desc())
    )
    return list(db.scalars(stmt).all())

# Resumen del día

def resumen_pedidos_dia(db: Session, fecha: date) -> schemas.ResumenDia:
    total_stmt = (
        select(
            func.coalesce(func.sum(models.Pedido.valor), 0),
            func.count(models.Pedido.id),
        )
        .where(models.Pedido.fecha == fecha)
    )
    total_val, count_val = db.execute(total_stmt).one()

    dist_stmt = (
        select(
            models.Pedido.distribuidor,
            func.coalesce(func.sum(models.Pedido.valor), 0),
            func.count(models.Pedido.id),
        )
        .where(models.Pedido.fecha == fecha)
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