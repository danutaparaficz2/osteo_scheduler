"""
Data input/output module for loading and saving timetable data.
"""

import json
from typing import List, Dict, Any
from models import (
    Subject, Lecturer, Room, Block, Availability, 
    ScheduleEntry, Timetable, TimeSlot
)


class DataManager:
    """Manages loading and saving of timetable data."""
    
    def __init__(self):
        self.lecturers: Dict[str, Lecturer] = {}
        self.rooms: Dict[str, Room] = {}
        self.subjects: Dict[str, Subject] = {}
        self.blocks: Dict[str, Block] = {}
        self.time_slots: Dict[str, TimeSlot] = {}
    
    def load_from_json(self, data: Dict[str, Any]):
        """Load data from a JSON structure."""
        # Load time slots
        for slot_data in data.get('time_slots', []):
            time_slot = TimeSlot(
                day=slot_data['day'],
                start_time=slot_data['start_time'],
                end_time=slot_data['end_time']
            )
            slot_id = f"{slot_data['day']}_{slot_data['start_time']}"
            self.time_slots[slot_id] = time_slot
        
        # Load lecturers
        for lecturer_data in data.get('lecturers', []):
            lecturer = Lecturer(
                id=lecturer_data['id'],
                name=lecturer_data['name']
            )
            self.lecturers[lecturer.id] = lecturer
        
        # Load rooms
        for room_data in data.get('rooms', []):
            room = Room(
                id=room_data['id'],
                name=room_data['name'],
                capacity=room_data['capacity']
            )
            self.rooms[room.id] = room
        
        # Load blocks
        for block_data in data.get('blocks', []):
            slot_id = f"{block_data['day']}_{block_data['start_time']}"
            if slot_id in self.time_slots:
                time_slot = self.time_slots[slot_id]
            else:
                time_slot = TimeSlot(
                    day=block_data['day'],
                    start_time=block_data['start_time'],
                    end_time=block_data['end_time']
                )
                self.time_slots[slot_id] = time_slot
            
            block = Block(
                id=block_data['id'],
                time_slot=time_slot,
                duration_hours=block_data['duration_hours']
            )
            self.blocks[block.id] = block
        
        # Load subjects
        for subject_data in data.get('subjects', []):
            lecturer = self.lecturers.get(subject_data['lecturer_id'])
            if not lecturer:
                print(f"Warning: Lecturer {subject_data['lecturer_id']} not found for subject {subject_data['name']}")
                continue
            
            subject = Subject(
                id=subject_data['id'],
                name=subject_data['name'],
                lecturer=lecturer,
                required_hours=subject_data['required_hours'],
                min_students=subject_data['min_students'],
                max_students=subject_data['max_students']
            )
            self.subjects[subject.id] = subject
    
    def load_from_file(self, filepath: str):
        """Load data from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.load_from_json(data)
    
    def save_to_file(self, filepath: str):
        """Save current data to a JSON file."""
        data = {
            'time_slots': [
                {
                    'day': ts.day,
                    'start_time': ts.start_time,
                    'end_time': ts.end_time
                }
                for ts in self.time_slots.values()
            ],
            'lecturers': [
                {
                    'id': l.id,
                    'name': l.name
                }
                for l in self.lecturers.values()
            ],
            'rooms': [
                {
                    'id': r.id,
                    'name': r.name,
                    'capacity': r.capacity
                }
                for r in self.rooms.values()
            ],
            'blocks': [
                {
                    'id': b.id,
                    'day': b.time_slot.day,
                    'start_time': b.time_slot.start_time,
                    'end_time': b.time_slot.end_time,
                    'duration_hours': b.duration_hours
                }
                for b in self.blocks.values()
            ],
            'subjects': [
                {
                    'id': s.id,
                    'name': s.name,
                    'lecturer_id': s.lecturer.id,
                    'required_hours': s.required_hours,
                    'min_students': s.min_students,
                    'max_students': s.max_students
                }
                for s in self.subjects.values()
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_all_lecturers(self) -> List[Lecturer]:
        """Get all loaded lecturers."""
        return list(self.lecturers.values())
    
    def get_all_rooms(self) -> List[Room]:
        """Get all loaded rooms."""
        return list(self.rooms.values())
    
    def get_all_subjects(self) -> List[Subject]:
        """Get all loaded subjects."""
        return list(self.subjects.values())
    
    def get_all_blocks(self) -> List[Block]:
        """Get all loaded blocks."""
        return list(self.blocks.values())


def export_timetable_to_json(timetable: Timetable, filepath: str):
    """Export a timetable to JSON format."""
    data = {
        'weeks': timetable.weeks,
        'entries': [
            {
                'subject_id': entry.subject.id,
                'subject_name': entry.subject.name,
                'lecturer': entry.subject.lecturer.name,
                'room_id': entry.room.id,
                'room_name': entry.room.name,
                'block_id': entry.block.id,
                'day': entry.block.time_slot.day,
                'start_time': entry.block.time_slot.start_time,
                'end_time': entry.block.time_slot.end_time,
                'week': entry.week,
                'is_fixed': entry.is_fixed
            }
            for entry in timetable.entries
        ]
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
