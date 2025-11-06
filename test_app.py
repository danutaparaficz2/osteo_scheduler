"""
Simple test to verify the Flask app works correctly.
"""

from app import app
import json


def test_routes():
    """Test basic Flask routes."""
    with app.test_client() as client:
        # Test home page
        print("Testing home page...")
        response = client.get('/')
        assert response.status_code == 200
        print("  ✓ Home page works")
        
        # Test setup page
        print("Testing setup page...")
        response = client.get('/setup')
        assert response.status_code == 200
        print("  ✓ Setup page works")
        
        # Test schedule page
        print("Testing schedule page...")
        response = client.get('/schedule')
        assert response.status_code == 200
        print("  ✓ Schedule page works")
        
        # Test API - initialize sample data
        print("\nTesting API - initialize sample data...")
        response = client.post('/api/initialize-sample-data',
                               headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = json.loads(response.data)
        print(f"  ✓ Sample data initialized: {data}")
        
        # Test API - get lecturers
        print("\nTesting API - get lecturers...")
        response = client.get('/api/lecturers')
        assert response.status_code == 200
        data = json.loads(response.data)
        print(f"  ✓ Retrieved {len(data)} lecturers")
        
        # Test API - get rooms
        print("\nTesting API - get rooms...")
        response = client.get('/api/rooms')
        assert response.status_code == 200
        data = json.loads(response.data)
        print(f"  ✓ Retrieved {len(data)} rooms")
        
        # Test API - get subjects
        print("\nTesting API - get subjects...")
        response = client.get('/api/subjects')
        assert response.status_code == 200
        data = json.loads(response.data)
        print(f"  ✓ Retrieved {len(data)} subjects")
        
        # Test API - generate schedule
        print("\nTesting API - generate schedule...")
        response = client.post('/api/generate-schedule',
                               data=json.dumps({'max_attempts': 500, 'randomize': True}),
                               headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        data = json.loads(response.data)
        print(f"  ✓ Schedule generated: {data['session_count']} sessions")
        
        # Test API - get schedule
        print("\nTesting API - get schedule...")
        response = client.get('/api/schedule')
        assert response.status_code == 200
        data = json.loads(response.data)
        print(f"  ✓ Retrieved schedule with {len(data['sessions'])} sessions")
        
        # Test API - export PDF
        print("\nTesting API - export PDF...")
        response = client.post('/api/export-pdf',
                               data=json.dumps({'view_type': 'weekly'}),
                               headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        print(f"  ✓ PDF exported successfully ({len(response.data)} bytes)")


if __name__ == '__main__':
    print("="*60)
    print("Flask App Test")
    print("="*60 + "\n")
    
    test_routes()
    
    print("\n" + "="*60)
    print("All tests passed!")
    print("="*60)
