"""
Flask web application for the osteo_scheduler system.

This module provides the web interface for:
- Input data entry (subjects, lecturers, rooms, etc.)
- Schedule generation and viewing
- Manual adjustments to schedules
- PDF export functionality
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import json
import os
from datetime import datetime
from typing import Dict, List

from models import (
    Subject, Lecturer, Room, Week, TimeSlot, Block,
    ScheduledSession, Schedule, DayOfWeek
)
from scheduler import SchedulingAlgorithm, SchedulingHelper
from pdf_export import PDFExporter

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# In-memory storage (in production, use a database)
app_data = {
    'subjects': [],
    'lecturers': [],
    'rooms': [],
    'weeks': [],
    'blocks': [],
    'schedule': None,
    'fixed_sessions': []
}


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/setup')
def setup():
    """Setup page for data entry."""
    return render_template('setup.html')


@app.route('/schedule')
def schedule_view():
    """Schedule viewing page."""
    return render_template('schedule.html')


# API Endpoints

@app.route('/api/lecturers', methods=['GET', 'POST', 'DELETE'])
def lecturers_api():
    """Manage lecturers."""
    if request.method == 'GET':
        return jsonify([{
            'id': l.id,
            'name': l.name,
            'max_hours_per_week': l.max_hours_per_week,
            'available_slots': [{
                'day': slot.day.name,
                'start_hour': slot.start_hour,
                'start_minute': slot.start_minute,
                'duration_minutes': slot.duration_minutes
            } for slot in l.available_slots]
        } for l in app_data['lecturers']])
    
    elif request.method == 'POST':
        data = request.json
        
        # Parse available slots
        available_slots = []
        for slot_data in data.get('available_slots', []):
            available_slots.append(TimeSlot(
                day=DayOfWeek[slot_data['day']],
                start_hour=slot_data['start_hour'],
                start_minute=slot_data['start_minute'],
                duration_minutes=slot_data['duration_minutes']
            ))
        
        lecturer = Lecturer(
            id=data['id'],
            name=data['name'],
            available_slots=available_slots,
            max_hours_per_week=data.get('max_hours_per_week')
        )
        
        app_data['lecturers'].append(lecturer)
        return jsonify({'status': 'success', 'id': lecturer.id})
    
    elif request.method == 'DELETE':
        lecturer_id = request.json.get('id')
        app_data['lecturers'] = [l for l in app_data['lecturers'] if l.id != lecturer_id]
        return jsonify({'status': 'success'})


@app.route('/api/rooms', methods=['GET', 'POST', 'DELETE'])
def rooms_api():
    """Manage rooms."""
    if request.method == 'GET':
        return jsonify([{
            'id': r.id,
            'name': r.name,
            'capacity': r.capacity,
            'features': list(r.features)
        } for r in app_data['rooms']])
    
    elif request.method == 'POST':
        data = request.json
        room = Room(
            id=data['id'],
            name=data['name'],
            capacity=data['capacity'],
            features=set(data.get('features', []))
        )
        app_data['rooms'].append(room)
        return jsonify({'status': 'success', 'id': room.id})
    
    elif request.method == 'DELETE':
        room_id = request.json.get('id')
        app_data['rooms'] = [r for r in app_data['rooms'] if r.id != room_id]
        return jsonify({'status': 'success'})


@app.route('/api/subjects', methods=['GET', 'POST', 'DELETE'])
def subjects_api():
    """Manage subjects."""
    if request.method == 'GET':
        return jsonify([{
            'id': s.id,
            'name': s.name,
            'duration_minutes': s.duration_minutes,
            'required_lecturers': [l.id for l in s.required_lecturers],
            'min_capacity': s.min_capacity,
            'required_features': list(s.required_features),
            'preferred_days': [d.name for d in s.preferred_days] if s.preferred_days else None,
            'sessions_per_week': s.sessions_per_week
        } for s in app_data['subjects']])
    
    elif request.method == 'POST':
        data = request.json
        
        # Find lecturer objects
        required_lecturers = [
            l for l in app_data['lecturers'] 
            if l.id in data.get('required_lecturers', [])
        ]
        
        # Parse preferred days
        preferred_days = None
        if data.get('preferred_days'):
            preferred_days = [DayOfWeek[d] for d in data['preferred_days']]
        
        subject = Subject(
            id=data['id'],
            name=data['name'],
            duration_minutes=data['duration_minutes'],
            required_lecturers=required_lecturers,
            min_capacity=data['min_capacity'],
            required_features=set(data.get('required_features', [])),
            preferred_days=preferred_days,
            sessions_per_week=data.get('sessions_per_week', 1)
        )
        
        app_data['subjects'].append(subject)
        return jsonify({'status': 'success', 'id': subject.id})
    
    elif request.method == 'DELETE':
        subject_id = request.json.get('id')
        app_data['subjects'] = [s for s in app_data['subjects'] if s.id != subject_id]
        return jsonify({'status': 'success'})


@app.route('/api/weeks', methods=['GET', 'POST'])
def weeks_api():
    """Manage weeks."""
    if request.method == 'GET':
        return jsonify([{
            'week_number': w.week_number,
            'year': w.year,
            'blocks': [b.id for b in w.blocks]
        } for w in app_data['weeks']])
    
    elif request.method == 'POST':
        data = request.json
        
        # Find or create blocks
        blocks = []
        for block_id in data.get('blocks', []):
            block = next((b for b in app_data['blocks'] if b.id == block_id), None)
            if block:
                blocks.append(block)
        
        week = Week(
            week_number=data['week_number'],
            year=data['year'],
            blocks=blocks
        )
        
        app_data['weeks'].append(week)
        return jsonify({'status': 'success'})


@app.route('/api/blocks', methods=['GET', 'POST'])
def blocks_api():
    """Manage blocks."""
    if request.method == 'GET':
        return jsonify([{
            'id': b.id,
            'name': b.name,
            'time_slots': [{
                'day': slot.day.name,
                'start_hour': slot.start_hour,
                'start_minute': slot.start_minute,
                'duration_minutes': slot.duration_minutes
            } for slot in b.time_slots]
        } for b in app_data['blocks']])
    
    elif request.method == 'POST':
        data = request.json
        
        # Parse time slots
        time_slots = []
        for slot_data in data.get('time_slots', []):
            time_slots.append(TimeSlot(
                day=DayOfWeek[slot_data['day']],
                start_hour=slot_data['start_hour'],
                start_minute=slot_data['start_minute'],
                duration_minutes=slot_data['duration_minutes']
            ))
        
        block = Block(
            id=data['id'],
            name=data['name'],
            time_slots=time_slots
        )
        
        app_data['blocks'].append(block)
        return jsonify({'status': 'success', 'id': block.id})


@app.route('/api/generate-schedule', methods=['POST'])
def generate_schedule():
    """Generate a schedule using the scheduling algorithm."""
    try:
        data = request.json
        max_attempts = data.get('max_attempts', 1000)
        randomize = data.get('randomize', True)
        
        # Create scheduling algorithm
        algorithm = SchedulingAlgorithm(
            subjects=app_data['subjects'],
            rooms=app_data['rooms'],
            weeks=app_data['weeks'],
            fixed_sessions=app_data['fixed_sessions']
        )
        
        # Generate schedule
        schedule = algorithm.generate_schedule(
            max_attempts=max_attempts,
            randomize=randomize
        )
        
        if schedule:
            app_data['schedule'] = schedule
            stats = SchedulingHelper.get_schedule_statistics(schedule)
            
            return jsonify({
                'status': 'success',
                'message': 'Schedule generated successfully',
                'statistics': stats,
                'session_count': len(schedule.sessions)
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate a complete schedule'
            }), 400
    
    except Exception as e:
        # Log the error internally but don't expose stack trace details
        app.logger.error(f'Schedule generation error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while generating the schedule. Please check your input data and try again.'
        }), 500


@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    """Get the current schedule."""
    if not app_data['schedule']:
        return jsonify({'status': 'error', 'message': 'No schedule generated'}), 404
    
    schedule = app_data['schedule']
    return jsonify({
        'sessions': [{
            'subject_id': s.subject.id,
            'subject_name': s.subject.name,
            'week_number': s.week.week_number,
            'year': s.week.year,
            'day': s.time_slot.day.name,
            'start_hour': s.time_slot.start_hour,
            'start_minute': s.time_slot.start_minute,
            'duration_minutes': s.time_slot.duration_minutes,
            'room_id': s.room.id,
            'room_name': s.room.name,
            'lecturers': [l.name for l in s.subject.required_lecturers],
            'is_fixed': s.is_fixed
        } for s in schedule.sessions]
    })


@app.route('/api/schedule/session', methods=['DELETE', 'PUT'])
def modify_session():
    """Delete or modify a session (manual adjustment)."""
    if not app_data['schedule']:
        return jsonify({'status': 'error', 'message': 'No schedule generated'}), 404
    
    data = request.json
    schedule = app_data['schedule']
    
    if request.method == 'DELETE':
        # Find and remove session
        session_index = data.get('session_index')
        if 0 <= session_index < len(schedule.sessions):
            removed_session = schedule.sessions.pop(session_index)
            return jsonify({
                'status': 'success',
                'message': f'Removed session: {removed_session.subject.name}'
            })
        return jsonify({'status': 'error', 'message': 'Invalid session index'}), 400
    
    elif request.method == 'PUT':
        # Move a session to a different time/room
        session_index = data.get('session_index')
        if 0 <= session_index < len(schedule.sessions):
            session = schedule.sessions[session_index]
            
            # Update time slot if provided
            if 'time_slot' in data:
                ts_data = data['time_slot']
                session.time_slot = TimeSlot(
                    day=DayOfWeek[ts_data['day']],
                    start_hour=ts_data['start_hour'],
                    start_minute=ts_data['start_minute'],
                    duration_minutes=ts_data['duration_minutes']
                )
            
            # Update room if provided
            if 'room_id' in data:
                room = next((r for r in app_data['rooms'] if r.id == data['room_id']), None)
                if room:
                    session.room = room
            
            # Check for conflicts
            if schedule.is_valid():
                return jsonify({'status': 'success', 'message': 'Session updated'})
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Update would create conflicts'
                }), 400
        
        return jsonify({'status': 'error', 'message': 'Invalid session index'}), 400


@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """Export schedule to PDF."""
    if not app_data['schedule']:
        return jsonify({'status': 'error', 'message': 'No schedule generated'}), 404
    
    data = request.json
    view_type = data.get('view_type', 'weekly')
    
    # Create PDF exporter
    exporter = PDFExporter(app_data['schedule'])
    
    # Generate PDF to buffer
    buffer = exporter.export_to_buffer(view_type=view_type)
    
    # Send file
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'schedule_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )


@app.route('/api/initialize-sample-data', methods=['POST'])
def initialize_sample_data():
    """Initialize with sample data for testing."""
    # Clear existing data
    app_data['subjects'] = []
    app_data['lecturers'] = []
    app_data['rooms'] = []
    app_data['weeks'] = []
    app_data['blocks'] = []
    app_data['schedule'] = None
    app_data['fixed_sessions'] = []
    
    # Create sample lecturers
    all_slots = SchedulingHelper.create_standard_time_slots()
    
    lecturer1 = Lecturer(id='L1', name='Dr. Smith', available_slots=all_slots)
    lecturer2 = Lecturer(id='L2', name='Dr. Johnson', available_slots=all_slots)
    lecturer3 = Lecturer(id='L3', name='Dr. Williams', available_slots=all_slots)
    
    app_data['lecturers'] = [lecturer1, lecturer2, lecturer3]
    
    # Create sample rooms
    room1 = Room(id='R1', name='Room A', capacity=30, features={'projector', 'whiteboard'})
    room2 = Room(id='R2', name='Room B', capacity=50, features={'projector', 'computer'})
    room3 = Room(id='R3', name='Lab 1', capacity=20, features={'lab_equipment'})
    
    app_data['rooms'] = [room1, room2, room3]
    
    # Create sample subjects
    subject1 = Subject(
        id='S1', name='Anatomy', duration_minutes=60,
        required_lecturers=[lecturer1], min_capacity=30,
        required_features={'projector'}, sessions_per_week=2
    )
    subject2 = Subject(
        id='S2', name='Physiology', duration_minutes=60,
        required_lecturers=[lecturer2], min_capacity=30,
        required_features={'projector'}, sessions_per_week=2
    )
    subject3 = Subject(
        id='S3', name='Practical Lab', duration_minutes=120,
        required_lecturers=[lecturer3], min_capacity=20,
        required_features={'lab_equipment'}, sessions_per_week=1
    )
    
    app_data['subjects'] = [subject1, subject2, subject3]
    
    # Create blocks
    block_definitions = {
        'Morning': (8, 12),
        'Afternoon': (13, 17)
    }
    blocks = SchedulingHelper.create_blocks_from_slots(all_slots, block_definitions)
    app_data['blocks'] = blocks
    
    # Create sample weeks
    week1 = Week(week_number=1, year=2025, blocks=blocks)
    week2 = Week(week_number=2, year=2025, blocks=blocks)
    
    app_data['weeks'] = [week1, week2]
    
    return jsonify({
        'status': 'success',
        'message': 'Sample data initialized',
        'lecturers': len(app_data['lecturers']),
        'rooms': len(app_data['rooms']),
        'subjects': len(app_data['subjects']),
        'weeks': len(app_data['weeks'])
    })


if __name__ == '__main__':
    # Get debug mode from environment variable, default to False for production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
