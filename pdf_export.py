"""
PDF export functionality for the osteo_scheduler system.

This module provides utilities to export schedules to PDF format.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from typing import List, Dict
from models import Schedule, Week, Room, Lecturer, DayOfWeek, ScheduledSession
from datetime import datetime
import io


class PDFExporter:
    """Export schedules to PDF format."""
    
    def __init__(self, schedule: Schedule):
        self.schedule = schedule
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CenterTitle',
            parent=self.styles['Heading1'],
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading2'],
            alignment=TA_LEFT,
            spaceAfter=10
        ))
    
    def export_to_file(self, filename: str, view_type: str = 'weekly') -> str:
        """
        Export schedule to a PDF file.
        
        Args:
            filename: Output filename
            view_type: Type of view ('weekly', 'by_room', 'by_lecturer')
        
        Returns:
            The filename of the created PDF
        """
        doc = SimpleDocTemplate(
            filename,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=18
        )
        
        story = []
        
        # Add title
        title = Paragraph("Timetable Schedule", self.styles['CenterTitle'])
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # Add generation date
        date_text = Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles['Normal']
        )
        story.append(date_text)
        story.append(Spacer(1, 0.3*inch))
        
        # Generate content based on view type
        if view_type == 'weekly':
            story.extend(self._generate_weekly_view())
        elif view_type == 'by_room':
            story.extend(self._generate_room_view())
        elif view_type == 'by_lecturer':
            story.extend(self._generate_lecturer_view())
        else:
            story.extend(self._generate_weekly_view())
        
        # Build PDF
        doc.build(story)
        return filename
    
    def export_to_buffer(self, view_type: str = 'weekly') -> io.BytesIO:
        """
        Export schedule to a BytesIO buffer for web downloads.
        
        Args:
            view_type: Type of view ('weekly', 'by_room', 'by_lecturer')
        
        Returns:
            BytesIO buffer containing the PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=18
        )
        
        story = []
        
        # Add title
        title = Paragraph("Timetable Schedule", self.styles['CenterTitle'])
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # Generate content
        if view_type == 'weekly':
            story.extend(self._generate_weekly_view())
        elif view_type == 'by_room':
            story.extend(self._generate_room_view())
        elif view_type == 'by_lecturer':
            story.extend(self._generate_lecturer_view())
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _generate_weekly_view(self) -> List:
        """Generate weekly view of the schedule."""
        elements = []
        
        # Group sessions by week
        weeks = {}
        for session in self.schedule.sessions:
            week_key = (session.week.week_number, session.week.year)
            if week_key not in weeks:
                weeks[week_key] = []
            weeks[week_key].append(session)
        
        # Generate a table for each week
        for (week_num, year), sessions in sorted(weeks.items()):
            # Week title
            week_title = Paragraph(
                f"Week {week_num}, {year}",
                self.styles['SubTitle']
            )
            elements.append(week_title)
            elements.append(Spacer(1, 0.1*inch))
            
            # Create table data
            table_data = self._create_weekly_table_data(sessions)
            
            # Create table
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(table)
            elements.append(PageBreak())
        
        return elements
    
    def _create_weekly_table_data(self, sessions: List[ScheduledSession]) -> List[List[str]]:
        """Create table data for weekly view."""
        # Header row
        days = ['Time'] + [day.name[:3] for day in DayOfWeek if day.value < 7]
        data = [days]
        
        # Get unique time slots
        time_slots = {}
        for session in sessions:
            time_key = (session.time_slot.start_hour, session.time_slot.start_minute)
            if time_key not in time_slots:
                time_slots[time_key] = {}
            day = session.time_slot.day
            if day not in time_slots[time_key]:
                time_slots[time_key][day] = []
            time_slots[time_key][day].append(session)
        
        # Create rows for each time slot
        for (hour, minute) in sorted(time_slots.keys()):
            row = [f"{hour:02d}:{minute:02d}"]
            for day in DayOfWeek:
                if day.value >= 7:
                    continue
                if day in time_slots[(hour, minute)]:
                    sessions_at_time = time_slots[(hour, minute)][day]
                    cell_text = "\n".join([
                        f"{s.subject.name}\n{s.room.name}\n({', '.join(l.name for l in s.subject.required_lecturers)})"
                        for s in sessions_at_time
                    ])
                    row.append(cell_text)
                else:
                    row.append("")
            data.append(row)
        
        return data if len(data) > 1 else [days, ["No sessions scheduled"]]
    
    def _generate_room_view(self) -> List:
        """Generate room-based view of the schedule."""
        elements = []
        
        # Group sessions by room
        rooms = {}
        for session in self.schedule.sessions:
            room_id = session.room.id
            if room_id not in rooms:
                rooms[room_id] = {'room': session.room, 'sessions': []}
            rooms[room_id]['sessions'].append(session)
        
        # Generate a section for each room
        for room_id, room_data in sorted(rooms.items()):
            room = room_data['room']
            sessions = sorted(room_data['sessions'], 
                            key=lambda s: (s.week.week_number, s.time_slot.day.value, 
                                         s.time_slot.start_hour, s.time_slot.start_minute))
            
            # Room title
            room_title = Paragraph(
                f"Room: {room.name} (Capacity: {room.capacity})",
                self.styles['SubTitle']
            )
            elements.append(room_title)
            elements.append(Spacer(1, 0.1*inch))
            
            # Create table
            table_data = [['Week', 'Day', 'Time', 'Subject', 'Lecturers']]
            for session in sessions:
                table_data.append([
                    f"Week {session.week.week_number}",
                    session.time_slot.day.name,
                    f"{session.time_slot.start_hour:02d}:{session.time_slot.start_minute:02d}",
                    session.subject.name,
                    ', '.join(l.name for l in session.subject.required_lecturers)
                ])
            
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _generate_lecturer_view(self) -> List:
        """Generate lecturer-based view of the schedule."""
        elements = []
        
        # Group sessions by lecturer
        lecturers = {}
        for session in self.schedule.sessions:
            for lecturer in session.subject.required_lecturers:
                if lecturer.id not in lecturers:
                    lecturers[lecturer.id] = {'lecturer': lecturer, 'sessions': []}
                lecturers[lecturer.id]['sessions'].append(session)
        
        # Generate a section for each lecturer
        for lecturer_id, lecturer_data in sorted(lecturers.items()):
            lecturer = lecturer_data['lecturer']
            sessions = sorted(lecturer_data['sessions'],
                            key=lambda s: (s.week.week_number, s.time_slot.day.value,
                                         s.time_slot.start_hour, s.time_slot.start_minute))
            
            # Lecturer title
            lecturer_title = Paragraph(
                f"Lecturer: {lecturer.name}",
                self.styles['SubTitle']
            )
            elements.append(lecturer_title)
            elements.append(Spacer(1, 0.1*inch))
            
            # Create table
            table_data = [['Week', 'Day', 'Time', 'Subject', 'Room']]
            for session in sessions:
                table_data.append([
                    f"Week {session.week.week_number}",
                    session.time_slot.day.name,
                    f"{session.time_slot.start_hour:02d}:{session.time_slot.start_minute:02d}",
                    session.subject.name,
                    session.room.name
                ])
            
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
        
        return elements
