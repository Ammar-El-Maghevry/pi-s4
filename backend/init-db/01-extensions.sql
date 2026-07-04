-- Active l'extension pgvector, requise par la colonne face_embedding.
-- Ce script est exécuté automatiquement au premier démarrage du conteneur
-- PostgreSQL (répertoire /docker-entrypoint-initdb.d/).
CREATE EXTENSION IF NOT EXISTS vector;
