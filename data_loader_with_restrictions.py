"""
Data loader that parses JSON files with time restriction data.
Extends data_manager to support the new time restriction format.
"""

import json
from typing import Dict, List
from datetime import date, datetime
from models import Lecturer, Room, Subject, Block, TimeSlot
from time_restrictions import (
    create_lecturer_availability_from_list,
    create_lecturer_availability_from_ranges
)


def load_lecturer_time_restrictions(lecturer_data: dict) -> dict:
    """
    Load time restrictions from lecturer data dictionary.
    
    Args:
        lecturer_data: Dictionary containing lecturer info and time_restrictions
        
    Returns:
        Dictionary with lecturer_id as key and Availability object as value
    """
    restrictions = {}
    
    for lecturer_info in lecturer_data:
        lecturer_id = lecturer_info['id']
        
        if 'time_restrictions' not in lecturer_info:
            continue
        
        restriction_data = lecturer_info['time_restrictions']
        restriction_type = restriction_data.get('type', 'specific_dates')
        
        if restriction_type == 'specific_dates':
            # Load from list of specific dates
            available_dates = restriction_data.get('available_dates', [])
            if available_dates:
                availability = create_lecturer_availability_from_list(
                    lecturer_id,
                    available_dates
                )
                restrictions[lecturer_id] = availability
        
        elif restriction_type == 'date_ranges':
            # Load from date ranges
            available_ranges = restriction_data.get('available_ranges', [])
            unavailable_dates = restriction_data.get('unavailable_dates', [])
            if available_ranges:
                availability = create_lecturer_availability_from_ranges(
                    lecturer_id,
                    available_ranges,
                    unavailable_dates
                )
                restrictions[lecturer_id] = availability
    
    return restrictions


def load_data_with_time_restrictions(json_file_path: str) -> dict:
    """
    Load scheduling data from JSON file including time restrictions.
    
    Args:
        json_file_path: Path to JSON file
        
    Returns:
        Dictionary containing:
            - lecturers: List of Lecturer objects
            - rooms: List of Room objects
            - subjects: List of Subject objects
            - blocks: List of Block objects
            - lecturer_restrictions: Dict of lecturer_id -> Availability
            - start_date: Starting date for the schedule (if provided)
            - weeks: Number of weeks (if provided)
    """
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Load lecturers
    lecturers = []
    lecturer_dict = {}
    for l_data in data.get('lecturers', []):
        lecturer = Lecturer(
            id=l_data['id'],
            name=l_data['name']
        )
        lecturers.append(lecturer)
        lecturer_dict[lecturer.id] = lecturer
    
    # Load rooms
    rooms = []
    for r_data in data.get('rooms', []):
        room = Room(
            id=r_data['id'],
            name=r_data['name'],
            capacity=r_data['capacity']
        )
        rooms.append(room)
    
    # Load subjects
    subjects = []
    for s_data in data.get('subjects', []):
        lecturer = lecturer_dict.get(s_data['lecturer_id'])
        if lecturer:
            subject = Subject(
                id=s_data['id'],
                name=s_data['name'],
                lecturer=lecturer,
                required_hours=s_data['required_hours'],
                min_students=s_data['min_students'],
                max_students=s_data['max_students']
            )
            subjects.append(subject)
    
    # Load blocks
    blocks = []
    for b_data in data.get('blocks', []):
        time_slot = TimeSlot(
            day=b_data['day'],
            start_time=b_data['start_time'],
            end_time=b_data['end_time']
        )
        block = Block(
            id=b_data['id'],
            time_slot=time_slot,
            duration_hours=b_data['duration_hours']
        )
        blocks.append(block)
    
    # Load time restrictions
    lecturer_restrictions = load_lecturer_time_restrictions(data.get('lecturers', []))
    
    # Load schedule configuration
    schedule_config = data.get('schedule_config', {})
    start_date_str = schedule_config.get('start_date')
    start_date = None
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    
    weeks = schedule_config.get('weeks', 1)
    
    return {
        'lecturers': lecturers,
        'rooms': rooms,
        'subjects': subjects,
        'blocks': blocks,
        'lecturer_restrictions': lecturer_restrictions,
        'start_date': start_date,
        'weeks': weeks
    }


def print_time_restrictions_summary(lecturer_restrictions: dict, lecturers: List[Lecturer]):
    """
    Print a summary of lecturer time restrictions.
    
    Args:
        lecturer_restrictions: Dict of lecturer_id -> Availability
        lecturers: List of Lecturer objects
    """
    print("\n" + "=" * 70)
    print("LECTURER TIME RESTRICTIONS SUMMARY")
    print("=" * 70)
    
    lecturer_dict = {l.id: l for l in lecturers}
    
    for lecturer_id, availability in lecturer_restrictions.items():
        lecturer = lecturer_dict.get(lecturer_id)
        if not lecturer:
            continue
        
        print(f"\n{lecturer.name} ({lecturer_id}):")
        
        if availability.date_time_restrictions:
            restriction = availability.date_time_restrictions
            
            # Print available dates
            if restriction.available_dates:
                sorted_dates = sorted(restriction.available_dates)
                print(f"  Available on {len(sorted_dates)} specific dates:")
                
                # Group consecutive dates
                if sorted_dates:
                    start_range = sorted_dates[0]
                    end_range = sorted_dates[0]
                    
                    for i in range(1, len(sorted_dates)):
                        if (sorted_dates[i] - end_range).days == 1:
                            end_range = sorted_dates[i]
                        else:
                            if start_range == end_range:
                                print(f"    - {start_range}")
                            else:
                                print(f"    - {start_range} to {end_range}")
                            start_range = sorted_dates[i]
                            end_range = sorted_dates[i]
                    
                    # Print last range
                    if start_range == end_range:
                        print(f"    - {start_range}")
                    else:
                        print(f"    - {start_range} to {end_range}")
            
            # Print unavailable dates
            if restriction.unavailable_dates:
                sorted_unavail = sorted(restriction.unavailable_dates)
                print(f"  Unavailable on {len(sorted_unavail)} dates:")
                for unavail_date in sorted_unavail:
                    print(f"    - {unavail_date}")
            
            # Print time of day restrictions for specific dates
            if restriction.available_time_of_day:
                print(f"  Time-of-day restrictions:")
                for restrict_date, times in sorted(restriction.available_time_of_day.items()):
                    time_str = ", ".join([t.value.capitalize() for t in times])
                    print(f"    - {restrict_date}: {time_str}")
            
            # Print default availability
            if restriction.default_time_of_day:
                default_str = ", ".join([t.value.capitalize() for t in restriction.default_time_of_day])
                print(f"  Default time availability: {default_str}")
        else:
            print("  No time restrictions")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    # Test the loader with the sample data
    data = load_data_with_time_restrictions(
        'examples/sample_data_with_time_restrictions.json'
    )
    
    print("Loaded scheduling data:")
    print(f"  Lecturers: {len(data['lecturers'])}")
    print(f"  Rooms: {len(data['rooms'])}")
    print(f"  Subjects: {len(data['subjects'])}")
    print(f"  Blocks: {len(data['blocks'])}")
    print(f"  Start date: {data['start_date']}")
    print(f"  Weeks: {data['weeks']}")
    
    print_time_restrictions_summary(
        data['lecturer_restrictions'],
        data['lecturers']
    )
