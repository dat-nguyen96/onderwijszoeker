import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from rio_client import (
    fetch_erkenningen,
    fetch_erkenning_detail,
    fetch_erkenning_locaties,
    fetch_erkenning_onderwijslicenties,
    fetch_erkenning_organisatorische_eenheden,
    fetch_aangeboden_opleidingen,
    fetch_opleiding_detail,
    fetch_aangeboden_opleiding_cohorten,
)

BASE_DIR = Path(__file__).resolve().parent

# ---------- RIO LOD API config ----------
RIO_BASE_URL = "https://lod.onderwijsregistratie.nl/api/rio/v2"

app = FastAPI(
    title="Onderwijsvisualisatie RIO",
    description="MVP op RIO LOD API zonder Node-build.",
)

# CORS (voor als je later nog een aparte frontend wilt testen)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Jinja2 templates & static
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ---------- Feature A: Plaats → erkende instellingen ----------

@app.get("/api/erkenningen")
async def api_erkenningen(
    plaatsnaam: str = Query(..., min_length=1),
    datum: Optional[str] = None,
    page: int = 0,
    page_size: int = Query(50, ge=1, le=100),
):
    try:
        datum_geldig_op: Optional[datetime.date] = None
        if datum:
            datum_geldig_op = datetime.date.fromisoformat(datum)
    except ValueError:
        raise HTTPException(status_code=400, detail="Datum moet in formaat YYYY-MM-DD")

    try:
        data = await fetch_erkenningen(
            plaatsnaam=plaatsnaam,
            datum_geldig_op=datum_geldig_op,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RIO API-fout: {e}")

    return {"results": data}


# ---------- Feature B: Instelling → locaties + licenties ----------

@app.get("/api/erkenningen/{erkenning_id}")
async def api_erkenning_detail(erkenning_id: str, datum: Optional[str] = None):
    try:
        datum_geldig_op: Optional[datetime.date] = None
        if datum:
            datum_geldig_op = datetime.date.fromisoformat(datum)
    except ValueError:
        raise HTTPException(status_code=400, detail="Datum moet in formaat YYYY-MM-DD")

    try:
        detail = await fetch_erkenning_detail(erkenning_id)
        locaties = await fetch_erkenning_locaties(erkenning_id, datum_geldig_op)
        licenties = await fetch_erkenning_onderwijslicenties(erkenning_id, datum_geldig_op)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RIO API-fout: {e}")

    return {
        "erkenning": detail,
        "locaties": locaties,
        "onderwijslicenties": licenties,
    }


# ---------- Organisatorische eenheden per erkenning ----------

@app.get("/api/erkenningen/{erkenning_id}/organisatorische-eenheden")
async def api_erkenning_organisatorische_eenheden(
    erkenning_id: str,
    datum: Optional[str] = None,
):
    try:
        datum_geldig_op: Optional[datetime.date] = None
        if datum:
            datum_geldig_op = datetime.date.fromisoformat(datum)
    except ValueError:
        raise HTTPException(status_code=400, detail="Datum moet in formaat YYYY-MM-DD")

    try:
        org_eenheden = await fetch_erkenning_organisatorische_eenheden(erkenning_id, datum_geldig_op)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RIO API-fout: {e}")

    return {"results": org_eenheden}


# ---------- Feature C: Aangeboden opleidingen per instelling (legacy endpoint) ----------

@app.get("/api/instellingen/{organisatorische_eenheidcode}/aangeboden-opleidingen")
async def api_aangeboden_opleidingen_legacy(
    organisatorische_eenheidcode: str,
    datum: Optional[str] = None,
    page: int = 0,
    page_size: int = Query(50, ge=1, le=100),
):
    """
    Legacy endpoint - gebruik /api/instellingen/{code}/opleidingen voor verbeterde versie
    """
    try:
        datum_geldig_op: Optional[datetime.date] = None
        if datum:
            datum_geldig_op = datetime.date.fromisoformat(datum)
    except ValueError:
        raise HTTPException(status_code=400, detail="Datum moet in formaat YYYY-MM-DD")

    try:
        # Basislijst ophalen
        ao_list = await fetch_aangeboden_opleidingen_for_instelling(
            organisatorische_eenheidcode=organisatorische_eenheidcode,
            datum_geldig_op=datum,
            max_pages=1,  # beperk tot 1 pagina voor legacy
            page_size=page_size,
        )

        # Voor elke aangeboden opleiding, haal ook de opleidingsdetails op
        enriched_opleidingen = []
        for opleiding in ao_list:
            try:
                # Haal opleidingsdetails op
                opleiding_detail = await fetch_opleiding_detail(opleiding["id"])

                # Haal cohorten op om te checken of er cohorten zijn
                cohorten = await fetch_aangeboden_opleiding_cohorten(opleiding["id"])
                heeft_cohorten = len(cohorten) > 0

                enriched_opleiding = {
                    "id": opleiding["id"],
                    "opleiding": opleiding_detail,
                    "heeftCohorten": heeft_cohorten,
                    "cohorten": cohorten if heeft_cohorten else [],
                }
                enriched_opleidingen.append(enriched_opleiding)
            except Exception as e:
                # Als het ophalen van details mislukt, voeg toch de basisinfo toe
                enriched_opleidingen.append({
                    "id": opleiding["id"],
                    "opleiding": {"naam": "Fout bij ophalen details", "type": "ONBEKEND"},
                    "heeftCohorten": False,
                    "cohorten": [],
                    "error": str(e)
                })

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RIO API-fout: {e}")

    return {"results": enriched_opleidingen}


# ---------- NIEUW: helper voor RIO-calls ----------

async def fetch_aangeboden_opleidingen_for_instelling(
    organisatorische_eenheidcode: str,
    datum_geldig_op: Optional[str] = None,
    max_pages: int = 2,
    page_size: int = 50,
) -> List[Dict[str, Any]]:
    """
    Haalt aangeboden opleidingen op voor één instelling via RIO,
    eventueel met een peildatum (datumGeldigOp).

    LET OP: max_pages beperkt het aantal pagina's (MVP).
    """
    resultaten: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for page in range(max_pages):
            params = {
                "organisatorischeEenheidcode": organisatorische_eenheidcode,
                "page": page,
                "pageSize": page_size,
            }
            if datum_geldig_op:
                params["datumGeldigOp"] = datum_geldig_op

            resp = await client.get(f"{RIO_BASE_URL}/aangeboden-opleidingen", params=params)
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                print("RIO error (aangeboden-opleidingen):", e)
                raise HTTPException(
                    status_code=502,
                    detail="Fout bij ophalen aangeboden opleidingen uit RIO",
                )

            data = resp.json()
            # Handle HAL response format
            if isinstance(data, dict) and "_embedded" in data:
                ao_data = data["_embedded"].get("AangebodenOpleidingen", [])
            else:
                ao_data = data if isinstance(data, list) else []

            if not ao_data:
                break

            resultaten.extend(ao_data)

            # eenvoudige stop-conditie
            if len(data) < page_size:
                break

    return resultaten


async def enrich_with_opleiding_details(
    aangeboden_opleidingen: List[Dict[str, Any]],
    datum_geldig_op: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Voor elk RIO 'AangebodenOpleiding'-object één call naar
    /aangeboden-opleidingen/{id}/opleiding om de opleiding op te halen.
    Probeert naam + niveau te extraheren.
    """
    enriched: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for ao in aangeboden_opleidingen:
            ao_id = ao.get("id")
            opleiding_data: Optional[Dict[str, Any]] = None
            opleiding_naam: Optional[str] = None
            opleiding_niveau: Optional[str] = None

            if ao_id:
                params = {}
                if datum_geldig_op:
                    params["datumGeldigOp"] = datum_geldig_op

                try:
                    resp = await client.get(
                        f"{RIO_BASE_URL}/aangeboden-opleidingen/{ao_id}/opleiding",
                        params=params,
                    )
                    if resp.status_code == 200:
                        opleiding_data = resp.json()

                        # BEST EFFORT: veldnamen kunnen varieren per type,
                        # dus we proberen een paar opties.
                        opleiding_naam = (
                            opleiding_data.get("naam")
                            or opleiding_data.get("crohoNaam")
                            or opleiding_data.get("volledigeNaam")
                        )

                        niveau_val = (
                            opleiding_data.get("niveau")
                            or opleiding_data.get("EQFniveau")
                        )
                        if isinstance(niveau_val, dict):
                            opleiding_niveau = (
                                niveau_val.get("code")
                                or niveau_val.get("waarde")
                                or str(niveau_val)
                            )
                        else:
                            opleiding_niveau = niveau_val

                except httpx.HTTPError as e:
                    print("RIO error (opleiding details):", e)

            enriched.append(
                {
                    "aangebodenOpleidingId": ao_id,
                    "organisatorischeEenheidcode": ao.get("organisatorischeEenheidcode"),
                    "type": ao.get("type"),
                    "begindatum": ao.get("begindatum"),
                    "einddatum": ao.get("einddatum"),
                    "opleidingNaam": opleiding_naam,
                    "opleidingNiveau": opleiding_niveau,
                    "aangebodenOpleiding": ao,
                    "opleiding": opleiding_data,
                }
            )

    return enriched


# ---------- NIEUW: verbeterde 3e endpoint: opleidingen per instelling ----------

@app.get("/api/instellingen/{organisatorische_eenheidcode}/opleidingen")
async def opleidingen_per_instelling(
    organisatorische_eenheidcode: str,
    datum_geldig_op: Optional[str] = None,
):
    """
    Geeft een lijst van aangeboden opleidingen voor één instelling,
    aangevuld met opleiding-details (naam + niveau waar mogelijk).

    Voorbeeld:
    GET /api/instellingen/123A456/opleidingen?datum_geldig_op=2025-11-21
    """
    # 1) basislijst ophalen
    ao_list = await fetch_aangeboden_opleidingen_for_instelling(
        organisatorische_eenheidcode=organisatorische_eenheidcode,
        datum_geldig_op=datum_geldig_op,
    )

    # 2) aanvullen met /{id}/opleiding
    enriched = await enrich_with_opleiding_details(
        aangeboden_opleidingen=ao_list,
        datum_geldig_op=datum_geldig_op,
    )

    return {
        "instellingCode": organisatorische_eenheidcode,
        "peildatum": datum_geldig_op,
        "aantalOpleidingen": len(enriched),
        "items": enriched,
    }


# ---------- HTML UI ----------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Simpele UI:
    - Zoekveld voor plaatsnaam
    - Resultaten in een tabel
    - Bij klik op een erkenning ID lazy load detail via JS fetch.
    """
    return templates.TemplateResponse("home.html", {"request": request})
