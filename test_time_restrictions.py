"""
Test suite for lecturer time restrictions functionality.
"""

import unittest
from datetime import date, datetime
from models import Lecturer, TimeOfDay, DateTimeRestriction, Availability, TimeSlot
from time_restrictions import (
    LecturerTimeRestrictionBuilder,
    create_lecturer_availability_from_list,
    create_lecturer_availability_from_ranges
)


class TestTimeOfDay(unittest.TestCase):
    """Test the TimeOfDay enum."""
    
    def test_from_time_string_morning(self):
        """Test morning time classification."""
        self.assertEqual(TimeOfDay.from_time_string("08:00"), TimeOfDay.MORNING)
        self.assertEqual(TimeOfDay.from_time_string("09:30"), TimeOfDay.MORNING)
        self.assertEqual(TimeOfDay.from_time_string("11:45"), TimeOfDay.MORNING)
    
    def test_from_time_string_afternoon(self):
        """Test afternoon time classification."""
        self.assertEqual(TimeOfDay.from_time_string("12:00"), TimeOfDay.AFTERNOON)
        self.assertEqual(TimeOfDay.from_time_string("14:30"), TimeOfDay.AFTERNOON)
        self.assertEqual(TimeOfDay.from_time_string("17:59"), TimeOfDay.AFTERNOON)
    
    def test_from_time_string_invalid(self):
        """Test invalid time classifications."""
        self.assertIsNone(TimeOfDay.from_time_string("07:00"))  # Too early
        self.assertIsNone(TimeOfDay.from_time_string("18:00"))  # Too late
        self.assertIsNone(TimeOfDay.from_time_string("invalid"))


class TestDateTimeRestriction(unittest.TestCase):
    """Test the DateTimeRestriction class."""
    
    def test_available_date(self):
        """Test checking available dates."""
        restriction = DateTimeRestriction(
            available_dates={date(2025, 1, 15), date(2025, 1, 16)}
        )
        
        self.assertTrue(restriction.is_available_on_date(date(2025, 1, 15)))
        self.assertTrue(restriction.is_available_on_date(date(2025, 1, 16)))
        self.assertFalse(restriction.is_available_on_date(date(2025, 1, 17)))
    
    def test_unavailable_date(self):
        """Test checking unavailable dates."""
        restriction = DateTimeRestriction(
            available_dates={date(2025, 1, 15), date(2025, 1, 16)},
            unavailable_dates={date(2025, 1, 15)}
        )
        
        self.assertFalse(restriction.is_available_on_date(date(2025, 1, 15)))
        self.assertTrue(restriction.is_available_on_date(date(2025, 1, 16)))
    
    def test_time_of_day_restriction(self):
        """Test time of day restrictions."""
        restriction = DateTimeRestriction(
            available_dates={date(2025, 1, 15)},
            available_time_of_day={
                date(2025, 1, 15): {TimeOfDay.MORNING}
            }
        )
        
        self.assertTrue(restriction.is_available_on_date(
            date(2025, 1, 15), TimeOfDay.MORNING
        ))
        self.assertFalse(restriction.is_available_on_date(
            date(2025, 1, 15), TimeOfDay.AFTERNOON
        ))


class TestLecturerTimeRestrictionBuilder(unittest.TestCase):
    """Test the LecturerTimeRestrictionBuilder class."""
    
    def test_add_single_date(self):
        """Test adding a single available date."""
        builder = LecturerTimeRestrictionBuilder("L1")
        builder.add_available_date("2025-01-15", morning=True, afternoon=False)
        availability = builder.build()
        
        self.assertIn(date(2025, 1, 15), 
                     availability.date_time_restrictions.available_dates)
    
    def test_add_date_range(self):
        """Test adding a date range."""
        builder = LecturerTimeRestrictionBuilder("L1")
        builder.add_available_date_range("2025-01-15", "2025-01-17")
        availability = builder.build()
        
        expected_dates = {date(2025, 1, 15), date(2025, 1, 16), date(2025, 1, 17)}
        self.assertEqual(
            availability.date_time_restrictions.available_dates,
            expected_dates
        )
    
    def test_add_unavailable_date(self):
        """Test adding unavailable dates."""
        builder = LecturerTimeRestrictionBuilder("L1")
        builder.add_available_date_range("2025-01-15", "2025-01-17")
        builder.add_unavailable_date("2025-01-16")
        availability = builder.build()
        
        self.assertNotIn(date(2025, 1, 16), 
                        availability.date_time_restrictions.available_dates)
        self.assertIn(date(2025, 1, 16), 
                     availability.date_time_restrictions.unavailable_dates)
    
    def test_time_of_day_settings(self):
        """Test time of day settings."""
        builder = LecturerTimeRestrictionBuilder("L1")
        builder.add_available_date("2025-01-15", morning=True, afternoon=False)
        availability = builder.build()
        
        time_of_day = availability.date_time_restrictions.available_time_of_day[
            date(2025, 1, 15)
        ]
        self.assertIn(TimeOfDay.MORNING, time_of_day)
        self.assertNotIn(TimeOfDay.AFTERNOON, time_of_day)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for creating availability."""
    
    def test_create_from_list(self):
        """Test creating availability from a list."""
        available_dates = [
            {"date": "2025-01-15", "morning": True, "afternoon": False},
            {"date": "2025-01-16", "morning": True, "afternoon": True}
        ]
        
        availability = create_lecturer_availability_from_list("L1", available_dates)
        
        self.assertEqual(availability.entity_id, "L1")
        self.assertEqual(len(availability.date_time_restrictions.available_dates), 2)
    
    def test_create_from_ranges(self):
        """Test creating availability from ranges."""
        available_ranges = [
            {"start": "2025-01-15", "end": "2025-01-17", "morning": True, "afternoon": True}
        ]
        unavailable_dates = ["2025-01-16"]
        
        availability = create_lecturer_availability_from_ranges(
            "L1", available_ranges, unavailable_dates
        )
        
        self.assertEqual(availability.entity_id, "L1")
        self.assertIn(date(2025, 1, 15), 
                     availability.date_time_restrictions.available_dates)
        self.assertIn(date(2025, 1, 16), 
                     availability.date_time_restrictions.unavailable_dates)


class TestAvailabilityIntegration(unittest.TestCase):
    """Test the integrated Availability class with date restrictions."""
    
    def test_is_available_with_date(self):
        """Test availability checking with dates."""
        restriction = DateTimeRestriction(
            available_dates={date(2025, 1, 15)},
            available_time_of_day={
                date(2025, 1, 15): {TimeOfDay.MORNING}
            }
        )
        
        availability = Availability(
            entity_id="L1",
            entity_type="lecturer",
            date_time_restrictions=restriction
        )
        
        time_slot = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        
        self.assertTrue(availability.is_available(time_slot, date(2025, 1, 15)))
        self.assertFalse(availability.is_available(time_slot, date(2025, 1, 16)))
    
    def test_is_available_afternoon_restriction(self):
        """Test afternoon time restrictions."""
        restriction = DateTimeRestriction(
            available_dates={date(2025, 1, 15)},
            available_time_of_day={
                date(2025, 1, 15): {TimeOfDay.AFTERNOON}
            }
        )
        
        availability = Availability(
            entity_id="L1",
            entity_type="lecturer",
            date_time_restrictions=restriction
        )
        
        morning_slot = TimeSlot(day="Monday", start_time="09:00", end_time="10:00")
        afternoon_slot = TimeSlot(day="Monday", start_time="14:00", end_time="15:00")
        
        self.assertFalse(availability.is_available(morning_slot, date(2025, 1, 15)))
        self.assertTrue(availability.is_available(afternoon_slot, date(2025, 1, 15)))


def run_tests():
    """Run all tests."""
    print("Running Time Restrictions Tests")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestTimeOfDay))
    suite.addTests(loader.loadTestsFromTestCase(TestDateTimeRestriction))
    suite.addTests(loader.loadTestsFromTestCase(TestLecturerTimeRestrictionBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestAvailabilityIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed")
    
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
