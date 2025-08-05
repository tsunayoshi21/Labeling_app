#!/bin/bash

# Ruta al archivo de backup
# BACKUP_FILE="./backups/backup_2025-08-04_22-43-20.dump"

# Nombre del contenedor
CONTAINER_NAME="db"

# Copiar el archivo de backup al contenedor
echo "📦 Copiando backup al contenedor..."
docker cp "$BACKUP_FILE" "$CONTAINER_NAME":/tmp/restore.dump

# Ejecutar el restore dentro del contenedor
echo "♻️  Restaurando base de datos '$DATABASE_NAME' desde el dump..."
docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$CONTAINER_NAME" \
    pg_restore -U "$DB_USER" -d "$DATABASE_NAME" --clean --verbose /tmp/restore.dump

# Borrar el archivo dentro del contenedor (opcional)
echo "🧹 Limpiando archivo temporal..."
docker exec "$CONTAINER_NAME" rm /tmp/restore.dump

echo "✅ Restauración completada."
