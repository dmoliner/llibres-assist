from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llibres_assist_core.scraper.aladi import AladiScraper, SearchType
from llibres_assist_core.models.book import SearchResult, Book
from llibres_assist_core.scraper.llibres_cat import LlibresCatScraper
from llibres_assist_core.assistant.agent import run_assistant_chat

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

GEMINI_API_KEY = "AIzaSyACQ7rDac5_dcDBiWCUyWyiR8ty_Xp1_jE"

class ChatRequest(BaseModel):
    message: str
    history: list
    scope: int = 171

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

@app.post("/api/chat")
def chat_assistant(request: ChatRequest):
    """
    Endpoint per interactuar amb l'assistent d'IA.
    Gestiona recomanacions literàries i cerca automàtica al catàleg de la DIBA.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="El missatge de l'usuari no pot estar buit.")
    
    try:
        response_text, updated_history = run_assistant_chat(
            api_key=GEMINI_API_KEY,
            message=request.message,
            history=request.history,
            scope=request.scope
        )
        return {
            "response": response_text,
            "history": updated_history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en processar el xat: {str(e)}")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "llibres-assist-backend"}

