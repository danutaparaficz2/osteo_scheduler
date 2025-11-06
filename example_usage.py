#!/usr/bin/env python
"""
Example demonstrating programmatic usage of the timetable scheduler.
This shows how to use the scheduler as a library in your own Python code.
"""

from models import Room, Lecturer, Subject, TimeSlot, Block, Timetable
from scheduler import TimetableScheduler, SchedulerConstraints
from pdf_exporter import PDFExporter


def create_sample_data():
    """Create sample data programmatically."""
    
    # Create lecturers
    lecturer1 = Lecturer(id="L1", name="Dr. Sarah Thompson")
    lecturer2 = Lecturer(id="L2", name="Prof. Michael Chen")
    
    # Create rooms
    room1 = Room(id="R1", name="Lecture Hall A", capacity=50)
    room2 = Room(id="R2", name="Seminar Room 1", capacity=25)
    
    # Create subjects
    subject1 = Subject(
        id="S1",
        name="Osteopathic Principles",
        lecturer=lecturer1,
        required_hours=3,
        min_students=20,
        max_students=50
    )
    
    subject2 = Subject(
        id="S2",
        name="Clinical Practice",
        lecturer=lecturer2,
        required_hours=2,
        min_students=10,
        max_students=25
    )
    
    # Create time blocks
    blocks = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    times = [
        ("09:00", "10:00"),
        ("10:00", "11:00"),
        ("11:00", "12:00"),
        ("14:00", "15:00"),
        ("15:00", "16:00")
    ]
    
    block_id = 1
    for day in days:
        for start_time, end_time in times:
            time_slot = TimeSlot(day=day, start_time=start_time, end_time=end_time)
            block = Block(id=f"B{block_id}", time_slot=time_slot, duration_hours=1)
            blocks.append(block)
            block_id += 1
    
    return {
        'lecturers': [lecturer1, lecturer2],
        'rooms': [room1, room2],
        'subjects': [subject1, subject2],
        'blocks': blocks
    }


def main():
    print("Timetable Scheduler - Programmatic Example")
    print("=" * 50)
    
    # Step 1: Create data
    print("\n1. Creating sample data...")
    data = create_sample_data()
    print(f"   - {len(data['lecturers'])} lecturers")
    print(f"   - {len(data['rooms'])} rooms")
    print(f"   - {len(data['subjects'])} subjects")
    print(f"   - {len(data['blocks'])} time blocks")
    
    # Step 2: Set up constraints
    print("\n2. Setting up constraints...")
    constraints = SchedulerConstraints()
    
    # All constraints are optional - the scheduler will work with basic validation
    # You can add availability constraints, fixed entries, etc. here
    print("   - Using default constraints (all rooms/lecturers always available)")
    
    # Step 3: Create scheduler and generate timetable
    print("\n3. Generating timetable...")
    scheduler = TimetableScheduler(constraints)
    
    timetable = scheduler.generate_timetable(
        subjects=data['subjects'],
        rooms=data['rooms'],
        blocks=data['blocks'],
        weeks=2  # Generate for 2 weeks
    )
    
    print(f"   - Generated {len(timetable.entries)} schedule entries")
    
    # Step 4: Display schedule summary
    print("\n4. Schedule Summary:")
    print("-" * 50)
    
    for week in range(1, timetable.weeks + 1):
        week_entries = timetable.get_entries_by_week(week)
        print(f"\nWeek {week}: {len(week_entries)} classes")
        
        # Group by day
        day_groups = {}
        for entry in week_entries:
            day = entry.block.time_slot.day
            if day not in day_groups:
                day_groups[day] = []
            day_groups[day].append(entry)
        
        # Display each day
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            if day in day_groups:
                print(f"\n  {day}:")
                for entry in sorted(day_groups[day], 
                                   key=lambda e: e.block.time_slot.start_time):
                    print(f"    {entry.block.time_slot.start_time}-{entry.block.time_slot.end_time}: "
                          f"{entry.subject.name} ({entry.subject.lecturer.name}) "
                          f"in {entry.room.name}")
    
    # Step 5: Export to PDF
    print("\n5. Exporting to PDF...")
    exporter = PDFExporter()
    exporter.export_timetable(timetable, "example_schedule.pdf", 
                             title="Example Timetable")
    print("   - Exported to: example_schedule.pdf")
    
    # Step 6: Demonstrate manual entry addition
    print("\n6. Demonstrating manual entry addition...")
    
    # Create a new timetable for manual demonstration
    manual_timetable = Timetable(weeks=1)
    
    # Add a manual entry
    success, message = scheduler.add_manual_entry(
        timetable=manual_timetable,
        subject=data['subjects'][0],
        room=data['rooms'][0],
        block=data['blocks'][0],  # Monday 09:00-10:00
        week=1
    )
    
    print(f"   - Add entry result: {success}")
    print(f"   - Message: {message}")
    print(f"   - Total entries in manual timetable: {len(manual_timetable.entries)}")
    
    # Try to add a conflicting entry (should fail)
    print("\n7. Demonstrating conflict detection...")
    success, message = scheduler.add_manual_entry(
        timetable=manual_timetable,
        subject=data['subjects'][1],
        room=data['rooms'][0],  # Same room
        block=data['blocks'][0],  # Same time block
        week=1
    )
    
    print(f"   - Add conflicting entry result: {success}")
    print(f"   - Message: {message}")
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")
    print("\nGenerated files:")
    print("  - example_schedule.pdf")


if __name__ == '__main__':
    main()
