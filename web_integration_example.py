"""
Integration example for the web application.
Shows how to integrate time restrictions into the Flask web app.
"""

from flask import Flask, render_template, request, jsonify
from datetime import date, datetime
from models import Lecturer, Room, Subject, Block, TimeSlot
from scheduler import SchedulerConstraints, TimetableScheduler
from time_restrictions import LecturerTimeRestrictionBuilder
from data_loader_with_restrictions import load_data_with_time_restrictions


def create_scheduler_with_restrictions(data_file_path, custom_restrictions=None):
    """
    Create a scheduler with time restrictions loaded from JSON file.
    
    Args:
        data_file_path: Path to JSON data file
        custom_restrictions: Optional dict of additional restrictions to add
        
    Returns:
        Tuple of (scheduler, data_dict)
    """
    # Load data from JSON
    data = load_data_with_time_restrictions(data_file_path)
    
    # Set up constraints
    constraints = SchedulerConstraints()
    
    # Add lecturer time restrictions from JSON
    for lecturer_id, availability in data['lecturer_restrictions'].items():
        constraints.add_lecturer_availability(lecturer_id, availability)
    
    # Add any custom restrictions
    if custom_restrictions:
        for lecturer_id, availability in custom_restrictions.items():
            constraints.add_lecturer_availability(lecturer_id, availability)
    
    # Create scheduler
    scheduler = TimetableScheduler(constraints)
    
    return scheduler, data


def generate_schedule_from_web_form(form_data):
    """
    Generate a schedule from web form input.
    
    Expected form_data format:
    {
        'data_file': 'path/to/data.json',
        'start_date': '2025-01-15',
        'weeks': 4,
        'lecturer_restrictions': [
            {
                'lecturer_id': 'L1',
                'available_dates': [
                    {'date': '2025-01-15', 'morning': True, 'afternoon': False}
                ]
            }
        ]
    }
    """
    # Parse form data
    data_file = form_data.get('data_file')
    start_date_str = form_data.get('start_date')
    weeks = int(form_data.get('weeks', 1))
    
    # Parse start date
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    
    # Build custom restrictions from form
    custom_restrictions = {}
    lecturer_restrictions_data = form_data.get('lecturer_restrictions', [])
    
    for restriction_data in lecturer_restrictions_data:
        lecturer_id = restriction_data['lecturer_id']
        
        if 'available_dates' in restriction_data:
            # Use list format
            from time_restrictions import create_lecturer_availability_from_list
            availability = create_lecturer_availability_from_list(
                lecturer_id,
                restriction_data['available_dates']
            )
            custom_restrictions[lecturer_id] = availability
        
        elif 'available_ranges' in restriction_data:
            # Use range format
            from time_restrictions import create_lecturer_availability_from_ranges
            availability = create_lecturer_availability_from_ranges(
                lecturer_id,
                restriction_data['available_ranges'],
                restriction_data.get('unavailable_dates', [])
            )
            custom_restrictions[lecturer_id] = availability
    
    # Create scheduler
    scheduler, data = create_scheduler_with_restrictions(data_file, custom_restrictions)
    
    # Generate timetable
    timetable = scheduler.generate_timetable(
        subjects=data['subjects'],
        rooms=data['rooms'],
        blocks=data['blocks'],
        weeks=weeks,
        start_date=start_date
    )
    
    return timetable, data


def timetable_to_json(timetable):
    """
    Convert timetable to JSON-serializable format for web display.
    
    Returns:
        List of dictionaries representing schedule entries
    """
    entries = []
    
    for entry in sorted(timetable.entries, key=lambda e: (e.week, e.block.id)):
        entries.append({
            'week': entry.week,
            'date': str(entry.scheduled_date) if entry.scheduled_date else None,
            'day': entry.block.time_slot.day,
            'start_time': entry.block.time_slot.start_time,
            'end_time': entry.block.time_slot.end_time,
            'duration': entry.block.duration_hours,
            'subject_id': entry.subject.id,
            'subject_name': entry.subject.name,
            'lecturer_id': entry.subject.lecturer.id,
            'lecturer_name': entry.subject.lecturer.name,
            'room_id': entry.room.id,
            'room_name': entry.room.name,
            'is_fixed': entry.is_fixed
        })
    
    return entries


# Example Flask routes (to be added to app.py)

"""
# Add to app.py:

@app.route('/api/generate_schedule_with_restrictions', methods=['POST'])
def api_generate_schedule_with_restrictions():
    '''
    API endpoint to generate schedule with time restrictions.
    
    POST body example:
    {
        "data_file": "examples/sample_data_with_time_restrictions.json",
        "start_date": "2025-01-15",
        "weeks": 4,
        "lecturer_restrictions": [
            {
                "lecturer_id": "L1",
                "available_ranges": [
                    {"start": "2025-01-15", "end": "2025-02-15", "morning": true, "afternoon": false}
                ]
            }
        ]
    }
    '''
    try:
        form_data = request.json
        
        # Generate schedule
        timetable, data = generate_schedule_from_web_form(form_data)
        
        # Convert to JSON
        schedule_json = timetable_to_json(timetable)
        
        return jsonify({
            'success': True,
            'schedule': schedule_json,
            'total_entries': len(schedule_json),
            'weeks': timetable.weeks,
            'start_date': str(timetable.start_date)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/validate_lecturer_availability', methods=['POST'])
def api_validate_lecturer_availability():
    '''
    API endpoint to validate if a lecturer is available at a specific date/time.
    
    POST body example:
    {
        "lecturer_id": "L1",
        "date": "2025-01-15",
        "time": "09:00"
    }
    '''
    try:
        data = request.json
        lecturer_id = data['lecturer_id']
        check_date_str = data['date']
        check_time = data['time']
        
        # Parse date
        check_date = datetime.strptime(check_date_str, "%Y-%m-%d").date()
        
        # Determine time of day
        from models import TimeOfDay
        time_of_day = TimeOfDay.from_time_string(check_time)
        
        # Load lecturer restrictions (you'd need to maintain this in session or database)
        # For now, this is a placeholder
        # availability = get_lecturer_availability(lecturer_id)
        
        # Check availability
        # is_available = availability.date_time_restrictions.is_available_on_date(
        #     check_date, time_of_day
        # )
        
        return jsonify({
            'success': True,
            'lecturer_id': lecturer_id,
            'date': check_date_str,
            'time': check_time,
            'time_of_day': time_of_day.value if time_of_day else None,
            # 'is_available': is_available
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/lecturer_restrictions_form')
def lecturer_restrictions_form():
    '''
    Render form for setting up lecturer time restrictions.
    '''
    return render_template('lecturer_restrictions.html')
"""


# Example HTML template (lecturer_restrictions.html)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Lecturer Time Restrictions</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h1>Lecturer Time Restrictions</h1>
        
        <form id="restrictionsForm">
            <div class="form-group">
                <label>Lecturer:</label>
                <select id="lecturerId" name="lecturer_id">
                    <!-- Populated dynamically -->
                </select>
            </div>
            
            <div class="form-group">
                <label>Restriction Type:</label>
                <select id="restrictionType" name="restriction_type">
                    <option value="specific_dates">Specific Dates</option>
                    <option value="date_ranges">Date Ranges</option>
                </select>
            </div>
            
            <div id="specificDatesSection" style="display:none;">
                <h3>Available Dates</h3>
                <div id="datesList"></div>
                <button type="button" onclick="addDateEntry()">Add Date</button>
            </div>
            
            <div id="dateRangesSection" style="display:none;">
                <h3>Available Date Ranges</h3>
                <div id="rangesList"></div>
                <button type="button" onclick="addRangeEntry()">Add Range</button>
                
                <h3>Unavailable Dates (Exceptions)</h3>
                <div id="unavailableList"></div>
                <button type="button" onclick="addUnavailableDate()">Add Exception</button>
            </div>
            
            <button type="submit">Save Restrictions</button>
        </form>
    </div>
    
    <script>
        // JavaScript for dynamic form handling
        document.getElementById('restrictionType').addEventListener('change', function() {
            const type = this.value;
            document.getElementById('specificDatesSection').style.display = 
                type === 'specific_dates' ? 'block' : 'none';
            document.getElementById('dateRangesSection').style.display = 
                type === 'date_ranges' ? 'block' : 'none';
        });
        
        function addDateEntry() {
            const container = document.getElementById('datesList');
            const entry = document.createElement('div');
            entry.className = 'date-entry';
            entry.innerHTML = `
                <input type="date" name="date[]" required>
                <label><input type="checkbox" name="morning[]" checked> Morning</label>
                <label><input type="checkbox" name="afternoon[]" checked> Afternoon</label>
                <button type="button" onclick="this.parentElement.remove()">Remove</button>
            `;
            container.appendChild(entry);
        }
        
        function addRangeEntry() {
            const container = document.getElementById('rangesList');
            const entry = document.createElement('div');
            entry.className = 'range-entry';
            entry.innerHTML = `
                <label>Start: <input type="date" name="range_start[]" required></label>
                <label>End: <input type="date" name="range_end[]" required></label>
                <label><input type="checkbox" name="range_morning[]" checked> Morning</label>
                <label><input type="checkbox" name="range_afternoon[]" checked> Afternoon</label>
                <button type="button" onclick="this.parentElement.remove()">Remove</button>
            `;
            container.appendChild(entry);
        }
        
        function addUnavailableDate() {
            const container = document.getElementById('unavailableList');
            const entry = document.createElement('div');
            entry.className = 'unavailable-entry';
            entry.innerHTML = `
                <input type="date" name="unavailable[]" required>
                <button type="button" onclick="this.parentElement.remove()">Remove</button>
            `;
            container.appendChild(entry);
        }
        
        // Form submission
        document.getElementById('restrictionsForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Collect form data
            const formData = new FormData(this);
            const data = {
                lecturer_id: formData.get('lecturer_id'),
                restriction_type: formData.get('restriction_type')
            };
            
            // Process based on type
            if (data.restriction_type === 'specific_dates') {
                data.available_dates = [];
                const dates = formData.getAll('date[]');
                const mornings = formData.getAll('morning[]');
                const afternoons = formData.getAll('afternoon[]');
                
                dates.forEach((date, i) => {
                    data.available_dates.push({
                        date: date,
                        morning: mornings.includes(i.toString()),
                        afternoon: afternoons.includes(i.toString())
                    });
                });
            } else {
                data.available_ranges = [];
                const starts = formData.getAll('range_start[]');
                const ends = formData.getAll('range_end[]');
                const mornings = formData.getAll('range_morning[]');
                const afternoons = formData.getAll('range_afternoon[]');
                
                starts.forEach((start, i) => {
                    data.available_ranges.push({
                        start: start,
                        end: ends[i],
                        morning: mornings.includes(i.toString()),
                        afternoon: afternoons.includes(i.toString())
                    });
                });
                
                data.unavailable_dates = formData.getAll('unavailable[]');
            }
            
            // Send to server
            try {
                const response = await fetch('/api/save_lecturer_restrictions', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                if (result.success) {
                    alert('Restrictions saved successfully!');
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error saving restrictions: ' + error);
            }
        });
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    print("Web Integration Example")
    print("=" * 70)
    print("\nThis file demonstrates how to integrate time restrictions")
    print("into the Flask web application.")
    print("\nKey functions:")
    print("  - create_scheduler_with_restrictions()")
    print("  - generate_schedule_from_web_form()")
    print("  - timetable_to_json()")
    print("\nSee the comments in this file for example Flask routes")
    print("and HTML template code to add to your web app.")
    print("\n" + "=" * 70)
