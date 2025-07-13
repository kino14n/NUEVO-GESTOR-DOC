# Backend Flask listo para Render

Endpoints funcionales:
- `/api/search` (POST): responde JSON de ejemplo.
- `/api/docs` (GET): responde JSON de ejemplo.

**CORS** habilitado SOLO para https://kino14n.github.io (frontend GitHub Pages).

## Deploy en Render:
1. Sube estos archivos a la carpeta backend en tu repo.
2. Render detectará el Procfile y requirements.txt, instalará dependencias y correrá la app automáticamente.
3. Los endpoints quedarán disponibles en tu dominio de Render.

## Limpieza:
- Borra archivos `.DS_Store` y carpetas `__MACOSX/` si aparecen.
