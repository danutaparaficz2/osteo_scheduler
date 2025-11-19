"""
Data models for the timetable scheduler.
Includes: Subjects, Lecturers, Blocks, Weeks, Rooms, and Availability.
"""

from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict
from datetime import time, date, datetime
import datetime as dt
from enum import Enum


class TimeOfDay(Enum):
    """Represents time of day periods."""
    MORNING = "morning"  # Typically 08:00 - 12:00
    AFTERNOON = "afternoon"  # Typically 12:00 - 18:00
    
    @staticmethod
    def from_time_string(time_str: str) -> Optional['TimeOfDay']:
        """Determine time of day from a time string (HH:MM format)."""
        try:
            hour = int(time_str.split(':')[0])
            if 8 <= hour < 12:
                return TimeOfDay.MORNING
            elif 12 <= hour < 18:
                return TimeOfDay.AFTERNOON
            return None
        except (ValueError, IndexError):
            return None


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
class DateTimeRestriction:
    """Represents date and time-of-day based availability restrictions."""
    available_dates: Set[date] = field(default_factory=set)  # Specific dates when available
    unavailable_dates: Set[date] = field(default_factory=set)  # Specific dates when unavailable
    available_time_of_day: Dict[date, Set[TimeOfDay]] = field(default_factory=dict)  # Time of day availability per date
    default_time_of_day: Set[TimeOfDay] = field(default_factory=lambda: {TimeOfDay.MORNING, TimeOfDay.AFTERNOON})  # Default if not specified
    
    def is_available_on_date(self, check_date: date, time_of_day: Optional[TimeOfDay] = None) -> bool:
        """Check if available on a specific date and optionally at a specific time of day."""
        # If there are unavailable dates specified and this date is in them, not available
        if check_date in self.unavailable_dates:
            return False
        
        # If there are available dates specified and this date is not in them, not available
        if self.available_dates and check_date not in self.available_dates:
            return False
        
        # Check time of day restrictions
        if time_of_day is not None:
            if check_date in self.available_time_of_day:
                return time_of_day in self.available_time_of_day[check_date]
            else:
                # Use default time of day availability
                return time_of_day in self.default_time_of_day
        
        return True


@dataclass
class Availability:
    """Represents when a lecturer or room is available."""
    entity_id: str  # ID of lecturer or room
    entity_type: str  # "lecturer" or "room"
    available_slots: Set[TimeSlot] = field(default_factory=set)
    date_time_restrictions: Optional[DateTimeRestriction] = None  # Date-based restrictions
    
    def is_available(self, time_slot: TimeSlot, check_date: Optional[date] = None) -> bool:
        """Check if the entity is available at the given time slot and date."""
        # First check slot-based availability (legacy support)
        if self.available_slots and time_slot not in self.available_slots:
            return False
        
        # Then check date-based restrictions if provided
        if self.date_time_restrictions is not None and check_date is not None:
            time_of_day = TimeOfDay.from_time_string(time_slot.start_time)
            if time_of_day is None:
                return False  # Time is outside defined periods
            return self.date_time_restrictions.is_available_on_date(check_date, time_of_day)
        
        # If no date restrictions or no date provided, check only slots
        return not self.available_slots or time_slot in self.available_slots


@dataclass
class ScheduleEntry:
    """Represents a single entry in the timetable."""
    subject: Subject
    room: Room
    block: Block
    week: int  # Week number (1-based)
    scheduled_date: Optional[date] = None  # Actual calendar date for this entry
    is_fixed: bool = False  # Whether this is a fixed appointment
    
    def __hash__(self):
        return hash((self.subject.id, self.room.id, self.block.id, self.week))


@dataclass
class Timetable:
    """Represents a complete timetable schedule."""
    entries: List[ScheduleEntry] = field(default_factory=list)
    weeks: int = 1  # Number of weeks in the schedule
    start_date: Optional[date] = None  # Starting date of the timetable (for calculating actual dates)
    
    def get_date_for_entry(self, week: int, day_name: str) -> Optional[date]:
        """Calculate the actual date for a given week and day name."""
        if self.start_date is None:
            return None
        
        # Map day names to weekday numbers (Monday=0, Sunday=6)
        day_map = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        
        if day_name not in day_map:
            return None
        
        target_weekday = day_map[day_name]
        # Calculate days offset from start_date
        days_offset = (week - 1) * 7 + (target_weekday - self.start_date.weekday()) % 7
        return self.start_date + dt.timedelta(days=days_offset)
    
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
