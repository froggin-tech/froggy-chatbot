#
# Versión 1.0
# Fecha: 20 de septiembre de 2025
#
# Autores: Helena Ruiz Ramírez
# Función: Enumeradores y diccionarios para los canales en LiveConnect por ID, las sucursales por etiqueta, el ID
#           del equipo correspondiente según el ID del canal, IDs y nombres de usuarios e IDs y nombres de etiquetas
#
from enum import Enum, StrEnum


class Unidades(StrEnum):
    __order__ = "ELITE SANNICOLAS DOMINIO ESCOBEDO DEFAULT"
    ELITE = "ELI"
    SANNICOLAS = "SAN"
    DOMINIO = "DOM"
    ESCOBEDO = "ESC"
    DEFAULT = "DEF"

    @classmethod
    def _missing_(cls, value):
        return Unidades.DEFAULT


# Identificador sucursal <- ID Equipo
class Canales(Enum):
    ELI = ("115", "4124") # 02 Elite (WA), 02 Elite Facebook
    SAN = ("243", "19026") # 04 SanNicolas QR, 04 SanNicolas Facebook
    DOM = ("735", "19027") # 05 Dominio (WA), 05 Dominio Facebook
    ESC = ("235", "19028") # 06 Escobedo (WA), 06 Escobedo Facebook
    DEF = ()

    @classmethod
    def from_value(cls, value):
        for member in cls:
            if str(value) in member.value:
                return member
        return Canales.DEF


# Identificador sucursal -> Nombre de la sucursal
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


# ID Canal -> ID Equipo
equipos_IDs = {
    "115": "9089", # 02 Elite WA = 02 Elite
    "4124": "10094", # 02 Elite Facebook = 02 Elite Facebook
    "243": "4041", # 04 SanNicolas QR = 04 SanNicolas
    "19026": "10096", # 04 SanNicolas Facebook = 04 SanNicolas Facebook
    "735": "9091", # 05 Dominio WA = 05 Dominio
    "19027": "10098", # 05 Dominio Facebook = 05 Dominio Facebook
    "235": "9092", # 06 Escobedo WA = 06 Escobedo
    "19028": "10099" # 06 Escobedo Facebook = 06 Escobedo Facebook
}


# Identificador sucursal -> ID Etiqueta
class EtiquetaAtender(Enum):
    ELI = "36887" # 02Elite.ADM Atender
    SAN = "36889" # 04SanNicolas.ADM Atender
    DOM = "36890" # 05Dominio.ADM Atender
    ESC = "36891" # 06Escobedo.ADM Atender
    DEF = "06127" # 00Brenda - Soporte (Si hay error)

    @classmethod
    def from_value(cls, value):
        for member in cls:
            if value == member.name:
                return member
        return Sucursales.DEF


# Identificador -> ID Etiqueta
tag_IDs = {
    "facebook": "50863", #  FB campaña
    "instagram": "50862", #  IG campaña
    "fase chatbot": "74937", # Fase Chatbot
    "live": "75792" # !! EN VIVO
}


# Identificador -> Nombre Usuario o ID Usuario
user_IDs = {
    "nuevos": {"name": "Franny Chatbot (Nuevos)", "id": "53415"},
    "existentes": {"name": "Franny Chatbot (Existentes)", "id": "53958"}
}