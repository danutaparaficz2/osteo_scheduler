# Osteopathic Timetable Scheduler

A comprehensive, semi-automated timetable scheduling system designed to efficiently manage and generate schedules for educational institutions. The system handles complex constraints including room capacity, lecturer availability, time conflicts, and fixed appointments.

## Features

- **Structured Data Management**: Efficient organization of Subjects, Lecturers, Blocks, Weeks, Rooms, and Availability
- **Constraint-Based Scheduling**: Automated schedule generation with validation for:
  - Room capacity limits
  - Lecturer conflicts prevention
  - Fixed appointments support
  - Block structure compliance
  - Availability constraints
- **User-Friendly Interface**: Web-based UI for:
  - Data input via JSON files or direct entry
  - Schedule viewing and visualization
  - Manual adjustments capability
  - PDF and JSON export functionality

## Installation

1. Clone the repository:
```bash
git clone https://github.com/danutaparaficz2/osteo_scheduler.git
cd osteo_scheduler
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

Start the Flask web server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Data Input

The system accepts JSON-formatted data with the following structure:

```json
{
  "lecturers": [
    {"id": "L1", "name": "Dr. Smith"}
  ],
  "rooms": [
    {"id": "R1", "name": "Room 101", "capacity": 30}
  ],
  "subjects": [
    {
      "id": "S1",
      "name": "Anatomy",
      "lecturer_id": "L1",
      "required_hours": 4,
      "min_students": 20,
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
```

An example data file is provided in `examples/sample_data.json`.

### Workflow

1. **Input Data**: Navigate to the "Input Data" page and upload a JSON file or paste JSON data directly
2. **Generate Schedule**: Go to "Generate Schedule" and specify the number of weeks
3. **View Schedule**: Review the generated timetable on the "View Schedule" page
4. **Export**: Export the final schedule as PDF or JSON format

## Project Structure

```
osteo_scheduler/
├── app.py                 # Flask web application
├── models.py             # Data models (Subject, Lecturer, Room, etc.)
├── scheduler.py          # Scheduling engine with constraints
├── data_manager.py       # Data input/output handling
├── pdf_exporter.py       # PDF export functionality
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── data_input.html
│   ├── generate_schedule.html
│   └── view_schedule.html
├── examples/             # Example data files
│   └── sample_data.json
└── requirements.txt      # Python dependencies
```

## API Endpoints

- `GET /` - Home page
- `GET/POST /data/input` - Data input page
- `POST /api/data/upload` - Upload JSON data file
- `GET /api/data/current` - Get current loaded data
- `GET/POST /schedule/generate` - Generate timetable
- `GET /schedule/view` - View current schedule
- `GET /api/schedule/current` - Get schedule as JSON
- `POST /api/schedule/export/pdf` - Export schedule as PDF
- `GET /api/schedule/export/json` - Export schedule as JSON

## Constraints and Validation

The scheduler validates:
- **Room Capacity**: Ensures room capacity meets subject requirements
- **Room Availability**: Checks if rooms are available at scheduled times
- **Lecturer Availability**: Verifies lecturer availability for time slots
- **Conflict Prevention**: Prevents double-booking of rooms or lecturers
- **Fixed Entries**: Respects pre-defined fixed appointments

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.