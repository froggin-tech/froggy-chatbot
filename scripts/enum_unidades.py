#
# Versión 1.0
# Fecha: 25 de julio de 2025
#
# Autores: Helena Ruiz Ramírez
# Función: Enumerador de las unidades activas en Froggin. Se utiliza para identificar carpetas.
#
from enum import StrEnum

class Unidades(StrEnum):
    ELITE = 'E'
    SANNICOLAS = 'S'
    DOMINIO = 'D'
    ESCOBEDO = 'B'
    DEFAULT = 'L'

    @classmethod
    def _missing_(cls, value):
        return Unidades.DEFAULT