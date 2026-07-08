"""Consulta de datos de persona por DNI (RENIEC) con plan de contingencia.

Réplica del ReniecService del proyecto dre_sistema_control: intenta primero
la fuente principal (decolecta.com) y, si falla, recorre las contingencias
configuradas (PeruDevs y ApiPeru.dev) en orden hasta obtener una respuesta.
"""
import re
import logging
from typing import Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

DNI_PATTERN = re.compile(r"^\d{8}$")


def _formatear_nombre_completo(nombres: str, apellido_paterno: str, apellido_materno: str) -> str:
    partes = [p.strip() for p in (nombres, apellido_paterno, apellido_materno) if p and p.strip()]
    return " ".join(partes).upper()


class ReniecService:
    def __init__(self):
        settings = get_settings()
        self.reniec_url = settings.reniec_api_url
        self.reniec_token = settings.reniec_api_token
        self.perudevs_url = settings.perudevs_dni_url
        self.perudevs_token = settings.perudevs_dni_token
        self.apiperu_url = settings.apiperu_dni_url
        self.apiperu_token = settings.apiperu_dni_token

    async def consultar_dni(self, dni: str) -> dict:
        if not DNI_PATTERN.match(dni):
            return {
                "success": False,
                "message": "El DNI debe tener exactamente 8 dígitos numéricos.",
                "data": None,
            }

        data = await self._consultar_reniec(dni)
        if data:
            return {"success": True, "message": "Consulta exitosa", "data": data}

        data = await self._consultar_perudevs(dni)
        if data:
            return {"success": True, "message": "Consulta exitosa (Contingencia PeruDevs)", "data": data}

        data = await self._consultar_apiperu(dni)
        if data:
            return {"success": True, "message": "Consulta exitosa (Contingencia ApiPeru)", "data": data}

        return {
            "success": False,
            "message": "No se pudo obtener información del DNI. Verifique que el número sea correcto.",
            "data": None,
        }

    async def _consultar_reniec(self, dni: str) -> Optional[dict]:
        if not self.reniec_token:
            return None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    self.reniec_url,
                    params={"numero": dni},
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.reniec_token}",
                    },
                )
            if response.status_code != 200:
                logger.warning("RENIEC API error %s: %s", response.status_code, response.text)
                return None

            payload = response.json()
            if payload.get("error"):
                return None

            nombres = payload.get("first_name") or ""
            apellido_paterno = payload.get("first_last_name") or ""
            apellido_materno = payload.get("second_last_name") or ""
            if not nombres and not payload.get("full_name"):
                return None

            return {
                "dni": payload.get("document_number") or dni,
                "nombres": nombres,
                "apellido_paterno": apellido_paterno,
                "apellido_materno": apellido_materno,
                "nombre_completo": _formatear_nombre_completo(nombres, apellido_paterno, apellido_materno),
            }
        except httpx.HTTPError as e:
            logger.error("RENIEC API exception: %s", e)
            return None

    async def _consultar_perudevs(self, dni: str) -> Optional[dict]:
        if not self.perudevs_url or not self.perudevs_token:
            return None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    self.perudevs_url,
                    params={"document": dni, "key": self.perudevs_token},
                )
            if response.status_code != 200:
                return None

            payload = response.json()
            if payload.get("estado") is not True or "resultado" not in payload:
                return None

            resultado = payload["resultado"]
            nombres = resultado.get("nombres") or ""
            apellido_paterno = resultado.get("apellido_paterno") or ""
            apellido_materno = resultado.get("apellido_materno") or ""

            return {
                "dni": resultado.get("id") or dni,
                "nombres": nombres,
                "apellido_paterno": apellido_paterno,
                "apellido_materno": apellido_materno,
                "nombre_completo": resultado.get("nombre_completo")
                or _formatear_nombre_completo(nombres, apellido_paterno, apellido_materno),
            }
        except httpx.HTTPError as e:
            logger.error("PeruDevs contingencia exception: %s", e)
            return None

    async def _consultar_apiperu(self, dni: str) -> Optional[dict]:
        if not self.apiperu_url or not self.apiperu_token:
            return None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.apiperu_url,
                    json={"dni": dni},
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.apiperu_token}",
                    },
                )
            if response.status_code != 200:
                return None

            payload = response.json()
            if payload.get("success") is not True or "data" not in payload:
                return None

            persona = payload["data"]
            nombres = persona.get("nombres") or ""
            apellido_paterno = persona.get("apellido_paterno") or ""
            apellido_materno = persona.get("apellido_materno") or ""

            return {
                "dni": persona.get("numero") or dni,
                "nombres": nombres,
                "apellido_paterno": apellido_paterno,
                "apellido_materno": apellido_materno,
                "nombre_completo": persona.get("nombre_completo")
                or _formatear_nombre_completo(nombres, apellido_paterno, apellido_materno),
            }
        except httpx.HTTPError as e:
            logger.error("ApiPeru contingencia exception: %s", e)
            return None


reniec_service = ReniecService()
