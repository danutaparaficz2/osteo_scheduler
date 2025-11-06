"""
PDF export functionality for timetables.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from models import Timetable, ScheduleEntry
from typing import List, Dict
from collections import defaultdict


class PDFExporter:
    """Exports timetables to PDF format."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=1  # Center alignment
        )
    
    def export_timetable(self, timetable: Timetable, filepath: str, title: str = "Timetable Schedule"):
        """
        Export a timetable to PDF format.
        
        Args:
            timetable: The timetable to export
            filepath: Path where the PDF should be saved
            title: Title for the PDF document
        """
        # Use landscape orientation for better table display
        doc = SimpleDocTemplate(filepath, pagesize=landscape(A4))
        story = []
        
        # Add title
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Generate timetable for each week
        for week in range(1, timetable.weeks + 1):
            week_entries = timetable.get_entries_by_week(week)
            
            if week_entries:
                # Add week header
                week_title = Paragraph(f"<b>Week {week}</b>", self.styles['Heading2'])
                story.append(week_title)
                story.append(Spacer(1, 0.1 * inch))
                
                # Create table for this week
                table_data = self._create_week_table(week_entries)
                table = Table(table_data, repeatRows=1)
                
                # Style the table
                table.setStyle(TableStyle([
                    # Header row
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING', (0, 0), (-1, 0), 12),
                    # Data rows
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                story.append(table)
                
                # Add page break between weeks (except for the last week)
                if week < timetable.weeks:
                    story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
    
    def _create_week_table(self, entries: List[ScheduleEntry]) -> List[List[str]]:
        """
        Create a table structure for a week's schedule.
        
        Returns a 2D list suitable for reportlab Table.
        """
        # Group entries by day and time
        schedule_grid: Dict[str, Dict[str, List[ScheduleEntry]]] = defaultdict(lambda: defaultdict(list))
        
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        time_slots = set()
        
        for entry in entries:
            day = entry.block.time_slot.day
            time_key = f"{entry.block.time_slot.start_time}-{entry.block.time_slot.end_time}"
            schedule_grid[day][time_key].append(entry)
            time_slots.add(time_key)
        
        # Sort time slots
        time_slots_sorted = sorted(list(time_slots))
        
        # Build table data
        table_data = []
        
        # Header row
        header = ['Time'] + [day for day in days_order if day in schedule_grid]
        table_data.append(header)
        
        # Data rows
        for time_slot in time_slots_sorted:
            row = [time_slot]
            for day in days_order:
                if day in schedule_grid:
                    entries_at_slot = schedule_grid[day].get(time_slot, [])
                    if entries_at_slot:
                        cell_content = '\n'.join([
                            f"{entry.subject.name}\n{entry.subject.lecturer.name}\nRoom: {entry.room.name}"
                            for entry in entries_at_slot
                        ])
                        row.append(cell_content)
                    else:
                        row.append('-')
            table_data.append(row)
        
        return table_data
    
    def export_by_lecturer(self, timetable: Timetable, filepath: str):
        """Export timetable organized by lecturer."""
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Add title
        story.append(Paragraph("Timetable by Lecturer", self.title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Group by lecturer
        lecturer_schedules: Dict[str, List[ScheduleEntry]] = defaultdict(list)
        for entry in timetable.entries:
            lecturer_schedules[entry.subject.lecturer.name].append(entry)
        
        # Create a section for each lecturer
        for lecturer_name in sorted(lecturer_schedules.keys()):
            story.append(Paragraph(f"<b>{lecturer_name}</b>", self.styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))
            
            entries = lecturer_schedules[lecturer_name]
            table_data = [['Subject', 'Day', 'Time', 'Room', 'Week']]
            
            for entry in sorted(entries, key=lambda e: (e.week, e.block.time_slot.day)):
                table_data.append([
                    entry.subject.name,
                    entry.block.time_slot.day,
                    f"{entry.block.time_slot.start_time}-{entry.block.time_slot.end_time}",
                    entry.room.name,
                    str(entry.week)
                ])
            
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 0.3 * inch))
        
        doc.build(story)
