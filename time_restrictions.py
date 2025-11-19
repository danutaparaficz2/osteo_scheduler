"""
Helper utilities for managing lecturer time restrictions.
Provides convenient methods to define when lecturers are available.
"""

from typing import List, Set, Union
from datetime import date, datetime
from models import Availability, DateTimeRestriction, TimeOfDay, Lecturer


class LecturerTimeRestrictionBuilder:
    """
    Builder class to easily create time restrictions for lecturers.
    
    Example usage:
        builder = LecturerTimeRestrictionBuilder(lecturer_id="L1")
        
        # Add specific available dates with time of day
        builder.add_available_date("2025-01-15", morning=True, afternoon=False)
        builder.add_available_date("2025-01-16", morning=True, afternoon=True)
        
        # Add a range of dates
        builder.add_available_date_range("2025-01-20", "2025-01-25", morning=True, afternoon=True)
        
        # Add unavailable dates
        builder.add_unavailable_date("2025-01-22")
        
        # Build the availability object
        availability = builder.build()
    """
    
    def __init__(self, lecturer_id: str):
        """
        Initialize the builder for a specific lecturer.
        
        Args:
            lecturer_id: The ID of the lecturer
        """
        self.lecturer_id = lecturer_id
        self.available_dates: Set[date] = set()
        self.unavailable_dates: Set[date] = set()
        self.date_time_map: dict[date, Set[TimeOfDay]] = {}
        self.default_morning = True
        self.default_afternoon = True
    
    def add_available_date(
        self, 
        date_str: Union[str, date], 
        morning: bool = True, 
        afternoon: bool = True
    ) -> 'LecturerTimeRestrictionBuilder':
        """
        Add a specific date when the lecturer is available.
        
        Args:
            date_str: Date in YYYY-MM-DD format or date object
            morning: Whether available in the morning (8:00-12:00)
            afternoon: Whether available in the afternoon (12:00-18:00)
            
        Returns:
            Self for method chaining
        """
        if isinstance(date_str, str):
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            target_date = date_str
        
        self.available_dates.add(target_date)
        
        # Set time of day availability
        time_of_day_set = set()
        if morning:
            time_of_day_set.add(TimeOfDay.MORNING)
        if afternoon:
            time_of_day_set.add(TimeOfDay.AFTERNOON)
        
        if time_of_day_set:
            self.date_time_map[target_date] = time_of_day_set
        
        return self
    
    def add_available_date_range(
        self,
        start_date_str: Union[str, date],
        end_date_str: Union[str, date],
        morning: bool = True,
        afternoon: bool = True
    ) -> 'LecturerTimeRestrictionBuilder':
        """
        Add a range of dates when the lecturer is available.
        
        Args:
            start_date_str: Start date in YYYY-MM-DD format or date object
            end_date_str: End date in YYYY-MM-DD format or date object (inclusive)
            morning: Whether available in the morning
            afternoon: Whether available in the afternoon
            
        Returns:
            Self for method chaining
        """
        if isinstance(start_date_str, str):
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = start_date_str
        
        if isinstance(end_date_str, str):
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            end_date = end_date_str
        
        from datetime import timedelta
        current_date = start_date
        while current_date <= end_date:
            self.add_available_date(current_date, morning=morning, afternoon=afternoon)
            current_date += timedelta(days=1)
        
        return self
    
    def add_unavailable_date(self, date_str: Union[str, date]) -> 'LecturerTimeRestrictionBuilder':
        """
        Add a specific date when the lecturer is NOT available.
        
        Args:
            date_str: Date in YYYY-MM-DD format or date object
            
        Returns:
            Self for method chaining
        """
        if isinstance(date_str, str):
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            target_date = date_str
        
        self.unavailable_dates.add(target_date)
        
        # Remove from available dates if it was there
        if target_date in self.available_dates:
            self.available_dates.remove(target_date)
        if target_date in self.date_time_map:
            del self.date_time_map[target_date]
        
        return self
    
    def add_unavailable_date_range(
        self,
        start_date_str: Union[str, date],
        end_date_str: Union[str, date]
    ) -> 'LecturerTimeRestrictionBuilder':
        """
        Add a range of dates when the lecturer is NOT available.
        
        Args:
            start_date_str: Start date in YYYY-MM-DD format or date object
            end_date_str: End date in YYYY-MM-DD format or date object (inclusive)
            
        Returns:
            Self for method chaining
        """
        if isinstance(start_date_str, str):
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = start_date_str
        
        if isinstance(end_date_str, str):
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            end_date = end_date_str
        
        from datetime import timedelta
        current_date = start_date
        while current_date <= end_date:
            self.add_unavailable_date(current_date)
            current_date += timedelta(days=1)
        
        return self
    
    def set_default_availability(
        self, 
        morning: bool = True, 
        afternoon: bool = True
    ) -> 'LecturerTimeRestrictionBuilder':
        """
        Set the default time of day availability for dates not explicitly specified.
        
        Args:
            morning: Default morning availability
            afternoon: Default afternoon availability
            
        Returns:
            Self for method chaining
        """
        self.default_morning = morning
        self.default_afternoon = afternoon
        return self
    
    def build(self) -> Availability:
        """
        Build and return the Availability object with all configured restrictions.
        
        Returns:
            Availability object ready to use in constraints
        """
        # Build default time of day set
        default_time_of_day = set()
        if self.default_morning:
            default_time_of_day.add(TimeOfDay.MORNING)
        if self.default_afternoon:
            default_time_of_day.add(TimeOfDay.AFTERNOON)
        
        # Create the restriction object
        restriction = DateTimeRestriction(
            available_dates=self.available_dates,
            unavailable_dates=self.unavailable_dates,
            available_time_of_day=self.date_time_map,
            default_time_of_day=default_time_of_day
        )
        
        # Create and return the availability object
        return Availability(
            entity_id=self.lecturer_id,
            entity_type="lecturer",
            available_slots=set(),  # Empty set for date-based restrictions
            date_time_restrictions=restriction
        )


def create_lecturer_availability_from_list(
    lecturer_id: str,
    available_dates: List[dict]
) -> Availability:
    """
    Create lecturer availability from a list of date/time specifications.
    
    Args:
        lecturer_id: The ID of the lecturer
        available_dates: List of dictionaries with keys:
            - 'date': Date string in YYYY-MM-DD format
            - 'morning': Boolean (optional, default True)
            - 'afternoon': Boolean (optional, default True)
    
    Example:
        availability = create_lecturer_availability_from_list(
            lecturer_id="L1",
            available_dates=[
                {"date": "2025-01-15", "morning": True, "afternoon": False},
                {"date": "2025-01-16", "morning": True, "afternoon": True},
                {"date": "2025-01-17", "morning": False, "afternoon": True}
            ]
        )
    
    Returns:
        Availability object
    """
    builder = LecturerTimeRestrictionBuilder(lecturer_id)
    
    for date_spec in available_dates:
        date_str = date_spec.get('date')
        morning = date_spec.get('morning', True)
        afternoon = date_spec.get('afternoon', True)
        builder.add_available_date(date_str, morning=morning, afternoon=afternoon)
    
    return builder.build()


def create_lecturer_availability_from_ranges(
    lecturer_id: str,
    available_ranges: List[dict],
    unavailable_dates: List[str] = None
) -> Availability:
    """
    Create lecturer availability from date ranges.
    
    Args:
        lecturer_id: The ID of the lecturer
        available_ranges: List of dictionaries with keys:
            - 'start': Start date string in YYYY-MM-DD format
            - 'end': End date string in YYYY-MM-DD format
            - 'morning': Boolean (optional, default True)
            - 'afternoon': Boolean (optional, default True)
        unavailable_dates: List of specific unavailable dates in YYYY-MM-DD format
    
    Example:
        availability = create_lecturer_availability_from_ranges(
            lecturer_id="L1",
            available_ranges=[
                {"start": "2025-01-15", "end": "2025-01-20", "morning": True, "afternoon": True},
                {"start": "2025-01-25", "end": "2025-01-31", "morning": True, "afternoon": False}
            ],
            unavailable_dates=["2025-01-18", "2025-01-27"]
        )
    
    Returns:
        Availability object
    """
    builder = LecturerTimeRestrictionBuilder(lecturer_id)
    
    for range_spec in available_ranges:
        start = range_spec.get('start')
        end = range_spec.get('end')
        morning = range_spec.get('morning', True)
        afternoon = range_spec.get('afternoon', True)
        builder.add_available_date_range(start, end, morning=morning, afternoon=afternoon)
    
    if unavailable_dates:
        for date_str in unavailable_dates:
            builder.add_unavailable_date(date_str)
    
    return builder.build()
