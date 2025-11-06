"""
Data models for the osteo_scheduler timetable scheduling system.

This module defines the core data structures for scheduling:
- Subject: Course/class to be scheduled
- Lecturer: Instructor with availability
- Block: Time slot structure
- Week: Calendar week
- Room: Physical space with capacity
- Availability: Time slot availability for lecturers
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set
from enum import Enum


class DayOfWeek(Enum):
    """Days of the week."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass
class TimeSlot:
    """Represents a specific time slot in a day."""
    day: DayOfWeek
    start_hour: int
    start_minute: int
    duration_minutes: int
    
    def __str__(self):
        return f"{self.day.name} {self.start_hour:02d}:{self.start_minute:02d} ({self.duration_minutes}min)"
    
    def overlaps_with(self, other: 'TimeSlot') -> bool:
        """Check if this time slot overlaps with another."""
        if self.day != other.day:
            return False
        
        self_start = self.start_hour * 60 + self.start_minute
        self_end = self_start + self.duration_minutes
        other_start = other.start_hour * 60 + other.start_minute
        other_end = other_start + other.duration_minutes
        
        return not (self_end <= other_start or other_end <= self_start)


@dataclass
class Room:
    """Represents a physical room with capacity constraints."""
    id: str
    name: str
    capacity: int
    features: Set[str] = field(default_factory=set)
    
    def __str__(self):
        return f"{self.name} (capacity: {self.capacity})"
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Lecturer:
    """Represents an instructor with availability constraints."""
    id: str
    name: str
    available_slots: List[TimeSlot] = field(default_factory=list)
    max_hours_per_week: Optional[int] = None
    
    def __str__(self):
        return self.name
    
    def __hash__(self):
        return hash(self.id)
    
    def is_available(self, slot: TimeSlot) -> bool:
        """Check if lecturer is available during a given time slot."""
        for avail_slot in self.available_slots:
            if avail_slot.day != slot.day:
                continue
            
            # Check if the requested slot fits within the available slot
            avail_start = avail_slot.start_hour * 60 + avail_slot.start_minute
            avail_end = avail_start + avail_slot.duration_minutes
            slot_start = slot.start_hour * 60 + slot.start_minute
            slot_end = slot_start + slot.duration_minutes
            
            # Available slot must completely contain the requested slot
            if avail_start <= slot_start and slot_end <= avail_end:
                return True
        
        return False


@dataclass
class Subject:
    """Represents a course/class to be scheduled."""
    id: str
    name: str
    duration_minutes: int
    required_lecturers: List[Lecturer]
    min_capacity: int
    required_features: Set[str] = field(default_factory=set)
    preferred_days: Optional[List[DayOfWeek]] = None
    sessions_per_week: int = 1
    
    def __str__(self):
        return self.name
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Block:
    """Represents a structural block of time (e.g., morning block, afternoon block)."""
    id: str
    name: str
    time_slots: List[TimeSlot]
    
    def __str__(self):
        return self.name
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Week:
    """Represents a calendar week."""
    week_number: int
    year: int
    blocks: List[Block] = field(default_factory=list)
    
    def __str__(self):
        return f"Week {self.week_number}, {self.year}"
    
    def __hash__(self):
        return hash((self.week_number, self.year))


@dataclass
class ScheduledSession:
    """Represents a scheduled session (a subject in a specific time slot and room)."""
    subject: Subject
    time_slot: TimeSlot
    room: Room
    week: Week
    is_fixed: bool = False  # Fixed appointments cannot be moved
    
    def __str__(self):
        return f"{self.subject.name} at {self.time_slot} in {self.room.name}"
    
    def conflicts_with(self, other: 'ScheduledSession') -> bool:
        """Check if this session conflicts with another."""
        # Same week check
        if self.week != other.week:
            return False
        
        # Time overlap check
        if not self.time_slot.overlaps_with(other.time_slot):
            return False
        
        # Room conflict
        if self.room == other.room:
            return True
        
        # Lecturer conflict
        self_lecturers = set(self.subject.required_lecturers)
        other_lecturers = set(other.subject.required_lecturers)
        if self_lecturers & other_lecturers:
            return True
        
        return False


@dataclass
class Schedule:
    """Represents a complete timetable schedule."""
    sessions: List[ScheduledSession] = field(default_factory=list)
    
    def add_session(self, session: ScheduledSession) -> bool:
        """Add a session to the schedule if it doesn't conflict."""
        for existing_session in self.sessions:
            if session.conflicts_with(existing_session):
                return False
        self.sessions.append(session)
        return True
    
    def remove_session(self, session: ScheduledSession):
        """Remove a session from the schedule."""
        if session in self.sessions:
            self.sessions.remove(session)
    
    def get_sessions_by_week(self, week: Week) -> List[ScheduledSession]:
        """Get all sessions for a specific week."""
        return [s for s in self.sessions if s.week == week]
    
    def get_sessions_by_room(self, room: Room) -> List[ScheduledSession]:
        """Get all sessions in a specific room."""
        return [s for s in self.sessions if s.room == room]
    
    def get_sessions_by_lecturer(self, lecturer: Lecturer) -> List[ScheduledSession]:
        """Get all sessions for a specific lecturer."""
        return [s for s in self.sessions if lecturer in s.subject.required_lecturers]
    
    def is_valid(self) -> bool:
        """Check if the schedule is valid (no conflicts)."""
        for i, session1 in enumerate(self.sessions):
            for session2 in self.sessions[i+1:]:
                if session1.conflicts_with(session2):
                    return False
        return True
