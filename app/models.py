from sqlalchemy import Column, Integer, String, Date, Numeric, Index
from .database import Base

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    distribuidor = Column(String, nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    # Numeric para trabajar bien con Decimal (evitar Float)
    valor = Column(Numeric(12, 2), nullable=False)
    descripcion = Column(String, nullable=True)

# Índices compuestos recomendados
Index("ix_pedidos_fecha_distribuidor", Pedido.fecha, Pedido.distribuidor)