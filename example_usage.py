"""
Example usage of the osteo_scheduler system.

This script demonstrates how to use the scheduling system programmatically.
"""

from models import (
    Subject, Lecturer, Room, Week, TimeSlot, Block,
    ScheduledSession, Schedule, DayOfWeek
)
from scheduler import SchedulingAlgorithm, SchedulingHelper
from pdf_export import PDFExporter


def example_basic_schedule():
    """Example: Create a basic schedule."""
    print("Example: Basic Schedule Generation")
    print("-" * 60)
    
    # Step 1: Create time slots (Monday-Friday, 8 AM - 6 PM)
    time_slots = SchedulingHelper.create_standard_time_slots()
    print(f"Created {len(time_slots)} time slots")
    
    # Step 2: Create lecturers with availability
    dr_smith = Lecturer(
        id='L1',
        name='Dr. Smith',
        available_slots=time_slots,
        max_hours_per_week=20
    )
    
    dr_johnson = Lecturer(
        id='L2',
        name='Dr. Johnson',
        available_slots=time_slots,
        max_hours_per_week=20
    )
    
    dr_williams = Lecturer(
        id='L3',
        name='Dr. Williams',
        available_slots=time_slots,
        max_hours_per_week=15
    )
    
    print(f"Created 3 lecturers")
    
    # Step 3: Create rooms
    rooms = [
        Room('R1', 'Lecture Hall A', 50, {'projector', 'whiteboard'}),
        Room('R2', 'Lecture Hall B', 40, {'projector', 'computer'}),
        Room('R3', 'Laboratory', 20, {'lab_equipment', 'safety_gear'})
    ]
    print(f"Created {len(rooms)} rooms")
    
    # Step 4: Create subjects
    subjects = [
        Subject(
            id='S1',
            name='Anatomy Lecture',
            duration_minutes=60,
            required_lecturers=[dr_smith],
            min_capacity=40,
            required_features={'projector'},
            sessions_per_week=2
        ),
        Subject(
            id='S2',
            name='Physiology Lecture',
            duration_minutes=60,
            required_lecturers=[dr_johnson],
            min_capacity=40,
            required_features={'projector'},
            sessions_per_week=2
        ),
        Subject(
            id='S3',
            name='Practical Lab',
            duration_minutes=120,
            required_lecturers=[dr_williams],
            min_capacity=18,
            required_features={'lab_equipment'},
            sessions_per_week=1
        )
    ]
    print(f"Created {len(subjects)} subjects")
    
    # Step 5: Create blocks and weeks
    block_definitions = {
        'Morning Block': (8, 12),
        'Afternoon Block': (13, 17)
    }
    blocks = SchedulingHelper.create_blocks_from_slots(time_slots, block_definitions)
    
    weeks = [
        Week(week_number=1, year=2025, blocks=blocks),
        Week(week_number=2, year=2025, blocks=blocks)
    ]
    print(f"Created {len(weeks)} weeks with {len(blocks)} blocks each")
    
    # Step 6: Generate schedule
    print("\nGenerating schedule...")
    algorithm = SchedulingAlgorithm(
        subjects=subjects,
        rooms=rooms,
        weeks=weeks
    )
    
    schedule = algorithm.generate_schedule(max_attempts=1000, randomize=True)
    
    if schedule:
        print(f"✓ Schedule generated successfully!")
        print(f"  Total sessions: {len(schedule.sessions)}")
        print(f"  Valid: {schedule.is_valid()}")
        
        # Get statistics
        stats = SchedulingHelper.get_schedule_statistics(schedule)
        print(f"\nStatistics:")
        print(f"  Sessions: {stats['total_sessions']}")
        print(f"  Rooms used: {stats['rooms_used']}")
        print(f"  Lecturers used: {stats['lecturers_used']}")
        print(f"  Weeks used: {stats['weeks_used']}")
        
        # Show sample sessions
        print("\nSample sessions:")
        for i, session in enumerate(schedule.sessions[:3]):
            print(f"  {i+1}. {session}")
        
        return schedule
    else:
        print("✗ Failed to generate schedule")
        return None


def example_with_fixed_appointments():
    """Example: Schedule with fixed appointments."""
    print("\n\nExample: Schedule with Fixed Appointments")
    print("-" * 60)
    
    # Setup basic data
    time_slots = SchedulingHelper.create_standard_time_slots()
    
    lecturer = Lecturer('L1', 'Dr. Smith', time_slots)
    room = Room('R1', 'Room A', 30, {'projector'})
    
    subject1 = Subject('S1', 'Morning Class', 60, [lecturer], 25, sessions_per_week=2)
    subject2 = Subject('S2', 'Afternoon Class', 60, [lecturer], 25, sessions_per_week=1)
    
    blocks = SchedulingHelper.create_blocks_from_slots(
        time_slots, {'Morning': (8, 12), 'Afternoon': (13, 17)}
    )
    week = Week(1, 2025, blocks)
    
    # Create a fixed appointment (every Monday at 9 AM)
    fixed_slot = TimeSlot(DayOfWeek.MONDAY, 9, 0, 60)
    fixed_session = ScheduledSession(
        subject=subject1,
        time_slot=fixed_slot,
        room=room,
        week=week,
        is_fixed=True
    )
    
    print("Created 1 fixed appointment")
    
    # Generate schedule with fixed appointment
    algorithm = SchedulingAlgorithm(
        subjects=[subject1, subject2],
        rooms=[room],
        weeks=[week],
        fixed_sessions=[fixed_session]
    )
    
    schedule = algorithm.generate_schedule()
    
    if schedule:
        print(f"✓ Schedule generated with fixed appointments")
        print(f"  Total sessions: {len(schedule.sessions)}")
        
        # Show which sessions are fixed
        fixed_count = sum(1 for s in schedule.sessions if s.is_fixed)
        print(f"  Fixed sessions: {fixed_count}")
        print(f"  Flexible sessions: {len(schedule.sessions) - fixed_count}")
        
        return schedule
    else:
        print("✗ Failed to generate schedule")
        return None


def example_pdf_export(schedule):
    """Example: Export schedule to PDF."""
    if not schedule:
        print("\nSkipping PDF export example (no schedule)")
        return
    
    print("\n\nExample: PDF Export")
    print("-" * 60)
    
    exporter = PDFExporter(schedule)
    
    # Export in different formats
    formats = ['weekly', 'by_room', 'by_lecturer']
    
    for format_type in formats:
        filename = f'/tmp/schedule_{format_type}.pdf'
        exporter.export_to_file(filename, view_type=format_type)
        print(f"✓ Exported {format_type} view to {filename}")


def example_manual_adjustments():
    """Example: Manual schedule adjustments."""
    print("\n\nExample: Manual Schedule Adjustments")
    print("-" * 60)
    
    # Create a simple schedule
    time_slots = SchedulingHelper.create_standard_time_slots()
    lecturer = Lecturer('L1', 'Dr. Smith', time_slots)
    room = Room('R1', 'Room A', 30, set())
    subject = Subject('S1', 'Test Class', 60, [lecturer], 25, sessions_per_week=1)
    
    blocks = SchedulingHelper.create_blocks_from_slots(
        time_slots, {'All Day': (8, 18)}
    )
    week = Week(1, 2025, blocks)
    
    algorithm = SchedulingAlgorithm([subject], [room], [week])
    schedule = algorithm.generate_schedule()
    
    if schedule:
        print(f"Initial schedule: {len(schedule.sessions)} sessions")
        
        # Remove a session
        if schedule.sessions:
            removed = schedule.sessions[0]
            schedule.remove_session(removed)
            print(f"✓ Removed session: {removed.subject.name}")
            print(f"  Remaining sessions: {len(schedule.sessions)}")
        
        # Add a new session manually
        new_slot = TimeSlot(DayOfWeek.TUESDAY, 10, 0, 60)
        new_session = ScheduledSession(
            subject=subject,
            time_slot=new_slot,
            room=room,
            week=week
        )
        
        if schedule.add_session(new_session):
            print(f"✓ Added new session: {new_session}")
            print(f"  Total sessions: {len(schedule.sessions)}")
        else:
            print(f"✗ Could not add session (conflict detected)")
        
        print(f"\nSchedule is valid: {schedule.is_valid()}")


def main():
    """Run all examples."""
    print("="*60)
    print("Osteo Scheduler - Usage Examples")
    print("="*60 + "\n")
    
    # Run examples
    schedule1 = example_basic_schedule()
    schedule2 = example_with_fixed_appointments()
    example_pdf_export(schedule1)
    example_manual_adjustments()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == '__main__':
    main()
