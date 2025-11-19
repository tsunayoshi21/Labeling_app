#!/bin/bash

# Fail fast on pipeline errors but allow Telegram send to fail without aborting backup
set -euo pipefail

###############################
# Configuración y Paths
###############################
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"  # Ajustar si se mueve el script
BACKUP_DIR="$SCRIPT_DIR/backups"
LOG_FILE="$SCRIPT_DIR/backup.log"

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
FILENAME="backup_${TIMESTAMP}.dump"
DEST_FILE="${BACKUP_DIR}/${FILENAME}"

# Cargar variables de entorno si existe un .env junto al script
if [[ -f "$SCRIPT_DIR/.env" ]]; then
	# shellcheck disable=SC2046
	export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs -d '\n' -I {} echo {}) || true
fi

mkdir -p "$BACKUP_DIR"

{
	echo "[$(date +%Y-%m-%dT%H:%M:%S)] Iniciando backup..."

	###############################
	# Backup de Postgres
	###############################
	echo "Creando dump dentro del contenedor..."
	docker exec -t db pg_dump -U labeling_user -d labeling_db -F c -f /tmp/backup.dump

	echo "Copiando dump al host: $DEST_FILE"
	docker cp db:/tmp/backup.dump "$DEST_FILE"

	echo "Eliminando dump temporal del contenedor"
	docker exec db rm /tmp/backup.dump || echo "Advertencia: No se pudo eliminar /tmp/backup.dump"

	echo "✅ Backup guardado en: $DEST_FILE"

	###############################
	# Envío por Telegram
	###############################
	SEND_SCRIPT="$SCRIPT_DIR/send_file_telegram.py"
	if [[ -f "$SEND_SCRIPT" ]]; then
		echo "Enviando archivo por Telegram..."
		# Usar python dentro del PATH (cron puede tener PATH limitado)
		if command -v python3 >/dev/null 2>&1; then
			PYTHON_BIN="python3"
		else
			PYTHON_BIN="python"
		fi
		set +e
		"$PYTHON_BIN" "$SEND_SCRIPT" "$DEST_FILE"
		SEND_STATUS=$?
		set -e
		if [[ $SEND_STATUS -ne 0 ]]; then
			echo "❌ Falló el envío por Telegram (exit code $SEND_STATUS). El backup sigue siendo válido: $DEST_FILE"
		else
			echo "📤 Archivo enviado por Telegram correctamente"
		fi
	else
		echo "⚠️ Script de envío Telegram no encontrado: $SEND_SCRIPT"
	fi

	echo "[$(date +%Y-%m-%dT%H:%M:%S)] Proceso completado"
} | tee -a "$LOG_FILE"

exit 0
