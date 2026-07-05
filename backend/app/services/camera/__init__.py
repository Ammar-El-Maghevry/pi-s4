"""
Paquet des services liés aux caméras.

Pour l'instant : uniquement le test de connexion à un flux (`connection`).
Le pipeline d'inférence temps réel reste un module futur séparé
(voir `../ai/README.md`).
"""
from app.services.camera.connection import test_camera_connection

__all__ = ["test_camera_connection"]
