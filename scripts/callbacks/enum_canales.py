#
# Versión 0.1
# Fecha: 26 de agosto de 2025
#
# Autores: Helena Ruiz Ramírez
# Función: Enumerador de los canales en LiveConnect por ID. Se utiliza para asignar la sucursal del contacto.
#
from enum import Enum


class Canales(Enum):
    ELI = ("115", "4124") # 02 Elite (WA), 02 Elite Facebook 
    SAN = ("243", "19026") # 04 SanNicolas (WA), 04 SanNicolas Facebook
    DOM = ("735", "19027") # 05 Dominio (WA), 05 Dominio Facebook
    ESC = ("235", "19028") # 06 Escobedo (WA), 06 Escobedo Facebook
    DEF = ()

    @classmethod
    def from_value(cls, value):
        for member in cls:
            if str(value) in member.value:
                return member
        return Canales.DEF

class Sucursales(Enum):
    ELI = "Cumbres Elite"
    SAN = "San Nicolás"
    DOM = "Cumbres Dominio"
    ESC = "Escobedo"
    DEF = "Cumbres Elite"

    @classmethod
    def from_value(cls, value):
        for member in cls:
            if value == member.name:
                return member
        return Sucursales.DEF
