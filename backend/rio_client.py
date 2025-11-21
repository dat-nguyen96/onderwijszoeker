import datetime
from typing import Any, Dict, List, Optional

import httpx

RIO_BASE_URL = "https://lod.onderwijsregistratie.nl/api/rio/v2"


async def fetch_erkenningen(
    plaatsnaam: str,
    datum_geldig_op: Optional[datetime.date] = None,
    page: int = 0,
    page_size: int = 50,
) -> List[Dict[str, Any]]:
    """
    Vraagt erkende organisaties op in een plaats.
    Deze functie geeft de ruwe JSON-objecten van de RIO API terug.
    """
    params = {
        "plaatsnaam": plaatsnaam,
        "page": page,
        "pageSize": page_size,
    }
    if datum_geldig_op:
        params["datumGeldigOp"] = datum_geldig_op.isoformat()

    async with httpx.AsyncClient(base_url=RIO_BASE_URL, timeout=10.0) as client:
        resp = await client.get("/erkenningen", params=params)
        resp.raise_for_status()
        data = resp.json()
        # Extract the embedded erkenningen from HAL response
        return data.get("_embedded", {}).get("Erkenningen", [])


async def fetch_erkenning_detail(erkenning_id: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(base_url=RIO_BASE_URL, timeout=10.0) as client:
        resp = await client.get(f"/erkenningen/{erkenning_id}")
        resp.raise_for_status()
        return resp.json()


async def fetch_erkenning_locaties(
    erkenning_id: str,
    datum_geldig_op: Optional[datetime.date] = None,
) -> List[Dict[str, Any]]:
    params: Dict[str, str] = {}
    if datum_geldig_op:
        params["datumGeldigOp"] = datum_geldig_op.isoformat()

    async with httpx.AsyncClient(base_url=RIO_BASE_URL, timeout=10.0) as client:
        resp = await client.get(
            f"/erkenningen/{erkenning_id}/onderwijslocatiegebruiken",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        # Handle HAL response format
        return data.get("_embedded", {}).get("onderwijslocatiegebruiken", [])


async def fetch_erkenning_onderwijslicenties(
    erkenning_id: str,
    datum_geldig_op: Optional[datetime.date] = None,
) -> List[Dict[str, Any]]:
    params: Dict[str, str] = {}
    if datum_geldig_op:
        params["datumGeldigOp"] = datum_geldig_op.isoformat()

    async with httpx.AsyncClient(base_url=RIO_BASE_URL, timeout=10.0) as client:
        resp = await client.get(
            f"/erkenningen/{erkenning_id}/onderwijslicenties",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        # Handle HAL response format
        return data.get("_embedded", {}).get("Onderwijslicenties", [])


async def fetch_erkenning_organisatorische_eenheden(
    erkenning_id: str,
    datum_geldig_op: Optional[datetime.date] = None,
) -> List[Dict[str, Any]]:
    """
    Haalt organisatorische eenheden op voor een specifieke erkenning.
    """
    params: Dict[str, str] = {}
    if datum_geldig_op:
        params["datumGeldigOp"] = datum_geldig_op.isoformat()

    async with httpx.AsyncClient(base_url=RIO_BASE_URL, timeout=10.0) as client:
        resp = await client.get(
            f"/erkenningen/{erkenning_id}/organisatorische-eenheden",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        # Extract the embedded organisatorische-eenheden from HAL response
        return data.get("_embedded", {}).get("organisatorischeEenheden", [])


async def fetch_aangeboden_opleidingen(
    organisatorische_eenheidcode: str,
    datum_geldig_op: Optional[datetime.date] = None,
    page: int = 0,
    page_size: int = 50,
) -> List[Dict[str, Any]]:
    """
    Vraagt aangeboden opleidingen op voor een organisatorische eenheid.
    """
    params = {
        "organisatorischeEenheidcode": organisatorische_eenheidcode,
        "page": page,
        "pageSize": page_size,
    }
    if datum_geldig_op:
        params["datumGeldigOp"] = datum_geldig_op.isoformat()

    async with httpx.AsyncClient(base_url=RIO_BASE_URL, timeout=10.0) as client:
        resp = await client.get("/aangeboden-opleidingen", params=params)
        resp.raise_for_status()
        data = resp.json()
        # Extract the embedded aangeboden-opleidingen from HAL response
        return data.get("_embedded", {}).get("AangebodenOpleidingen", [])


async def fetch_opleiding_detail(aangeboden_opleiding_id: str) -> Dict[str, Any]:
    """
    Haalt details van een specifieke aangeboden opleiding op, inclusief de gekoppelde opleiding.
    """
    async with httpx.AsyncClient(base_url=RIO_BASE_URL, timeout=10.0) as client:
        resp = await client.get(f"/aangeboden-opleidingen/{aangeboden_opleiding_id}/opleiding")
        resp.raise_for_status()
        return resp.json()


async def fetch_aangeboden_opleiding_cohorten(aangeboden_opleiding_id: str) -> List[Dict[str, Any]]:
    """
    Haalt cohorten op voor een specifieke aangeboden opleiding.
    """
    async with httpx.AsyncClient(base_url=RIO_BASE_URL, timeout=10.0) as client:
        resp = await client.get(f"/aangeboden-opleidingen/{aangeboden_opleiding_id}/aangeboden-opleiding-cohorten")
        resp.raise_for_status()
        return resp.json()
