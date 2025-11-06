"""
Integration test for the web application.
Tests the Flask application endpoints without running a full server.
"""

import unittest
import json
import tempfile
from app import app


class TestWebApplication(unittest.TestCase):
    """Test Flask web application endpoints."""
    
    def setUp(self):
        """Set up test client."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_home_page(self):
        """Test home page loads."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Timetable Scheduler', response.data)
    
    def test_data_input_page(self):
        """Test data input page loads."""
        response = self.app.get('/data/input')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Input Data', response.data)
    
    def test_generate_schedule_page(self):
        """Test schedule generation page loads."""
        response = self.app.get('/schedule/generate')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Generate Schedule', response.data)
    
    def test_api_upload_data(self):
        """Test data upload via API."""
        test_data = {
            "lecturers": [
                {"id": "L1", "name": "Dr. Test"}
            ],
            "rooms": [
                {"id": "R1", "name": "Room 1", "capacity": 30}
            ],
            "subjects": [
                {
                    "id": "S1",
                    "name": "Test Subject",
                    "lecturer_id": "L1",
                    "required_hours": 2,
                    "min_students": 10,
                    "max_students": 30
                }
            ],
            "blocks": [
                {
                    "id": "B1",
                    "day": "Monday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "duration_hours": 1
                }
            ]
        }
        
        response = self.app.post('/data/input',
                                data=json.dumps(test_data),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_api_get_current_data(self):
        """Test getting current data via API."""
        # First load some data
        test_data = {
            "lecturers": [{"id": "L1", "name": "Dr. Test"}],
            "rooms": [{"id": "R1", "name": "Room 1", "capacity": 30}],
            "subjects": [{
                "id": "S1",
                "name": "Test Subject",
                "lecturer_id": "L1",
                "required_hours": 2,
                "min_students": 10,
                "max_students": 30
            }],
            "blocks": [{
                "id": "B1",
                "day": "Monday",
                "start_time": "09:00",
                "end_time": "10:00",
                "duration_hours": 1
            }]
        }
        
        self.app.post('/data/input',
                     data=json.dumps(test_data),
                     content_type='application/json')
        
        # Now get the data back
        response = self.app.get('/api/data/current')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['lecturers']), 1)
        self.assertEqual(len(data['rooms']), 1)
        self.assertEqual(len(data['subjects']), 1)
        self.assertEqual(len(data['blocks']), 1)
    
    def test_api_generate_schedule(self):
        """Test schedule generation via API."""
        # First load data
        test_data = {
            "lecturers": [{"id": "L1", "name": "Dr. Test"}],
            "rooms": [{"id": "R1", "name": "Room 1", "capacity": 30}],
            "subjects": [{
                "id": "S1",
                "name": "Test Subject",
                "lecturer_id": "L1",
                "required_hours": 1,
                "min_students": 10,
                "max_students": 30
            }],
            "blocks": [{
                "id": "B1",
                "day": "Monday",
                "start_time": "09:00",
                "end_time": "10:00",
                "duration_hours": 1
            }]
        }
        
        self.app.post('/data/input',
                     data=json.dumps(test_data),
                     content_type='application/json')
        
        # Generate schedule
        response = self.app.post('/schedule/generate',
                                data=json.dumps({"weeks": 1, "availability": []}),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_api_get_current_schedule(self):
        """Test getting current schedule via API."""
        # Load data and generate schedule first
        test_data = {
            "lecturers": [{"id": "L1", "name": "Dr. Test"}],
            "rooms": [{"id": "R1", "name": "Room 1", "capacity": 30}],
            "subjects": [{
                "id": "S1",
                "name": "Test Subject",
                "lecturer_id": "L1",
                "required_hours": 1,
                "min_students": 10,
                "max_students": 30
            }],
            "blocks": [{
                "id": "B1",
                "day": "Monday",
                "start_time": "09:00",
                "end_time": "10:00",
                "duration_hours": 1
            }]
        }
        
        self.app.post('/data/input',
                     data=json.dumps(test_data),
                     content_type='application/json')
        
        self.app.post('/schedule/generate',
                     data=json.dumps({"weeks": 1, "availability": []}),
                     content_type='application/json')
        
        # Get the schedule
        response = self.app.get('/api/schedule/current')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('entries', data)
        self.assertIn('weeks', data)


if __name__ == '__main__':
    unittest.main()
