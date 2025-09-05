#
# Versión 0.3
# Fecha: 03 de septiembre de 2025
#
# Autores: Helena Ruiz Ramírez
# Función: Enumeradores para los canales en LiveConnect por ID, las sucursales por etiqueta y el 
#           ID del equipo correspondiente según el ID del canal.
#
from enum import Enum


class Canales(Enum):
    ELI = (115, 4124) # 02 Elite (WA), 02 Elite Facebook 
    SAN = (243, 19026) # 04 SanNicolas (WA), 04 SanNicolas Facebook
    DOM = (735, 19027) # 05 Dominio (WA), 05 Dominio Facebook
    ESC = (235, 19028) # 06 Escobedo (WA), 06 Escobedo Facebook
    DEF = ()

    @classmethod
    def from_value(cls, value):
        for member in cls:
            if value in member.value:
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


# ID Canal = ID Equipo
equipos_IDs = {
    115: 9089, # 02 Elite WA = 02 Elite
    4124: 10094, # 02 Elite Facebook = 02 Elite Facebook
    243: 4041, # 04 SanNicolas WA = 04 SanNicolas
    19026: 10096, # 04 SanNicolas Facebook = 04 SanNicolas Facebook
    735: 9091, # 05 Dominio WA = 05 Dominio
    19027: 10098, # 05 Dominio Facebook = 05 Dominio Facebook
    235: 9092, # 06 Escobedo WA = 06 Escobedo
    19028: 10099 # 06 Escobedo Facebook = 06 Escobedo Facebook
}