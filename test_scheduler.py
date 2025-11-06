"""
Unit tests for the timetable scheduler.
"""

import unittest
from models import (
    Room, Lecturer, Subject, TimeSlot, Block, 
    Availability, ScheduleEntry, Timetable
)
from scheduler import TimetableScheduler, SchedulerConstraints
from data_manager import DataManager


class TestModels(unittest.TestCase):
    """Test data models."""
    
    def test_room_creation(self):
        """Test room creation and properties."""
        room = Room(id="R1", name="Room 101", capacity=30)
        self.assertEqual(room.id, "R1")
        self.assertEqual(room.name, "Room 101")
        self.assertEqual(room.capacity, 30)
    
    def test_lecturer_creation(self):
        """Test lecturer creation."""
        lecturer = Lecturer(id="L1", name="Dr. Smith")
        self.assertEqual(lecturer.id, "L1")
        self.assertEqual(lecturer.name, "Dr. Smith")
    
    def test_subject_creation(self):
        """Test subject creation."""
        lecturer = Lecturer(id="L1", name="Dr. Smith")
        subject = Subject(
            id="S1",
            name="Anatomy",
            lecturer=lecturer,
            required_hours=4,
            min_students=20,
            max_students=30
        )
        self.assertEqual(subject.id, "S1")
        self.assertEqual(subject.name, "Anatomy")
        self.assertEqual(subject.lecturer.name, "Dr. Smith")
    
    def test_time_slot_creation(self):
        """Test time slot creation."""
        time_slot = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        self.assertEqual(time_slot.day, "Monday")
        self.assertEqual(time_slot.start_time, "09:00")
    
    def test_block_creation(self):
        """Test block creation."""
        time_slot = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        block = Block(id="B1", time_slot=time_slot, duration_hours=1)
        self.assertEqual(block.id, "B1")
        self.assertEqual(block.duration_hours, 1)
    
    def test_availability(self):
        """Test availability checking."""
        time_slot1 = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        time_slot2 = TimeSlot(day="Tuesday", start_time="09:00", end_time="10:00")
        
        availability = Availability(
            entity_id="L1",
            entity_type="lecturer",
            available_slots={time_slot1}
        )
        
        self.assertTrue(availability.is_available(time_slot1))
        self.assertFalse(availability.is_available(time_slot2))


class TestTimetable(unittest.TestCase):
    """Test timetable functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.lecturer = Lecturer(id="L1", name="Dr. Smith")
        self.room = Room(id="R1", name="Room 101", capacity=30)
        self.subject = Subject(
            id="S1",
            name="Anatomy",
            lecturer=self.lecturer,
            required_hours=2,
            min_students=20,
            max_students=30
        )
        self.time_slot = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        self.block = Block(id="B1", time_slot=self.time_slot, duration_hours=1)
    
    def test_timetable_add_entry(self):
        """Test adding entries to timetable."""
        timetable = Timetable(weeks=1)
        entry = ScheduleEntry(
            subject=self.subject,
            room=self.room,
            block=self.block,
            week=1
        )
        
        self.assertTrue(timetable.add_entry(entry))
        self.assertEqual(len(timetable.entries), 1)
    
    def test_timetable_conflict_detection_room(self):
        """Test room conflict detection."""
        timetable = Timetable(weeks=1)
        
        # Add first entry
        entry1 = ScheduleEntry(
            subject=self.subject,
            room=self.room,
            block=self.block,
            week=1
        )
        timetable.add_entry(entry1)
        
        # Try to add conflicting entry (same room, same time)
        subject2 = Subject(
            id="S2",
            name="Physiology",
            lecturer=Lecturer(id="L2", name="Dr. Jones"),
            required_hours=2,
            min_students=15,
            max_students=25
        )
        entry2 = ScheduleEntry(
            subject=subject2,
            room=self.room,  # Same room
            block=self.block,  # Same block
            week=1
        )
        
        self.assertFalse(timetable.add_entry(entry2))
        self.assertEqual(len(timetable.entries), 1)
    
    def test_timetable_conflict_detection_lecturer(self):
        """Test lecturer conflict detection."""
        timetable = Timetable(weeks=1)
        
        # Add first entry
        entry1 = ScheduleEntry(
            subject=self.subject,
            room=self.room,
            block=self.block,
            week=1
        )
        timetable.add_entry(entry1)
        
        # Try to add conflicting entry (same lecturer, same time, different room)
        subject2 = Subject(
            id="S2",
            name="Physiology",
            lecturer=self.lecturer,  # Same lecturer
            required_hours=2,
            min_students=15,
            max_students=25
        )
        room2 = Room(id="R2", name="Room 102", capacity=40)
        entry2 = ScheduleEntry(
            subject=subject2,
            room=room2,  # Different room
            block=self.block,  # Same block
            week=1
        )
        
        self.assertFalse(timetable.add_entry(entry2))
        self.assertEqual(len(timetable.entries), 1)
    
    def test_get_entries_by_week(self):
        """Test filtering entries by week."""
        timetable = Timetable(weeks=2)
        
        entry1 = ScheduleEntry(
            subject=self.subject,
            room=self.room,
            block=self.block,
            week=1
        )
        timetable.add_entry(entry1)
        
        time_slot2 = TimeSlot(day="Tuesday", start_time="09:00", end_time="10:00")
        block2 = Block(id="B2", time_slot=time_slot2, duration_hours=1)
        entry2 = ScheduleEntry(
            subject=self.subject,
            room=self.room,
            block=block2,
            week=2
        )
        timetable.add_entry(entry2)
        
        week1_entries = timetable.get_entries_by_week(1)
        week2_entries = timetable.get_entries_by_week(2)
        
        self.assertEqual(len(week1_entries), 1)
        self.assertEqual(len(week2_entries), 1)


class TestScheduler(unittest.TestCase):
    """Test scheduling functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.lecturer1 = Lecturer(id="L1", name="Dr. Smith")
        self.lecturer2 = Lecturer(id="L2", name="Dr. Jones")
        
        self.room1 = Room(id="R1", name="Room 101", capacity=30)
        self.room2 = Room(id="R2", name="Room 102", capacity=40)
        
        self.subject1 = Subject(
            id="S1",
            name="Anatomy",
            lecturer=self.lecturer1,
            required_hours=2,
            min_students=20,
            max_students=30
        )
        
        self.subject2 = Subject(
            id="S2",
            name="Physiology",
            lecturer=self.lecturer2,
            required_hours=2,
            min_students=15,
            max_students=35
        )
        
        self.time_slot1 = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        self.time_slot2 = TimeSlot(day="Monday", start_time="10:00", end_time="11:00")
        self.time_slot3 = TimeSlot(day="Tuesday", start_time="09:00", end_time="10:00")
        
        self.block1 = Block(id="B1", time_slot=self.time_slot1, duration_hours=1)
        self.block2 = Block(id="B2", time_slot=self.time_slot2, duration_hours=1)
        self.block3 = Block(id="B3", time_slot=self.time_slot3, duration_hours=1)
        
        self.blocks = [self.block1, self.block2, self.block3]
        self.rooms = [self.room1, self.room2]
        self.subjects = [self.subject1, self.subject2]
    
    def test_room_capacity_validation(self):
        """Test room capacity constraint validation."""
        constraints = SchedulerConstraints()
        
        # Subject requires min 20 students, room has 30 capacity - should pass
        self.assertTrue(constraints.validate_room_capacity(self.subject1, self.room1))
        
        # Subject requires min 20 students, create room with 15 capacity - should fail
        small_room = Room(id="R3", name="Small Room", capacity=15)
        self.assertFalse(constraints.validate_room_capacity(self.subject1, small_room))
    
    def test_scheduler_generates_timetable(self):
        """Test that scheduler generates a timetable."""
        constraints = SchedulerConstraints()
        scheduler = TimetableScheduler(constraints)
        
        timetable = scheduler.generate_timetable(
            subjects=self.subjects,
            rooms=self.rooms,
            blocks=self.blocks,
            weeks=1
        )
        
        self.assertIsNotNone(timetable)
        self.assertGreater(len(timetable.entries), 0)
    
    def test_manual_entry_addition(self):
        """Test manual entry addition to timetable."""
        constraints = SchedulerConstraints()
        scheduler = TimetableScheduler(constraints)
        
        timetable = Timetable(weeks=1)
        
        success, message = scheduler.add_manual_entry(
            timetable=timetable,
            subject=self.subject1,
            room=self.room1,
            block=self.block1,
            week=1
        )
        
        self.assertTrue(success)
        self.assertEqual(len(timetable.entries), 1)


class TestDataManager(unittest.TestCase):
    """Test data management functionality."""
    
    def test_load_from_json(self):
        """Test loading data from JSON."""
        data = {
            "lecturers": [
                {"id": "L1", "name": "Dr. Smith"}
            ],
            "rooms": [
                {"id": "R1", "name": "Room 101", "capacity": 30}
            ],
            "subjects": [
                {
                    "id": "S1",
                    "name": "Anatomy",
                    "lecturer_id": "L1",
                    "required_hours": 4,
                    "min_students": 20,
                    "max_students": 30
                }
            ],
            "blocks": [
                {
                    "id": "B1",
                    "day": "Monday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "duration_hours": 1
                }
            ]
        }
        
        manager = DataManager()
        manager.load_from_json(data)
        
        self.assertEqual(len(manager.get_all_lecturers()), 1)
        self.assertEqual(len(manager.get_all_rooms()), 1)
        self.assertEqual(len(manager.get_all_subjects()), 1)
        self.assertEqual(len(manager.get_all_blocks()), 1)


if __name__ == '__main__':
    unittest.main()
