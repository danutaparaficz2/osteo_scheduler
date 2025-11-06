# Usage Guide - Timetable Scheduler

This guide provides detailed instructions on how to use the Osteopathic Timetable Scheduler.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Data Format](#data-format)
3. [Using the Web Interface](#using-the-web-interface)
4. [Using the Command Line](#using-the-command-line)
5. [Advanced Features](#advanced-features)
6. [Examples](#examples)

## Getting Started

### Installation

1. Clone the repository:
```bash
git clone https://github.com/danutaparaficz2/osteo_scheduler.git
cd osteo_scheduler
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Quick Start

**Option 1: Web Interface**
```bash
python app.py
```
Then open your browser to `http://localhost:5000`

**Option 2: Command Line**
```bash
python cli.py examples/sample_data.json --weeks 2 --output-pdf schedule.pdf
```

## Data Format

The scheduler accepts data in JSON format with the following structure:

### Lecturers

Define all lecturers who will teach courses:

```json
{
  "lecturers": [
    {
      "id": "L1",          // Unique identifier
      "name": "Dr. Smith"  // Full name
    }
  ]
}
```

### Rooms

Define all available rooms with their capacities:

```json
{
  "rooms": [
    {
      "id": "R1",           // Unique identifier
      "name": "Room 101",   // Room name
      "capacity": 30        // Maximum capacity
    }
  ]
}
```

### Subjects

Define courses/subjects to be scheduled:

```json
{
  "subjects": [
    {
      "id": "S1",              // Unique identifier
      "name": "Anatomy",       // Subject name
      "lecturer_id": "L1",     // ID of assigned lecturer
      "required_hours": 4,     // Total hours per week
      "min_students": 20,      // Minimum students
      "max_students": 30       // Maximum students
    }
  ]
}
```

### Time Blocks

Define available time slots for scheduling:

```json
{
  "blocks": [
    {
      "id": "B1",                  // Unique identifier
      "day": "Monday",             // Day of week
      "start_time": "09:00",       // Start time (24h format)
      "end_time": "10:00",         // End time (24h format)
      "duration_hours": 1          // Duration in hours
    }
  ]
}
```

### Complete Example

See `examples/sample_data.json` for a complete working example with:
- 3 lecturers
- 4 rooms
- 4 subjects
- 25 time blocks (Monday-Friday, 09:00-16:00)

## Using the Web Interface

### Step 1: Input Data

1. Navigate to **Input Data** from the menu
2. Choose one of two methods:
   - **Upload JSON File**: Click "Choose File" and select your JSON data file
   - **Paste JSON**: Copy and paste JSON data directly into the text area
3. Click the appropriate button to load the data
4. Verify the data in the "Current Data" section

### Step 2: Generate Schedule

1. Navigate to **Generate Schedule**
2. Set the number of weeks you want to schedule
3. Click "Generate Timetable"
4. Wait for the generation process to complete
5. Click "View Schedule" to see the results

### Step 3: View and Export

1. Navigate to **View Schedule**
2. Review the generated timetable organized by week and day
3. Export options:
   - **Export as PDF**: Standard timetable view
   - **Export by Lecturer (PDF)**: Organized by lecturer
   - **Export as JSON**: Machine-readable format

## Using the Command Line

The CLI tool provides a quick way to generate schedules without the web interface.

### Basic Usage

```bash
python cli.py <input_file> [options]
```

### Options

- `--weeks N`: Generate schedule for N weeks (default: 1)
- `--output-json FILE`: Export schedule to JSON file
- `--output-pdf FILE`: Export schedule to PDF file
- `--pdf-by-lecturer`: Organize PDF by lecturer instead of by week

### Examples

**Generate 2-week schedule and export to both formats:**
```bash
python cli.py examples/sample_data.json --weeks 2 \
  --output-json my_schedule.json \
  --output-pdf my_schedule.pdf
```

**Generate schedule organized by lecturer:**
```bash
python cli.py examples/sample_data.json \
  --output-pdf lecturer_schedule.pdf \
  --pdf-by-lecturer
```

**Quick generation without export:**
```bash
python cli.py examples/sample_data.json --weeks 1
```

## Advanced Features

### Availability Constraints

You can specify when lecturers or rooms are available using the API:

```python
from models import TimeSlot, Availability
from scheduler import SchedulerConstraints

# Create constraints
constraints = SchedulerConstraints()

# Define available time slots
monday_9am = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
monday_10am = TimeSlot(day="Monday", start_time="10:00", end_time="11:00")

# Set lecturer availability
lecturer_availability = Availability(
    entity_id="L1",
    entity_type="lecturer",
    available_slots={monday_9am, monday_10am}
)
constraints.add_lecturer_availability("L1", lecturer_availability)
```

### Fixed Appointments

You can mark certain schedule entries as fixed (cannot be changed):

```python
from models import ScheduleEntry

entry = ScheduleEntry(
    subject=my_subject,
    room=my_room,
    block=my_block,
    week=1,
    is_fixed=True  # This entry cannot be moved
)

constraints.add_fixed_entry(entry)
```

### Manual Adjustments

You can manually add or remove entries from a timetable:

```python
from scheduler import TimetableScheduler

scheduler = TimetableScheduler(constraints)

# Add a manual entry
success, message = scheduler.add_manual_entry(
    timetable=my_timetable,
    subject=my_subject,
    room=my_room,
    block=my_block,
    week=1
)

# Remove an entry (if not fixed)
success, message = scheduler.remove_manual_entry(
    timetable=my_timetable,
    entry=entry_to_remove
)
```

## Examples

### Example 1: Simple Schedule

Create a minimal data file with 1 lecturer, 1 room, 1 subject, and a few time blocks:

```json
{
  "lecturers": [{"id": "L1", "name": "Dr. Smith"}],
  "rooms": [{"id": "R1", "name": "Room 101", "capacity": 30}],
  "subjects": [{
    "id": "S1",
    "name": "Anatomy",
    "lecturer_id": "L1",
    "required_hours": 2,
    "min_students": 20,
    "max_students": 30
  }],
  "blocks": [
    {"id": "B1", "day": "Monday", "start_time": "09:00", "end_time": "10:00", "duration_hours": 1},
    {"id": "B2", "day": "Monday", "start_time": "10:00", "end_time": "11:00", "duration_hours": 1}
  ]
}
```

Generate:
```bash
python cli.py simple_data.json --output-pdf simple_schedule.pdf
```

### Example 2: Complex Multi-Week Schedule

Use the provided `examples/sample_data.json` with:
- Multiple lecturers
- Multiple rooms with different capacities
- Multiple subjects with varying requirements
- Full week of time blocks

Generate a 4-week schedule:
```bash
python cli.py examples/sample_data.json --weeks 4 \
  --output-json 4week_schedule.json \
  --output-pdf 4week_schedule.pdf
```

## Troubleshooting

### "No suitable rooms found for subject"

**Problem**: A subject's minimum student requirement exceeds all room capacities.

**Solution**: Either:
- Add a larger room to your data
- Reduce the subject's `min_students` requirement

### "Only scheduled X/Y hours for subject"

**Problem**: Not enough time blocks or rooms to satisfy all required hours.

**Solution**:
- Add more time blocks
- Add more rooms
- Reduce the `required_hours` for subjects
- Increase the number of weeks

### Conflicts Not Detected

**Problem**: Schedule appears to have conflicts (same lecturer in two places).

**Solution**: This shouldn't happen as the scheduler validates conflicts. If you see this:
1. Check that lecturer IDs are consistent
2. Verify the week numbers
3. Report as a bug with your data file

## Tips for Best Results

1. **Balanced Load**: Ensure you have enough time blocks and rooms for all subjects
2. **Room Sizes**: Have a variety of room sizes to match different subject requirements
3. **Time Blocks**: Define blocks for all days you want to schedule
4. **Buffer Time**: Consider adding buffer time between classes if needed
5. **Start Small**: Test with a simple schedule first, then scale up

## API Reference

For programmatic usage, see the docstrings in:
- `models.py`: Data model classes
- `scheduler.py`: Scheduling engine
- `data_manager.py`: Data I/O operations
- `pdf_exporter.py`: PDF generation

## Support

For issues or questions:
1. Check this documentation
2. Review the example data file
3. Run the unit tests: `python test_scheduler.py`
4. Open an issue on GitHub
