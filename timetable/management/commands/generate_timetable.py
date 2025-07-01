from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from datetime import datetime
import random
from collections import defaultdict, Counter

from timetable.models import (
    SchoolProfile, Class, Subject, Teacher, TeacherSubjectAssignment, TimeTableSlot
)


class Command(BaseCommand):
    help = 'Generate automated timetable for a school'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-id',
            type=int,
            help='School ID to generate timetable for'
        )
        parser.add_argument(
            '--academic-year',
            type=str,
            default='',
            help='Academic year for the timetable'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            default=True,
            help='Clear existing timetable slots before generating new ones'
        )
        parser.add_argument(
            '--max-attempts',
            type=int,
            default=100,
            help='Maximum attempts for conflict resolution'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )

    def handle(self, *args, **options):
        school_id = options['school_id']
        academic_year = options['academic_year']
        clear_existing = options['clear_existing']
        max_attempts = options['max_attempts']
        verbose = options['verbose']

        try:
            if school_id:
                school = SchoolProfile.objects.get(id=school_id)
            else:
                # If no school specified, use the first available school
                school = SchoolProfile.objects.first()
                if not school:
                    raise CommandError("No schools found in the database")

            self.stdout.write(
                self.style.SUCCESS(f'Generating timetable for school: {school.school_name}')
            )

            # Generate timetable
            result = self.generate_timetable(
                school, academic_year, clear_existing, max_attempts, verbose
            )

            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Timetable generated successfully! "
                        f"Created {result['slots_created']} slots. "
                        f"Attempts: {result['attempts']}"
                    )
                )
                
                if result['warnings']:
                    self.stdout.write(
                        self.style.WARNING("Warnings:")
                    )
                    for warning in result['warnings']:
                        self.stdout.write(f"  - {warning}")
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to generate timetable: {result['error']}")
                )

        except SchoolProfile.DoesNotExist:
            raise CommandError(f"School with ID {school_id} does not exist")
        except Exception as e:
            raise CommandError(f"Error generating timetable: {str(e)}")

    def generate_timetable(self, school, academic_year, clear_existing, max_attempts, verbose):
        """
        Generate timetable for a school
        """
        try:
            with transaction.atomic():
                # Clear existing timetable if requested
                if clear_existing:
                    TimeTableSlot.objects.filter(school=school, academic_year=academic_year).delete()
                    if verbose:
                        self.stdout.write("Cleared existing timetable slots")

                # Get all active classes for the school
                classes = Class.objects.filter(school=school, is_active=True)
                if not classes.exists():
                    return {
                        'success': False,
                        'error': 'No active classes found for the school'
                    }

                # Get all active subjects for the school
                subjects = Subject.objects.filter(school=school, is_active=True)
                if not subjects.exists():
                    return {
                        'success': False,
                        'error': 'No active subjects found for the school'
                    }

                # Get all active teachers for the school
                teachers = Teacher.objects.filter(school=school, is_active=True)
                if not teachers.exists():
                    return {
                        'success': False,
                        'error': 'No active teachers found for the school'
                    }

                # Get teacher-subject assignments
                teacher_assignments = TeacherSubjectAssignment.objects.filter(
                    teacher__school=school,
                    subject__school=school
                ).select_related('teacher', 'subject')

                if not teacher_assignments.exists():
                    return {
                        'success': False,
                        'error': 'No teacher-subject assignments found'
                    }

                # Create teacher-subject mapping
                teacher_subject_map = defaultdict(list)
                for assignment in teacher_assignments:
                    teacher_subject_map[assignment.subject.id].append(assignment.teacher)

                # Get school configuration
                total_periods_per_day = school.total_periods_per_day
                working_days = school.working_days or ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

                if verbose:
                    self.stdout.write(f"Working days: {working_days}")
                    self.stdout.write(f"Periods per day: {total_periods_per_day}")

                # Initialize tracking variables
                teacher_schedule = defaultdict(set)  # teacher -> set of (day, period)
                teacher_weekly_periods = Counter()  # teacher -> periods count
                class_subject_periods = defaultdict(Counter)  # class -> subject -> periods count
                slots_created = 0
                warnings = []

                # Generate timetable
                for attempt in range(max_attempts):
                    try:
                        # Reset tracking for this attempt
                        teacher_schedule.clear()
                        teacher_weekly_periods.clear()
                        class_subject_periods.clear()
                        
                        # Clear any slots created in previous attempt
                        TimeTableSlot.objects.filter(school=school, academic_year=academic_year).delete()

                        # Generate timetable for each class
                        for class_obj in classes:
                            class_subjects = list(class_obj.subjects.filter(is_active=True))
                            
                            if not class_subjects:
                                warnings.append(f"Class {class_obj.class_name}-{class_obj.section} has no subjects assigned")
                                continue

                            # Calculate periods per subject (distribute evenly)
                            total_class_periods = len(working_days) * total_periods_per_day
                            periods_per_subject = total_class_periods // len(class_subjects)
                            extra_periods = total_class_periods % len(class_subjects)

                            # Assign periods to subjects
                            subject_periods = {}
                            for i, subject in enumerate(class_subjects):
                                periods = periods_per_subject + (1 if i < extra_periods else 0)
                                subject_periods[subject] = periods

                            # Generate slots for each day and period
                            for day in working_days:
                                for period in range(1, total_periods_per_day + 1):
                                    # Find available subject for this slot
                                    available_subjects = [
                                        subject for subject in class_subjects
                                        if class_subject_periods[class_obj.id][subject.id] < subject_periods[subject]
                                    ]

                                    if not available_subjects:
                                        continue

                                    # Try to assign a subject and teacher
                                    slot_created = False
                                    for _ in range(10):  # Try up to 10 times for this slot
                                        subject = random.choice(available_subjects)
                                        
                                        # Find available teachers for this subject
                                        available_teachers = [
                                            teacher for teacher in teacher_subject_map[subject.id]
                                            if (teacher.id, day, period) not in teacher_schedule[teacher.id]
                                            and teacher_weekly_periods[teacher.id] < 25  # Max 25 periods per week
                                        ]

                                        if available_teachers:
                                            teacher = random.choice(available_teachers)
                                            
                                            # Create the slot
                                            TimeTableSlot.objects.create(
                                                school=school,
                                                class_obj=class_obj,
                                                subject=subject,
                                                teacher=teacher,
                                                day=day,
                                                period_number=period,
                                                academic_year=academic_year,
                                                is_active=True
                                            )

                                            # Update tracking
                                            teacher_schedule[teacher.id].add((teacher.id, day, period))
                                            teacher_weekly_periods[teacher.id] += 1
                                            class_subject_periods[class_obj.id][subject.id] += 1
                                            slots_created += 1
                                            slot_created = True
                                            break

                                    if not slot_created:
                                        # Could not assign this slot, will retry in next attempt
                                        raise ValueError(f"Could not assign slot for {class_obj.class_name}-{class_obj.section} on {day} period {period}")

                        # If we reach here, timetable generation was successful
                        break

                    except ValueError as e:
                        if verbose:
                            self.stdout.write(f"Attempt {attempt + 1} failed: {str(e)}")
                        if attempt == max_attempts - 1:
                            return {
                                'success': False,
                                'error': f'Failed to generate timetable after {max_attempts} attempts: {str(e)}',
                                'attempts': attempt + 1
                            }
                        continue

                # Check for any remaining issues
                for class_obj in classes:
                    class_slots = TimeTableSlot.objects.filter(
                        school=school, 
                        class_obj=class_obj, 
                        academic_year=academic_year
                    ).count()
                    expected_slots = len(working_days) * total_periods_per_day
                    
                    if class_slots < expected_slots:
                        warnings.append(
                            f"Class {class_obj.class_name}-{class_obj.section}: "
                            f"Only {class_slots}/{expected_slots} slots created"
                        )

                # Check teacher workload
                for teacher in teachers:
                    teacher_slots = TimeTableSlot.objects.filter(
                        school=school, 
                        teacher=teacher, 
                        academic_year=academic_year
                    ).count()
                    
                    if teacher_slots > 25:
                        warnings.append(
                            f"Teacher {teacher.name}: {teacher_slots} periods assigned (over recommended limit)"
                        )

                return {
                    'success': True,
                    'slots_created': slots_created,
                    'attempts': attempt + 1,
                    'warnings': warnings
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Database error: {str(e)}',
                'attempts': 0
            } 