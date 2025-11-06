"""
Test script to verify the osteo_scheduler system functionality.
"""

from models import (
    Subject, Lecturer, Room, Week, TimeSlot, Block,
    ScheduledSession, Schedule, DayOfWeek
)
from scheduler import SchedulingAlgorithm, SchedulingHelper
from pdf_export import PDFExporter


def test_data_models():
    """Test basic data model functionality."""
    print("Testing data models...")
    
    # Create a time slot
    slot = TimeSlot(DayOfWeek.MONDAY, 9, 0, 60)
    print(f"  ✓ Created time slot: {slot}")
    
    # Create a room
    room = Room('R1', 'Room A', 30, {'projector'})
    print(f"  ✓ Created room: {room}")
    
    # Create a lecturer
    lecturer = Lecturer('L1', 'Dr. Smith', [slot])
    print(f"  ✓ Created lecturer: {lecturer}")
    
    # Create a subject
    subject = Subject('S1', 'Anatomy', 60, [lecturer], 25)
    print(f"  ✓ Created subject: {subject}")
    
    print("Data models test: PASSED\n")


def test_scheduling_helper():
    """Test scheduling helper functions."""
    print("Testing scheduling helper...")
    
    # Create standard time slots
    slots = SchedulingHelper.create_standard_time_slots()
    print(f"  ✓ Created {len(slots)} standard time slots")
    
    # Create blocks
    block_defs = {'Morning': (8, 12), 'Afternoon': (13, 17)}
    blocks = SchedulingHelper.create_blocks_from_slots(slots, block_defs)
    print(f"  ✓ Created {len(blocks)} blocks")
    
    print("Scheduling helper test: PASSED\n")


def test_schedule_generation():
    """Test schedule generation."""
    print("Testing schedule generation...")
    
    # Setup data
    slots = SchedulingHelper.create_standard_time_slots()
    
    lecturer1 = Lecturer('L1', 'Dr. Smith', slots)
    lecturer2 = Lecturer('L2', 'Dr. Johnson', slots)
    
    room1 = Room('R1', 'Room A', 30, {'projector'})
    room2 = Room('R2', 'Room B', 50, {'projector'})
    
    subject1 = Subject('S1', 'Anatomy', 60, [lecturer1], 25, 
                       required_features={'projector'}, sessions_per_week=2)
    subject2 = Subject('S2', 'Physiology', 60, [lecturer2], 30,
                       required_features={'projector'}, sessions_per_week=2)
    
    blocks = SchedulingHelper.create_blocks_from_slots(
        slots, {'Morning': (8, 12), 'Afternoon': (13, 17)}
    )
    week1 = Week(1, 2025, blocks)
    
    # Generate schedule
    algorithm = SchedulingAlgorithm(
        subjects=[subject1, subject2],
        rooms=[room1, room2],
        weeks=[week1]
    )
    
    schedule = algorithm.generate_schedule(max_attempts=500)
    
    if schedule:
        print(f"  ✓ Schedule generated with {len(schedule.sessions)} sessions")
        print(f"  ✓ Schedule is valid: {schedule.is_valid()}")
        
        # Show statistics
        stats = SchedulingHelper.get_schedule_statistics(schedule)
        print(f"  ✓ Statistics: {stats}")
        
        print("Schedule generation test: PASSED\n")
        return schedule
    else:
        print("  ✗ Failed to generate schedule")
        print("Schedule generation test: FAILED\n")
        return None


def test_pdf_export(schedule):
    """Test PDF export."""
    if not schedule:
        print("Skipping PDF export test (no schedule)\n")
        return
    
    print("Testing PDF export...")
    
    exporter = PDFExporter(schedule)
    
    try:
        # Test exporting to file
        filename = '/tmp/test_schedule.pdf'
        exporter.export_to_file(filename, view_type='weekly')
        print(f"  ✓ Exported to {filename}")
        
        # Test exporting to buffer
        buffer = exporter.export_to_buffer(view_type='by_room')
        print(f"  ✓ Exported to buffer ({len(buffer.getvalue())} bytes)")
        
        print("PDF export test: PASSED\n")
    except Exception as e:
        print(f"  ✗ PDF export failed: {e}")
        print("PDF export test: FAILED\n")


def test_constraint_validation():
    """Test constraint validation."""
    print("Testing constraint validation...")
    
    from scheduler import SchedulingConstraints
    
    # Setup test data
    room = Room('R1', 'Room A', 30, {'projector'})
    small_room = Room('R2', 'Small Room', 10, set())
    
    slot = TimeSlot(DayOfWeek.MONDAY, 9, 0, 60)
    lecturer = Lecturer('L1', 'Dr. Smith', [slot])
    
    subject = Subject('S1', 'Anatomy', 60, [lecturer], 25, 
                      required_features={'projector'})
    
    constraints = SchedulingConstraints()
    
    # Test room capacity
    assert constraints.check_room_capacity(subject, room) == True
    assert constraints.check_room_capacity(subject, small_room) == False
    print("  ✓ Room capacity constraint works")
    
    # Test room features
    assert constraints.check_room_features(subject, room) == True
    assert constraints.check_room_features(subject, small_room) == False
    print("  ✓ Room features constraint works")
    
    # Test lecturer availability
    assert constraints.check_lecturer_availability(subject, slot) == True
    other_slot = TimeSlot(DayOfWeek.MONDAY, 15, 0, 60)
    assert constraints.check_lecturer_availability(subject, other_slot) == False
    print("  ✓ Lecturer availability constraint works")
    
    print("Constraint validation test: PASSED\n")


def main():
    """Run all tests."""
    print("="*60)
    print("Osteo Scheduler - System Test")
    print("="*60 + "\n")
    
    test_data_models()
    test_scheduling_helper()
    test_constraint_validation()
    schedule = test_schedule_generation()
    test_pdf_export(schedule)
    
    print("="*60)
    print("All tests completed!")
    print("="*60)


if __name__ == '__main__':
    main()
