#!/usr/bin/env python3
"""Script de prueba para el endpoint de anotaciones de imagen"""

import requests
import json

BASE_URL = "http://localhost:5000/api/v2"

def test_admin_endpoints():
    """Prueba los endpoints de administración"""
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
    
    # Probar endpoint de anotaciones de imagen
    image_id = 1
    response = session.get(f"{BASE_URL}/admin/images/{image_id}/annotations")
    print(f"\nImage annotations response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Annotations found: {len(data['annotations'])}")
        if data['annotations']:
            print(f"Sample annotation: {data['annotations'][0]}")
    else:
        print(f"Failed: {response.text}")
    
    # Probar endpoint de todas las imágenes
    response = session.get(f"{BASE_URL}/admin/images")
    print(f"\nAll images response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Images found: {len(data['images'])}")
        if data['images']:
            print(f"Sample image: {data['images'][0]}")
    else:
        print(f"Failed: {response.text}")
    
    # Probar endpoint de todos los usuarios
    response = session.get(f"{BASE_URL}/admin/users")
    print(f"\nAll users response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Users found: {len(data['users'])}")
        if data['users']:
            print(f"Sample user: {data['users'][0]}")
    else:
        print(f"Failed: {response.text}")

if __name__ == "__main__":
    test_admin_endpoints()
