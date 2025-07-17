#!/bin/bash

# Este script se usa para configurar variables de entorno en Clever Cloud
# cuando tu despliegue es activado por un git push desde GitHub.

# --- Variables de Configuración ---
APP_ID="app_TU_APP_ID_AQUI" # ¡IMPORTANTE: Reemplaza con el ID real de tu aplicación!
CELLAR_BUCKET_NAME="pdfs-app" # ¡IMPORTANTE: Reemplaza con el nombre real de tu bucket!

# --- Colores para la salida ---
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===============================================${NC}"
echo -e "${YELLOW}  Script de Configuración de Variables de Entorno en Clever Cloud ${NC}"
echo -e "${YELLOW}===============================================${NC}"

# --- 1. Verificar Clever Cloud CLI ---
echo -e "\n${YELLOW}Verificando la instalación y configuración del CLI de Clever Cloud...${NC}"
if ! command -v clever &> /dev/null
then
    echo -e "${RED}Error: El CLI de Clever Cloud (clever) no está instalado o no está en tu PATH.${NC}"
    echo -e "${RED}Por favor, instálalo siguiendo las instrucciones en la documentación de Clever Cloud.${NC}"
    exit 1
fi
echo -e "${GREEN}CLI de Clever Cloud encontrado.${NC}"

# --- 2. Enlazar la aplicación (si no está ya enlazada) ---
echo -e "\n${YELLOW}Verificando enlace de la aplicación con el ID: ${APP_ID}...${NC}"
CURRENT_APP_ID=$(clever get --id 2>/dev/null)
if [ "$CURRENT_APP_ID" != "$APP_ID" ]; then
    echo -e "${YELLOW}El directorio actual no está enlazado al APP_ID proporcionado. Enlazando...${NC}"
    clever link --id "$APP_ID" || { echo -e "${RED}Error al enlazar la aplicación. Verifica el APP_ID.${NC}"; exit 1; }
    echo -e "${GREEN}Aplicación enlazada exitosamente a ${APP_ID}.${NC}"
else
    echo -e "${GREEN}Aplicación ya enlazada a ${APP_ID}.${NC}"
fi

# --- 3. Configurar la variable de entorno del bucket de Cellar ---
echo -e "\n${YELLOW}Configurando la variable de entorno CELLAR_ADDON_BUCKET...${NC}"
echo -e "Estableciendo CELLAR_ADDON_BUCKET a: ${CELLAR_BUCKET_NAME}"

clever env set CELLAR_ADDON_BUCKET "$CELLAR_BUCKET_NAME" -a "$APP_ID" || { echo -e "${RED}Error al configurar CELLAR_ADDON_BUCKET.${NC}"; exit 1; }
echo -e "${GREEN}CELLAR_ADDON_BUCKET configurado exitosamente.${NC}"

# --- Opcional: Verificar variables de entorno (para depuración) ---
echo -e "\n${YELLOW}Verificando variables de entorno de la aplicación (últimas 5 líneas)...${NC}"
clever env -a "$APP_ID" | tail -n 5

echo -e "\n${GREEN}===============================================${NC}"
echo -e "${GREEN}  Configuración de variables de entorno completada. ${NC}"
echo -e "${GREEN}  Ahora haz un 'git push' a GitHub para activar el despliegue en Clever Cloud. ${NC}"
echo -e "${GREEN}===============================================${NC}"

exit 0