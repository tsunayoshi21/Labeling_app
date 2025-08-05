"""
Servicio de base de datos para la aplicación de anotación colaborativa
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from models.database import DatabaseManager, User, Image, Annotation
import os
from config import Config
# Configurar logger para este módulo
logger = logging.getLogger(__name__)

class DatabaseService:
    """Servicio para operaciones de base de datos"""
    
    def __init__(self, database_url=None):
        config = Config.from_env()
        if database_url is None:
            database_url = config.DATABASE_URL
        self.db_manager = DatabaseManager(database_url)
        logger.info(f"DatabaseService inicializado con URL: {database_url}")
        
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
                logger.info(f"Usuario autenticado exitosamente: {username}")
                # Crear una nueva instancia desvinculada de la sesión
                detached_user = User(username=user.username, password='dummy', role=user.role)
                # Sobrescribir con los valores reales
                detached_user.id = user.id
                detached_user.password_hash = user.password_hash
                return detached_user
            else:
                logger.warning(f"Fallo de autenticación para usuario: {username}")
                return None
        except Exception as e:
            logger.error(f"Error autenticando usuario {username}: {e}")
            return None
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por ID"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                logger.debug(f"Usuario encontrado por ID: {user_id}")
                # Crear una nueva instancia desvinculada de la sesión
                detached_user = User(username=user.username, password='dummy', role=user.role)
                # Sobrescribir con los valores reales
                detached_user.id = user.id
                detached_user.password_hash = user.password_hash
                return detached_user
            else:
                logger.warning(f"Usuario no encontrado por ID: {user_id}")
                return None
        except Exception as e:
            logger.error(f"Error obteniendo usuario por ID {user_id}: {e}")
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
                        annotation.updated_at = datetime.now(timezone.utc)
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

                # Subconsulta: todos los image_id que están en Annotation, excepto los del admin con status 'pending'
                excluded_image_ids = session.query(Annotation.image_id).filter(
                    ~((Annotation.user_id == 1) & (Annotation.status == 'pending'))
                )

                # Consulta principal: dame solo imágenes cuyo id NO está en la subconsulta anterior
                available_images = session.query(Image).filter(
                    ~Image.id.in_(excluded_image_ids)
                ).order_by(func.random()).limit(count).all()

                
            else:
                # Subconsulta: IDs de imágenes que el usuario actual ya tiene asignadas
                user_image_ids = session.query(Annotation.image_id).filter(
                    Annotation.user_id == user_id
                )

                # Subconsulta: IDs de imágenes que el admin ha anotado con estado distinto a 'pending'
                admin_image_ids = session.query(Annotation.image_id).filter(
                    (Annotation.user_id == 1) & (Annotation.status != 'pending')
                )

                # Consulta final: imágenes que están en la lista del admin, pero NO en la del usuario actual
                available_images = session.query(Image).filter(
                    Image.id.in_(admin_image_ids),
                    ~Image.id.in_(user_image_ids)
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
                    annotation.updated_at = datetime.now(timezone.utc)
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
            
            # Crear una instancia desvinculada antes de cerrar la sesión
            detached_user = User(username=user.username, password="", role=user.role)
            detached_user.id = user.id
            detached_user.password_hash = user.password_hash
            
            return detached_user
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
            
            # Crear una instancia desvinculada antes de cerrar la sesión
            detached_image = Image(image_path=image.image_path, initial_ocr_text=image.initial_ocr_text)
            detached_image.id = image.id
            
            return detached_image
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()
    
    # Métodos de estadísticas
    def get_user_stats(self, user_id: int) -> dict:
        """Obtiene estadísticas de un usuario - Optimizada con comparación admin"""
        session = self.get_session()
        try:
            from sqlalchemy import func, case, and_, exists
            
            # Una sola consulta con COUNT y CASE para obtener todas las estadísticas básicas
            result = session.query(
                func.count(Annotation.id).label('total'),
                func.sum(case((Annotation.status == 'pending', 1), else_=0)).label('pending'),
                func.sum(case((Annotation.status == 'corrected', 1), else_=0)).label('corrected'),
                func.sum(case((Annotation.status == 'approved', 1), else_=0)).label('approved'),
                func.sum(case((Annotation.status == 'discarded', 1), else_=0)).label('discarded')
            ).filter(Annotation.user_id == user_id).first()
            
            # Consulta separada para estadísticas de comparación con admin
            # Alias para las anotaciones
            UserAnnotation = session.query(Annotation).filter(
                and_(
                    Annotation.user_id == user_id,
                    Annotation.status.in_(['corrected', 'approved', 'discarded'])
                )
            ).subquery('user_ann')
            
            AdminAnnotation = session.query(Annotation).filter(
                and_(
                    Annotation.user_id == 1,
                    Annotation.status.in_(['corrected', 'approved', 'discarded'])
                )
            ).subquery('admin_ann')
            
            # Anotaciones del usuario que también fueron revieweadas por admin (misma imagen)
            reviewed_by_both = session.query(func.count(UserAnnotation.c.id)).filter(
                exists().where(
                    AdminAnnotation.c.image_id == UserAnnotation.c.image_id
                )
            ).scalar() or 0
            
            # Anotaciones con el mismo status entre usuario y admin (misma imagen y mismo texto corregido)
            matching_with_admin = session.query(func.count(UserAnnotation.c.id)).filter(
                exists().where(
                    and_(
                        AdminAnnotation.c.image_id == UserAnnotation.c.image_id,
                        AdminAnnotation.c.corrected_text == UserAnnotation.c.corrected_text
                    )
                )
            ).scalar() or 0
            
            # Calcular accuracy (porcentaje de coincidencias)
            accuracy_with_admin = round((matching_with_admin / reviewed_by_both * 100), 1) if reviewed_by_both > 0 else 0
            
            stats = {
                'total': result.total or 0,
                'pending': result.pending or 0,
                'corrected': result.corrected or 0,
                'approved': result.approved or 0,
                'discarded': result.discarded or 0,
                'reviewed_by_admin_count': reviewed_by_both,
                'accuracy_with_admin': accuracy_with_admin
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
        """Obtiene la actividad reciente de usuarios - Solo actividad real (no asignaciones)"""
        session = self.get_session()
        try:
            from sqlalchemy import func, desc, and_, case
            
            # Subconsulta para obtener la última actividad real de cada usuario (solo anotaciones revisadas)
            last_activity_subquery = session.query(
                Annotation.user_id,
                func.max(Annotation.updated_at).label('last_activity')
            ).filter(
                Annotation.status.in_(['corrected', 'approved', 'discarded'])
            ).group_by(Annotation.user_id).subquery()
            
            # Query principal que obtiene estadísticas completas pero ordena por actividad real
            user_activity = session.query(
                User.id,
                User.username,
                last_activity_subquery.c.last_activity,
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
            ).join(
                last_activity_subquery, User.id == last_activity_subquery.c.user_id
            ).filter(
                Annotation.user_id.isnot(None)
            ).group_by(
                User.id, User.username, last_activity_subquery.c.last_activity
            ).having(
                last_activity_subquery.c.last_activity.isnot(None)
            ).order_by(
                desc(last_activity_subquery.c.last_activity)
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
    
    def get_all_images_with_annotations(self) -> List[dict]:
        """Obtiene todas las imágenes con información de sus anotaciones"""
        session = self.get_session()
        try:
            from sqlalchemy import func, case
            
            # Obtener imágenes con estadísticas de anotaciones
            images_query = session.query(
                Image,
                func.count(Annotation.id).label('total_annotations'),
                func.sum(case((Annotation.status == 'pending', 1), else_=0)).label('pending'),
                func.sum(case((Annotation.status == 'corrected', 1), else_=0)).label('corrected'),
                func.sum(case((Annotation.status == 'approved', 1), else_=0)).label('approved'),
                func.sum(case((Annotation.status == 'discarded', 1), else_=0)).label('discarded')
            ).outerjoin(Annotation).group_by(Image.id).all()
            
            result = []
            for image, total_annotations, pending, corrected, approved, discarded in images_query:
                result.append({
                    'id': image.id,
                    'image_path': image.image_path,
                    'initial_ocr_text': image.initial_ocr_text[:100] + '...' if len(image.initial_ocr_text) > 100 else image.initial_ocr_text,
                    'total_annotations': total_annotations or 0,
                    'pending': pending or 0,
                    'corrected': corrected or 0,
                    'approved': approved or 0,
                    'discarded': discarded or 0
                })
            
            return result
        finally:
            session.close()

    def get_all_users_with_stats(self) -> List[dict]:
        """Obtiene todos los usuarios con sus estadísticas de tareas"""
        session = self.get_session()
        try:
            from sqlalchemy import func, case
            
            # Consulta que une usuarios con estadísticas de anotaciones
            result = session.query(
                User.id,
                User.username,
                User.role,
                func.count(Annotation.id).label('total_assigned'),
                func.sum(case((Annotation.status.in_(['corrected', 'approved', 'discarded']), 1), else_=0)).label('completed'),
                func.sum(case((Annotation.status == 'pending', 1), else_=0)).label('pending')
            ).outerjoin(Annotation, User.id == Annotation.user_id)\
             .group_by(User.id, User.username, User.role)\
             .order_by(User.username).all()
            
            users_with_stats = []
            for row in result:
                user_dict = {
                    'id': row.id,
                    'username': row.username,
                    'role': row.role,
                    'total_assigned': row.total_assigned or 0,
                    'completed': row.completed or 0,
                    'pending': row.pending or 0
                }
                users_with_stats.append(user_dict)
            
            return users_with_stats
        finally:
            session.close()
    
    def get_user_annotations_detailed(self, user_id: int) -> List[dict]:
        """Obtiene todas las anotaciones de un usuario con detalles, ordenadas por fecha"""
        session = self.get_session()
        try:
            annotations = session.query(Annotation, Image).join(
                Image, Annotation.image_id == Image.id
            ).filter(
                Annotation.user_id == user_id
            ).order_by(Annotation.updated_at.desc()).all()
            
            result = []
            for annotation, image in annotations:
                result.append({
                    'annotation_id': annotation.id,
                    'image_id': image.id,
                    'image_path': image.image_path,
                    'initial_ocr_text': image.initial_ocr_text[:100] + '...' if len(image.initial_ocr_text) > 100 else image.initial_ocr_text,
                    'corrected_text': annotation.corrected_text[:100] + '...' if annotation.corrected_text and len(annotation.corrected_text) > 100 else annotation.corrected_text,
                    'status': annotation.status,
                    'updated_at': annotation.updated_at.isoformat() if annotation.updated_at else None
                })
            
            return result
        finally:
            session.close()

    def delete_user_annotation(self, annotation_id: int, user_id: int) -> bool:
        """Elimina una anotación específica de un usuario"""
        session = self.get_session()
        try:
            annotation = session.query(Annotation).filter_by(
                id=annotation_id,
                user_id=user_id
            ).first()
            
            if annotation:
                session.delete(annotation)
                session.commit()
                logger.info(f"Anotación {annotation_id} del usuario {user_id} eliminada")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error eliminando anotación {annotation_id}: {e}")
            return False
        finally:
            session.close()

    def delete_user_annotations_by_status(self, user_id: int, statuses: List[str]) -> int:
        """Elimina todas las anotaciones de un usuario por estado(s)"""
        session = self.get_session()
        try:
            deleted_count = session.query(Annotation).filter(
                Annotation.user_id == user_id,
                Annotation.status.in_(statuses)
            ).delete(synchronize_session=False)
            
            session.commit()
            logger.info(f"Eliminadas {deleted_count} anotaciones del usuario {user_id} con estados {statuses}")
            return deleted_count
        except Exception as e:
            session.rollback()
            logger.error(f"Error eliminando anotaciones del usuario {user_id}: {e}")
            return 0
        finally:
            session.close()

    def delete_user_completely(self, user_id: int) -> bool:
        """Elimina un usuario y todas sus anotaciones"""
        session = self.get_session()
        try:
            # Primero eliminar todas las anotaciones del usuario
            deleted_annotations = session.query(Annotation).filter_by(user_id=user_id).delete()
            
            # Luego eliminar el usuario
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                session.delete(user)
                session.commit()
                logger.info(f"Usuario {user_id} eliminado junto con {deleted_annotations} anotaciones")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error eliminando usuario {user_id}: {e}")
            return False
        finally:
            session.close()

    def transfer_user_annotations(self, from_user_id: int, to_user_id: int, 
                                 include_pending: bool = True, include_reviewed: bool = True) -> dict:
        """Transfiere anotaciones de un usuario a otro"""
        session = self.get_session()
        try:
            # Verificar que ambos usuarios existen
            from_user = session.query(User).filter_by(id=from_user_id).first()
            to_user = session.query(User).filter_by(id=to_user_id).first()
            
            if not from_user or not to_user:
                return {'success': False, 'error': 'Usuario origen o destino no encontrado'}
            
            # Determinar qué estados incluir
            statuses_to_transfer = []
            if include_pending:
                statuses_to_transfer.append('pending')
            if include_reviewed:
                statuses_to_transfer.extend(['corrected', 'approved', 'discarded'])
            
            if not statuses_to_transfer:
                return {'success': False, 'error': 'No se especificaron estados para transferir'}
            
            # Obtener anotaciones a transferir
            annotations_to_transfer = session.query(Annotation).filter(
                Annotation.user_id == from_user_id,
                Annotation.status.in_(statuses_to_transfer)
            ).all()
            
            transferred_count = 0
            skipped_count = 0
            
            for annotation in annotations_to_transfer:
                # Verificar si el usuario destino ya tiene esta imagen asignada
                existing = session.query(Annotation).filter_by(
                    user_id=to_user_id,
                    image_id=annotation.image_id
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Transferir la anotación
                annotation.user_id = to_user_id
                # Si es una anotación revisada, mantener el estado; si es pending, resetear fecha
                if annotation.status == 'pending':
                    annotation.updated_at = datetime.now(timezone.utc)
                
                transferred_count += 1
            
            session.commit()
            
            logger.info(f"Transferidas {transferred_count} anotaciones de usuario {from_user_id} a {to_user_id}")
            
            return {
                'success': True,
                'transferred': transferred_count,
                'skipped': skipped_count,
                'total_attempted': len(annotations_to_transfer)
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error transfiriendo anotaciones: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            session.close()
