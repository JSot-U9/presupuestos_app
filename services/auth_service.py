# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from models.auditoria import Auditoria
from models.usuario import Usuario
from utils.logger import get_logger
from utils.security import hash_password, verify_password
from utils.validators import ValidationError, validar_password, validar_username

logger = get_logger(__name__)


class AuthError(Exception):
    """Credenciales inválidas o usuario inactivo."""


class AuthService:
    @staticmethod
    def login(session: Session, username: str, password: str) -> Usuario:
        usuario = session.query(Usuario).filter_by(username=username.strip()).one_or_none()
        if usuario is None or not verify_password(password, usuario.password_hash):
            raise AuthError("Usuario o contraseña incorrectos.")
        if not usuario.activo:
            raise AuthError("El usuario está deshabilitado. Contacte al administrador.")

        session.add(Auditoria(usuario=usuario.username, accion="LOGIN", entidad="Usuario"))
        logger.info("Login exitoso: %s", usuario.username)
        return usuario

    @staticmethod
    def crear_usuario(
        session: Session,
        username: str,
        password: str,
        nombre_completo: str,
        rol: str = "VISUALIZADOR",
    ) -> Usuario:
        username = validar_username(username)
        validar_password(password)
        if session.query(Usuario).filter_by(username=username).one_or_none():
            raise ValidationError(f"El usuario '{username}' ya existe.")

        usuario = Usuario(
            username=username,
            password_hash=hash_password(password),
            nombre_completo=nombre_completo.strip() or username,
            rol=rol,
        )
        session.add(usuario)
        session.flush()
        session.add(Auditoria(usuario=username, accion="CREAR", entidad="Usuario"))
        return usuario

    @staticmethod
    def listar_usuarios(session: Session) -> list[Usuario]:
        return session.query(Usuario).order_by(Usuario.username).all()

    @staticmethod
    def asegurar_admin_inicial(session: Session) -> Optional[Usuario]:
        """Crea un usuario admin/admin123 si la tabla está vacía (solo demo)."""
        if session.query(Usuario).count() > 0:
            return None
        admin = AuthService.crear_usuario(
            session, "admin", "admin123", "Administrador del Sistema", rol="ADMIN"
        )
        logger.warning("Usuario admin creado por defecto (admin/admin123). Cámbielo en producción.")
        return admin
