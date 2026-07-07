# -*- coding: utf-8 -*-
"""Gestión de la conexión a la base de datos (PostgreSQL en producción,
SQLite por defecto para desarrollo/demo). Compatible con ambos motores
porque todo el código usa SQLAlchemy Core/ORM sin SQL crudo específico
de un dialecto.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import DATABASE_URL, SQL_ECHO
from database.base import Base
from utils.logger import get_logger

logger = get_logger(__name__)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=SQL_ECHO, future=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def init_db() -> None:
    """Crea todas las tablas si no existen. Importa los modelos primero
    para que queden registrados en Base.metadata."""
    from models import (  # noqa: F401  (import necesario para registrar tablas)
        auditoria,
        ejecucion,
        presupuesto,
        proyecto,
        usuario,
    )

    Base.metadata.create_all(bind=engine)
    logger.info("Base de datos inicializada (%s).", DATABASE_URL)


@contextmanager
def get_session() -> Iterator[Session]:
    """Context manager que garantiza commit/rollback/close correctos."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
