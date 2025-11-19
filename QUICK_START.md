# Quick Start Guide - Lecturer Time Restrictions

## 🚀 Getting Started in 5 Minutes

### Step 1: Basic Setup

```python
from datetime import date
from models import Lecturer
from time_restrictions import LecturerTimeRestrictionBuilder
from scheduler import SchedulerConstraints, TimetableScheduler

# Create a lecturer
lecturer = Lecturer(id="L1", name="Dr. Smith")
```

### Step 2: Define When the Lecturer is Available

```python
# Create restrictions using the builder
availability = (LecturerTimeRestrictionBuilder(lecturer.id)
    # Available Jan 15-20, mornings only
    .add_available_date_range("2025-01-15", "2025-01-20", 
                             morning=True, afternoon=False)
    # Not available on Jan 18
    .add_unavailable_date("2025-01-18")
    # Build the availability object
    .build())
```

### Step 3: Use in Scheduling

```python
# Add to constraints
constraints = SchedulerConstraints()
constraints.add_lecturer_availability(lecturer.id, availability)

# Create scheduler
scheduler = TimetableScheduler(constraints)

# Generate schedule (requires subjects, rooms, blocks - see full examples)
timetable = scheduler.generate_timetable(
    subjects=your_subjects,
    rooms=your_rooms,
    blocks=your_blocks,
    weeks=1,
    start_date=date(2025, 1, 15)  # Important: specify start date!
)
```

## 📋 Common Use Cases

### Use Case 1: Lecturer Available on Specific Dates

```python
builder = LecturerTimeRestrictionBuilder("L1")
builder.add_available_date("2025-01-15", morning=True, afternoon=True)
builder.add_available_date("2025-01-16", morning=True, afternoon=False)
builder.add_available_date("2025-01-17", morning=False, afternoon=True)
availability = builder.build()
```

### Use Case 2: Lecturer Available for Weeks with Exceptions

```python
builder = LecturerTimeRestrictionBuilder("L1")
# Available for 4 weeks
builder.add_available_date_range("2025-01-15", "2025-02-15")
# Except these days (holidays/conferences)
builder.add_unavailable_date("2025-01-25")
builder.add_unavailable_date("2025-02-01")
availability = builder.build()
```

### Use Case 3: Morning-Only or Afternoon-Only Lecturer

```python
# Morning only (8am-12pm)
morning_only = (LecturerTimeRestrictionBuilder("L1")
    .add_available_date_range("2025-01-15", "2025-02-15", 
                             morning=True, afternoon=False)
    .build())

# Afternoon only (12pm-6pm)
afternoon_only = (LecturerTimeRestrictionBuilder("L2")
    .add_available_date_range("2025-01-15", "2025-02-15", 
                             morning=False, afternoon=True)
    .build())
```

### Use Case 4: Using JSON Configuration

**Create a JSON file** (`my_schedule.json`):
```json
{
  "lecturers": [
    {
      "id": "L1",
      "name": "Dr. Smith",
      "time_restrictions": {
        "type": "date_ranges",
        "available_ranges": [
          {"start": "2025-01-15", "end": "2025-02-15", "morning": true, "afternoon": false}
        ],
        "unavailable_dates": ["2025-01-25"]
      }
    }
  ],
  "schedule_config": {
    "start_date": "2025-01-15",
    "weeks": 4
  }
}
```

**Load and use**:
```python
from data_loader_with_restrictions import load_data_with_time_restrictions

# Load everything from JSON
data = load_data_with_time_restrictions('my_schedule.json')

# Set up constraints
constraints = SchedulerConstraints()
for lecturer_id, availability in data['lecturer_restrictions'].items():
    constraints.add_lecturer_availability(lecturer_id, availability)

# Generate schedule
scheduler = TimetableScheduler(constraints)
timetable = scheduler.generate_timetable(
    subjects=data['subjects'],
    rooms=data['rooms'],
    blocks=data['blocks'],
    weeks=data['weeks'],
    start_date=data['start_date']
)
```

## ⚡ Quick Reference

### Time Periods
- **Morning**: 08:00 - 12:00
- **Afternoon**: 12:00 - 18:00

### Builder Methods
```python
builder = LecturerTimeRestrictionBuilder(lecturer_id)

# Add single date
builder.add_available_date("2025-01-15", morning=True, afternoon=True)

# Add date range
builder.add_available_date_range("2025-01-15", "2025-02-15", 
                                 morning=True, afternoon=True)

# Mark date as unavailable
builder.add_unavailable_date("2025-01-20")

# Mark range as unavailable
builder.add_unavailable_date_range("2025-01-20", "2025-01-25")

# Set defaults for unspecified dates
builder.set_default_availability(morning=True, afternoon=True)

# Build the final object
availability = builder.build()
```

### JSON Format Options

**Option 1: Specific Dates**
```json
{
  "type": "specific_dates",
  "available_dates": [
    {"date": "2025-01-15", "morning": true, "afternoon": false},
    {"date": "2025-01-16", "morning": true, "afternoon": true}
  ]
}
```

**Option 2: Date Ranges**
```json
{
  "type": "date_ranges",
  "available_ranges": [
    {"start": "2025-01-15", "end": "2025-02-15", "morning": true, "afternoon": true}
  ],
  "unavailable_dates": ["2025-01-20", "2025-01-25"]
}
```

## 🎯 Complete Minimal Example

```python
from datetime import date
from models import Lecturer, Room, Subject, Block, TimeSlot
from time_restrictions import LecturerTimeRestrictionBuilder
from scheduler import SchedulerConstraints, TimetableScheduler

# 1. Create lecturer
lecturer = Lecturer(id="L1", name="Dr. Smith")

# 2. Set time restrictions (mornings only in January)
availability = (LecturerTimeRestrictionBuilder(lecturer.id)
    .add_available_date_range("2025-01-15", "2025-01-31", 
                             morning=True, afternoon=False)
    .build())

# 3. Create room and subject
room = Room(id="R1", name="Room A", capacity=30)
subject = Subject(id="S1", name="Physics", lecturer=lecturer,
                 required_hours=4, min_students=20, max_students=30)

# 4. Create time blocks
blocks = [
    Block(id="B1", 
          time_slot=TimeSlot(day="Monday", start_time="09:00", end_time="11:00"),
          duration_hours=2),
    Block(id="B2", 
          time_slot=TimeSlot(day="Wednesday", start_time="09:00", end_time="11:00"),
          duration_hours=2),
]

# 5. Set up and run scheduler
constraints = SchedulerConstraints()
constraints.add_lecturer_availability(lecturer.id, availability)

scheduler = TimetableScheduler(constraints)
timetable = scheduler.generate_timetable(
    subjects=[subject],
    rooms=[room],
    blocks=blocks,
    weeks=2,
    start_date=date(2025, 1, 15)  # Monday, Jan 15, 2025
)

# 6. View results
print(f"Generated {len(timetable.entries)} schedule entries:")
for entry in timetable.entries:
    print(f"  {entry.scheduled_date} ({entry.block.time_slot.day}) "
          f"{entry.block.time_slot.start_time}: {entry.subject.name}")
```

## 📚 Learn More

- **Full Documentation**: See `TIME_RESTRICTIONS_GUIDE.md`
- **Complete Examples**: Run `python example_time_restrictions.py`
- **JSON Examples**: See `examples/sample_data_with_time_restrictions.json`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`

## ❓ Troubleshooting

**Q: Schedule is empty or has fewer entries than expected**  
A: Check that your time blocks match the lecturer's available time periods (morning/afternoon)

**Q: Getting "not available" errors**  
A: Verify start_date is set and matches your available date ranges

**Q: How do I see what restrictions are set?**  
A: Use `data_loader_with_restrictions.print_time_restrictions_summary()`

**Q: Can I mix slot-based and date-based restrictions?**  
A: Yes, but typically use one or the other for clarity

## 💡 Pro Tips

1. **Use date ranges** for regular availability patterns
2. **Use specific dates** for irregular schedules
3. **Always set start_date** when using time restrictions
4. **Test with small examples** before full scheduling
5. **Use JSON files** to manage complex configurations

---

**Ready to try it?** Run: `python example_time_restrictions.py`
