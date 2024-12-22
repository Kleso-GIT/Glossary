from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Form


class Term(SQLModel, table=True):
    term: str = Field(primary_key=True)
    description: str | None = Field(default=None)


sqlite_file_name = "glossary.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/glossary/")
def create_term(term: Term, session: SessionDep) -> Term:
    session.add(term)
    session.commit()
    session.refresh(term)
    return term


@app.post("/search", response_class=HTMLResponse)
def search_term_page(request: Request, session: SessionDep, term: str = Form(...)):
    db_term = session.get(Term, term)
    if not db_term:
        if not db_term:
            return templates.TemplateResponse("search_results.html", {
                "request": request,
                "message": f"Term '{term}' not found."
            })
    return templates.TemplateResponse("search_results.html", {
        "request": request,
        "term": db_term.term,
        "description": db_term.description or "No description available",
        "edit_url": f"/edit/{db_term.term}",
        "delete_url": f"/glossary/{db_term.term}"
    })


@app.delete("/glossary/{term}")
def delete_term(term: str, session: SessionDep):
    db_term = session.get(Term, term)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    session.delete(db_term)
    session.commit()
    return {"ok": True}


# Фронтенд маршруты
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/add", response_class=HTMLResponse)
def add_page(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
def terms_page(request: Request,
               session: SessionDep,
               offset: int = 0,
               limit: Annotated[int, Query(le=100)] = 100,
               ):
    terms = session.exec(select(Term).offset(offset).limit(limit)).all()
    return templates.TemplateResponse("terms.html", {"request": request, "terms": terms})


@app.get("/edit/{term}", response_class=HTMLResponse)
def edit_page(request: Request, term: str, session: SessionDep):
    db_term = session.get(Term, term)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    return templates.TemplateResponse("edit.html", {"request": request, "term": db_term})


@app.put("/glossary/{term}")
async def update_term(term: str, request: Request, session: SessionDep) -> Term:
    data = await request.json()  # Получение данных в формате JSON
    description = data.get("description")
    if not description:
        raise HTTPException(status_code=400, detail="Description is required")

    db_term = session.get(Term, term)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    db_term.description = description
    session.add(db_term)
    session.commit()
    session.refresh(db_term)
    return db_term


@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})
