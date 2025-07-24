#!/usr/bin/env python3
"""
Script para actualizar el review_status en archivos de progreso existentes.
Este script compara el diccionario de checkpoint con el original para determinar
el estado de cada imagen hasta el current_index.
"""

import os
import json
import glob
from datetime import datetime

# CONFIGURACIÓN - Ajusta estas rutas según tu setup
JSON_ORIGINAL_PATH = "data/words_raw_dict.json"
PROGRESS_FILES_PATTERN = "data/words_raw_dict_corrected_*.json"

def load_original_data():
    """Cargar el JSON original"""
    if not os.path.exists(JSON_ORIGINAL_PATH):
        raise FileNotFoundError(f"No se encontró el archivo JSON original: {JSON_ORIGINAL_PATH}")
    
    with open(JSON_ORIGINAL_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def determine_review_status(original_data, current_data, image_keys, current_index):
    """
    Determinar el estado de revisión comparando original vs actual hasta current_index.
    
    Lógica:
    - Si la key no existe en current_data: 'discarded'
    - Si la key existe y el valor es igual al original: 'correct'
    - Si la key existe y el valor es diferente al original: 'edited'
    """
    review_status = {}
    
    # Solo revisar hasta el current_index
    for i in range(min(current_index, len(image_keys))):
        image_key = image_keys[i]
        
        if image_key not in current_data:
            # La imagen fue descartada
            review_status[image_key] = 'discarded'
        elif image_key in original_data:
            # Comparar transcripciones
            if current_data[image_key] == original_data[image_key]:
                review_status[image_key] = 'correct'
            else:
                review_status[image_key] = 'edited'
        else:
            # Caso extraño: imagen en current pero no en original (no debería pasar)
            print(f"⚠️ Advertencia: {image_key} está en current_data pero no en original_data")
            review_status[image_key] = 'edited'  # Asumir editada por precaución
    
    return review_status

def update_progress_file(file_path, original_data):
    """Actualizar un archivo de progreso específico"""
    print(f"\n📄 Procesando: {file_path}")
    
    # Leer archivo de progreso
    with open(file_path, 'r', encoding='utf-8') as f:
        progress_data = json.load(f)
    
    # Verificar formato
    if not isinstance(progress_data, dict) or 'data' not in progress_data:
        print(f"❌ Archivo {file_path} no tiene el formato esperado (falta 'data')")
        return False
    
    current_data = progress_data['data']
    current_index = progress_data.get('current_index', 0)
    image_keys = list(original_data.keys())  # Mantener orden original
    
    print(f"   📊 Current index: {current_index}")
    print(f"   📊 Total imágenes originales: {len(image_keys)}")
    print(f"   📊 Imágenes en current_data: {len(current_data)}")
    
    # Calcular review_status
    new_review_status = determine_review_status(original_data, current_data, image_keys, current_index)
    
    # Estadísticas del review_status calculado
    correct_count = sum(1 for status in new_review_status.values() if status == 'correct')
    edited_count = sum(1 for status in new_review_status.values() if status == 'edited')
    discarded_count = sum(1 for status in new_review_status.values() if status == 'discarded')
    
    print(f"   ✅ Correctas: {correct_count}")
    print(f"   ✏️ Editadas: {edited_count}")
    print(f"   🗑️ Descartadas: {discarded_count}")
    print(f"   📋 Total revisadas: {len(new_review_status)}")
    
    # Actualizar el archivo de progreso
    progress_data['review_status'] = new_review_status
    progress_data['updated_timestamp'] = datetime.now().isoformat()
    progress_data['migration_note'] = 'review_status actualizado automáticamente por update_review_status.py'
    
    # Crear backup
    backup_path = file_path + '.backup'
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        print(f"   💾 Backup creado: {backup_path}")
    
    # Guardar archivo actualizado
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ Archivo actualizado exitosamente!")
    return True

def main():
    """Función principal"""
    print("🔄 Iniciando actualización de review_status...")
    
    try:
        # Cargar datos originales
        print(f"📖 Cargando datos originales desde: {JSON_ORIGINAL_PATH}")
        original_data = load_original_data()
        print(f"   ✅ {len(original_data)} imágenes originales cargadas")
        
        # Buscar archivos de progreso
        progress_files = glob.glob(PROGRESS_FILES_PATTERN)
        if not progress_files:
            print(f"❌ No se encontraron archivos de progreso con el patrón: {PROGRESS_FILES_PATTERN}")
            return
        
        print(f"📂 Encontrados {len(progress_files)} archivos de progreso:")
        for f in progress_files:
            print(f"   - {f}")
        
        # Procesar cada archivo
        updated_count = 0
        for file_path in progress_files:
            if update_progress_file(file_path, original_data):
                updated_count += 1
        
        print(f"\n🎉 Proceso completado!")
        print(f"   📊 Archivos procesados: {len(progress_files)}")
        print(f"   ✅ Archivos actualizados: {updated_count}")
        print(f"   ❌ Archivos con errores: {len(progress_files) - updated_count}")
        
        if updated_count > 0:
            print("\n💡 Recomendaciones:")
            print("   - Los archivos originales se respaldaron con extensión .backup")
            print("   - Reinicia la aplicación Flask para ver las estadísticas actualizadas")
            print("   - Verifica que las métricas se vean correctas en la interfaz web")
        
    except Exception as e:
        print(f"💥 Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
