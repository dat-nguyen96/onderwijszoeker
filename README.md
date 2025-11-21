# Onderwijszoeker - RIO LOD API MVP

Een minimalistische webapplicatie voor het verkennen van erkende onderwijsinstellingen in Nederland via de RIO LOD API.

## Features

### Feature A: Onderwijslandschap per plaats
- Zoek erkende instellingen op plaatsnaam
- Toont type erkenning, verkorte/volledige naam, bekostigingscode

### Feature B: Campus/onderwijscluster verkenner
- Klik op een erkenning voor detailinformatie
- Toont onderwijslocaties en onderwijslicenties per locatie

### Feature C: Aangeboden opleidingen per instelling
- Zoek opleidingen per organisatorische eenheid code
- Toont opleidingsnaam, niveau en type
- Werkende voorbeeld codes:
  - `115A122`: Hilal (Basisonderwijs)
  - `110A838`: Conservatorium van Amsterdam
  - `101A214`: Alfa-college Groningen
  - `100A385`: MBO Amersfoort School voor Techniek
- Gebruikt RIO API endpoints: `/aangeboden-opleidingen` en `/{id}/opleiding`

## Technische Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/CSS/JavaScript (geen build tools)
- **API**: RIO LOD API (onderwijsregistratie.nl)
- **Deployment**: Railway (Docker)

## Lokale Development

```bash
# Dependencies installeren
cd backend
pip install -r requirements.txt

# Applicatie starten
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Open http://localhost:8000 in browser
```

## Deployment naar Railway

1. Repository pushen naar GitHub
2. Railway project aanmaken
3. GitHub repository connecteren
4. Railway detecteert automatisch de Dockerfile
5. Deploy!

## Project Structuur

```
.
├── Dockerfile              # Railway deployment
├── README.md              # Deze file
├── backend/
│   ├── main.py            # FastAPI applicatie
│   ├── requirements.txt   # Python dependencies
│   ├── rio_client.py      # RIO API wrapper
│   ├── templates/
│   │   └── home.html      # Hoofdpagina template
│   └── static/
│       └── style.css      # Styling
└── test_rio_api.py        # API test script
```

## API Endpoints

- `GET /` - Hoofdpagina
- `GET /api/health` - Health check
- `GET /api/erkenningen?plaatsnaam={plaats}&datum={YYYY-MM-DD}` - Zoek erkenningen
- `GET /api/erkenningen/{id}` - Erkenning details (locaties + licenties)
- `GET /api/erkenningen/{id}/organisatorische-eenheden` - Organisatorische eenheden per erkenning
- `GET /api/instellingen/{organisatorische_eenheidcode}/opleidingen?datum_geldig_op={YYYY-MM-DD}` - Opleidingen per instelling (nieuw!)
- `GET /api/instellingen/{organisatorische_eenheidcode}/aangeboden-opleidingen` - Legacy endpoint voor opleidingen

## RIO API

Deze applicatie gebruikt de [RIO LOD API](https://lod.onderwijsregistratie.nl) van DUO voor actuele onderwijsregistratie data.

## Licentie

MIT License
