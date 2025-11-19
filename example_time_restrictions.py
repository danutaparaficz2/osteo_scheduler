"""
Example demonstrating how to use lecturer time restrictions.

This example shows how to:
1. Define time restrictions for lecturers using specific dates and times of day
2. Create a schedule that respects these restrictions
3. Verify that the generated schedule follows the constraints
"""

from datetime import date, datetime
from models import Lecturer, Room, Subject, Block, TimeSlot
from scheduler import SchedulerConstraints, TimetableScheduler
from time_restrictions import (
    LecturerTimeRestrictionBuilder,
    create_lecturer_availability_from_list,
    create_lecturer_availability_from_ranges
)


def example_1_basic_usage():
    """
    Example 1: Basic usage with specific dates and time of day restrictions.
    
    Scenario: Dr. Smith is only available on certain dates, and on some dates
    only in the morning or afternoon.
    """
    print("=" * 70)
    print("Example 1: Basic Time Restrictions")
    print("=" * 70)
    
    # Create a lecturer
    lecturer = Lecturer(id="L1", name="Dr. Sarah Smith")
    
    # Build time restrictions using the builder
    builder = LecturerTimeRestrictionBuilder(lecturer.id)
    
    # Dr. Smith is available on these specific dates:
    # Jan 15, 2025 - Morning only
    builder.add_available_date("2025-01-15", morning=True, afternoon=False)
    
    # Jan 16, 2025 - All day
    builder.add_available_date("2025-01-16", morning=True, afternoon=True)
    
    # Jan 17, 2025 - Afternoon only
    builder.add_available_date("2025-01-17", morning=False, afternoon=True)
    
    # Jan 20-22, 2025 - All day
    builder.add_available_date_range("2025-01-20", "2025-01-22", morning=True, afternoon=True)
    
    # But not available on Jan 21 (exception)
    builder.add_unavailable_date("2025-01-21")
    
    # Build the availability constraint
    availability = builder.build()
    
    print(f"\nLecturer: {lecturer.name}")
    print(f"Available dates: {len(availability.date_time_restrictions.available_dates)}")
    print("Details:")
    
    # Check some specific dates
    test_dates = [
        ("2025-01-15", "morning"),
        ("2025-01-15", "afternoon"),
        ("2025-01-16", "morning"),
        ("2025-01-17", "morning"),
        ("2025-01-17", "afternoon"),
        ("2025-01-21", "morning"),
        ("2025-01-22", "afternoon")
    ]
    
    from models import TimeOfDay
    for date_str, time_period in test_dates:
        check_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        tod = TimeOfDay.MORNING if time_period == "morning" else TimeOfDay.AFTERNOON
        is_available = availability.date_time_restrictions.is_available_on_date(check_date, tod)
        print(f"  {date_str} {time_period:10s}: {'✓ Available' if is_available else '✗ Not available'}")
    
    return lecturer, availability


def example_2_from_list():
    """
    Example 2: Create restrictions from a list of date specifications.
    
    This is useful when you have availability data in a structured format.
    """
    print("\n" + "=" * 70)
    print("Example 2: Creating Restrictions from a List")
    print("=" * 70)
    
    lecturer = Lecturer(id="L2", name="Prof. Michael Chen")
    
    # Define availability as a list of date specifications
    available_dates = [
        {"date": "2025-01-15", "morning": True, "afternoon": False},
        {"date": "2025-01-16", "morning": True, "afternoon": True},
        {"date": "2025-01-17", "morning": False, "afternoon": True},
        {"date": "2025-01-20", "morning": True, "afternoon": True},
        {"date": "2025-01-22", "morning": True, "afternoon": True},
    ]
    
    availability = create_lecturer_availability_from_list(lecturer.id, available_dates)
    
    print(f"\nLecturer: {lecturer.name}")
    print(f"Available on {len(available_dates)} specific dates")
    print("\nAvailability schedule:")
    for date_spec in available_dates:
        morning = "Morning" if date_spec["morning"] else ""
        afternoon = "Afternoon" if date_spec["afternoon"] else ""
        times = ", ".join(filter(None, [morning, afternoon]))
        print(f"  {date_spec['date']}: {times}")
    
    return lecturer, availability


def example_3_from_ranges():
    """
    Example 3: Create restrictions from date ranges.
    
    This is useful when a lecturer is available for extended periods.
    """
    print("\n" + "=" * 70)
    print("Example 3: Creating Restrictions from Date Ranges")
    print("=" * 70)
    
    lecturer = Lecturer(id="L3", name="Dr. Emily Rodriguez")
    
    # Define availability as ranges
    available_ranges = [
        # First two weeks of January - all day
        {"start": "2025-01-06", "end": "2025-01-17", "morning": True, "afternoon": True},
        
        # Last week of January - mornings only
        {"start": "2025-01-27", "end": "2025-01-31", "morning": True, "afternoon": False},
    ]
    
    # Except these specific dates (e.g., conferences, holidays)
    unavailable_dates = ["2025-01-10", "2025-01-15"]
    
    availability = create_lecturer_availability_from_ranges(
        lecturer.id,
        available_ranges,
        unavailable_dates
    )
    
    print(f"\nLecturer: {lecturer.name}")
    print("\nAvailable periods:")
    for range_spec in available_ranges:
        morning = "Morning" if range_spec["morning"] else ""
        afternoon = "Afternoon" if range_spec["afternoon"] else ""
        times = ", ".join(filter(None, [morning, afternoon]))
        print(f"  {range_spec['start']} to {range_spec['end']}: {times}")
    
    if unavailable_dates:
        print(f"\nExceptions (unavailable): {', '.join(unavailable_dates)}")
    
    return lecturer, availability


def example_4_complete_scheduling():
    """
    Example 4: Complete scheduling example with time restrictions.
    
    This shows how to integrate time restrictions into the full scheduling process.
    """
    print("\n" + "=" * 70)
    print("Example 4: Complete Scheduling with Time Restrictions")
    print("=" * 70)
    
    # Create lecturers
    lecturer1 = Lecturer(id="L1", name="Dr. Sarah Smith")
    lecturer2 = Lecturer(id="L2", name="Prof. Michael Chen")
    
    # Set up time restrictions
    # Dr. Smith: Available Jan 15-19, mornings only
    availability1 = (LecturerTimeRestrictionBuilder(lecturer1.id)
                    .add_available_date_range("2025-01-15", "2025-01-19", 
                                             morning=True, afternoon=False)
                    .build())
    
    # Prof. Chen: Available Jan 15-19, afternoons only
    availability2 = (LecturerTimeRestrictionBuilder(lecturer2.id)
                    .add_available_date_range("2025-01-15", "2025-01-19", 
                                             morning=False, afternoon=True)
                    .build())
    
    # Create rooms
    rooms = [
        Room(id="R1", name="Lecture Hall A", capacity=50),
        Room(id="R2", name="Seminar Room 1", capacity=25),
    ]
    
    # Create subjects
    subjects = [
        Subject(
            id="S1",
            name="Osteopathic Principles",
            lecturer=lecturer1,
            required_hours=4,
            min_students=20,
            max_students=50
        ),
        Subject(
            id="S2",
            name="Clinical Practice",
            lecturer=lecturer2,
            required_hours=3,
            min_students=10,
            max_students=25
        ),
    ]
    
    # Create time blocks
    blocks = [
        # Monday morning
        Block(
            id="B1",
            time_slot=TimeSlot(day="Monday", start_time="09:00", end_time="11:00"),
            duration_hours=2
        ),
        # Monday afternoon
        Block(
            id="B2",
            time_slot=TimeSlot(day="Monday", start_time="14:00", end_time="16:00"),
            duration_hours=2
        ),
        # Wednesday morning
        Block(
            id="B3",
            time_slot=TimeSlot(day="Wednesday", start_time="09:00", end_time="11:00"),
            duration_hours=2
        ),
        # Wednesday afternoon
        Block(
            id="B4",
            time_slot=TimeSlot(day="Wednesday", start_time="14:00", end_time="16:00"),
            duration_hours=2
        ),
    ]
    
    # Set up constraints
    constraints = SchedulerConstraints()
    constraints.add_lecturer_availability(lecturer1.id, availability1)
    constraints.add_lecturer_availability(lecturer2.id, availability2)
    
    # Create scheduler
    scheduler = TimetableScheduler(constraints)
    
    # Generate timetable
    # Start date: Monday, January 15, 2025
    start_date = date(2025, 1, 15)
    timetable = scheduler.generate_timetable(
        subjects=subjects,
        rooms=rooms,
        blocks=blocks,
        weeks=1,
        start_date=start_date
    )
    
    print(f"\nGenerated timetable starting from {start_date}")
    print(f"Total entries scheduled: {len(timetable.entries)}\n")
    
    # Display the schedule
    print("Schedule:")
    print("-" * 70)
    for entry in sorted(timetable.entries, key=lambda e: (e.week, e.block.id)):
        time_slot = entry.block.time_slot
        time_info = f"{time_slot.day:10s} {time_slot.start_time}-{time_slot.end_time}"
        date_info = f"({entry.scheduled_date})" if entry.scheduled_date else ""
        print(f"  {time_info} {date_info:15s} | {entry.subject.name:25s} | "
              f"{entry.subject.lecturer.name:20s} | {entry.room.name}")
    
    # Verify constraints
    print("\n" + "-" * 70)
    print("Verification:")
    all_valid = True
    for entry in timetable.entries:
        time_slot = entry.block.time_slot
        lecturer = entry.subject.lecturer
        
        # Check if this entry respects the lecturer's time restrictions
        avail = constraints.lecturer_availability.get(lecturer.id)
        if avail:
            is_valid = avail.is_available(time_slot, entry.scheduled_date)
            status = "✓" if is_valid else "✗"
            if not is_valid:
                all_valid = False
                print(f"{status} INVALID: {lecturer.name} scheduled on {entry.scheduled_date} "
                      f"{time_slot.day} {time_slot.start_time}")
    
    if all_valid:
        print("✓ All entries respect lecturer time restrictions!")
    
    return timetable


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "LECTURER TIME RESTRICTIONS - EXAMPLES" + " " * 21 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    # Run examples
    example_1_basic_usage()
    example_2_from_list()
    example_3_from_ranges()
    example_4_complete_scheduling()
    
    print("\n" + "=" * 70)
    print("Examples completed successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
