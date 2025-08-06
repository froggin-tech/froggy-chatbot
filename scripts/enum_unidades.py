#
# Versión 1.1
# Fecha: 31 de julio de 2025
#
# Autores: Helena Ruiz Ramírez
# Función: Enumerador de las unidades activas en Froggin. Se utiliza para identificar carpetas.
#
from enum import StrEnum


class Unidades(StrEnum):
    ELITE = "ELI"
    SANNICOLAS = "SAN"
    DOMINIO = "DOM"
    ESCOBEDO = "ESC"
    DEFAULT = "DEF"

    @classmethod
    def _missing_(cls, value):
        return Unidades.DEFAULT
