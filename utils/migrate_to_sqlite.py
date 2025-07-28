#!/usr/bin/env python3
"""
Script de migración de datos JSON a SQLite
Migra los datos existentes de la aplicación de anotación a la nueva base de datos SQLite
"""
import json
import os
import sys
from pathlib import Path
from sqlalchemy import func

# Agregar el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

from models.database import DatabaseManager, User, Image, Annotation

class DataMigrator:
    """Clase para migrar datos de JSON a SQLite"""
    
    def __init__(self, json_path, corrected_json_path=None, database_url='sqlite:///labeling_app.db'):
        self.json_path = json_path
        self.corrected_json_path = corrected_json_path or json_path.replace('.json', '_corrected.json')
        self.db_manager = DatabaseManager(database_url)
        
    def load_json_data(self):
        """Carga los datos JSON existentes"""
        original_data = {}
        corrected_data = {}
        review_status = {}
        
        # Cargar datos originales
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    raw_original = json.load(f)
                    # El archivo original es un diccionario simple
                    original_data = raw_original
                print(f"Cargados {len(original_data)} elementos del archivo original: {self.json_path}")
            except Exception as e:
                print(f"Error cargando {self.json_path}: {e}")
        
        # Cargar datos corregidos
        if os.path.exists(self.corrected_json_path):
            try:
                with open(self.corrected_json_path, 'r', encoding='utf-8') as f:
                    raw_corrected = json.load(f)
                    
                    # El archivo corregido tiene estructura compleja con "data", "review_status", etc.
                    if isinstance(raw_corrected, dict):
                        if 'data' in raw_corrected:
                            corrected_data = raw_corrected['data']
                            review_status = raw_corrected.get('review_status', {})
                            print(f"Archivo corregido con estructura compleja:")
                            print(f"  - Datos corregidos: {len(corrected_data)}")
                            print(f"  - Estados de revisión: {len(review_status)}")
                            print(f"  - Índice actual: {raw_corrected.get('current_index', 'N/A')}")
                            print(f"  - Total original: {raw_corrected.get('original_count', 'N/A')}")
                        else:
                            # Es un diccionario simple
                            corrected_data = raw_corrected
                            print(f"Cargados {len(corrected_data)} elementos del archivo corregido (formato simple)")
                    else:
                        print("Formato de archivo corregido no reconocido")
                        
            except Exception as e:
                print(f"Error cargando {self.corrected_json_path}: {e}")
        
        return original_data, corrected_data, review_status
    
    def create_database(self):
        """Crea la base de datos y las tablas"""
        print("Creando estructura de base de datos...")
        self.db_manager.create_tables()
        
        # Crear usuario administrador por defecto
        self.db_manager.init_admin_user()
        
        print("Base de datos creada exitosamente")
    
    def migrate_images_and_annotations(self, original_data, corrected_data, review_status=None):
        """Migra las imágenes y crea anotaciones"""
        session = self.db_manager.get_session()
        
        try:
            # Obtener o crear usuario admin para las anotaciones existentes
            admin_user = session.query(User).filter_by(role='admin').first()
            if not admin_user:
                print("Error: No se encontró usuario administrador")
                return
            
            images_created = 0
            annotations_created = 0
            
            # Procesar cada imagen del JSON original
            for image_name, ocr_text in original_data.items():
                # Crear imagen
                image = Image(
                    image_path=image_name,
                    initial_ocr_text=ocr_text
                )
                session.add(image)
                session.flush()  # Para obtener el ID
                images_created += 1
                
                # Determinar el texto corregido y el estado
                corrected_text = corrected_data.get(image_name)
                
                # Verificar el estado de revisión si existe
                is_reviewed = review_status and image_name in review_status
                review_value = review_status.get(image_name) if review_status else None
                
                # Determinar el estado de la anotación
                if is_reviewed and ((review_value == 'correct') or (review_value == 'edited' and corrected_text == ocr_text)):
                    # La imagen fue revisada y marcada como correcta
                    status = 'approved'
                    # Si hay texto corregido diferente, usarlo; sino usar el original
                    final_text = corrected_text if corrected_text else ocr_text
                elif is_reviewed and review_value == 'edited':
                    # Hay texto corregido diferente al original
                    status = 'corrected'
                    final_text = corrected_text if corrected_text else ocr_text
                elif is_reviewed and review_value == 'discarded':
                    status = 'discarded'
                    final_text = None
                else:
                    # No hay corrección o es igual al original
                    status = 'pending'
                    final_text = None
                
                annotation = Annotation(
                    image_id=image.id,
                    user_id=admin_user.id,
                    corrected_text=final_text,
                    status=status
                )
                session.add(annotation)
                annotations_created += 1
            
            session.commit()
            print(f"Migración completada:")
            print(f"  - Imágenes creadas: {images_created}")
            print(f"  - Anotaciones creadas: {annotations_created}")
            
            # Mostrar estadísticas de estados
            stats = session.query(Annotation.status, func.count(Annotation.id)).group_by(Annotation.status).all()
            print(f"  - Estados de anotaciones:")
            for status, count in stats:
                print(f"    * {status}: {count}")
            
        except Exception as e:
            session.rollback()
            print(f"Error en la migración: {e}")
            raise
        finally:
            session.close()
    
    def create_sample_users(self):
        """Crea usuarios de ejemplo para pruebas"""
        session = self.db_manager.get_session()
        
        try:
            sample_users = [
                ('annotator1', 'password123', 'annotator'),
                ('annotator2', 'password123', 'annotator'),
                ('reviewer', 'password123', 'annotator'),
            ]
            
            users_created = 0
            for username, password, role in sample_users:
                # Verificar si el usuario ya existe
                existing_user = session.query(User).filter_by(username=username).first()
                if not existing_user:
                    user = User(username=username, password=password, role=role)
                    session.add(user)
                    users_created += 1
            
            session.commit()
            if users_created > 0:
                print(f"Usuarios de ejemplo creados: {users_created}")
            
        except Exception as e:
            session.rollback()
            print(f"Error creando usuarios de ejemplo: {e}")
        finally:
            session.close()
    
    def assign_sample_tasks(self):
        """Asigna algunas tareas de ejemplo a los usuarios"""
        session = self.db_manager.get_session()
        
        try:
            # Obtener usuarios anotadores
            annotators = session.query(User).filter_by(role='annotator').limit(2).all()
            if len(annotators) < 2:
                print("No hay suficientes usuarios anotadores para asignar tareas")
                return
            
            # Obtener las primeras 5 imágenes
            images = session.query(Image).limit(5).all()
            if not images:
                print("No hay imágenes para asignar")
                return
            
            assignments_created = 0
            
            # Asignar cada imagen a ambos anotadores (overlap para control de calidad)
            for image in images:
                for annotator in annotators:
                    # Verificar que no exista ya una asignación
                    existing = session.query(Annotation).filter_by(
                        image_id=image.id,
                        user_id=annotator.id
                    ).first()
                    
                    if not existing:
                        annotation = Annotation(
                            image_id=image.id,
                            user_id=annotator.id,
                            status='pending'
                        )
                        session.add(annotation)
                        assignments_created += 1
            
            session.commit()
            print(f"Tareas de ejemplo asignadas: {assignments_created}")
            
        except Exception as e:
            session.rollback()
            print(f"Error asignando tareas: {e}")
        finally:
            session.close()
    
    def run_migration(self):
        """Ejecuta la migración completa"""
        print("=== Iniciando migración de JSON a SQLite ===")
        
        # 1. Crear base de datos
        self.create_database()
        
        # 2. Cargar datos JSON
        original_data, corrected_data, review_status = self.load_json_data()
        
        if not original_data:
            print("No se encontraron datos originales para migrar")
            return
        
        # 3. Migrar imágenes y anotaciones
        self.migrate_images_and_annotations(original_data, corrected_data, review_status)
        
        # 4. Crear usuarios de ejemplo
        self.create_sample_users()
        
        # 5. Asignar algunas tareas de ejemplo
        self.assign_sample_tasks()
        
        print("=== Migración completada exitosamente ===")
        print("\nCredenciales por defecto:")
        print("  Admin: admin / admin123")
        print("  Anotadores: annotator1 / password123, annotator2 / password123")

def main():
    """Función principal"""
    # Configuración por defecto basada en los archivos que tienes
    json_path = "data/words_raw_dict.json"
    corrected_json_path = "data/words_raw_dict_corrected_20250724_150949.json"
    
    # Verificar si se pasaron argumentos de línea de comandos
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    if len(sys.argv) > 2:
        corrected_json_path = sys.argv[2]
    
    print(f"Archivos a procesar:")
    print(f"  Original: {json_path}")
    print(f"  Corregido: {corrected_json_path}")
    
    # Ejecutar migración
    migrator = DataMigrator(json_path, corrected_json_path)
    try:
        migrator.run_migration()
    except Exception as e:
        print(f"Error en la migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
