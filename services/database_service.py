"""
Servicio de base de datos para la aplicación de anotación colaborativa
"""
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from models.database import DatabaseManager, User, Image, Annotation

class DatabaseService:
    """Servicio para operaciones de base                    annotation.user_id = user_id
                    annotation.image_id = image.id
                    annotation.status = 'pending'
                    annotation.updated_at = datetime.now()
                    session.add(annotation)
                    assignments_created += 1tos"""
    
    def __init__(self, database_url='sqlite:///labeling_app.db'):
        self.db_manager = DatabaseManager(database_url)
        
    def get_session(self) -> Session:
        """Obtiene una sesión de base de datos"""
        return self.db_manager.get_session()
    
    # Métodos de autenticación
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Autentica un usuario"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user and user.check_password(password):
                # Crear una nueva instancia desvinculada de la sesión usando dict
                user_dict = {
                    'id': user.id,
                    'username': user.username,
                    'password_hash': user.password_hash,
                    'role': user.role
                }
                # Crear instancia temporal con valores dummy para el constructor
                detached_user = User(username=user.username, password='dummy', role=user.role)
                # Sobrescribir con los valores reales
                detached_user.id = user.id
                detached_user.password_hash = user.password_hash
                return detached_user
            return None
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por ID"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                # Crear una nueva instancia desvinculada de la sesión
                detached_user = User(username=user.username, password='dummy', role=user.role)
                # Sobrescribir con los valores reales
                detached_user.id = user.id
                detached_user.password_hash = user.password_hash
                return detached_user
            return None
        finally:
            session.close()
    
    # Métodos para tareas (anotaciones)
    def get_next_pending_task(self, user_id: int) -> Optional[Tuple[Annotation, Image]]:
        """Obtiene la siguiente tarea pendiente para un usuario"""
        session = self.get_session()
        try:
            annotation = session.query(Annotation).join(Image).filter(
                Annotation.user_id == user_id,
                Annotation.status == 'pending'
            ).first()
            
            if annotation:
                # Cargar explícitamente la imagen dentro de la sesión
                image = annotation.image
                
                # Crear instancias desvinculadas
                detached_annotation = Annotation()
                detached_annotation.id = annotation.id
                detached_annotation.image_id = annotation.image_id
                detached_annotation.user_id = annotation.user_id
                detached_annotation.corrected_text = annotation.corrected_text
                detached_annotation.status = annotation.status
                detached_annotation.updated_at = annotation.updated_at
                
                detached_image = Image()
                detached_image.id = image.id
                detached_image.image_path = image.image_path
                detached_image.initial_ocr_text = image.initial_ocr_text
                
                return detached_annotation, detached_image
            return None
        finally:
            session.close()

    def get_user_task_history(self, user_id: int, limit: int = 10) -> List[Tuple[Annotation, Image]]:
        """Obtiene el historial de tareas completadas del usuario"""
        session = self.get_session()
        try:
            annotations = session.query(Annotation).join(Image).filter(
                Annotation.user_id == user_id,
                Annotation.status.in_(['corrected', 'approved', 'discarded'])
            ).order_by(Annotation.updated_at.desc()).limit(limit).all()
            
            # Crear instancias desvinculadas
            result = []
            for annotation in annotations:
                image = annotation.image
                
                detached_annotation = Annotation()
                detached_annotation.id = annotation.id
                detached_annotation.image_id = annotation.image_id
                detached_annotation.user_id = annotation.user_id
                detached_annotation.corrected_text = annotation.corrected_text
                detached_annotation.status = annotation.status
                detached_annotation.updated_at = annotation.updated_at
                
                detached_image = Image()
                detached_image.id = image.id
                detached_image.image_path = image.image_path
                detached_image.initial_ocr_text = image.initial_ocr_text
                
                result.append((detached_annotation, detached_image))
            
            return result
        finally:
            session.close()

    def get_pending_tasks_preview(self, user_id: int, limit: int = 10) -> List[Tuple[Annotation, Image]]:
        """Obtiene una vista previa de las próximas tareas pendientes"""
        session = self.get_session()
        try:
            annotations = session.query(Annotation).join(Image).filter(
                Annotation.user_id == user_id,
                Annotation.status == 'pending'
            ).limit(limit).all()
            
            # Crear instancias desvinculadas (solo necesitamos IDs para la preview)
            result = []
            for annotation in annotations:
                image = annotation.image
                
                detached_annotation = Annotation()
                detached_annotation.id = annotation.id
                detached_annotation.image_id = annotation.image_id
                detached_annotation.user_id = annotation.user_id
                detached_annotation.status = annotation.status
                
                detached_image = Image()
                detached_image.id = image.id
                
                result.append((detached_annotation, detached_image))
            
            return result
        finally:
            session.close()

    def get_specific_task(self, annotation_id: int, user_id: int) -> Optional[Tuple[Annotation, Image]]:
        """Obtiene una tarea específica por annotation_id"""
        session = self.get_session()
        try:
            annotation = session.query(Annotation).join(Image).filter(
                Annotation.id == annotation_id,
                Annotation.user_id == user_id
            ).first()
            
            if annotation:
                image = annotation.image
                
                # Crear instancias desvinculadas
                detached_annotation = Annotation()
                detached_annotation.id = annotation.id
                detached_annotation.image_id = annotation.image_id
                detached_annotation.user_id = annotation.user_id
                detached_annotation.corrected_text = annotation.corrected_text
                detached_annotation.status = annotation.status
                detached_annotation.updated_at = annotation.updated_at
                
                detached_image = Image()
                detached_image.id = image.id
                detached_image.image_path = image.image_path
                detached_image.initial_ocr_text = image.initial_ocr_text
                
                return detached_annotation, detached_image
            return None
        finally:
            session.close()
    
    def update_annotation(self, annotation_id: int, user_id: int, status: str, corrected_text: str = None) -> bool:
        """Actualiza una anotación"""
        session = self.get_session()
        try:
            annotation = session.query(Annotation).filter_by(
                id=annotation_id,
                user_id=user_id
            ).first()
            
            if not annotation:
                return False
            
            # Si se aprueba sin texto corregido, usar el texto original
            if status == 'approved' and not corrected_text:
                # Obtener el texto original de la imagen
                image = session.query(Image).filter_by(id=annotation.image_id).first()
                if image:
                    corrected_text = image.initial_ocr_text
            
            annotation.update_status(status, corrected_text)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_annotation_by_id(self, annotation_id: int, user_id: int = None) -> Optional[Annotation]:
        """Obtiene una anotación por ID, opcionalmente filtrada por usuario"""
        session = self.get_session()
        try:
            query = session.query(Annotation).filter_by(id=annotation_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
            annotation = query.first()
            
            if annotation:
                # Crear una nueva instancia desvinculada usando los atributos directamente
                detached_annotation = Annotation()
                detached_annotation.id = annotation.id
                detached_annotation.image_id = annotation.image_id
                detached_annotation.user_id = annotation.user_id
                detached_annotation.corrected_text = annotation.corrected_text
                detached_annotation.status = annotation.status
                detached_annotation.updated_at = annotation.updated_at
                return detached_annotation
            return None
        finally:
            session.close()
    
    # Métodos de administración
    def assign_tasks(self, user_ids: List[int], image_ids: List[int]) -> int:
        """Asigna tareas a usuarios (solo para admins)"""
        session = self.get_session()
        try:
            assignments_created = 0
            for user_id in user_ids:
                for image_id in image_ids:
                    # Verificar si ya existe la asignación
                    existing = session.query(Annotation).filter_by(
                        user_id=user_id,
                        image_id=image_id
                    ).first()
                    
                    if not existing:
                        annotation = Annotation()
                        annotation.user_id = user_id
                        annotation.image_id = image_id
                        annotation.status = 'pending'
                        annotation.updated_at = datetime.now()
                        session.add(annotation)
                        assignments_created += 1
            
            session.commit()
            return assignments_created
        except Exception:
            session.rollback()
            return 0
        finally:
            session.close()

    def assign_random_tasks(self, user_id: int, count: int, priority_unannotated: bool = True) -> int:
        """Asigna N tareas random a un usuario"""
        session = self.get_session()
        try:
            from sqlalchemy import func, text
            
            # Verificar que el usuario existe
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                raise ValueError(f"Usuario con ID {user_id} no existe")
            
            assignments_created = 0
            
            if priority_unannotated:
                # Priorizar imágenes que nadie ha anotado
                subquery = session.query(Annotation.image_id).subquery()
                available_images = session.query(Image).filter(
                    ~Image.id.in_(session.query(subquery.c.image_id))
                ).order_by(func.random()).limit(count).all()
                
                # Si no hay suficientes imágenes sin anotar, completar con imágenes ya anotadas
                if len(available_images) < count:
                    remaining = count - len(available_images)
                    used_image_ids = [img.id for img in available_images]
                    
                    # Obtener imágenes ya anotadas que no están asignadas a este usuario
                    additional_images = session.query(Image).filter(
                        ~Image.id.in_(used_image_ids),
                        ~Image.id.in_(
                            session.query(Annotation.image_id).filter_by(user_id=user_id)
                        )
                    ).order_by(func.random()).limit(remaining).all()
                    
                    available_images.extend(additional_images)
            else:
                # Obtener imágenes random que no estén ya asignadas a este usuario
                available_images = session.query(Image).filter(
                    ~Image.id.in_(
                        session.query(Annotation.image_id).filter_by(user_id=user_id)
                    )
                ).order_by(func.random()).limit(count).all()
            
            # Crear las asignaciones
            for image in available_images:
                # Verificar que no exista ya la asignación
                existing = session.query(Annotation).filter_by(
                    user_id=user_id,
                    image_id=image.id
                ).first()
                
                if not existing:
                    annotation = Annotation()
                    annotation.user_id = user_id
                    annotation.image_id = image.id
                    annotation.status = 'pending'
                    annotation.updated_at = datetime.utcnow()
                    session.add(annotation)
                    assignments_created += 1
            
            session.commit()
            return assignments_created
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_image_annotations(self, image_id: int) -> List[Annotation]:
        """Obtiene todas las anotaciones de una imagen"""
        session = self.get_session()
        try:
            annotations = session.query(Annotation).filter(
                Annotation.image_id == image_id
            ).all()
            
            # Crear instancias desvinculadas
            detached_annotations = []
            for annotation in annotations:
                detached_annotation = Annotation()
                detached_annotation.id = annotation.id
                detached_annotation.image_id = annotation.image_id
                detached_annotation.user_id = annotation.user_id
                detached_annotation.corrected_text = annotation.corrected_text
                detached_annotation.status = annotation.status
                detached_annotation.updated_at = annotation.updated_at
                detached_annotations.append(detached_annotation)
            
            return detached_annotations
        finally:
            session.close()
    
    def get_all_images(self) -> List[Image]:
        """Obtiene todas las imágenes"""
        session = self.get_session()
        try:
            images = session.query(Image).all()
            
            # Crear instancias desvinculadas
            detached_images = []
            for image in images:
                detached_image = Image()
                detached_image.id = image.id
                detached_image.image_path = image.image_path
                detached_image.initial_ocr_text = image.initial_ocr_text
                detached_images.append(detached_image)
            
            return detached_images
        finally:
            session.close()
    
    def get_all_users(self) -> List[User]:
        """Obtiene todos los usuarios"""
        session = self.get_session()
        try:
            users = session.query(User).all()
            
            # Crear instancias desvinculadas
            detached_users = []
            for user in users:
                detached_user = User(username=user.username, password='dummy', role=user.role)
                detached_user.id = user.id
                detached_user.password_hash = user.password_hash
                detached_users.append(detached_user)
            
            return detached_users
        finally:
            session.close()
    
    def create_user(self, username: str, password: str, role: str = 'annotator') -> Optional[User]:
        """Crea un nuevo usuario"""
        session = self.get_session()
        try:
            # Verificar que no exista el usuario
            existing = session.query(User).filter_by(username=username).first()
            if existing:
                return None
            
            user = User(username=username, password=password, role=role)
            session.add(user)
            session.commit()
            return user
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()
    
    def create_image(self, image_path: str, initial_ocr_text: str) -> Optional[Image]:
        """Crea una nueva imagen"""
        session = self.get_session()
        try:
            image = Image(image_path=image_path, initial_ocr_text=initial_ocr_text)
            session.add(image)
            session.commit()
            return image
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()
    
    # Métodos de estadísticas
    def get_user_stats(self, user_id: int) -> dict:
        """Obtiene estadísticas de un usuario - Optimizada"""
        session = self.get_session()
        try:
            from sqlalchemy import func, case
            
            # Una sola consulta con COUNT y CASE para obtener todas las estadísticas
            result = session.query(
                func.count(Annotation.id).label('total'),
                func.sum(case((Annotation.status == 'pending', 1), else_=0)).label('pending'),
                func.sum(case((Annotation.status == 'corrected', 1), else_=0)).label('corrected'),
                func.sum(case((Annotation.status == 'approved', 1), else_=0)).label('approved'),
                func.sum(case((Annotation.status == 'discarded', 1), else_=0)).label('discarded')
            ).filter(Annotation.user_id == user_id).first()
            
            stats = {
                'total': result.total or 0,
                'pending': result.pending or 0,
                'corrected': result.corrected or 0,
                'approved': result.approved or 0,
                'discarded': result.discarded or 0
            }
            return stats
        finally:
            session.close()

    def get_general_stats(self) -> dict:
        """Obtiene estadísticas generales del sistema - Optimizada"""
        session = self.get_session()
        try:
            from sqlalchemy import func, distinct, case, and_
            
            # Consultas separadas pero más eficientes
            total_users = session.query(func.count(distinct(User.id))).scalar()
            total_images = session.query(func.count(distinct(Image.id))).scalar()
            
            # Consulta única para estadísticas de anotaciones
            annotation_stats = session.query(
                # Anotaciones totales (solo usuarios no-admin)
                func.sum(case((User.role != 'admin', 1), else_=0)).label('total_annotations'),
                # Tareas pendientes (solo usuarios no-admin)
                func.sum(case((and_(Annotation.status == 'pending', User.role != 'admin'), 1), else_=0)).label('pending_tasks'),
                # Tareas completadas (solo usuarios no-admin)
                func.sum(case((and_(Annotation.status.in_(['corrected', 'approved', 'discarded']), User.role != 'admin'), 1), else_=0)).label('completed_tasks'),
                # Imágenes únicas con anotaciones completadas (todos los usuarios para progreso)
                func.count(distinct(case((Annotation.status.in_(['corrected', 'approved', 'discarded']), Annotation.image_id)))).label('annotated_images_for_progress')
            ).join(User, Annotation.user_id == User.id).first()
            
            total_annotations = annotation_stats.total_annotations or 0
            pending_tasks = annotation_stats.pending_tasks or 0
            completed_tasks = annotation_stats.completed_tasks or 0
            annotated_images_for_progress = annotation_stats.annotated_images_for_progress or 0
            
            # Imágenes sin anotar
            unannotated_images = total_images - annotated_images_for_progress
            
            # Calcular progreso
            progress_percentage = round((annotated_images_for_progress / total_images * 100), 1) if total_images > 0 else 0
            
            return {
                'total_users': total_users,
                'total_images': total_images,
                'total_annotations': total_annotations,
                'pending_tasks': pending_tasks,
                'completed_tasks': completed_tasks,
                'unannotated_images': unannotated_images,
                'annotated_images': annotated_images_for_progress,
                'progress_percentage': progress_percentage
            }
        finally:
            session.close()

    def get_recent_user_activity(self, limit: int = 6) -> List[dict]:
        """Obtiene la actividad reciente de usuarios"""
        session = self.get_session()
        try:
            from sqlalchemy import func, desc, and_, case
            
            # Query para obtener usuarios con su última actividad y estadísticas detalladas
            user_activity = session.query(
                User.id,
                User.username,
                func.max(Annotation.updated_at).label('last_activity'),
                func.count(Annotation.id).label('total_assigned'),
                func.sum(
                    case(
                        (Annotation.status.in_(['corrected', 'approved', 'discarded']), 1),
                        else_=0
                    )
                ).label('completed'),
                func.sum(
                    case(
                        (Annotation.status == 'approved', 1),
                        else_=0
                    )
                ).label('approved'),
                func.sum(
                    case(
                        (Annotation.status == 'corrected', 1),
                        else_=0
                    )
                ).label('corrected'),
                func.sum(
                    case(
                        (Annotation.status == 'discarded', 1),
                        else_=0
                    )
                ).label('discarded')
            ).join(
                Annotation, User.id == Annotation.user_id
            ).filter(
                Annotation.user_id.isnot(None)
            ).group_by(
                User.id, User.username
            ).having(
                func.max(Annotation.updated_at).isnot(None)
            ).order_by(
                desc(func.max(Annotation.updated_at))
            ).limit(limit).all()
            
            # Formatear los resultados
            activity_list = []
            for user_id, username, last_activity, total_assigned, completed, approved, corrected, discarded in user_activity:
                # Calcular porcentajes
                approved = approved or 0
                corrected = corrected or 0
                discarded = discarded or 0
                completed = completed or 0
                
                approved_pct = round((approved / completed * 100), 1) if completed > 0 else 0
                corrected_pct = round((corrected / completed * 100), 1) if completed > 0 else 0
                discarded_pct = round((discarded / completed * 100), 1) if completed > 0 else 0
                
                activity_list.append({
                    'user_id': user_id,
                    'username': username,
                    'last_activity': last_activity.isoformat() if last_activity else None,
                    'total_assigned': total_assigned or 0,
                    'completed': completed,
                    'approved': approved,
                    'approved_pct': approved_pct,
                    'corrected': corrected,
                    'corrected_pct': corrected_pct,
                    'discarded': discarded,
                    'discarded_pct': discarded_pct
                })
            
            return activity_list
        except Exception as e:
            print(f"Error in get_recent_user_activity: {e}")
            return []
        finally:
            session.close()
