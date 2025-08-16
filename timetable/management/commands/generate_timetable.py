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
        Generate timetable for a school with improved teacher workload distribution
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

                # Ensure core subjects exist (auto-create if missing) and are active
                core_subject_names = [
                    'English', 'Urdu', 'Mathematics', 'Computer', 'Computer Science', 'General Knowledge',
                    'Biology', 'Chemistry', 'Physics', 'Islamiat', 'Pakistan Studies', 'Science', 'Social Studies'
                ]
                existing_subjects = {s.name.lower(): s for s in Subject.objects.filter(school=school)}
                for name in core_subject_names:
                    if name.lower() not in existing_subjects:
                        Subject.objects.create(
                            school=school,
                            name=name,
                            code=name.replace(' ', '_').upper()[:10],
                            description=f'Auto-created {name}',
                            is_active=True,
                        )

                # Get all active subjects for the school (post auto-create)
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

                # Auto-create teacher-subject assignments if missing (based on teacher.subject_specialist)
                subject_by_name = {s.name.lower(): s for s in Subject.objects.filter(school=school)}
                name_map = {
                    'math': 'Mathematics', 'mathematics': 'Mathematics', 'eng': 'English', 'english': 'English',
                    'urdu': 'Urdu', 'computer science': 'Computer Science', 'computer': 'Computer Science', 'it': 'Computer Science', 'physics': 'Physics',
                    'chemistry': 'Chemistry', 'bio': 'Biology', 'biology': 'Biology',
                    'islamiat': 'Islamiat', 'pakistan studies': 'Pakistan Studies', 'science': 'Science', 'social studies': 'Social Studies'
                }
                for teacher in Teacher.objects.filter(school=school, is_active=True):
                    spec = (teacher.subject_specialist or '').strip().lower()
                    target = None
                    if spec in subject_by_name:
                        target = subject_by_name[spec]
                    else:
                        for key, canonical in name_map.items():
                            if key in spec and canonical.lower() in subject_by_name:
                                target = subject_by_name[canonical.lower()]
                                break
                    if target:
                        TeacherSubjectAssignment.objects.get_or_create(
                            teacher=teacher, subject=target,
                            defaults={'is_primary': True, 'max_periods_per_week': 25}
                        )

                # Ensure all teachers can also teach common crossover subjects for balancing
                fallback_subjects = ['Islamiat', 'Social Studies']
                for fs in fallback_subjects:
                    subj = subject_by_name.get(fs.lower())
                    if subj:
                        for teacher in Teacher.objects.filter(school=school, is_active=True):
                            TeacherSubjectAssignment.objects.get_or_create(
                                teacher=teacher, subject=subj,
                                defaults={'is_primary': False, 'max_periods_per_week': 25}
                            )

                # Get teacher-subject assignments (post auto-create)
                teacher_assignments = TeacherSubjectAssignment.objects.filter(
                    teacher__school=school,
                    subject__school=school
                ).select_related('teacher', 'subject')

                if not teacher_assignments.exists():
                    return {
                        'success': False,
                        'error': 'No teacher-subject assignments found'
                    }

                # Build teacher-subject mapping from final assignments
                teacher_subject_map = defaultdict(list)
                for assignment in teacher_assignments:
                    teacher_subject_map[assignment.subject.id].append(assignment.teacher)

                # Get school configuration
                total_periods_per_day = school.total_periods_per_day
                working_days = school.working_days or ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

                if verbose:
                    self.stdout.write(f"Working days: {working_days}")
                    self.stdout.write(f"Periods per day: {total_periods_per_day}")

                            # Calculate optimal teacher workload distribution
            total_available_periods = len(working_days) * total_periods_per_day * classes.count()
            total_teachers = teachers.count()
            target_periods_per_teacher = total_available_periods / total_teachers if total_teachers > 0 else 0
            
            # Enhanced workload balancing with subject distribution
            teacher_subject_workload = {}
            for teacher in teachers:
                teacher_subject_workload[teacher.id] = {
                    'total_periods': 0,
                    'daily_loads': {day: 0 for day in working_days},
                    'subject_distribution': {},
                    'consecutive_periods': 0,
                    'max_daily_load': 0
                }

                if verbose:
                    self.stdout.write(f"Total available periods: {total_available_periods}")
                    self.stdout.write(f"Target periods per teacher: {target_periods_per_teacher:.2f}")

                # Initialize tracking variables with improved workload balancing
                teacher_schedule = defaultdict(set)  # teacher -> set of (day, period)
                teacher_weekly_periods = Counter()  # teacher -> periods count
                teacher_daily_periods = defaultdict(Counter)  # teacher -> day -> count
                # Subject variety trackers
                teacher_daily_subject = defaultdict(lambda: defaultdict(Counter))  # teacher -> day -> subject_id -> count
                teacher_weekly_subject = defaultdict(Counter)  # teacher -> subject_id -> count
                # Limits: encourage variety (at most 1 period of same subject per day per teacher; at most 8 per week)
                daily_subject_limit = 1
                weekly_subject_limit = 8
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

                        # Helper: required subjects by class level and section
                        def required_subjects_for_class(class_obj):
                            # Try to parse numeric level from class_name
                            level = None
                            try:
                                # class_name might be like "Class 5" or "5" or "Grade 8"
                                import re
                                digits = re.findall(r"\d+", str(class_obj.class_name))
                                if digits:
                                    level = int(digits[0])
                            except Exception:
                                level = None

                            section = (class_obj.section or '').strip().upper()
                            subjects_set = []

                            if level is not None and 1 <= level <= 5:
                                subjects_set = ['English', 'Urdu', 'Mathematics', 'General Knowledge', 'Islamiat']
                            elif level is not None and 6 <= level <= 8:
                                subjects_set = ['English', 'Urdu', 'Mathematics', 'Science', 'Islamiat', 'Social Studies', 'Computer Science']
                            elif level in (9, 10):
                                core_9_10 = ['English', 'Islamiat', 'Chemistry', 'Physics', 'Mathematics']
                                # Pakistan Studies only for 10th
                                if level == 10:
                                    core_9_10.append('Pakistan Studies')
                                # Biology for A, Computer Science for B (if exist)
                                if section == 'A':
                                    core_9_10.append('Biology')
                                elif section == 'B':
                                    core_9_10.append('Computer Science')
                                else:
                                    # Default to Science group if section unknown
                                    core_9_10.append('Biology')
                                subjects_set = core_9_10
                            else:
                                # Fallback minimal set
                                subjects_set = ['English', 'Urdu', 'Mathematics', 'Science']

                            return subjects_set

                        # Generate timetable for each class
                        for class_obj in classes:
                            # Respect class-selected subjects; only auto-fill if none set
                            if class_obj.subjects.count() == 0:
                                required_names = required_subjects_for_class(class_obj)
                                for name in required_names:
                                    subj = Subject.objects.filter(school=school, name=name, is_active=True).first()
                                    if subj and subj not in class_obj.subjects.all():
                                        class_obj.subjects.add(subj)
                            class_subjects = list(class_obj.subjects.filter(is_active=True))
                            
                            if not class_subjects:
                                warnings.append(f"Class {class_obj.class_name}-{class_obj.section} has no subjects assigned")
                                continue

                            # Calculate periods per subject with improved distribution
                            total_class_periods = len(working_days) * total_periods_per_day
                            # Give core subjects baseline of 1 per day if possible
                            baseline = {s.id: 0 for s in class_subjects}
                            for s in class_subjects:
                                if s.name in ['Mathematics', 'English', 'Urdu']:
                                    baseline[s.id] = min(len(working_days), total_class_periods)
                            remaining_periods = total_class_periods - sum(min(1, baseline[s.id] and 1) for s in class_subjects)
                            # Evenly distribute remaining
                            periods_per_subject = remaining_periods // max(1, len(class_subjects))
                            extra_periods = remaining_periods % max(1, len(class_subjects))

                            # Assign periods to subjects
                            subject_periods = {}
                            for i, subject in enumerate(class_subjects):
                                base = 1 if baseline[subject.id] else 0
                                periods = base + periods_per_subject + (1 if i < extra_periods else 0)
                                subject_periods[subject] = periods

                            # Generate slots for each day and period
                            for day in working_days:
                                for period in range(1, total_periods_per_day + 1):
                                    # Check if this period should be a break period
                                    break_period = next((bp for bp in school.break_periods if bp['period'] == period), None)
                                    
                                    if break_period:
                                        # Create break period slot
                                        start_time, end_time = school.get_period_times(period)
                                        TimeTableSlot.objects.create(
                                            school=school,
                                            class_obj=class_obj,
                                            subject=None,  # No subject for break periods
                                            teacher=None,  # No teacher for break periods
                                            day=day,
                                            period_number=period,
                                            academic_year=academic_year,
                                            is_break_period=True,
                                            break_name=break_period['name'],
                                            period_start_time=start_time,
                                            period_end_time=end_time
                                        )
                                        continue
                                    
                                    # Find available subject for this slot
                                    available_subjects = [
                                        subject for subject in class_subjects
                                        if class_subject_periods[class_obj.id][subject.id] < subject_periods[subject]
                                    ]

                                    if not available_subjects:
                                        continue

                                    # Try to assign a subject and teacher with improved workload balancing
                                    slot_created = False
                                    for _ in range(10):  # Try up to 10 times for this slot
                                        # Build balanced candidate list prioritizing workload balance
                                        candidates = []
                                        for subject in available_subjects:
                                            possible = [
                                                t for t in teacher_subject_map.get(subject.id, [])
                                                if (t.id, day, period) not in teacher_schedule[t.id]
                                                and teacher_weekly_periods[t.id] < 25
                                                and teacher_daily_periods[t.id][day] < max(0, total_periods_per_day - 1)
                                                and teacher_daily_subject[t.id][day][subject.id] < daily_subject_limit
                                                and teacher_weekly_subject[t.id][subject.id] < weekly_subject_limit
                                            ]
                                            for t in possible:
                                                # Enhanced workload scoring system
                                                workload_deviation = abs(teacher_weekly_periods[t.id] - target_periods_per_teacher)
                                                daily_load = teacher_daily_periods[t.id][day]
                                                
                                                # Calculate enhanced score (lower is better)
                                                score = workload_deviation * 2  # Primary factor: workload balance
                                                score += daily_load * 0.5       # Secondary factor: daily load
                                                
                                                # Penalty for consecutive periods of same subject
                                                consecutive_penalty = 0
                                                if period > 1:
                                                    prev_period = period - 1
                                                    if (t.id, day, prev_period) in teacher_schedule[t.id]:
                                                        # Check if same subject in previous period
                                                        prev_slot = TimeTableSlot.objects.filter(
                                                            school=school, teacher=t, day=day, 
                                                            period_number=prev_period, academic_year=academic_year
                                                        ).first()
                                                        if prev_slot and prev_slot.subject.id == subject.id:
                                                            consecutive_penalty = 5
                                
                                                # Penalty for exceeding max daily load
                                                daily_load_penalty = 0
                                                if daily_load >= 6:
                                                    daily_load_penalty = 10
                                                elif daily_load >= 5:
                                                    daily_load_penalty = 5
                                
                                                # Bonus for teachers with low subject distribution
                                                subject_distribution_bonus = 0
                                                teacher_subjects = set()
                                                for slot in TimeTableSlot.objects.filter(
                                                    school=school, teacher=t, academic_year=academic_year
                                                ):
                                                    teacher_subjects.add(slot.subject.id)
                                                if len(teacher_subjects) < 3:
                                                    subject_distribution_bonus = -2
                                
                                                final_score = score + consecutive_penalty + daily_load_penalty + subject_distribution_bonus
                                                candidates.append((subject, t, final_score, daily_load, workload_deviation))

                                        if not candidates:
                                            break

                                        # Sort candidates by enhanced score (lower is better)
                                        candidates.sort(key=lambda x: x[2])

                                        # If first period and class teacher is eligible, prefer them if not significantly worse
                                        preferred = None
                                        if period == 1 and class_obj.class_teacher:
                                            for subject in available_subjects:
                                                if class_obj.class_teacher in teacher_subject_map.get(subject.id, []):
                                                    # Check caps
                                                    t = class_obj.class_teacher
                                                    if (t.id, day, period) not in teacher_schedule[t.id] \
                                                       and teacher_weekly_periods[t.id] < 25 \
                                                       and teacher_daily_periods[t.id][day] < max(0, total_periods_per_day - 1):
                                                        # Calculate score for class teacher
                                                        workload_deviation = abs(teacher_weekly_periods[t.id] - target_periods_per_teacher)
                                                        daily_load = teacher_daily_periods[t.id][day]
                                                        class_teacher_score = workload_deviation * 2 + daily_load * 0.5
                                                        preferred = (subject, t, class_teacher_score, daily_load, workload_deviation)
                                                        break

                                        chosen = None
                                        if preferred is not None:
                                            # Allow preference if it doesn't significantly worsen workload balance
                                            if preferred[2] <= candidates[0][2] + 3:  # Allow slight deviation for class teacher preference
                                                chosen = preferred
                                        if chosen is None:
                                            chosen = candidates[0]

                                        if chosen:
                                            c_subject, c_teacher, _, _, _ = chosen
                                            
                                            # Calculate period timing
                                            start_time, end_time = school.get_period_times(period)
                                            
                                            # Create the slot
                                            TimeTableSlot.objects.create(
                                                school=school,
                                                class_obj=class_obj,
                                                subject=c_subject,
                                                teacher=c_teacher,
                                                day=day,
                                                period_number=period,
                                                academic_year=academic_year,
                                                is_active=True,
                                                period_start_time=start_time,
                                                period_end_time=end_time,
                                                is_break_period=False
                                            )
                                            # Update tracking (apply to chosen)
                                            teacher_schedule[c_teacher.id].add((c_teacher.id, day, period))
                                            teacher_weekly_periods[c_teacher.id] += 1
                                            teacher_daily_periods[c_teacher.id][day] += 1
                                            teacher_daily_subject[c_teacher.id][day][c_subject.id] += 1
                                            teacher_weekly_subject[c_teacher.id][c_subject.id] += 1
                                            class_subject_periods[class_obj.id][c_subject.id] += 1
                                            slots_created += 1
                                            slot_created = True
                                            break

                                    if not slot_created:
                                        # Could not assign this slot; record warning and continue filling others
                                        warnings.append(
                                            f"Unfilled slot: {class_obj.class_name}-{class_obj.section} {day} P{period}"
                                        )
                                        continue

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

                # Check for any remaining issues and provide workload analysis
                teacher_workload_summary = {}
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
                    
                    teacher_workload_summary[teacher.name] = {
                        'periods': teacher_slots,
                        'deviation_from_target': round(teacher_slots - target_periods_per_teacher, 2)
                    }

                # Check class completion
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

                if verbose:
                    self.stdout.write("\nTeacher Workload Summary:")
                    for teacher_name, workload in teacher_workload_summary.items():
                        status = "Optimal" if abs(workload['deviation_from_target']) <= 2 else "Under-utilized" if workload['deviation_from_target'] < -2 else "Over-utilized"
                        self.stdout.write(f"  {teacher_name}: {workload['periods']} periods ({status}, deviation: {workload['deviation_from_target']})")

                return {
                    'success': True,
                    'slots_created': slots_created,
                    'attempts': attempt + 1,
                    'warnings': warnings,
                    'teacher_workload_summary': teacher_workload_summary,
                    'target_periods_per_teacher': round(target_periods_per_teacher, 2)
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Database error: {str(e)}',
                'attempts': 0
            } 