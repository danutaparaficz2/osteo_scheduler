# Lecturer Time Restrictions - User Guide

## Overview

The scheduling system now supports **date-based time restrictions** for lecturers. You can specify:
- **Specific dates** when a lecturer is available
- **Date ranges** for availability periods
- **Time of day** restrictions (morning or afternoon)
- **Unavailable dates** (exceptions)

This allows you to accurately model lecturer availability throughout the academic year.

## Time Periods

The system divides each day into two periods:
- **Morning**: 08:00 - 12:00
- **Afternoon**: 12:00 - 18:00

## Usage Methods

### Method 1: Using the Builder Pattern (Programmatic)

The `LecturerTimeRestrictionBuilder` class provides a fluent API for creating restrictions:

```python
from time_restrictions import LecturerTimeRestrictionBuilder

# Create a builder for a lecturer
builder = LecturerTimeRestrictionBuilder(lecturer_id="L1")

# Add specific available dates
builder.add_available_date("2025-01-15", morning=True, afternoon=False)
builder.add_available_date("2025-01-16", morning=True, afternoon=True)

# Add a range of dates
builder.add_available_date_range("2025-01-20", "2025-01-25", 
                                 morning=True, afternoon=True)

# Add unavailable dates (exceptions)
builder.add_unavailable_date("2025-01-22")

# Build the availability object
availability = builder.build()
```

### Method 2: From a List of Dates

Useful when you have availability data in a structured format:

```python
from time_restrictions import create_lecturer_availability_from_list

available_dates = [
    {"date": "2025-01-15", "morning": True, "afternoon": False},
    {"date": "2025-01-16", "morning": True, "afternoon": True},
    {"date": "2025-01-17", "morning": False, "afternoon": True}
]

availability = create_lecturer_availability_from_list(
    lecturer_id="L1",
    available_dates=available_dates
)
```

### Method 3: From Date Ranges

Useful for lecturers available for extended periods:

```python
from time_restrictions import create_lecturer_availability_from_ranges

available_ranges = [
    {"start": "2025-01-15", "end": "2025-01-20", "morning": True, "afternoon": True},
    {"start": "2025-02-01", "end": "2025-02-15", "morning": True, "afternoon": False}
]

unavailable_dates = ["2025-01-18", "2025-02-10"]

availability = create_lecturer_availability_from_ranges(
    lecturer_id="L1",
    available_ranges=available_ranges,
    unavailable_dates=unavailable_dates
)
```

## Complete Scheduling Example

```python
from datetime import date
from models import Lecturer, Room, Subject, Block, TimeSlot
from scheduler import SchedulerConstraints, TimetableScheduler
from time_restrictions import LecturerTimeRestrictionBuilder

# 1. Create lecturers
lecturer1 = Lecturer(id="L1", name="Dr. Sarah Smith")
lecturer2 = Lecturer(id="L2", name="Prof. Michael Chen")

# 2. Define time restrictions
availability1 = (LecturerTimeRestrictionBuilder(lecturer1.id)
                .add_available_date_range("2025-01-15", "2025-01-25", 
                                         morning=True, afternoon=False)
                .build())

availability2 = (LecturerTimeRestrictionBuilder(lecturer2.id)
                .add_available_date_range("2025-01-15", "2025-01-25", 
                                         morning=False, afternoon=True)
                .build())

# 3. Create rooms
rooms = [
    Room(id="R1", name="Lecture Hall A", capacity=50),
    Room(id="R2", name="Seminar Room 1", capacity=25)
]

# 4. Create subjects
subjects = [
    Subject(id="S1", name="Osteopathic Principles", lecturer=lecturer1,
            required_hours=4, min_students=20, max_students=50),
    Subject(id="S2", name="Clinical Practice", lecturer=lecturer2,
            required_hours=3, min_students=10, max_students=25)
]

# 5. Create time blocks
blocks = [
    Block(id="B1", time_slot=TimeSlot(day="Monday", start_time="09:00", end_time="11:00"),
          duration_hours=2),
    Block(id="B2", time_slot=TimeSlot(day="Monday", start_time="14:00", end_time="16:00"),
          duration_hours=2),
    # ... more blocks
]

# 6. Set up constraints
constraints = SchedulerConstraints()
constraints.add_lecturer_availability(lecturer1.id, availability1)
constraints.add_lecturer_availability(lecturer2.id, availability2)

# 7. Create scheduler and generate timetable
scheduler = TimetableScheduler(constraints)
start_date = date(2025, 1, 15)  # Monday, January 15, 2025

timetable = scheduler.generate_timetable(
    subjects=subjects,
    rooms=rooms,
    blocks=blocks,
    weeks=2,
    start_date=start_date
)

# 8. View the schedule
for entry in timetable.entries:
    print(f"{entry.scheduled_date} {entry.block.time_slot.day} "
          f"{entry.block.time_slot.start_time}-{entry.block.time_slot.end_time}: "
          f"{entry.subject.name} - {entry.subject.lecturer.name} - {entry.room.name}")
```

## JSON Format for Data Files

You can define time restrictions in JSON files:

```json
{
  "lecturers": [
    {
      "id": "L1",
      "name": "Dr. Sarah Thompson",
      "time_restrictions": {
        "type": "date_ranges",
        "available_ranges": [
          {
            "start": "2025-01-15",
            "end": "2025-01-25",
            "morning": true,
            "afternoon": false
          }
        ],
        "unavailable_dates": ["2025-01-20"]
      }
    },
    {
      "id": "L2",
      "name": "Prof. Michael Chen",
      "time_restrictions": {
        "type": "specific_dates",
        "available_dates": [
          {"date": "2025-01-15", "morning": true, "afternoon": true},
          {"date": "2025-01-16", "morning": false, "afternoon": true}
        ]
      }
    }
  ],
  "schedule_config": {
    "start_date": "2025-01-15",
    "weeks": 4
  }
}
```

Then load it using:

```python
from data_loader_with_restrictions import load_data_with_time_restrictions

data = load_data_with_time_restrictions('path/to/your/data.json')

# Access the loaded data
lecturers = data['lecturers']
rooms = data['rooms']
subjects = data['subjects']
blocks = data['blocks']
lecturer_restrictions = data['lecturer_restrictions']
start_date = data['start_date']
weeks = data['weeks']

# Use in scheduling
constraints = SchedulerConstraints()
for lecturer_id, availability in lecturer_restrictions.items():
    constraints.add_lecturer_availability(lecturer_id, availability)

scheduler = TimetableScheduler(constraints)
timetable = scheduler.generate_timetable(
    subjects=subjects,
    rooms=rooms,
    blocks=blocks,
    weeks=weeks,
    start_date=start_date
)
```

## Key Features

### 1. Date-Based Scheduling
- Schedule entries are assigned actual calendar dates
- The system calculates which week day corresponds to which date
- Start date is specified when generating the timetable

### 2. Time of Day Restrictions
- Morning (08:00-12:00) and Afternoon (12:00-18:00) periods
- Can specify different availability for each period
- Blocks are automatically classified into time periods

### 3. Flexible Availability Patterns
- Specific dates with individual time-of-day settings
- Date ranges with consistent availability
- Exception dates (unavailable within available ranges)
- Default availability for unspecified dates

### 4. Automatic Validation
- The scheduler automatically checks lecturer availability
- Entries violating time restrictions are rejected
- Manual entry additions also validate against restrictions

## Examples

See the following files for complete working examples:
- `example_time_restrictions.py` - Comprehensive examples of all features
- `examples/sample_data_with_time_restrictions.json` - JSON format example
- `data_loader_with_restrictions.py` - Loading and using JSON data

To run the examples:
```bash
python example_time_restrictions.py
python data_loader_with_restrictions.py
```

## Migration from Old System

If you have existing code without time restrictions:

**Old way:**
```python
availability = Availability(
    entity_id="L1",
    entity_type="lecturer",
    available_slots={time_slot1, time_slot2}
)
```

**New way (backward compatible):**
```python
# Still works - will check only time slots
availability = Availability(
    entity_id="L1",
    entity_type="lecturer",
    available_slots={time_slot1, time_slot2}
)

# Or use date-based restrictions
availability = LecturerTimeRestrictionBuilder("L1")\
    .add_available_date_range("2025-01-15", "2025-03-15")\
    .build()
```

The system is **backward compatible** - existing code using time slots will continue to work.

## Tips

1. **Always specify a start_date** when generating timetables with time restrictions
2. **Use date ranges** for long availability periods (more efficient)
3. **Use specific dates** for irregular availability patterns
4. **Test restrictions** before running full scheduling to ensure they're correct
5. **Consider time zones** - all dates are treated as local dates

## Troubleshooting

**Problem**: Scheduler can't find valid slots
- Check that lecturer availability includes the dates in your scheduling period
- Verify that time blocks match the time-of-day availability (morning/afternoon)
- Ensure start_date is set when using date-based restrictions

**Problem**: Entries scheduled on wrong dates
- Verify the start_date parameter in generate_timetable()
- Check that day names in blocks match expected days (Monday, Tuesday, etc.)

**Problem**: Time restrictions not being enforced
- Make sure to add availability to constraints: `constraints.add_lecturer_availability()`
- Verify start_date is provided to generate_timetable()
- Check that scheduled_date is being set on entries
