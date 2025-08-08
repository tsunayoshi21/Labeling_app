"""
Tests para la aplicación OCR
"""
import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open
from services.data_service import DataManager, ImageData, Stats

class TestDataManager:
    
    @pytest.fixture
    def sample_data(self):
        """Datos de muestra para testing"""
        return {
            "image1.jpg": "texto1",
            "image2.jpg": "texto2", 
            "image3.jpg": "texto3"
        }
    
    @pytest.fixture
    def temp_files(self, sample_data):
        """Crear archivos temporales para testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Crear JSON temporal
            json_path = os.path.join(temp_dir, "test.json")
            with open(json_path, 'w') as f:
                json.dump(sample_data, f)
            
            # Crear carpeta de imágenes temporal
            images_dir = os.path.join(temp_dir, "images")
            os.makedirs(images_dir)
            
            # Crear archivos de imagen vacíos
            for image_name in sample_data.keys():
                image_path = os.path.join(images_dir, image_name)
                with open(image_path, 'w') as f:
                    f.write("")
            
            yield json_path, images_dir
    
    def test_load_data_success(self, temp_files, sample_data):
        """Test carga exitosa de datos"""
        json_path, images_dir = temp_files
        
        dm = DataManager(json_path, images_dir)
        dm.load_data()
        
        assert dm.original_data == sample_data
        assert dm.current_data == sample_data
        assert len(dm.image_keys) == 3
        assert dm.current_index == 0
    
    def test_load_data_missing_json(self):
        """Test error cuando falta el JSON"""
        dm = DataManager("nonexistent.json", "/tmp")
        
        with pytest.raises(FileNotFoundError):
            dm.load_data()
    
    def test_get_current_image(self, temp_files, sample_data):
        """Test obtener imagen actual"""
        json_path, images_dir = temp_files
        
        dm = DataManager(json_path, images_dir)
        dm.load_data()
        
        image_data = dm.get_current_image()
        
        assert isinstance(image_data, ImageData)
        assert image_data.key == "image1.jpg"
        assert image_data.transcription == "texto1"
        assert image_data.exists == True
        assert image_data.index == 0
        assert image_data.total == 3
    
    def test_submit_correction_correct(self, temp_files):
        """Test marcar imagen como correcta"""
        json_path, images_dir = temp_files
        
        dm = DataManager(json_path, images_dir)
        dm.load_data()
        
        success = dm.submit_correction('correct', 'image1.jpg')
        
        assert success == True
        assert dm.review_status['image1.jpg'] == 'correct'
        assert dm.current_index == 1
    
    def test_submit_correction_edit(self, temp_files):
        """Test editar transcripción"""
        json_path, images_dir = temp_files
        
        dm = DataManager(json_path, images_dir)
        dm.load_data()
        
        success = dm.submit_correction('edit', 'image1.jpg', 'nuevo_texto')
        
        assert success == True
        assert dm.current_data['image1.jpg'] == 'nuevo_texto'
        assert dm.review_status['image1.jpg'] == 'edited'
    
    def test_submit_correction_discard(self, temp_files):
        """Test descartar imagen"""
        json_path, images_dir = temp_files
        
        dm = DataManager(json_path, images_dir)
        dm.load_data()
        
        success = dm.submit_correction('discard', 'image1.jpg')
        
        assert success == True
        assert 'image1.jpg' not in dm.current_data
        assert dm.review_status['image1.jpg'] == 'discarded'
    
    def test_go_to_index_valid(self, temp_files):
        """Test navegar a índice válido"""
        json_path, images_dir = temp_files
        
        dm = DataManager(json_path, images_dir)
        dm.load_data()
        
        success = dm.go_to_index(2)
        
        assert success == True
        assert dm.current_index == 2
    
    def test_go_to_index_invalid(self, temp_files):
        """Test navegar a índice inválido"""
        json_path, images_dir = temp_files
        
        dm = DataManager(json_path, images_dir)
        dm.load_data()
        
        success = dm.go_to_index(10)
        
        assert success == False
        assert dm.current_index == 0  # No debería cambiar
    
    def test_get_stats(self, temp_files):
        """Test obtener estadísticas"""
        json_path, images_dir = temp_files
        
        dm = DataManager(json_path, images_dir)
        dm.load_data()
        
        # Simular algunas correcciones
        dm.submit_correction('correct', 'image1.jpg')
        dm.submit_correction('edit', 'image2.jpg', 'editado')
        dm.submit_correction('discard', 'image3.jpg')
        
        stats = dm.get_stats()
        
        assert isinstance(stats, Stats)
        assert stats.total_original == 3
        assert stats.reviewed == 3
        assert stats.correct == 1
        assert stats.edited == 1
        assert stats.discarded == 1
    
    def test_is_finished(self, temp_files):
        """Test verificar si terminó"""
        json_path, images_dir = temp_files
        
        dm = DataManager(json_path, images_dir)
        dm.load_data()
        
        assert dm.is_finished() == False
        
        # Avanzar al final
        dm.current_index = 3
        assert dm.is_finished() == True
    
    def test_save_progress(self, temp_files):
        """Test guardar progreso"""
        json_path, images_dir = temp_files
        
        dm = DataManager(json_path, images_dir)
        dm.load_data()
        dm.submit_correction('correct', 'image1.jpg')
        
        # Verificar que no lance excepción
        dm.save_progress()
        
        # Verificar que el archivo se creó
        assert os.path.exists(dm.corrected_json_path)

# Tests de integración para la API
class TestAPIRoutes:
    
    @pytest.fixture
    def client(self):
        """Cliente de test para Flask"""
        from app_refactored import create_app
        
        with patch('services.data_service.DataManager.load_data'):
            app, config = create_app()
            app.config['TESTING'] = True
            
            with app.test_client() as client:
                yield client
    
    def test_current_image_endpoint(self, client):
        """Test endpoint de imagen actual"""
        with patch('routes.api_routes.data_manager') as mock_dm:
            mock_dm.is_finished.return_value = False
            mock_dm.get_current_image.return_value = ImageData(
                key="test.jpg",
                filename="test.jpg", 
                transcription="test",
                exists=True,
                index=0,
                total=10
            )
            mock_dm.get_progress_percentage.return_value = 0.0
            
            response = client.get('/api/current_image')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['finished'] == False
            assert data['image_filename'] == 'test.jpg'
    
    def test_submit_correction_endpoint(self, client):
        """Test endpoint de envío de corrección"""
        with patch('routes.api_routes.data_manager') as mock_dm:
            mock_dm.is_finished.return_value = False
            mock_dm.submit_correction.return_value = True
            mock_dm.should_autosave.return_value = False
            mock_dm.current_index = 1
            
            response = client.post('/api/submit_correction', 
                                 json={'action': 'correct', 'image_key': 'test.jpg'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
    
    def test_stats_endpoint(self, client):
        """Test endpoint de estadísticas"""
        with patch('routes.api_routes.data_manager') as mock_dm:
            mock_stats = Stats(
                total_original=100,
                reviewed=50,
                remaining=50,
                correct=30,
                edited=15,
                discarded=5,
                error_rate=20.0,
                edit_rate=30.0,
                discard_rate=10.0
            )
            mock_dm.get_stats.return_value = mock_stats
            mock_dm.current_data = {}
            mock_dm.get_progress_percentage.return_value = 50.0
            
            response = client.get('/api/stats')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['reviewed'] == 50
            assert data['error_rate'] == 20.0

if __name__ == '__main__':
    pytest.main([__file__])
