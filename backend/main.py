from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from llibres_assist_core.scraper.aladi import AladiScraper, SearchType
from llibres_assist_core.models.book import SearchResult, Book
from llibres_assist_core.scraper.llibres_cat import LlibresCatScraper

app = FastAPI(
    title="Llibres Assist API",
    description="API de cerca al catàleg ALADI de la Diputació de Barcelona (DIBA)",
    version="0.1.0"
)

# Configurar CORS per permetre peticions des del frontend de desenvolupament
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producció s'ha de limitar, per a dev amb "*" és correcte
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/search", response_model=SearchResult)
def search_books(
    q: str = Query(..., description="Paraules clau a cercar (ex: 'les vuit muntanyes')"),
    desc: bool = Query(False, description="Enriquir resultats amb descripció i categoria de llibres.cat"),
    scope: int = Query(171, description="Àmbit de la cerca (default: 171 = tot el catàleg)")
):
    """
    Cerca llibres al catàleg ALADI de la DIBA.
    Opcionalment es pot enriquir amb la descripció i categoria de llibres.cat.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="El paràmetre de cerca 'q' no pot estar buit.")
        
    try:
        with AladiScraper() as scraper:
            result = scraper.search(
                q,
                search_type=SearchType.ANY_WORD,
                scope=scope,
                enrich=desc,
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durant la cerca: {str(e)}")

@app.get("/api/books/{book_id}/enrich", response_model=Book)
def enrich_single_book(
    book_id: str,
    title: str,
    author: str | None = None,
    publisher: str | None = None
):
    """
    Enriqueix un llibre concret amb la descripció i categoria de llibres.cat.
    """
    try:
        dummy_book = Book(
            id=book_id,
            title=title,
            author=author,
            publisher=publisher
        )
        with LlibresCatScraper() as enricher:
            enriched = enricher.enrich(dummy_book)
        return enriched
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en enriquiment de llibre: {str(e)}")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "llibres-assist-backend"}
