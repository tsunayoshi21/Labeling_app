# 🐳 Docker

La carpeta `docker` contiene todos los archivos necesarios para la creación y ejecución de contenedores Docker específicos para cada módulo del proyecto. Aquí encontrarás Dockerfiles, archivos docker-compose y requisitos específicos por módulo.

## 🗂️ Estructura interna

La estructura general de esta carpeta es:

```bash
docker/
├── modulo_1/
│   ├── Dockerfile
│   ├── compose.yml
│   └── requirements.txt
├── modulo_n/
│   ├── Dockerfile
│   ├── compose.yml
│   └── requirements.txt
```

## 📌 ¿Qué debe incluirse aquí?

- **Dockerfile:** Archivo para construir imágenes Docker personalizadas con todas las dependencias y configuraciones necesarias por módulo.
- **compose.yml:** Archivo para definir la configuración de ejecución del contenedor Docker (redes, volúmenes, puertos y variables de entorno).
- **requirements.txt:** Archivo que lista claramente las dependencias Python específicas del módulo para facilitar su instalación automática dentro del contenedor.

## 🚀 Ejemplo de `compose.yml`

Un ejemplo típico de archivo `compose.yml`:

```yaml
services:
  camera:
    container_name: modulo_x
    build:
      context: .
    devices:                  # para acceder a dispositivos de hardware
      - /dev/video0:/dev/video0
    volumes:                  # para acceder a archivos de configuración/data/cache
      - ./../../configs/modulo_x/config.yml:/config.yml
    ports:                    # para exponer puertos del contenedor en caso de querer acceder directo sin usar nginx
      - 8000:8000
    labels:
      - nginx                 # si queremos exponer el servicio a través de nginx
      - stream_nginx          # si queremos usar stream en nginx
      - sockets_nginx         # si queremos usar sockets en nginx
      - container_name_nginx  # si queremos usar el nombre del contenedor en la url de nginx
```

## 🔧 Buenas prácticas

- Usa nombres descriptivos y consistentes para cada archivo Dockerfile y compose.yml.
- Mantén actualizados los archivos de requisitos con las dependencias mínimas necesarias.
- Documenta claramente dentro de los archivos cualquier configuración específica o requerimiento particular del módulo.
- Reutiliza imágenes base siempre que sea posible para reducir tiempos de construcción y asegurar consistencia entre módulos.
- Los requirements.txt deben tener sus version de cada libreria.

---

✨ **Nota:** Al agregar nuevos módulos, sigue la estructura establecida para asegurar la claridad, mantenibilidad y coherencia del proyecto.
