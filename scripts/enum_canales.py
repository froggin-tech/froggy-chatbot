#
# Versión 1.0
# Fecha: 25 de julio de 2025
#
# Autores: Helena Ruiz Ramírez
# Función: Enumerador de los canales en LiveConnect por unidad y medio de comunicación. Se utiliza para identificar carpetas.
#
from enum import Enum

class Canales(Enum):
    ELITE = ("02 Elite", "02 Elite Facebook")
    SANNICOLAS = ("04 SanNicolas", "02 SanNicolas Facebook")
    DOMINIO = ("05 Dominio", "02 Dominio Facebook")
    ESCOBEDO = ("06 Escobedo", "02 Escobedo Facebook")
    DEFAULT = ()

    @classmethod
    def from_value(cls, value):
        for member in cls:
            if value in member.value:
                return member
        return Canales.DEFAULT