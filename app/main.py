from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select


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


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/glossary/")
def create_term(term: Term, session: SessionDep) -> Term:
    session.add(term)
    session.commit()
    session.refresh(term)
    return term


@app.put("/glossary/{term}")
def update_term(term: str, description: str, session: SessionDep) -> Term:
    db_term = session.get(Term, term)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    db_term.description = description
    session.add(db_term)
    session.commit()
    session.refresh(db_term)
    return db_term


@app.get("/glossary/")
def read_terms(
        session: SessionDep,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
) -> list[Term]:
    terms = session.exec(select(Term).offset(offset).limit(limit)).all()
    return terms


@app.get("/glossary/{term}")
def read_term(term: str, session: SessionDep) -> Term:
    db_term = session.get(Term, term)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    return db_term


@app.delete("/glossary/{term}")
def delete_term(term: str, session: SessionDep):
    db_term = session.get(Term, term)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    session.delete(db_term)
    session.commit()
    return {"ok": True}
