from fastapi import FastAPI, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import string
import random

from database import SessionLocal, Base, engine, URL

app = FastAPI()

# Создаём таблицы при старте (можно запускать init_db.py отдельно, это на выбор)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@app.get("/")
async def root():
    return {"message": "URL shortener is alive"}

@app.post("/shorten")
async def shorten_url(long_url: str = Form(...), db: Session = Depends(get_db)):
    if not long_url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL")

    # Генерируем уникальный short_code
    while True:
        short_code = generate_short_code()
        exists = db.query(URL).filter(URL.short_code == short_code).first()
        if not exists:
            break

    new_url = URL(short_code=short_code, long_url=long_url)
    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    short_url = f"https://info-tw.space/{short_code}"  # замени на свой домен
    return {"short_url": short_url}

@app.get("/{short_code}")
async def redirect_url(short_code: str, db: Session = Depends(get_db)):
    url = db.query(URL).filter(URL.short_code == short_code).first()
    if url:
        return RedirectResponse(url.long_url)
    raise HTTPException(status_code=404, detail="URL not found")
