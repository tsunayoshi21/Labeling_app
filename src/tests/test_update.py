#!/usr/bin/env python3
"""Script de prueba para verificar la actualización de anotaciones"""

import requests
import json

BASE_URL = "http://localhost:5000/api/v2"

def test_login_and_update():
    """Prueba el login y actualización de anotación"""
    session = requests.Session()
    
    # Login como admin
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    response = session.post(f"{BASE_URL}/login", json=login_data)
    print(f"Login response: {response.status_code}")
    if response.status_code == 200:
        print(f"Login successful: {response.json()}")
    else:
        print(f"Login failed: {response.text}")
        return
    
    # Obtener siguiente tarea
    response = session.get(f"{BASE_URL}/task/next")
    print(f"Next task response: {response.status_code}")
    if response.status_code == 200:
        task_data = response.json()
        print(f"Task data: {task_data}")
        
        annotation_id = task_data['annotation_id']
        
        # Probar actualización con status 'approved' sin texto corregido
        update_data = {
            'status': 'approved'  # Sin corrected_text para probar la funcionalidad
        }
        
        response = session.put(f"{BASE_URL}/annotations/{annotation_id}", json=update_data)
        print(f"Update response: {response.status_code}")
        if response.status_code == 200:
            print(f"Update successful: {response.json()}")
        else:
            print(f"Update failed: {response.text}")
    else:
        print(f"No tasks available: {response.text}")

if __name__ == "__main__":
    test_login_and_update()
