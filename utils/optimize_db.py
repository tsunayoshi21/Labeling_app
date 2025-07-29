#!/usr/bin/env python3
"""
Script para recrear la base de datos con los nuevos índices optimizados
"""
import os
import sys
sys.path.append('/home/cristobal/Labeling_app')

from models.database import DatabaseManager

def recreate_database_with_indexes():
    """Recrear la base de datos con los nuevos índices"""
    print("Recreando base de datos con índices optimizados...")
    
    # Backup de la base de datos existente
    import shutil
    if os.path.exists('labeling_app.db'):
        shutil.copy('labeling_app.db', 'labeling_app_backup.db')
        print("Backup creado: labeling_app_backup.db")
    
    # Recrear con nuevos índices
    db_manager = DatabaseManager()
    db_manager.create_tables()
    db_manager.init_admin_user()
    
    print("Base de datos recreada con índices optimizados")
    print("Para restaurar datos, use el script de migración apropiado")

if __name__ == '__main__':
    recreate_database_with_indexes()
