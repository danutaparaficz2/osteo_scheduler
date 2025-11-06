"""
Data models for the timetable scheduler.
Includes: Subjects, Lecturers, Blocks, Weeks, Rooms, and Availability.
"""

from dataclasses import dataclass, field
from typing import List, Set, Optional
from datetime import time


@dataclass
class Room:
    """Represents a physical room where classes can be held."""
    id: str
    name: str
    capacity: int
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Room):
            return False
        return self.id == other.id


@dataclass
class Lecturer:
    """Represents a lecturer who teaches subjects."""
    id: str
    name: str
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Lecturer):
            return False
        return self.id == other.id


@dataclass
class Subject:
    """Represents a subject/course to be scheduled."""
    id: str
    name: str
    lecturer: Lecturer
    required_hours: int  # Total hours per week
    min_students: int
    max_students: int
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Subject):
            return False
        return self.id == other.id


@dataclass
class TimeSlot:
    """Represents a time slot in the schedule."""
    day: str  # e.g., "Monday", "Tuesday"
    start_time: str  # e.g., "09:00"
    end_time: str  # e.g., "10:00"
    
    def __hash__(self):
        return hash((self.day, self.start_time, self.end_time))
    
    def __eq__(self, other):
        if not isinstance(other, TimeSlot):
            return False
        return (self.day == other.day and 
                self.start_time == other.start_time and 
                self.end_time == other.end_time)


@dataclass
class Block:
    """Represents a block of time (e.g., a lecture period)."""
    id: str
    time_slot: TimeSlot
    duration_hours: int  # Duration in hours
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Block):
            return False
        return self.id == other.id


@dataclass
class Availability:
    """Represents when a lecturer or room is available."""
    entity_id: str  # ID of lecturer or room
    entity_type: str  # "lecturer" or "room"
    available_slots: Set[TimeSlot] = field(default_factory=set)
    
    def is_available(self, time_slot: TimeSlot) -> bool:
        """Check if the entity is available at the given time slot."""
        return time_slot in self.available_slots


@dataclass
class ScheduleEntry:
    """Represents a single entry in the timetable."""
    subject: Subject
    room: Room
    block: Block
    week: int  # Week number (1-based)
    is_fixed: bool = False  # Whether this is a fixed appointment
    
    def __hash__(self):
        return hash((self.subject.id, self.room.id, self.block.id, self.week))


@dataclass
class Timetable:
    """Represents a complete timetable schedule."""
    entries: List[ScheduleEntry] = field(default_factory=list)
    weeks: int = 1  # Number of weeks in the schedule
    
    def add_entry(self, entry: ScheduleEntry) -> bool:
        """Add an entry to the timetable if it doesn't conflict."""
        if self._has_conflict(entry):
            return False
        self.entries.append(entry)
        return True
    
    def _has_conflict(self, new_entry: ScheduleEntry) -> bool:
        """Check if a new entry conflicts with existing entries."""
        for entry in self.entries:
            # Same week and same time block
            if entry.week == new_entry.week and entry.block.id == new_entry.block.id:
                # Check for room conflict
                if entry.room.id == new_entry.room.id:
                    return True
                # Check for lecturer conflict
                if entry.subject.lecturer.id == new_entry.subject.lecturer.id:
                    return True
        return False
    
    def get_entries_by_week(self, week: int) -> List[ScheduleEntry]:
        """Get all entries for a specific week."""
        return [entry for entry in self.entries if entry.week == week]
    
    def get_entries_by_lecturer(self, lecturer_id: str) -> List[ScheduleEntry]:
        """Get all entries for a specific lecturer."""
        return [entry for entry in self.entries if entry.subject.lecturer.id == lecturer_id]
    
    def get_entries_by_room(self, room_id: str) -> List[ScheduleEntry]:
        """Get all entries for a specific room."""
        return [entry for entry in self.entries if entry.room.id == room_id]
    
    def remove_entry(self, entry: ScheduleEntry) -> bool:
        """Remove an entry from the timetable."""
        if entry in self.entries:
            self.entries.remove(entry)
            return True
        return False
