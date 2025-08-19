from sqlalchemy import Column, Integer, String, Date, Numeric, Index
from .database import Base

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    distribuidor = Column(String(100), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    valor = Column(Numeric(12, 2), nullable=False)
    descripcion = Column(String(255), nullable=True)

# Índice compuesto para mejorar búsquedas por fecha y distribuidor
Index("ix_pedidos_fecha_distribuidor", Pedido.fecha, Pedido.distribuidor)
