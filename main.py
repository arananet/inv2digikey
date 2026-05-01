from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os

import models
import schemas
import auth
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="inv2digikey", docs_url="/api/docs", redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.get("/api/auth/status")
def auth_status(db: Session = Depends(get_db)):
    """Return whether any users exist (used by frontend to show register vs login)."""
    has_users = db.query(models.User).count() > 0
    return {"has_users": has_users}


@app.post("/api/auth/register", response_model=schemas.Token)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user_count = db.query(models.User).count()
    if user_count > 0:
        # After the first user, registration requires a setup token
        setup_token = os.getenv("SETUP_TOKEN", "")
        if not setup_token:
            raise HTTPException(status_code=403, detail="Registration is closed")

    user = models.User(
        username=user_data.username,
        hashed_password=auth.hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


# ── Components ────────────────────────────────────────────────────────────────

@app.get("/api/components", response_model=List[schemas.Component])
def list_components(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Component).filter(models.Component.user_id == current_user.id)
    if search:
        term = f"%{search}%"
        query = query.filter(
            models.Component.digikey_pn.ilike(term)
            | models.Component.manufacturer_pn.ilike(term)
            | models.Component.description.ilike(term)
            | models.Component.manufacturer.ilike(term)
        )
    return query.order_by(models.Component.updated_at.desc()).all()


@app.post("/api/components", response_model=schemas.Component, status_code=status.HTTP_201_CREATED)
def create_component(
    component: schemas.ComponentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db_obj = models.Component(**component.model_dump(), user_id=current_user.id)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@app.get("/api/components/{component_id}", response_model=schemas.Component)
def get_component(
    component_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    obj = db.query(models.Component).filter(
        models.Component.id == component_id,
        models.Component.user_id == current_user.id,
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Component not found")
    return obj


@app.put("/api/components/{component_id}", response_model=schemas.Component)
def update_component(
    component_id: int,
    data: schemas.ComponentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    obj = db.query(models.Component).filter(
        models.Component.id == component_id,
        models.Component.user_id == current_user.id,
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Component not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj


@app.delete("/api/components/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_component(
    component_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    obj = db.query(models.Component).filter(
        models.Component.id == component_id,
        models.Component.user_id == current_user.id,
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Component not found")
    db.delete(obj)
    db.commit()


# ── Frontend ──────────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html")
