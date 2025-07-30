#
# Versión 1.1
# Fecha: 30 de julio de 2025
#
# Autores: Helena Ruiz Ramírez
# Función: Enumerador de los equipos en LiveConnect por unidad y medio de comunicación. Se utiliza para identificar carpetas.
#
from enum import Enum

class Equipos(Enum):
    ELITE = ("02 Elite", "02 Elite Facebook", "01 Leones Facebook", "02 Elite Instagram", "01 Leones Instagram")
    SANNICOLAS = ("04 SanNicolas", "02 SanNicolas Facebook", "04 San Nicolas Instagram")
    DOMINIO = ("05 Dominio", "02 Dominio Facebook", "05 Dominio Instagram")
    ESCOBEDO = ("06 Escobedo", "02 Escobedo Facebook", "06 Escobedo Instagram")
    DEFAULT = ()

    @classmethod
    def from_value(cls, value):
        for member in cls:
            if value in member.value:
                return member
        return Equipos.DEFAULT