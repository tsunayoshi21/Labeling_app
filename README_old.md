# Corrector de Transcripciones OCR

Una aplicación web para revisar y corregir transcripciones de imágenes de palabras de manera eficiente.

## Características

- ✅ Interfaz web moderna y responsive
- 🖼️ Visualización de imágenes con transcripciones
- ⚡ Acciones rápidas: Correcta, Editar, Descartar
- 📊 Barra de progreso y estadísticas en tiempo real
- 📈 Métricas de error (tasa de edición y descarte)
- ⌨️ Atajos de teclado para mayor eficiencia
- 💾 Guardado automático del progreso cada 10 imágenes
- 🔄 Botón de guardado manual con confirmación visual
- 📂 Reanudación automática del progreso anterior
- 🗂️ Creación automática de archivo JSON corregido

## Instalación

1. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

## Configuración

Antes de ejecutar la aplicación, debes configurar las rutas en el archivo `app.py`:

```python
# PARÁMETROS PARA CONFIGURAR - MODIFICA ESTAS RUTAS
IMAGES_FOLDER = "/ruta/a/tu/carpeta/de/imagenes"  # Ruta a la carpeta de imágenes
JSON_PATH = "/ruta/a/tu/archivo.json"             # Ruta al JSON original
```

### Ejemplo de configuración actual:
- **Carpeta de imágenes**: `/home/cristobal/BBcroping/resultados/words_cropped_raw`
- **JSON original**: `/home/cristobal/BBcroping/resultados/words_raw_dict.json`

## Formato del JSON

El JSON debe tener el siguiente formato:
```json
{
    "ruta/imagen1.jpg": "transcripción1",
    "ruta/imagen2.jpg": "transcripción2",
    ...
}
```

## Uso

1. Ejecutar la aplicación:
```bash
python app.py
```

2. Abrir el navegador en: `http://localhost:5000`

3. Revisar las imágenes usando las siguientes opciones:
   - **✓ Correcta**: La transcripción es correcta (tecla `1` o `→`)
   - **✏️ Editar**: Corregir la transcripción (tecla `2`)
   - **🗑️ Descartar**: Eliminar imagen del dataset (tecla `3` o `Delete`)

## Atajos de Teclado

- `1` o `→`: Marcar como correcta
- `2`: Editar transcripción
- `3` o `Delete`: Descartar imagen
- `Enter`: Confirmar edición o navegación

## Navegación

- Usa el campo "Ir a imagen" para saltar a cualquier índice específico
- La barra de progreso muestra el avance actual
- Las estadísticas se actualizan en tiempo real

## Archivos Generados

La aplicación crea automáticamente un archivo JSON con las correcciones:
- Formato: `[nombre_original]_corrected_[timestamp].json`
- Ejemplo: `words_raw_dict_corrected_20250724_143022.json`

## Características Técnicas

- **Framework**: Flask (Python)
- **Guardado automático**: Cada 10 imágenes revisadas
- **Manejo de errores**: Imágenes faltantes, archivos corruptos, etc.
- **Responsive**: Funciona en desktop y móvil
- **Persistencia**: El progreso se guarda automáticamente

## Estadísticas Mostradas

- **Total**: Número original de imágenes
- **Revisadas**: Imágenes procesadas hasta ahora
- **Restantes**: Imágenes por revisar
- **Correctas**: Imágenes marcadas como correctas
- **Editadas**: Imágenes con transcripciones corregidas
- **Descartadas**: Imágenes eliminadas del dataset

### Métricas de Error
- **Tasa de Error Total**: Porcentaje de imágenes editadas + descartadas respecto al total revisado
- **Editadas**: Porcentaje de imágenes editadas respecto al total revisado  
- **Descartadas**: Porcentaje de imágenes descartadas respecto al total revisado

## Guardado y Reanudación

### Guardado Automático
- Se guarda automáticamente cada 10 imágenes revisadas
- Se guarda al finalizar la sesión
- Formato del archivo incluye metadatos (índice actual, timestamp, etc.)

### Guardado Manual
- Botón "💾 Guardar Progreso" disponible en todo momento
- Confirmación visual cuando se guarda exitosamente
- Muestra la hora del último guardado

### Reanudación Automática
- Al iniciar la aplicación, busca automáticamente el archivo de progreso más reciente
- Continúa desde donde se quedó la última vez
- Mantiene todas las correcciones realizadas previamente

## Solución de Problemas

### Error: "No se encontró el archivo JSON"
Verifica que la ruta en `JSON_PATH` sea correcta y que el archivo exista.

### Error: "No se encontró la carpeta de imágenes"
Verifica que la ruta en `IMAGES_FOLDER` sea correcta y que la carpeta exista.

### Imagen no se muestra
La aplicación mostrará un mensaje de advertencia si la imagen no existe en la carpeta especificada, pero te permitirá continuar con la revisión.

## Estructura de Archivos

```
Labeling_app/
├── app.py                 # Aplicación principal
├── requirements.txt       # Dependencias
├── README.md             # Este archivo
└── templates/
    └── index.html        # Interfaz web
```
