"""
Modelos de base de datos SQLite para la aplicación de anotación colaborativa
"""
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash
import os

Base = declarative_base()

class User(Base):
    """Modelo de usuario"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(120), nullable=False)
    role = Column(String(20), nullable=False, default='annotator')  # 'annotator' o 'admin'
    
    # Relaciones
    annotations = relationship('Annotation', back_populates='user')
    
    # Índices para mejorar rendimiento
    __table_args__ = (
        Index('idx_user_role', 'role'),
        Index('idx_user_username', 'username'),
    )
    
    def __init__(self, username, password, role='annotator'):
        self.username = username
        self.set_password(password)
        self.role = role
    
    def set_password(self, password):
        """Establece la contraseña hasheada"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convierte el usuario a diccionario"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class Image(Base):
    """Modelo de imagen"""
    __tablename__ = 'images'
    
    id = Column(Integer, primary_key=True)
    image_path = Column(String(255), nullable=False)
    initial_ocr_text = Column(Text, nullable=False)
    
    # Relaciones
    annotations = relationship('Annotation', back_populates='image')
    
    def to_dict(self):
        """Convierte la imagen a diccionario"""
        return {
            'id': self.id,
            'image_path': self.image_path,
            'initial_ocr_text': self.initial_ocr_text
        }
    
    def __repr__(self):
        return f'<Image {self.image_path}>'

class Annotation(Base):
    """Modelo de anotación/tarea"""
    __tablename__ = 'annotations'
    
    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    corrected_text = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'corrected', 'approved', 'discarded'
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))


    # Relaciones
    image = relationship('Image', back_populates='annotations')
    user = relationship('User', back_populates='annotations')
    
    # Índices para mejorar rendimiento
    __table_args__ = (
        Index('idx_annotation_user_id', 'user_id'),
        Index('idx_annotation_status', 'status'),
        Index('idx_annotation_image_id', 'image_id'),
        Index('idx_annotation_user_status', 'user_id', 'status'),
        Index('idx_annotation_status_image', 'status', 'image_id'),
        Index('idx_annotation_updated_at', 'updated_at'),
    )
    
    def update_status(self, status, corrected_text=None):
        """Actualiza el estado y texto de la anotación"""
        self.status = status
        if corrected_text is not None:
            self.corrected_text = corrected_text
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Convierte la anotación a diccionario"""
        return {
            'id': self.id,
            'image_id': self.image_id,
            'user_id': self.user_id,
            'corrected_text': self.corrected_text,
            'status': self.status,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None

        }
    
    def to_dict_with_relations(self, user_dict=None, image_dict=None):
        """Convierte la anotación a diccionario incluyendo relaciones de forma segura"""
        result = self.to_dict()
        if user_dict:
            result['user'] = user_dict
        if image_dict:
            result['image'] = image_dict
        return result

class DatabaseManager:
    """Manejador de la base de datos"""
    
    def __init__(self, database_url=None):
        if database_url is None:
            database_url = os.getenv("DATABASE_URL", "sqlite:///labeling_app.db")
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Crea todas las tablas"""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """Obtiene una sesión de base de datos"""
        return self.SessionLocal()
    
    def init_admin_user(self, username='admin', password='admin123'):
        """Inicializa el usuario administrador por defecto"""
        session = self.get_session()
        try:
            # Verificar si ya existe un admin
            admin = session.query(User).filter_by(username=username, role='admin').first()
            if not admin:
                admin = User(username=username, password=password, role='admin')
                session.add(admin)
                session.commit()
                print(f"Usuario administrador creado: {username}")
            else:
                print(f"Usuario administrador ya existe: {username}")
        finally:
            session.close()
