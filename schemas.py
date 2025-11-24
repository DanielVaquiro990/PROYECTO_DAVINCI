from pydantic import BaseModel, Field
from typing import List, Optional, ClassVar
import math

class Fuerza(BaseModel):
    tipo: str
    magnitud: float
    direccion: str

class TanqueConFuerzas(BaseModel):
    masa: float
    radio_rueda: float
    fuerza_motriz: float
    coeficiente_rozamiento: float
    fuerzas: Optional[List[Fuerza]] = []

class SimulationInput(BaseModel):
    tanque: TanqueConFuerzas  # Usa el modelo del tanque
    tiempo: float = Field(..., gt=0, description="Tiempo en segundos para la simulación")

class SimulationOutput(BaseModel):
    aceleracion: float
    velocidad_final: float
    distancia_recorrida: float

class EcuacionConica(BaseModel):
    A: float = Field(0.0, description="Coeficiente de x^2")
    B: float = Field(0.0, description="Coeficiente de y^2")
    C: float = Field(0.0, description="Coeficiente de z^2")
    D: float = Field(0.0, description="Coeficiente de x*y")
    E: float = Field(0.0, description="Coeficiente de x*z")
    F: float = Field(0.0, description="Coeficiente de y*z")
    G: float = Field(0.0, description="Coeficiente de x")
    H: float = Field(0.0, description="Coeficiente de y")
    I: float = Field(0.0, description="Coeficiente de z")
    J: float = Field(0.0, description="Término constante")

class PuntoEvaluacion(BaseModel):
    x: float
    y: float
    z: float
    RADIO_CUADRADO: ClassVar[float] = 25.0

    def pertenece_a_ecuacion(self) -> bool:
        valor_calculado = self.x*2 + self.y2 + self.z*2
        TOLERANCIA = 1e-6
        return abs(valor_calculado - self.RADIO_CUADRADO) < TOLERANCIA

    def distancia_a_ecuacion(self) -> float:
        magnitud_punto = math.sqrt(self.x*2 + self.y2 + self.z*2)
        radio = math.sqrt(self.RADIO_CUADRADO)
        return abs(magnitud_punto - radio)

punto_dentro = PuntoEvaluacion(x=3.0, y=4.0, z=0.0)
print(f"Punto ({punto_dentro.x}, {punto_dentro.y}, {punto_dentro.z}):")
print(f"¿Pertenece? {punto_dentro.pertenece_a_ecuacion()}")
print(f"Distancia: {punto_dentro.distancia_a_ecuacion()}")

print("-" * 20)

punto_fuera = PuntoEvaluacion(x=5.0, y=5.0, z=0.0)
print(f"Punto ({punto_fuera.x}, {punto_fuera.y}, {punto_fuera.z}):")
print(f"¿Pertenece? {punto_fuera.pertenece_a_ecuacion()}")
print(f"Distancia: {punto_fuera.distancia_a_ecuacion()}")