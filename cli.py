#!/usr/bin/env python
"""
Command-line interface for the timetable scheduler.
Allows generating schedules and exporting without running the web server.
"""

import sys
import argparse
from data_manager import DataManager, export_timetable_to_json
from scheduler import TimetableScheduler, SchedulerConstraints
from pdf_exporter import PDFExporter


def main():
    parser = argparse.ArgumentParser(description='Timetable Scheduler CLI')
    parser.add_argument('input_file', help='Input JSON file with data')
    parser.add_argument('--weeks', type=int, default=1, help='Number of weeks to schedule (default: 1)')
    parser.add_argument('--output-json', help='Output JSON file for the generated timetable')
    parser.add_argument('--output-pdf', help='Output PDF file for the generated timetable')
    parser.add_argument('--pdf-by-lecturer', action='store_true', help='Organize PDF by lecturer')
    
    args = parser.parse_args()
    
    # Load data
    print(f"Loading data from {args.input_file}...")
    data_manager = DataManager()
    try:
        data_manager.load_from_file(args.input_file)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)
    
    print(f"Loaded:")
    print(f"  - {len(data_manager.get_all_lecturers())} lecturers")
    print(f"  - {len(data_manager.get_all_rooms())} rooms")
    print(f"  - {len(data_manager.get_all_subjects())} subjects")
    print(f"  - {len(data_manager.get_all_blocks())} time blocks")
    
    # Generate timetable
    print(f"\nGenerating timetable for {args.weeks} week(s)...")
    constraints = SchedulerConstraints()
    scheduler = TimetableScheduler(constraints)
    
    timetable = scheduler.generate_timetable(
        subjects=data_manager.get_all_subjects(),
        rooms=data_manager.get_all_rooms(),
        blocks=data_manager.get_all_blocks(),
        weeks=args.weeks
    )
    
    print(f"Generated {len(timetable.entries)} schedule entries")
    
    # Export to JSON
    if args.output_json:
        print(f"\nExporting to JSON: {args.output_json}...")
        export_timetable_to_json(timetable, args.output_json)
        print("JSON export complete")
    
    # Export to PDF
    if args.output_pdf:
        print(f"\nExporting to PDF: {args.output_pdf}...")
        exporter = PDFExporter()
        if args.pdf_by_lecturer:
            exporter.export_by_lecturer(timetable, args.output_pdf)
        else:
            exporter.export_timetable(timetable, args.output_pdf)
        print("PDF export complete")
    
    # Display summary
    print("\n=== Schedule Summary ===")
    for week in range(1, args.weeks + 1):
        week_entries = timetable.get_entries_by_week(week)
        print(f"\nWeek {week}: {len(week_entries)} entries")
        
        # Group by day
        days = {}
        for entry in week_entries:
            day = entry.block.time_slot.day
            if day not in days:
                days[day] = []
            days[day].append(entry)
        
        for day in sorted(days.keys()):
            print(f"  {day}: {len(days[day])} classes")


if __name__ == '__main__':
    main()
