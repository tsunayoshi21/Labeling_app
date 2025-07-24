# Corrector de Transcripciones OCR

Una aplicación web Flask para revisar y corregir transcripciones OCR de imágenes de palabras de manera eficiente.

## Características

- **Interfaz web moderna y responsive**: Diseño optimizado para una experiencia fluida
- **Hotkeys para todas las acciones**: Navegación rápida con teclado
- **Guardado automático y manual**: Preserva el progreso automáticamente y permite guardado manual
- **Reanudación de sesiones**: Continúa desde donde dejaste la última vez
- **Métricas en tiempo real**: Estadísticas de progreso, tasa de error, y rendimiento
- **Navegación flexible**: Avanza, retrocede o salta a cualquier imagen
- **Gestión de errores**: Manejo robusto de imágenes faltantes y errores de red

## Screenshots

![Interfaz Principal](screenshot.png)

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/tuusuario/Labeling_app.git
cd Labeling_app
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura los datos:
   - Coloca tu archivo JSON de transcripciones en `data/words_raw_dict.json`
   - Coloca las imágenes en `data/words_cropped_raw/`

## Uso

1. Ejecuta la aplicación:
```bash
python app.py
```

2. Abre tu navegador en `http://localhost:5000`

3. Usa los siguientes atajos de teclado:
   - **1** o **Espacio**: Marcar transcripción como correcta
   - **2** o **E**: Editar transcripción
   - **3** o **Del**: Descartar imagen
   - **←**: Ir a imagen anterior
   - **Ctrl+S**: Guardar progreso manualmente
   - **Enter**: Confirmar edición
   - **Esc**: Cancelar edición

## Estructura del Proyecto

```
Labeling_app/
├── app.py                 # Backend Flask principal
├── templates/
│   └── index.html        # Frontend HTML/CSS/JS
├── data/                 # Carpeta de datos (no incluida en git)
│   ├── words_raw_dict.json
│   └── words_cropped_raw/
├── requirements.txt      # Dependencias Python
└── README.md            # Este archivo
```

## Funcionalidades Técnicas

### Backend (Flask)
- API REST para navegación y corrección
- Carga incremental de imágenes
- Guardado automático cada 10 correcciones
- Gestión de sesiones y reanudación de progreso
- Cálculo de métricas en tiempo real

### Frontend (HTML/CSS/JS)
- Interfaz responsive con diseño centrado
- Hotkeys laterales para pantallas grandes
- Feedback visual en tiempo real
- Manejo de errores y estados de carga
- Optimización para diferentes tamaños de imagen

## Configuración

El archivo JSON de entrada debe tener la estructura:
```json
{
  "imagen1.jpg": "transcripcion1",
  "imagen2.jpg": "transcripcion2",
  ...
}
```

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## Autor

Creado para facilitar la corrección eficiente de transcripciones OCR en datasets de imágenes de texto.
