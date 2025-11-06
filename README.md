# Osteo Scheduler - Timetable Scheduling System

A comprehensive web-based timetable scheduling system for educational institutions, featuring automated schedule generation with constraint satisfaction, manual adjustments, and PDF export capabilities.

## Features

### 1. Data Model
Efficiently structured input data management for:
- **Subjects**: Courses/classes with duration, capacity, and feature requirements
- **Lecturers**: Instructors with availability constraints and maximum hours
- **Rooms**: Physical spaces with capacity limits and feature sets
- **Weeks**: Calendar weeks for scheduling
- **Blocks**: Time block structures (morning, afternoon, etc.)
- **Time Slots**: Specific time periods with day, start time, and duration

### 2. Scheduling Algorithm
Semi-automated scheduling using constraint satisfaction:
- **Room Constraints**: Capacity limits and required features
- **Lecturer Conflicts**: Availability checking and conflict resolution
- **Fixed Appointments**: Support for pre-scheduled sessions
- **Block Structure**: Respects time block definitions
- **Preferred Days**: Optional day preferences for subjects
- **Iterative Placement**: Backtracking algorithm for optimal placement

### 3. User Interface & Export
Web-based interface built with Flask:
- **Data Entry**: Intuitive forms for adding lecturers, rooms, and subjects
- **Schedule Generation**: Automated schedule creation with configurable parameters
- **Schedule Viewing**: Multiple views (weekly, by room, by lecturer)
- **Manual Adjustments**: Remove or modify individual sessions
- **PDF Export**: Export schedules in multiple formats

## Installation

1. **Clone the repository**:
```bash
git clone https://github.com/danutaparaficz2/osteo_scheduler.git
cd osteo_scheduler
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
```bash
# For development (enables debug mode)
export FLASK_DEBUG=true
python app.py

# For production (debug mode disabled by default)
python app.py
```

4. **Access the web interface**:
Open your browser and navigate to `http://localhost:5000`

## Security Notes

- **Production Deployment**: Debug mode is disabled by default. Never enable debug mode in production.
- **Secret Key**: Change the default secret key in production by setting the `SECRET_KEY` environment variable.
- **Web Server**: For production, use a production WSGI server like Gunicorn instead of Flask's development server.

## Quick Start

1. **Initialize Sample Data**: 
   - Click "Load Sample Data" on the home page to quickly populate the system with example data

2. **Or Set Up Manually**:
   - Navigate to "Setup Data" and add your lecturers, rooms, and subjects
   - The system automatically creates standard time slots (Mon-Fri, 8 AM - 6 PM)

3. **Generate Schedule**:
   - Click "Generate Schedule" to create an automated timetable
   - The algorithm will attempt to place all sessions while respecting constraints

4. **View and Adjust**:
   - Go to "View Schedule" to see the generated timetable
   - Remove sessions manually if needed
   - View statistics about your schedule

5. **Export to PDF**:
   - Select your preferred view (Weekly, By Room, or By Lecturer)
   - Click "Export PDF" to download the schedule

## Architecture

### Core Components

#### models.py
Defines all data structures:
- `Subject`, `Lecturer`, `Room`, `Week`, `Block`, `TimeSlot`
- `ScheduledSession`: Represents a placed session in the schedule
- `Schedule`: Container for all scheduled sessions with validation

#### scheduler.py
Implements the scheduling algorithm:
- `SchedulingConstraints`: Validates all constraints
- `SchedulingAlgorithm`: Iterative placement with backtracking
- `SchedulingHelper`: Utility functions for creating time slots and blocks

#### pdf_export.py
PDF generation functionality:
- `PDFExporter`: Creates formatted PDF documents
- Multiple view types: weekly grid, by room, by lecturer
- Uses ReportLab for PDF generation

#### app.py
Flask web application:
- RESTful API endpoints for data management
- Session management and schedule generation
- PDF export endpoint

### Scheduling Algorithm Details

The system uses an **iterative placement approach with backtracking**:

1. **Fixed Sessions First**: Pre-scheduled sessions are placed first
2. **Iterative Placement**: For each remaining subject:
   - Find all valid placements (checking all constraints)
   - Try placing the subject in a valid slot
   - Recursively place remaining subjects
   - Backtrack if no valid placement is found
3. **Constraint Checking**: Each placement is validated against:
   - Room capacity and features
   - Lecturer availability
   - Time conflicts (room and lecturer)
   - Preferred days (if specified)

### Constraints Supported

- **Room Capacity**: Ensures room can accommodate minimum required students
- **Room Features**: Matches required features (projector, lab equipment, etc.)
- **Lecturer Availability**: Checks lecturer is available during time slot
- **No Conflicts**: Prevents double-booking of rooms and lecturers
- **Preferred Days**: Respects subject preferences for specific days
- **Fixed Sessions**: Maintains pre-scheduled appointments
- **Sessions Per Week**: Schedules multiple sessions for subjects that need them

## API Endpoints

### Data Management
- `GET/POST/DELETE /api/lecturers` - Manage lecturers
- `GET/POST/DELETE /api/rooms` - Manage rooms
- `GET/POST/DELETE /api/subjects` - Manage subjects
- `GET/POST /api/weeks` - Manage weeks
- `GET/POST /api/blocks` - Manage time blocks

### Scheduling
- `POST /api/generate-schedule` - Generate a new schedule
- `GET /api/schedule` - Get current schedule
- `DELETE /api/schedule/session` - Remove a session
- `PUT /api/schedule/session` - Modify a session

### Utilities
- `POST /api/initialize-sample-data` - Load sample data
- `POST /api/export-pdf` - Export schedule as PDF

## Example Usage

### Python API Example

```python
from models import Subject, Lecturer, Room, Week, TimeSlot, DayOfWeek
from scheduler import SchedulingAlgorithm, SchedulingHelper

# Create lecturers
lecturer = Lecturer(
    id='L1',
    name='Dr. Smith',
    available_slots=SchedulingHelper.create_standard_time_slots()
)

# Create rooms
room = Room(id='R1', name='Room A', capacity=30, features={'projector'})

# Create subjects
subject = Subject(
    id='S1',
    name='Anatomy',
    duration_minutes=60,
    required_lecturers=[lecturer],
    min_capacity=25,
    sessions_per_week=2
)

# Create weeks with blocks
time_slots = SchedulingHelper.create_standard_time_slots()
blocks = SchedulingHelper.create_blocks_from_slots(
    time_slots,
    {'Morning': (8, 12), 'Afternoon': (13, 17)}
)
week = Week(week_number=1, year=2025, blocks=blocks)

# Generate schedule
algorithm = SchedulingAlgorithm(
    subjects=[subject],
    rooms=[room],
    weeks=[week]
)
schedule = algorithm.generate_schedule()

# Export to PDF
from pdf_export import PDFExporter
exporter = PDFExporter(schedule)
exporter.export_to_file('schedule.pdf', view_type='weekly')
```

## Technology Stack

- **Backend**: Python 3.x with Flask
- **Scheduling**: Custom constraint satisfaction algorithm
- **PDF Generation**: ReportLab
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Storage**: In-memory (can be extended to use database)

## Future Enhancements

Possible improvements for future versions:
- Database persistence (SQLite, PostgreSQL)
- User authentication and multi-tenancy
- More sophisticated optimization algorithms (genetic algorithms, simulated annealing)
- Real-time conflict detection during manual adjustments
- Import/export of data in CSV/Excel formats
- Calendar integration (iCal, Google Calendar)
- Mobile-responsive design improvements
- Advanced reporting and analytics

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.