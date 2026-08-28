"""Elige entre los proveedores de IA de texto disponibles (Groq y Gemini) y
va alternando entre ellos, con fallback automático: si el elegido falla (se
quedó sin cuota, tiró 429, lo que sea), prueba con el otro antes de rendirse.

Nace de un problema real de esta sesión: Groq tiene 200k tokens/día gratis y
en un rato de pruebas se agotó, bloqueando la generación por el resto del
día. Con dos proveedores turnándose, agotar los DOS el mismo día es mucho
menos probable — y si de última pasa, generate.py se entera con un solo
error claro en vez de silenciosamente no generar nada.

Si solo hay una API key cargada (p.ej. todavía no configuraste
GEMINI_API_KEY), se usa solo esa — no hace falta las dos para que el bot
siga funcionando como hasta ahora.
"""

import os
import random

import gemini_client
import groq_client


def _proveedores_disponibles() -> list[tuple[str, object]]:
    provs = []
    if os.environ.get("GROQ_API_KEY"):
        provs.append(("groq", groq_client))
    if os.environ.get("GEMINI_API_KEY"):
        provs.append(("gemini", gemini_client))
    if not provs:
        raise RuntimeError(
            "No hay ninguna API key de IA de texto configurada. "
            "Necesitás al menos GROQ_API_KEY o GEMINI_API_KEY en el .env."
        )
    random.shuffle(provs)
    return provs


def _con_fallback(nombre_metodo: str, *args) -> dict:
    last_error: Exception | None = None
    for nombre, mod in _proveedores_disponibles():
        try:
            print(f"  (texto: usando {nombre})")
            return getattr(mod, nombre_metodo)(*args)
        except Exception as e:
            print(f"  ({nombre} falló: {e})")
            last_error = e
    raise RuntimeError(f"Ningún proveedor de IA pudo generar la pieza: {last_error}")


def generate_carousel(pilar: str, angulo: str, rubro: str, con_foto: bool = False) -> dict:
    return _con_fallback("generate_carousel", pilar, angulo, rubro, con_foto)


def generate_humor(pilar: str, angulo: str, con_foto: bool = False) -> dict:
    return _con_fallback("generate_humor", pilar, angulo, con_foto)


def generate_sabias_que(pilar: str, angulo: str, con_foto: bool = False) -> dict:
    return _con_fallback("generate_sabias_que", pilar, angulo, con_foto)


def generate_chisme(pilar: str, angulo: str) -> dict:
    return _con_fallback("generate_chisme", pilar, angulo)


def generate_video_script(pilar: str, angulo: str, rubro: str) -> dict:
    return _con_fallback("generate_video_script", pilar, angulo, rubro)


def generate_angulos(pilar: str, formato: str | None, existentes: list[str], n: int,
                     rendimiento: str | None = None) -> dict:
    return _con_fallback("generate_angulos", pilar, formato, existentes, n, rendimiento)
