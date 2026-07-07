# -*- coding: utf-8 -*-
from __future__ import annotations

from database.connection import get_session
from models.usuario import Usuario
from services.auth_service import AuthError, AuthService
from utils.validators import ValidationError


class AuthController:
    @staticmethod
    def login(username: str, password: str) -> Usuario:
        """Devuelve un Usuario 'desconectado' (detached) seguro de usar en la UI
        tras cerrarse la sesión, evitando errores de sesión expirada."""
        with get_session() as session:
            usuario = AuthService.login(session, username, password)
            session.flush()
            session.expunge(usuario)
            return usuario

    @staticmethod
    def crear_usuario(username: str, password: str, nombre_completo: str, rol: str) -> Usuario:
        with get_session() as session:
            usuario = AuthService.crear_usuario(session, username, password, nombre_completo, rol)
            session.expunge(usuario)
            return usuario

    @staticmethod
    def listar_usuarios() -> list[Usuario]:
        with get_session() as session:
            usuarios = AuthService.listar_usuarios(session)
            for u in usuarios:
                session.expunge(u)
            return usuarios


__all__ = ["AuthController", "AuthError", "ValidationError"]
