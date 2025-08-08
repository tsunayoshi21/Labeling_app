import os
import sys
from sqlalchemy.orm import Session

# Asegura que src/ esté en el PYTHONPATH para importar correctamente
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from models.database import DatabaseManager, User, Image, Annotation

def migrate_data(sqlite_url, postgres_url):
    # Conectarse a SQLite y PostgreSQL
    sqlite_db = DatabaseManager(database_url=sqlite_url)
    postgres_db = DatabaseManager(database_url=postgres_url)

    # Crear tablas en PostgreSQL (si no existen)
    postgres_db.create_tables()

    # Iniciar sesiones
    sqlite_session: Session = sqlite_db.get_session()
    postgres_session: Session = postgres_db.get_session()

    try:
        print("→ Migrando usuarios...")
        for user in sqlite_session.query(User).all():
            new_user = User(
                username=user.username,
                password=user.password_hash,  # Ya está hasheada
                role=user.role
            )
            postgres_session.add(new_user)

        print("→ Migrando imágenes...")
        for image in sqlite_session.query(Image).all():
            new_image = Image(
                image_path=image.image_path,
                initial_ocr_text=image.initial_ocr_text
            )
            postgres_session.add(new_image)

        print("→ Migrando anotaciones...")
        for annotation in sqlite_session.query(Annotation).all():
            new_annotation = Annotation(
                image_id=annotation.image_id,
                user_id=annotation.user_id,
                corrected_text=annotation.corrected_text,
                status=annotation.status,
                updated_at=annotation.updated_at
            )
            postgres_session.add(new_annotation)

        postgres_session.commit()
        print("✅ Migración completada exitosamente.")
    except Exception as e:
        postgres_session.rollback()
        print("❌ Error durante la migración:", e)
    finally:
        sqlite_session.close()
        postgres_session.close()

if __name__ == "__main__":
    # Desde src/, la ruta relativa a labeling_app.db está dos niveles arriba
    SQLITE_URL = "sqlite:///labeling_app.db"
    POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://labeling_user:supersecret@localhost:5432/labeling_db")
    
    migrate_data(SQLITE_URL, POSTGRES_URL)
