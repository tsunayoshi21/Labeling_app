#!/bin/bash

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
FILENAME="backup_${TIMESTAMP}.dump"

# Crear carpeta si no existe
mkdir -p "$BACKUP_DIR"

# Crear el backup dentro del contenedor
docker exec -t db pg_dump -U ${DB_USER} -d ${DATABASE_NAME} -F c -f /tmp/backup.dump

# Copiar el backup al host
docker cp db:/tmp/backup.dump "${BACKUP_DIR}/${FILENAME}"

# Eliminar el backup temporal del contenedor
docker exec db rm /tmp/backup.dump

echo "✅ Backup guardado en: ${BACKUP_DIR}/${FILENAME}"
