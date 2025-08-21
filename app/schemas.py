from pydantic import BaseModel, field_validator, ConfigDict, Field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

class PedidoBase(BaseModel):
    distribuidor: str
    fecha: date
    valor: Decimal
    descripcion: str | None = None

    @field_validator("distribuidor")
    @classmethod
    def normalize_distribuidor(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El distribuidor es obligatorio")
        return v

    @field_validator("valor")
    @classmethod
    def positive_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("El valor debe ser positivo")
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @field_validator("descripcion")
    @classmethod
    def normalize_descripcion(cls, v: str | None) -> str | None:
        if v:
            v = v.strip()
            return v if v else None
        return None

class PedidoCreate(PedidoBase):
    pass

class PedidoOut(PedidoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ResumenDistribuidor(BaseModel):
    distribuidor: str
    total: Decimal
    cantidad: int

    model_config = ConfigDict(
        json_encoders={Decimal: lambda v: float(v)}  # <-- convierte Decimal a float
    )

class ResumenDia(BaseModel):
    fecha: date
    total: Decimal
    cantidad: int
    por_distribuidor: list[ResumenDistribuidor] = Field(default_factory=list)

    model_config = ConfigDict(
        json_encoders={Decimal: lambda v: float(v)}
    )
