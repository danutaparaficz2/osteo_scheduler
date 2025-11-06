"""
Scheduling engine that applies constraints to generate a valid timetable.
"""

from typing import List, Dict, Set, Optional
from models import (
    Subject, Lecturer, Room, Block, Availability, 
    ScheduleEntry, Timetable, TimeSlot
)
import random


class SchedulerConstraints:
    """Manages and validates scheduling constraints."""
    
    def __init__(self):
        self.room_availability: Dict[str, Availability] = {}
        self.lecturer_availability: Dict[str, Availability] = {}
        self.fixed_entries: List[ScheduleEntry] = []
    
    def add_room_availability(self, room_id: str, availability: Availability):
        """Add availability constraints for a room."""
        self.room_availability[room_id] = availability
    
    def add_lecturer_availability(self, lecturer_id: str, availability: Availability):
        """Add availability constraints for a lecturer."""
        self.lecturer_availability[lecturer_id] = availability
    
    def add_fixed_entry(self, entry: ScheduleEntry):
        """Add a fixed appointment that cannot be changed."""
        entry.is_fixed = True
        self.fixed_entries.append(entry)
    
    def validate_room_capacity(self, subject: Subject, room: Room) -> bool:
        """Check if room capacity meets subject requirements."""
        return room.capacity >= subject.min_students
    
    def validate_room_availability(self, room: Room, time_slot: TimeSlot) -> bool:
        """Check if room is available at the given time."""
        if room.id not in self.room_availability:
            return True  # No constraints means available
        return self.room_availability[room.id].is_available(time_slot)
    
    def validate_lecturer_availability(self, lecturer: Lecturer, time_slot: TimeSlot) -> bool:
        """Check if lecturer is available at the given time."""
        if lecturer.id not in self.lecturer_availability:
            return True  # No constraints means available
        return self.lecturer_availability[lecturer.id].is_available(time_slot)
    
    def validate_no_conflicts(self, timetable: Timetable, new_entry: ScheduleEntry) -> bool:
        """Check if adding the new entry would create conflicts."""
        for entry in timetable.entries:
            if entry.week == new_entry.week and entry.block.id == new_entry.block.id:
                # Room conflict
                if entry.room.id == new_entry.room.id:
                    return False
                # Lecturer conflict
                if entry.subject.lecturer.id == new_entry.subject.lecturer.id:
                    return False
        return True


class TimetableScheduler:
    """
    Semi-automated scheduler that generates timetables based on constraints.
    """
    
    def __init__(self, constraints: SchedulerConstraints):
        self.constraints = constraints
    
    def generate_timetable(
        self,
        subjects: List[Subject],
        rooms: List[Room],
        blocks: List[Block],
        weeks: int = 1
    ) -> Timetable:
        """
        Generate a timetable for the given subjects, rooms, and time blocks.
        
        Args:
            subjects: List of subjects to schedule
            rooms: List of available rooms
            blocks: List of time blocks available for scheduling
            weeks: Number of weeks to schedule
            
        Returns:
            A Timetable object with scheduled entries
        """
        timetable = Timetable(weeks=weeks)
        
        # First, add all fixed entries
        for fixed_entry in self.constraints.fixed_entries:
            timetable.add_entry(fixed_entry)
        
        # For each subject, schedule the required hours
        for subject in subjects:
            self._schedule_subject(subject, rooms, blocks, weeks, timetable)
        
        return timetable
    
    def _schedule_subject(
        self,
        subject: Subject,
        rooms: List[Room],
        blocks: List[Block],
        weeks: int,
        timetable: Timetable
    ):
        """Schedule a single subject across the available weeks."""
        hours_scheduled = 0
        attempts = 0
        max_attempts = len(rooms) * len(blocks) * weeks * 10
        
        # Filter suitable rooms by capacity
        suitable_rooms = [
            room for room in rooms 
            if self.constraints.validate_room_capacity(subject, room)
        ]
        
        if not suitable_rooms:
            print(f"Warning: No suitable rooms found for subject {subject.name}")
            return
        
        while hours_scheduled < subject.required_hours and attempts < max_attempts:
            attempts += 1
            
            # Randomly select a week, block, and room
            week = random.randint(1, weeks)
            block = random.choice(blocks)
            room = random.choice(suitable_rooms)
            
            # Create a potential entry
            entry = ScheduleEntry(
                subject=subject,
                room=room,
                block=block,
                week=week,
                is_fixed=False
            )
            
            # Validate all constraints
            if self._validate_entry(entry, timetable):
                if timetable.add_entry(entry):
                    hours_scheduled += block.duration_hours
        
        if hours_scheduled < subject.required_hours:
            print(f"Warning: Only scheduled {hours_scheduled}/{subject.required_hours} hours for {subject.name}")
    
    def _validate_entry(self, entry: ScheduleEntry, timetable: Timetable) -> bool:
        """Validate that an entry meets all constraints."""
        # Check room availability
        if not self.constraints.validate_room_availability(
            entry.room, entry.block.time_slot
        ):
            return False
        
        # Check lecturer availability
        if not self.constraints.validate_lecturer_availability(
            entry.subject.lecturer, entry.block.time_slot
        ):
            return False
        
        # Check for conflicts
        if not self.constraints.validate_no_conflicts(timetable, entry):
            return False
        
        return True
    
    def add_manual_entry(
        self,
        timetable: Timetable,
        subject: Subject,
        room: Room,
        block: Block,
        week: int
    ) -> tuple[bool, str]:
        """
        Manually add an entry to the timetable.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        entry = ScheduleEntry(
            subject=subject,
            room=room,
            block=block,
            week=week,
            is_fixed=False
        )
        
        # Validate constraints
        if not self.constraints.validate_room_capacity(subject, room):
            return False, f"Room capacity ({room.capacity}) is less than minimum students ({subject.min_students})"
        
        if not self.constraints.validate_room_availability(room, block.time_slot):
            return False, f"Room {room.name} is not available at this time"
        
        if not self.constraints.validate_lecturer_availability(subject.lecturer, block.time_slot):
            return False, f"Lecturer {subject.lecturer.name} is not available at this time"
        
        if not self.constraints.validate_no_conflicts(timetable, entry):
            return False, "This time slot conflicts with another entry"
        
        if timetable.add_entry(entry):
            return True, "Entry added successfully"
        
        return False, "Failed to add entry"
    
    def remove_manual_entry(
        self,
        timetable: Timetable,
        entry: ScheduleEntry
    ) -> tuple[bool, str]:
        """
        Remove an entry from the timetable (if not fixed).
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if entry.is_fixed:
            return False, "Cannot remove fixed entries"
        
        if timetable.remove_entry(entry):
            return True, "Entry removed successfully"
        
        return False, "Entry not found in timetable"
