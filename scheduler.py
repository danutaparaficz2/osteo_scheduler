"""
Scheduling algorithm for the osteo_scheduler system.

This module implements a constraint satisfaction approach to generate valid timetables
by applying all constraints: room limits, lecturer conflicts, fixed appointments, 
block structure, and availability.
"""

from typing import List, Optional, Dict, Tuple
from models import (
    Subject, Lecturer, Room, Week, TimeSlot, Block,
    ScheduledSession, Schedule, DayOfWeek
)
import random


class SchedulingConstraints:
    """Defines and validates scheduling constraints."""
    
    @staticmethod
    def check_room_capacity(subject: Subject, room: Room) -> bool:
        """Check if room has sufficient capacity for the subject."""
        return room.capacity >= subject.min_capacity
    
    @staticmethod
    def check_room_features(subject: Subject, room: Room) -> bool:
        """Check if room has required features for the subject."""
        return subject.required_features.issubset(room.features)
    
    @staticmethod
    def check_lecturer_availability(subject: Subject, time_slot: TimeSlot) -> bool:
        """Check if all required lecturers are available."""
        return all(lecturer.is_available(time_slot) for lecturer in subject.required_lecturers)
    
    @staticmethod
    def check_preferred_days(subject: Subject, time_slot: TimeSlot) -> bool:
        """Check if time slot is on a preferred day (if specified)."""
        if subject.preferred_days is None:
            return True
        return time_slot.day in subject.preferred_days
    
    @staticmethod
    def check_no_conflicts(schedule: Schedule, session: ScheduledSession) -> bool:
        """Check if session doesn't conflict with existing sessions."""
        for existing_session in schedule.sessions:
            if session.conflicts_with(existing_session):
                return False
        return True


class SchedulingAlgorithm:
    """
    Semi-automated scheduling algorithm using iterative placement with backtracking.
    """
    
    def __init__(
        self,
        subjects: List[Subject],
        rooms: List[Room],
        weeks: List[Week],
        fixed_sessions: Optional[List[ScheduledSession]] = None
    ):
        self.subjects = subjects
        self.rooms = rooms
        self.weeks = weeks
        self.fixed_sessions = fixed_sessions or []
        self.constraints = SchedulingConstraints()
    
    def generate_schedule(
        self,
        max_attempts: int = 1000,
        randomize: bool = True
    ) -> Optional[Schedule]:
        """
        Generate a valid schedule using iterative placement.
        
        Args:
            max_attempts: Maximum number of attempts to place all subjects
            randomize: Whether to randomize placement order
        
        Returns:
            A valid Schedule if successful, None otherwise
        """
        schedule = Schedule()
        
        # Add all fixed sessions first
        for fixed_session in self.fixed_sessions:
            schedule.add_session(fixed_session)
        
        # Create list of subjects to schedule (accounting for sessions per week)
        subjects_to_schedule = []
        for subject in self.subjects:
            # Check if already in fixed sessions
            fixed_count = sum(
                1 for fs in self.fixed_sessions 
                if fs.subject == subject
            )
            remaining = subject.sessions_per_week - fixed_count
            for _ in range(remaining):
                subjects_to_schedule.append(subject)
        
        # Try to schedule all subjects
        for attempt in range(max_attempts):
            if randomize:
                random.shuffle(subjects_to_schedule)
            
            test_schedule = Schedule(sessions=schedule.sessions.copy())
            success = self._place_subjects(test_schedule, subjects_to_schedule)
            
            if success:
                return test_schedule
        
        # Return partial schedule if full schedule couldn't be generated
        return schedule if schedule.sessions else None
    
    def _place_subjects(
        self,
        schedule: Schedule,
        subjects: List[Subject]
    ) -> bool:
        """
        Recursively place subjects into the schedule.
        
        Returns True if all subjects were successfully placed.
        """
        if not subjects:
            return True
        
        subject = subjects[0]
        remaining_subjects = subjects[1:]
        
        # Try all possible placements
        possible_placements = self._get_possible_placements(schedule, subject)
        
        for session in possible_placements:
            if schedule.add_session(session):
                if self._place_subjects(schedule, remaining_subjects):
                    return True
                schedule.remove_session(session)
        
        return False
    
    def _get_possible_placements(
        self,
        schedule: Schedule,
        subject: Subject
    ) -> List[ScheduledSession]:
        """
        Get all possible valid placements for a subject.
        """
        placements = []
        
        for week in self.weeks:
            for block in week.blocks:
                for time_slot in block.time_slots:
                    # Check lecturer availability
                    if not self.constraints.check_lecturer_availability(subject, time_slot):
                        continue
                    
                    # Check preferred days
                    if not self.constraints.check_preferred_days(subject, time_slot):
                        continue
                    
                    # Try each room
                    for room in self.rooms:
                        # Check room constraints
                        if not self.constraints.check_room_capacity(subject, room):
                            continue
                        if not self.constraints.check_room_features(subject, room):
                            continue
                        
                        # Create potential session
                        session = ScheduledSession(
                            subject=subject,
                            time_slot=time_slot,
                            room=room,
                            week=week,
                            is_fixed=False
                        )
                        
                        # Check for conflicts
                        if self.constraints.check_no_conflicts(schedule, session):
                            placements.append(session)
        
        return placements
    
    def optimize_schedule(self, schedule: Schedule) -> Schedule:
        """
        Attempt to optimize an existing schedule by rearranging non-fixed sessions.
        This could minimize gaps, balance lecturer workload, etc.
        """
        # Simple optimization: try to cluster sessions by day
        optimized = Schedule()
        
        # Keep fixed sessions
        fixed = [s for s in schedule.sessions if s.is_fixed]
        for session in fixed:
            optimized.add_session(session)
        
        # Re-schedule non-fixed sessions
        non_fixed = [s for s in schedule.sessions if not s.is_fixed]
        subjects_to_reschedule = [s.subject for s in non_fixed]
        
        # Try to place them in a more optimal way
        self._place_subjects(optimized, subjects_to_reschedule)
        
        return optimized


class SchedulingHelper:
    """Helper functions for scheduling operations."""
    
    @staticmethod
    def create_standard_time_slots(
        start_hour: int = 8,
        end_hour: int = 18,
        slot_duration: int = 60,
        days: Optional[List[DayOfWeek]] = None
    ) -> List[TimeSlot]:
        """
        Create a standard set of time slots for scheduling.
        
        Args:
            start_hour: Starting hour (default 8 AM)
            end_hour: Ending hour (default 6 PM)
            slot_duration: Duration of each slot in minutes (default 60)
            days: Days to create slots for (default Monday-Friday)
        
        Returns:
            List of TimeSlot objects
        """
        if days is None:
            days = [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
                   DayOfWeek.THURSDAY, DayOfWeek.FRIDAY]
        
        slots = []
        for day in days:
            hour = start_hour
            while hour < end_hour:
                slots.append(TimeSlot(
                    day=day,
                    start_hour=hour,
                    start_minute=0,
                    duration_minutes=slot_duration
                ))
                hour += slot_duration // 60
        
        return slots
    
    @staticmethod
    def create_blocks_from_slots(
        time_slots: List[TimeSlot],
        block_definitions: Dict[str, Tuple[int, int]]
    ) -> List[Block]:
        """
        Create blocks from time slots based on definitions.
        
        Args:
            time_slots: Available time slots
            block_definitions: Dict mapping block names to (start_hour, end_hour) tuples
        
        Returns:
            List of Block objects
        """
        blocks = []
        for block_name, (start_hour, end_hour) in block_definitions.items():
            block_slots = [
                slot for slot in time_slots
                if start_hour <= slot.start_hour < end_hour
            ]
            if block_slots:
                blocks.append(Block(
                    id=block_name.lower().replace(' ', '_'),
                    name=block_name,
                    time_slots=block_slots
                ))
        return blocks
    
    @staticmethod
    def get_schedule_statistics(schedule: Schedule) -> Dict[str, any]:
        """Get statistics about a schedule."""
        if not schedule.sessions:
            return {
                'total_sessions': 0,
                'rooms_used': 0,
                'lecturers_used': 0,
                'weeks_used': 0
            }
        
        rooms = set(s.room for s in schedule.sessions)
        lecturers = set()
        for session in schedule.sessions:
            lecturers.update(session.subject.required_lecturers)
        weeks = set(s.week for s in schedule.sessions)
        
        return {
            'total_sessions': len(schedule.sessions),
            'rooms_used': len(rooms),
            'lecturers_used': len(lecturers),
            'weeks_used': len(weeks),
            'is_valid': schedule.is_valid()
        }
