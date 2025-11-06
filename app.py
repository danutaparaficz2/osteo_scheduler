"""
Flask web application for the timetable scheduler.
Provides UI for data input, viewing schedules, and manual adjustments.
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
import os
import json
from models import TimeSlot, Availability
from data_manager import DataManager, export_timetable_to_json
from scheduler import TimetableScheduler, SchedulerConstraints
from pdf_exporter import PDFExporter
import tempfile

app = Flask(__name__)
app.secret_key = 'osteo-scheduler-secret-key-change-in-production'

# Global data manager and timetable storage
data_manager = DataManager()
current_timetable = None
scheduler = None


@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@app.route('/data/input', methods=['GET', 'POST'])
def data_input():
    """Page for inputting data."""
    if request.method == 'POST':
        try:
            data = request.get_json()
            data_manager.load_from_json(data)
            return jsonify({'success': True, 'message': 'Data loaded successfully'})
        except Exception as e:
            # Log the full error server-side, but don't expose details to user
            app.logger.error(f"Error loading data from JSON: {str(e)}")
            return jsonify({'success': False, 'message': 'Error loading data. Please check your JSON format.'}), 400
    
    return render_template('data_input.html')


@app.route('/api/data/upload', methods=['POST'])
def upload_data():
    """Upload JSON data file."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    if file and file.filename.endswith('.json'):
        try:
            data = json.load(file)
            data_manager.load_from_json(data)
            return jsonify({'success': True, 'message': 'Data uploaded successfully'})
        except Exception as e:
            # Log the full error server-side, but don't expose details to user
            app.logger.error(f"Error uploading file: {str(e)}")
            return jsonify({'success': False, 'message': 'Error loading data file. Please check the format.'}), 400
    
    return jsonify({'success': False, 'message': 'Invalid file type'}), 400


@app.route('/api/data/current', methods=['GET'])
def get_current_data():
    """Get currently loaded data."""
    return jsonify({
        'lecturers': [{'id': l.id, 'name': l.name} for l in data_manager.get_all_lecturers()],
        'rooms': [{'id': r.id, 'name': r.name, 'capacity': r.capacity} for r in data_manager.get_all_rooms()],
        'subjects': [
            {
                'id': s.id,
                'name': s.name,
                'lecturer': s.lecturer.name,
                'required_hours': s.required_hours,
                'min_students': s.min_students,
                'max_students': s.max_students
            }
            for s in data_manager.get_all_subjects()
        ],
        'blocks': [
            {
                'id': b.id,
                'day': b.time_slot.day,
                'start_time': b.time_slot.start_time,
                'end_time': b.time_slot.end_time,
                'duration_hours': b.duration_hours
            }
            for b in data_manager.get_all_blocks()
        ]
    })


@app.route('/schedule/generate', methods=['GET', 'POST'])
def generate_schedule():
    """Generate a new timetable."""
    global current_timetable, scheduler
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            weeks = data.get('weeks', 1)
            
            # Create constraints
            constraints = SchedulerConstraints()
            
            # Add availability constraints if provided
            if 'availability' in data:
                for avail_data in data['availability']:
                    if avail_data['type'] == 'room':
                        availability = Availability(
                            entity_id=avail_data['id'],
                            entity_type='room',
                            available_slots=set()
                        )
                        for slot_data in avail_data['slots']:
                            time_slot = TimeSlot(
                                day=slot_data['day'],
                                start_time=slot_data['start_time'],
                                end_time=slot_data['end_time']
                            )
                            availability.available_slots.add(time_slot)
                        constraints.add_room_availability(avail_data['id'], availability)
                    
                    elif avail_data['type'] == 'lecturer':
                        availability = Availability(
                            entity_id=avail_data['id'],
                            entity_type='lecturer',
                            available_slots=set()
                        )
                        for slot_data in avail_data['slots']:
                            time_slot = TimeSlot(
                                day=slot_data['day'],
                                start_time=slot_data['start_time'],
                                end_time=slot_data['end_time']
                            )
                            availability.available_slots.add(time_slot)
                        constraints.add_lecturer_availability(avail_data['id'], availability)
            
            # Create scheduler and generate timetable
            scheduler = TimetableScheduler(constraints)
            current_timetable = scheduler.generate_timetable(
                subjects=data_manager.get_all_subjects(),
                rooms=data_manager.get_all_rooms(),
                blocks=data_manager.get_all_blocks(),
                weeks=weeks
            )
            
            return jsonify({'success': True, 'message': 'Timetable generated successfully'})
        
        except Exception as e:
            # Log the full error server-side, but don't expose details to user
            app.logger.error(f"Error generating timetable: {str(e)}")
            return jsonify({'success': False, 'message': 'Error generating schedule. Please check your data.'}), 400
    
    return render_template('generate_schedule.html')


@app.route('/schedule/view')
def view_schedule():
    """View the current timetable."""
    if current_timetable is None:
        flash('No timetable generated yet. Please generate a schedule first.', 'warning')
        return redirect(url_for('generate_schedule'))
    
    return render_template('view_schedule.html')


@app.route('/api/schedule/current', methods=['GET'])
def get_current_schedule():
    """Get the current timetable as JSON."""
    if current_timetable is None:
        return jsonify({'success': False, 'message': 'No timetable generated'}), 404
    
    entries_data = []
    for entry in current_timetable.entries:
        entries_data.append({
            'subject_id': entry.subject.id,
            'subject_name': entry.subject.name,
            'lecturer': entry.subject.lecturer.name,
            'room_id': entry.room.id,
            'room_name': entry.room.name,
            'block_id': entry.block.id,
            'day': entry.block.time_slot.day,
            'start_time': entry.block.time_slot.start_time,
            'end_time': entry.block.time_slot.end_time,
            'week': entry.week,
            'is_fixed': entry.is_fixed
        })
    
    return jsonify({
        'success': True,
        'weeks': current_timetable.weeks,
        'entries': entries_data
    })


@app.route('/api/schedule/export/pdf', methods=['POST'])
def export_pdf():
    """Export current timetable to PDF."""
    if current_timetable is None:
        return jsonify({'success': False, 'message': 'No timetable to export'}), 404
    
    try:
        data = request.get_json()
        title = data.get('title', 'Timetable Schedule')
        export_type = data.get('type', 'standard')  # 'standard' or 'by_lecturer'
        
        # Create temporary PDF file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        exporter = PDFExporter()
        
        if export_type == 'by_lecturer':
            exporter.export_by_lecturer(current_timetable, temp_file.name)
        else:
            exporter.export_timetable(current_timetable, temp_file.name, title)
        
        return send_file(
            temp_file.name,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='timetable.pdf'
        )
    
    except Exception as e:
        # Log the full error server-side, but don't expose details to user
        app.logger.error(f"Error exporting timetable to PDF: {str(e)}")
        return jsonify({'success': False, 'message': 'Error exporting PDF. Please try again.'}), 500


@app.route('/api/schedule/export/json', methods=['GET'])
def export_json():
    """Export current timetable to JSON."""
    if current_timetable is None:
        return jsonify({'success': False, 'message': 'No timetable to export'}), 404
    
    try:
        # Create temporary JSON file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w')
        export_timetable_to_json(current_timetable, temp_file.name)
        temp_file.close()
        
        return send_file(
            temp_file.name,
            mimetype='application/json',
            as_attachment=True,
            download_name='timetable.json'
        )
    
    except Exception as e:
        # Log the full error server-side, but don't expose details to user
        app.logger.error(f"Error exporting timetable to JSON: {str(e)}")
        return jsonify({'success': False, 'message': 'Error exporting JSON. Please try again.'}), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Only enable debug mode if explicitly set via environment variable
    # Never use debug=True in production!
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
