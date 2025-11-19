#!/usr/bin/env python3
"""Enviar un archivo de backup de Postgres a un chat de Telegram.

Uso:
  python send_file_telegram.py /ruta/al/archivo.dump
  python send_file_telegram.py            # Envía el backup más reciente del directorio backups

Requisitos:
  Variables de entorno TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID.
  Opcional: archivo .env en el mismo directorio del script con esas claves.
"""

import os
import sys
import time
import json
import mimetypes
import traceback
from pathlib import Path
from typing import Optional

try:
	import requests  # type: ignore
except ImportError:  # Fallback mínimo sin romper
	print("ERROR: La librería 'requests' es necesaria. Instala con: pip install requests", file=sys.stderr)
	sys.exit(2)


def load_env_file(script_dir: Path) -> None:
	env_file = script_dir / '.env'
	if env_file.exists():
		for line in env_file.read_text(encoding='utf-8').splitlines():
			line = line.strip()
			if not line or line.startswith('#') or '=' not in line:
				continue
			key, value = line.split('=', 1)
			if key not in os.environ:  # No sobre-escribir si ya está definida
				os.environ[key] = value


def find_latest_backup(backups_dir: Path) -> Optional[Path]:
	if not backups_dir.exists():
		return None
	candidates = sorted(backups_dir.glob('backup_*.dump'), key=lambda p: p.stat().st_mtime, reverse=True)
	return candidates[0] if candidates else None


def send_file(token: str, chat_id: str, file_path: Path, caption: str = "Backup") -> None:
	url = f"https://api.telegram.org/bot{token}/sendDocument"
	mime_type, _ = mimetypes.guess_type(str(file_path))
	mime_type = mime_type or 'application/octet-stream'

	with file_path.open('rb') as fh:
		files = {'document': (file_path.name, fh, mime_type)}
		data = {'chat_id': chat_id, 'caption': caption}
		resp = requests.post(url, data=data, files=files, timeout=60)

	if resp.status_code != 200:
		raise RuntimeError(f"Telegram API respondió {resp.status_code}: {resp.text[:300]}")

	payload = resp.json()
	if not payload.get('ok'):
		raise RuntimeError(f"Error en respuesta Telegram: {json.dumps(payload, ensure_ascii=False)[:300]}")


def main():
	script_dir = Path(__file__).resolve().parent
	load_env_file(script_dir)

	token = os.getenv('TELEGRAM_BOT_TOKEN')
	chat_id = os.getenv('TELEGRAM_CHAT_ID')
	if not token or not chat_id:
		print("❌ Faltan variables TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID", file=sys.stderr)
		sys.exit(3)

	# Determinar archivo a enviar
	if len(sys.argv) > 1:
		target = Path(sys.argv[1]).expanduser().resolve()
	else:
		target = find_latest_backup(script_dir / 'backups')
		if target is None:
			print("❌ No se encontró ningún backup para enviar", file=sys.stderr)
			sys.exit(4)

	if not target.exists() or not target.is_file():
		print(f"❌ Archivo no válido: {target}", file=sys.stderr)
		sys.exit(5)

	size_mb = target.stat().st_size / (1024 * 1024)
	print(f"📦 Enviando '{target.name}' ({size_mb:.2f} MB) a Telegram...")

	caption = f"Backup {target.name} ({time.strftime('%Y-%m-%d %H:%M:%S')})"

	try:
		send_file(token, chat_id, target, caption=caption)
		print("✅ Envío completado correctamente")
	except Exception as e:  # noqa: BLE001
		print("❌ Error enviando archivo por Telegram:", file=sys.stderr)
		print(str(e), file=sys.stderr)
		traceback.print_exc()
		sys.exit(6)


if __name__ == '__main__':
	main()

