import streamlit as st
import pandas as pd
import random
from datetime import datetime, date, timedelta
import time

# Page Configuration
st.set_page_config(
    page_title="UniTimetable AI Scheduler",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================== DATA LOADING FUNCTIONS ==================
def load_courses_data():
    """Load courses data from CSV"""
    try:
        df = pd.read_csv('timetable_data.csv')
        # Ensure required columns exist
        required_columns = ['Class', 'Subject', 'Hours', 'Faculty', 'Code', 'Type']
        for col in required_columns:
            if col not in df.columns:
                st.error(f"Required column '{col}' not found in timetable_data.csv")
                return pd.DataFrame()
        
        df['Hours'] = pd.to_numeric(df['Hours'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Error loading timetable_data.csv: {e}")
        return pd.DataFrame()

def load_rooms_config():
    """Load rooms configuration"""
    try:
        return pd.read_csv('rooms_config.csv')
    except:
        st.warning("Using default rooms configuration")
        return pd.DataFrame({
            'Room': ['Room-101', 'Room-102', 'Room-103', 'Room-104', 'Room-105',
                    'Room-201', 'Room-202', 'Room-203', 'Room-204', 'Room-205',
                    'Lab-301', 'Lab-302', 'Lab-303', 'Lab-304'],
            'Type': ['Lecture', 'Lecture', 'Lecture', 'Lecture', 'Lecture',
                    'Lecture', 'Lecture', 'Lecture', 'Lecture', 'Lecture',
                    'Lab', 'Lab', 'Lab', 'Lab'],
            'Capacity': [40, 40, 40, 40, 40, 50, 50, 50, 50, 50, 30, 30, 30, 30]
        })

def load_time_config():
    """Load time slots configuration from 8 AM to 5 PM"""
    try:
        time_df = pd.read_csv('time_config.csv')
        return time_df
    except:
        st.warning("Using default time configuration (8 AM - 5 PM)")
        # Fixed time slots from 8 AM to 5 PM (9 hours)
        return pd.DataFrame({
            'Slot': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9'],
            'Start_Time': ['08:00 AM', '09:00 AM', '10:00 AM', '11:00 AM', '12:00 PM', 
                          '01:00 PM', '02:00 PM', '03:00 PM', '04:00 PM'],
            'End_Time': ['09:00 AM', '10:00 AM', '11:00 AM', '12:00 PM', '01:00 PM',
                        '02:00 PM', '03:00 PM', '04:00 PM', '05:00 PM']
        })

def load_days_config():
    """Load working days configuration"""
    try:
        days_df = pd.read_csv('days_config.csv')
        return days_df[days_df['Working'] == 'Yes']['Day'].tolist()
    except:
        st.warning("Using default days configuration")
        return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

# ================== USER SESSION MANAGEMENT ==================
def initialize_session_state():
    """Initialize session state variables"""
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'show_timetable' not in st.session_state:
        st.session_state.show_timetable = False
    if 'selected_class' not in st.session_state:
        st.session_state.selected_class = None
    if 'clash_log' not in st.session_state:
        st.session_state.clash_log = []
    if 'user_academic_info' not in st.session_state:
        st.session_state.user_academic_info = {}
    if 'selected_faculty' not in st.session_state:
        st.session_state.selected_faculty = None
    if 'faculty_schedule' not in st.session_state:
        st.session_state.faculty_schedule = {}
    if 'view_faculty_daily' not in st.session_state:
        st.session_state.view_faculty_daily = True
    if 'search_faculty_mode' not in st.session_state:
        st.session_state.search_faculty_mode = False
    if 'searched_faculty' not in st.session_state:
        st.session_state.searched_faculty = None
    if 'view_faculty_schedule' not in st.session_state:
        st.session_state.view_faculty_schedule = {}
    if 'timetable_data' not in st.session_state:
        st.session_state.timetable_data = None
    if 'generation_attempts' not in st.session_state:
        st.session_state.generation_attempts = 0

# ================== HELPER FUNCTIONS ==================
def get_unique_faculty(df):
    """Get unique faculty members from CSV data"""
    if df.empty:
        return []
    
    faculty_set = set()
    for faculty in df['Faculty'].unique():
        if pd.isna(faculty):
            continue
        if ';' in str(faculty):
            # Split multiple faculty separated by semicolon
            facs = [f.strip() for f in str(faculty).split(';')]
            faculty_set.update(facs)
        else:
            faculty_set.add(str(faculty).strip())
    
    # Sort alphabetically
    return sorted(list(faculty_set))

def get_faculty_courses(df, faculty_name):
    """Get all courses taught by a specific faculty"""
    if df.empty or not faculty_name:
        return pd.DataFrame()
    
    # Filter courses where faculty name appears in the Faculty column
    mask = df['Faculty'].astype(str).apply(lambda x: faculty_name in x if pd.notna(x) else False)
    return df[mask].copy()

def get_faculty_details(df, faculty_name):
    """Get details for a specific faculty member"""
    if df.empty or not faculty_name:
        return {}
    
    faculty_courses = get_faculty_courses(df, faculty_name)
    
    if faculty_courses.empty:
        return {}
    
    total_hours = faculty_courses['Hours'].sum()
    subjects = faculty_courses['Subject'].unique().tolist()
    classes = faculty_courses['Class'].unique().tolist()
    course_count = len(faculty_courses)
    
    return {
        'name': faculty_name,
        'total_hours': total_hours,
        'subject_count': len(subjects),
        'class_count': len(classes),
        'course_count': course_count,
        'subjects': subjects[:10],
        'classes': classes[:10]
    }

def get_class_details(df, class_name):
    """Get details for a specific class"""
    if df.empty:
        return {}
    
    class_data = df[df['Class'] == class_name]
    total_hours = class_data['Hours'].sum()
    subjects = class_data['Subject'].unique().tolist()
    
    faculty_set = set()
    for faculty in class_data['Faculty'].unique():
        if ';' in str(faculty):
            facs = [f.strip() for f in str(faculty).split(';')]
            faculty_set.update(facs)
        else:
            faculty_set.add(str(faculty))
    
    return {
        'class': class_name,
        'total_hours': total_hours,
        'subject_count': len(subjects),
        'faculty_count': len(faculty_set),
        'subjects': subjects[:5],
        'faculty': list(faculty_set)[:5]
    }

def get_day_name():
    """Get current day name"""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return days[date.today().weekday()]

def get_available_classes_for_selection(df, program, semester, section):
    """Get available classes based on program, semester and section"""
    if df.empty or not program or not semester or not section:
        return []
    
    class_pattern = f"{program}-{semester}{section}"
    
    if class_pattern in df['Class'].unique():
        return [class_pattern]
    else:
        available_classes = []
        for class_name in df['Class'].unique():
            try:
                class_program = class_name.split('-')[0]
                class_semester = class_name.split('-')[1][0]
                if class_program == program and class_semester == semester:
                    available_classes.append(class_name)
            except:
                continue
        
        return available_classes

def get_unique_programs(df):
    """Get unique programs from class names"""
    if df.empty:
        return []
    
    programs = set()
    for class_name in df['Class'].unique():
        try:
            program = class_name.split('-')[0]
            programs.add(program)
        except:
            continue
    
    return sorted(list(programs))

def get_unique_semesters(df):
    """Get unique semesters from class names"""
    if df.empty:
        return []
    
    semesters = set()
    for class_name in df['Class'].unique():
        try:
            semester = class_name.split('-')[1][0]
            semesters.add(semester)
        except:
            continue
    
    return sorted(list(semesters))

# ================== IMPROVED CLASH RESOLVER ==================
class AdvancedClashResolver:
    def __init__(self):
        self.room_schedule = {}  # (day, time, room) -> class
        self.faculty_schedule = {}  # (day, time, faculty) -> class
        self.class_schedule = {}  # (day, time, class) -> room
        self.subject_day_schedule = {}  # (class, subject, day) -> count
        self.daily_class_hours = {}  # (class, day) -> hours
        self.daily_faculty_hours = {}  # (faculty, day) -> hours
        self.room_utilization = {}  # room -> list of (day, time)
        self.faculty_workload = {}  # faculty -> total hours
    
    def check_and_resolve_clash(self, day, time_slot, room, faculty, class_name, subject):
        """Check for clashes and suggest alternatives"""
        clashes = []
        
        # Check room availability
        room_key = (day, time_slot, room)
        if room_key in self.room_schedule:
            clashes.append(f"Room {room} already occupied by {self.room_schedule[room_key]}")
        
        # Check faculty availability
        faculty_key = (day, time_slot, faculty)
        if faculty_key in self.faculty_schedule:
            clashes.append(f"Faculty {faculty} already teaching {self.faculty_schedule[faculty_key]}")
        
        # Check class availability
        class_key = (day, time_slot, class_name)
        if class_key in self.class_schedule:
            clashes.append(f"Class {class_name} already has class in {self.class_schedule[class_key]}")
        
        # Check subject per day limit (max 1 per day)
        subject_key = (class_name, subject, day)
        if subject_key in self.subject_day_schedule:
            clashes.append(f"Subject {subject} already scheduled for {class_name} on {day}")
        
        # Check daily class limit (max 4 hours per day)
        class_day_key = (class_name, day)
        if class_day_key in self.daily_class_hours and self.daily_class_hours[class_day_key] >= 4:
            clashes.append(f"Class {class_name} already has 4 hours on {day}")
        
        # Check daily faculty limit (max 5 hours per day)
        faculty_day_key = (faculty, day)
        if faculty_day_key in self.daily_faculty_hours and self.daily_faculty_hours[faculty_day_key] >= 5:
            clashes.append(f"Faculty {faculty} already has 5 hours on {day}")
        
        return clashes
    
    def add_schedule(self, day, time_slot, room, faculty, class_name, subject):
        """Add schedule to tracker"""
        room_key = (day, time_slot, room)
        faculty_key = (day, time_slot, faculty)
        class_key = (day, time_slot, class_name)
        subject_key = (class_name, subject, day)
        class_day_key = (class_name, day)
        faculty_day_key = (faculty, day)
        
        # Add to trackers
        self.room_schedule[room_key] = class_name
        self.faculty_schedule[faculty_key] = class_name
        self.class_schedule[class_key] = room
        self.subject_day_schedule[subject_key] = 1
        
        # Update daily hours
        if class_day_key not in self.daily_class_hours:
            self.daily_class_hours[class_day_key] = 0
        self.daily_class_hours[class_day_key] += 1
        
        if faculty_day_key not in self.daily_faculty_hours:
            self.daily_faculty_hours[faculty_day_key] = 0
        self.daily_faculty_hours[faculty_day_key] += 1
        
        # Update faculty workload
        if faculty not in self.faculty_workload:
            self.faculty_workload[faculty] = 0
        self.faculty_workload[faculty] += 1
        
        # Update room utilization
        if room not in self.room_utilization:
            self.room_utilization[room] = []
        self.room_utilization[room].append((day, time_slot))
    
    def find_alternative_slot(self, course, days_list, time_slots, rooms_by_type, used_slots):
        """Find alternative slot for a course"""
        course_type = course['Type']
        subject = course['Subject']
        class_name = course['Class']
        
        # Get faculty (handle multiple faculty)
        faculty_str = str(course['Faculty'])
        if ';' in faculty_str:
            faculty_options = [f.strip() for f in faculty_str.split(';')]
        else:
            faculty_options = [faculty_str.strip()]
        
        max_attempts_per_faculty = 50
        best_slot = None
        min_clashes = float('inf')
        
        for faculty in faculty_options:
            for attempt in range(max_attempts_per_faculty):
                # Try different days
                for day in random.sample(days_list, len(days_list)):
                    # Try different time slots
                    for time_idx in random.sample(range(len(time_slots)), len(time_slots)):
                        time_slot = time_slots[time_idx]
                        time_display = f"{time_slot.split('-')[0]} to {time_slot.split('-')[1]}"
                        
                        # Check if this slot already tried
                        slot_key = (day, time_slot, class_name, subject)
                        if slot_key in used_slots:
                            continue
                        
                        # Select appropriate room
                        if course_type == 'Lab':
                            room = random.choice(rooms_by_type['lab']) if rooms_by_type['lab'] else 'Lab-001'
                        else:
                            room = random.choice(rooms_by_type['lecture']) if rooms_by_type['lecture'] else 'Room-001'
                        
                        # Check for clashes
                        clashes = self.check_and_resolve_clash(day, time_slot, room, faculty, class_name, subject)
                        
                        if not clashes:
                            return {
                                'day': day,
                                'time_slot': time_slot,
                                'time_display': time_display,
                                'room': room,
                                'faculty': faculty,
                                'clashes': []
                            }
                        elif len(clashes) < min_clashes:
                            min_clashes = len(clashes)
                            best_slot = {
                                'day': day,
                                'time_slot': time_slot,
                                'time_display': time_display,
                                'room': room,
                                'faculty': faculty,
                                'clashes': clashes
                            }
                        
                        used_slots.add(slot_key)
        
        return best_slot

# ================== IMPROVED TIMETABLE GENERATOR ==================
def generate_optimized_timetable(courses_df, rooms_df, time_df, days_list, class_name=None, faculty_name=None):
    """Generate optimized timetable with advanced clash resolution"""
    if courses_df.empty or rooms_df.empty or time_df.empty:
        return pd.DataFrame()
    
    # Initialize clash resolver
    resolver = AdvancedClashResolver()
    
    # Filter courses
    if class_name:
        class_courses = courses_df[(courses_df['Class'] == class_name) & (courses_df['Hours'] > 0)].copy()
    elif faculty_name:
        class_courses = get_faculty_courses(courses_df, faculty_name)
        class_courses = class_courses[class_courses['Hours'] > 0].copy()
    else:
        class_courses = courses_df[courses_df['Hours'] > 0].copy()
    
    if class_courses.empty:
        return pd.DataFrame()
    
    # Get time slots
    time_slots = []
    time_display_list = []
    for _, slot in time_df.iterrows():
        time_slots.append(f"{slot['Start_Time']}-{slot['End_Time']}")
        time_display_list.append(f"{slot['Start_Time']} to {slot['End_Time']}")
    
    # Get rooms by type
    rooms_by_type = {
        'lecture': rooms_df[rooms_df['Type'] == 'Lecture']['Room'].tolist(),
        'lab': rooms_df[rooms_df['Type'] == 'Lab']['Room'].tolist()
    }
    
    # Sort courses by priority (more hours first, then labs)
    class_courses['Priority'] = class_courses['Hours'] * 10
    class_courses.loc[class_courses['Type'] == 'Lab', 'Priority'] += 5
    class_courses = class_courses.sort_values('Priority', ascending=False)
    
    timetable = []
    clash_log = []
    used_slots = set()
    
    # First pass: Schedule all courses without clashes if possible
    for _, course in class_courses.iterrows():
        hours_needed = int(course['Hours'])
        subject = course['Subject']
        class_name_course = course['Class']
        course_type = course['Type']
        
        # Track scheduled hours for this course
        scheduled_hours = 0
        
        while scheduled_hours < hours_needed:
            # Get faculty (handle multiple faculty)
            faculty_str = str(course['Faculty'])
            if ';' in faculty_str:
                faculty_options = [f.strip() for f in faculty_str.split(';')]
                faculty = random.choice(faculty_options)
            else:
                faculty = faculty_str.strip()
            
            # Find available slot
            slot_found = False
            attempts = 0
            max_attempts = 100
            
            while not slot_found and attempts < max_attempts:
                attempts += 1
                
                # Try different days
                day = random.choice(days_list)
                
                # Try different time slots
                time_idx = random.randint(0, len(time_slots) - 1)
                time_slot = time_slots[time_idx]
                time_display = time_display_list[time_idx]
                
                # Select appropriate room
                if course_type == 'Lab':
                    room = random.choice(rooms_by_type['lab']) if rooms_by_type['lab'] else 'Lab-001'
                else:
                    room = random.choice(rooms_by_type['lecture']) if rooms_by_type['lecture'] else 'Room-001'
                
                # Check for clashes
                clashes = resolver.check_and_resolve_clash(day, time_slot, room, faculty, class_name_course, subject)
                
                if not clashes:
                    # Check if this subject already scheduled for this class on this day
                    subject_key = (class_name_course, subject, day)
                    if subject_key in resolver.subject_day_schedule:
                        continue
                    
                    resolver.add_schedule(day, time_slot, room, faculty, class_name_course, subject)
                    
                    timetable.append({
                        'Class': class_name_course,
                        'Subject': subject,
                        'Faculty': course['Faculty'],
                        'Code': course['Code'],
                        'Type': course_type,
                        'Day': day,
                        'Time': time_display,
                        'Time_Slot': time_slot,
                        'Room': room,
                        'Status': '✅ Scheduled'
                    })
                    
                    scheduled_hours += 1
                    slot_found = True
                    used_slots.add((day, time_slot, class_name_course, subject))
            
            # If no slot found after attempts, use alternative method
            if not slot_found:
                alt_slot = resolver.find_alternative_slot(
                    course, days_list, time_slots, rooms_by_type, used_slots
                )
                
                if alt_slot:
                    resolver.add_schedule(
                        alt_slot['day'], 
                        alt_slot['time_slot'], 
                        alt_slot['room'], 
                        alt_slot['faculty'], 
                        class_name_course, 
                        subject
                    )
                    
                    status = '⚠️ Adjusted' if alt_slot['clashes'] else '✅ Scheduled'
                    
                    timetable.append({
                        'Class': class_name_course,
                        'Subject': subject,
                        'Faculty': alt_slot['faculty'],
                        'Code': course['Code'],
                        'Type': course_type,
                        'Day': alt_slot['day'],
                        'Time': alt_slot['time_display'],
                        'Time_Slot': alt_slot['time_slot'],
                        'Room': alt_slot['room'],
                        'Status': status
                    })
                    
                    if alt_slot['clashes']:
                        clash_log.append({
                            'Class': class_name_course,
                            'Subject': subject,
                            'Day': alt_slot['day'],
                            'Time': alt_slot['time_slot'],
                            'Clashes': alt_slot['clashes']
                        })
                    
                    scheduled_hours += 1
                    used_slots.add((alt_slot['day'], alt_slot['time_slot'], class_name_course, subject))
                else:
                    # Force schedule with minimum clashes
                    st.warning(f"Could not find suitable slot for {subject} in {class_name_course}")
                    break
    
    # Create DataFrame
    timetable_df = pd.DataFrame(timetable) if timetable else pd.DataFrame()
    
    # Store clash log in session state
    if clash_log:
        st.session_state.clash_log = clash_log
    
    return timetable_df

# ================== ROLE SELECTION ==================
def show_role_selection():
    """Show role selection interface"""
    st.title("📅 UniTimetable AI Scheduler")
    st.subheader("AI-Powered Clash-Free Timetable Scheduler")
    st.markdown("---")
    
    st.write("### Choose Your Role")
    st.write("Select your role to continue:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎓 Student")
        st.write("View your personalized timetable, check class schedules, and track academic progress")
        if st.button("Select Student Role", key="student_btn", use_container_width=True):
            st.session_state.user_role = 'student'
            st.rerun()
    
    with col2:
        st.markdown("#### 👨‍🏫 Teacher")
        st.write("Manage teaching schedules, view assigned classes, and check room availability")
        if st.button("Select Teacher Role", key="teacher_btn", use_container_width=True):
            st.session_state.user_role = 'teacher'
            st.rerun()

# ================== STUDENT PORTAL ==================
def show_student_portal(courses_df, rooms_df, time_df, days_list):
    """Show student portal interface"""
    st.title("🎓 Student Portal")
    st.markdown("---")
    
    if courses_df.empty:
        st.error("No course data found. Please upload timetable_data.csv")
        return
    
    # Get unique programs and semesters from data
    programs = get_unique_programs(courses_df)
    semesters = get_unique_semesters(courses_df)
    
    if not programs or not semesters:
        st.error("No valid class data found in CSV")
        return
    
    # Student Information Section
    st.header("📝 Enter Your Academic Information")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        # Semester selection
        semester_options = ["Select Semester"] + semesters
        semester = st.selectbox(
            "Semester",
            semester_options,
            index=0,
            help="Select your academic semester"
        )
        
        # Program selection
        program_disabled = (semester == "Select Semester")
        program_options = ["Select Program"] + programs
        program = st.selectbox(
            "Program",
            program_options,
            index=0,
            disabled=program_disabled,
            help="Select your academic program"
        )
    
    with col_info2:
        # Section selection
        section_disabled = (program == "Select Program") or (semester == "Select Semester")
        section = st.selectbox(
            "Section",
            ["Select Section", "A", "B", "C", "D"],
            index=0,
            disabled=section_disabled,
            help="Select your section"
        )
        
        # Automatically determine class
        selected_class = None
        if semester != "Select Semester" and program != "Select Program" and section != "Select Section":
            class_name = f"{program}-{semester}{section}"
            
            available_classes = get_available_classes_for_selection(courses_df, program, semester, section)
            
            if available_classes:
                if class_name in available_classes:
                    selected_class = class_name
                    st.success(f"Class found: **{selected_class}**")
                else:
                    selected_class = available_classes[0]
                    st.warning(f"Class {class_name} not found. Using available class: **{selected_class}**")
            else:
                st.error(f"No classes found for {program} Semester {semester} Section {section}")
        else:
            st.info("Please select Semester, Program, and Section to find your class")
    
    # Save button
    if selected_class:
        if st.button("Save Academic Information", type="primary", use_container_width=True):
            st.session_state.user_academic_info = {
                'program': program,
                'semester': f"Semester {semester}",
                'section': section,
                'class': selected_class
            }
            st.success("Academic information saved successfully!")
    
    # Display saved information
    if st.session_state.user_academic_info:
        info = st.session_state.user_academic_info
        st.info(f"**Academic Profile:** {info['program']} | {info['semester']} | Section {info['section']} | Class {info['class']}")
    
    # Class Statistics
    if selected_class:
        class_info = get_class_details(courses_df, selected_class)
        
        st.subheader("📊 Class Statistics")
        
        # Metrics
        col_metric1, col_metric2, col_metric3 = st.columns(3)
        with col_metric1:
            st.metric("Weekly Hours", class_info['total_hours'])
        with col_metric2:
            st.metric("Subjects", class_info['subject_count'])
        with col_metric3:
            st.metric("Faculty", class_info['faculty_count'])
        
        # Subjects and Faculty
        col_sub, col_fac = st.columns(2)
        with col_sub:
            st.write("**Subjects:**")
            for subject in class_info['subjects']:
                st.write(f"- {subject}")
        
        with col_fac:
            st.write("**Faculty:**")
            for faculty in class_info['faculty']:
                st.write(f"- {faculty}")
        
        # Generate Timetable Button
        st.markdown("---")
        if st.button("Generate Timetable", type="primary", use_container_width=True, 
                    help="Generate a clash-free timetable for your selected class"):
            st.session_state.show_timetable = True
            st.session_state.selected_class = selected_class
            st.session_state.clash_log = []
            st.session_state.generation_attempts = 0
            st.rerun()
    
    # Display Timetable
    if st.session_state.show_timetable:
        st.markdown("---")
        selected_class = st.session_state.selected_class
        
        st.header(f"📋 Timetable for Class {selected_class}")
        st.write("AI-Generated Clash-Free Schedule")
        st.write("✅ One subject per day | ⏰ 8:00 AM to 5:00 PM | 📌 Max 4 hours per day per class")
        
        with st.spinner(f"Generating optimal timetable for {selected_class}..."):
            # Generate timetable
            timetable_df = generate_optimized_timetable(
                courses_df, rooms_df, time_df, days_list, selected_class
            )
            
            if timetable_df.empty:
                st.warning(f"No courses found for class {selected_class}")
            else:
                # Store in session state
                st.session_state.timetable_data = timetable_df
                
                # Display clash summary
                clash_count = len(timetable_df[timetable_df['Status'] != '✅ Scheduled'])
                
                if clash_count > 0:
                    st.warning(f"⚠️ {clash_count} schedule adjustments needed")
                else:
                    st.success("✅ Perfect clash-free schedule generated!")
                
                # Day-wise display
                st.subheader("📅 Weekly Schedule View")
                day_cols = st.columns(len(days_list))
                
                for idx, day in enumerate(days_list):
                    with day_cols[idx]:
                        # Highlight today
                        if day == get_day_name():
                            st.markdown(f"**{day}** *(Today)*")
                        else:
                            st.markdown(f"**{day}**")
                        
                        day_classes = timetable_df[timetable_df['Day'] == day]
                        
                        if not day_classes.empty:
                            # Sort by time slot
                            day_classes = day_classes.sort_values('Time_Slot')
                            
                            # Count lectures for this day
                            lecture_count = len(day_classes)
                            st.caption(f"{lecture_count} classes")
                            
                            for _, cls in day_classes.iterrows():
                                # Format faculty display
                                faculty_display = cls['Faculty']
                                if ';' in str(faculty_display):
                                    faculty_display = faculty_display.split(';')[0].strip()
                                
                                # Create a card for each class
                                with st.container():
                                    if cls['Status'] != '✅ Scheduled':
                                        st.warning(f"**{cls['Subject']}**")
                                    else:
                                        st.success(f"**{cls['Subject']}**")
                                    
                                    st.write(f"🕒 {cls['Time']}")
                                    st.write(f"📍 {cls['Room']}")
                                    st.write(f"👨‍🏫 {faculty_display}")
                                    st.write(f"📚 {cls['Code']} | 🏫 {cls['Type']}")
                                    st.markdown("---")
                        else:
                            st.info("No classes scheduled")
                
                # Download section
                st.markdown("---")
                col_download1, col_download2 = st.columns([3, 1])
                with col_download1:
                    with st.expander("View Complete Timetable Table"):
                        st.dataframe(timetable_df[['Day', 'Time', 'Subject', 'Room', 'Faculty', 'Code', 'Type', 'Status']], 
                                   use_container_width=True)
                with col_download2:
                    csv = timetable_df.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        f"timetable_{selected_class}_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv",
                        use_container_width=True
                    )

# ================== TEACHER PORTAL ==================
def show_teacher_portal(courses_df, rooms_df, time_df, days_list):
    """Show teacher portal interface"""
    st.title("👨‍🏫 Teacher Portal")
    st.markdown("---")
    
    if courses_df.empty:
        st.error("No course data found")
        return
    
    # Teacher selection dropdown
    st.header("Select Your Profile")
    
    # Get all faculty members
    all_faculty = get_unique_faculty(courses_df)
    
    if all_faculty:
        selected_faculty = st.selectbox(
            "Select your name from the list:",
            ["Select Faculty"] + all_faculty,
            key="faculty_dropdown"
        )
        
        if selected_faculty and selected_faculty != "Select Faculty":
            st.session_state.selected_faculty = selected_faculty
        else:
            st.info("Please select a faculty member from the dropdown")
            return
    else:
        st.info("No faculty data available in the system")
        return
    
    # If a faculty is selected
    show_teacher_profile(courses_df, rooms_df, time_df, days_list)

def show_teacher_profile(courses_df, rooms_df, time_df, days_list):
    """Show teacher profile section"""
    if not st.session_state.selected_faculty:
        return
    
    selected_faculty = st.session_state.selected_faculty
    
    # Faculty Profile
    st.header(f"Professor {selected_faculty}")
    st.write("Faculty Profile & Teaching Schedule")
    
    # Find courses taught by this faculty
    faculty_courses = get_faculty_courses(courses_df, selected_faculty)
    
    if not faculty_courses.empty:
        # Detailed Statistics
        faculty_details = get_faculty_details(courses_df, selected_faculty)
        
        st.subheader("📊 Teaching Statistics")
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.metric("Total Hours", faculty_details['total_hours'])
        with col_stat2:
            st.metric("Courses", faculty_details['course_count'])
        with col_stat3:
            st.metric("Subjects", faculty_details['subject_count'])
        with col_stat4:
            st.metric("Classes", faculty_details['class_count'])
        
        # Courses and Classes Overview
        st.subheader("📚 Teaching Assignments")
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.write("**Subjects Taught:**")
            for subject in faculty_details['subjects'][:8]:
                st.write(f"- {subject}")
            if len(faculty_details['subjects']) > 8:
                st.write(f"...and {len(faculty_details['subjects']) - 8} more")
        
        with col_info2:
            st.write("**Classes Assigned:**")
            for class_name in faculty_details['classes'][:8]:
                st.write(f"- {class_name}")
            if len(faculty_details['classes']) > 8:
                st.write(f"...and {len(faculty_details['classes']) - 8} more")
        
        # Generate Schedule Section
        st.markdown("---")
        st.subheader("📅 Teaching Schedule Generator")
        
        col_gen1, col_gen2 = st.columns([3, 1])
        
        with col_gen1:
            view_option = st.radio(
                "Select Schedule View:",
                ["Today's Schedule", "Weekly Schedule"],
                key="faculty_view_option",
                horizontal=True
            )
        
        with col_gen2:
            generate_clicked = st.button(
                "Generate Schedule", 
                type="primary", 
                use_container_width=True,
                help="Generate clash-free teaching schedule"
            )
        
        # Generate and display schedule
        if generate_clicked:
            with st.spinner(f"Generating schedule for {selected_faculty}..."):
                faculty_timetable = generate_optimized_timetable(
                    courses_df, rooms_df, time_df, days_list, faculty_name=selected_faculty
                )
                
                if not faculty_timetable.empty:
                    # Store in session state
                    st.session_state.view_faculty_schedule[selected_faculty] = faculty_timetable
                    
                    # Display schedule
                    display_faculty_schedule(faculty_timetable, selected_faculty, view_option)
                else:
                    st.warning(f"No schedule could be generated for {selected_faculty}")
        
        # Display existing schedule if available
        elif selected_faculty in st.session_state.view_faculty_schedule:
            faculty_timetable = st.session_state.view_faculty_schedule[selected_faculty]
            display_faculty_schedule(faculty_timetable, selected_faculty, view_option)
    
    else:
        st.info(f"No teaching assignments found for {selected_faculty}")

def display_faculty_schedule(timetable_df, faculty_name, view_option):
    """Display faculty schedule"""
    if timetable_df.empty:
        return
    
    # Display clash summary
    clash_count = len(timetable_df[timetable_df['Status'] != '✅ Scheduled'])
    
    if clash_count > 0:
        st.warning(f"⚠️ {clash_count} schedule adjustments needed")
    else:
        st.success("✅ Perfect clash-free teaching schedule!")
    
    # Today's Schedule view
    if "Today's" in view_option:
        today = get_day_name()
        st.subheader(f"📅 Today's Teaching Schedule ({today})")
        
        today_classes = timetable_df[timetable_df['Day'] == today]
        
        if not today_classes.empty:
            # Count today's lectures
            today_count = len(today_classes)
            st.caption(f"Total classes today: {today_count}")
            
            # Sort by time
            today_classes = today_classes.sort_values('Time_Slot')
            
            for _, cls in today_classes.iterrows():
                with st.container():
                    if cls['Status'] != '✅ Scheduled':
                        st.warning(f"**{cls['Subject']}**")
                    else:
                        st.success(f"**{cls['Subject']}**")
                    
                    st.write(f"🕒 {cls['Time']}")
                    st.write(f"📍 {cls['Room']}")
                    st.write(f"👨‍🎓 Class: {cls['Class']}")
                    st.write(f"📚 {cls['Code']} | 🏫 {cls['Type']}")
                    st.markdown("---")
        else:
            st.info("No classes scheduled for today!")
        
        # Tomorrow's preview
        days_list = load_days_config()
        if today in days_list:
            today_index = days_list.index(today)
            tomorrow_index = (today_index + 1) % len(days_list)
            tomorrow = days_list[tomorrow_index]
            
            with st.expander(f"Tomorrow's Preview ({tomorrow})"):
                tomorrow_classes = timetable_df[timetable_df['Day'] == tomorrow]
                if not tomorrow_classes.empty:
                    tomorrow_classes = tomorrow_classes.sort_values('Time_Slot')
                    for _, cls in tomorrow_classes.iterrows():
                        st.write(f"**{cls['Time']}**: {cls['Subject']}")
                        st.write(f"Class: {cls['Class']} | Room: {cls['Room']}")
                        st.markdown("---")
                else:
                    st.info("No classes scheduled for tomorrow")
    
    # Weekly Schedule view
    else:
        st.subheader("📅 Weekly Teaching Schedule")
        
        days_list = load_days_config()
        for day in days_list:
            st.write(f"#### {day}")
            day_classes = timetable_df[timetable_df['Day'] == day]
            
            if not day_classes.empty:
                # Count lectures for this day
                day_count = len(day_classes)
                st.caption(f"{day_count} classes")
                
                # Sort by time
                day_classes = day_classes.sort_values('Time_Slot')
                
                for _, cls in day_classes.iterrows():
                    with st.container():
                        if cls['Status'] != '✅ Scheduled':
                            st.warning(f"**{cls['Subject']}**")
                        else:
                            st.success(f"**{cls['Subject']}**")
                        
                        st.write(f"🕒 {cls['Time']}")
                        st.write(f"📍 {cls['Room']}")
                        st.write(f"👨‍🎓 Class: {cls['Class']}")
                        st.write(f"📚 {cls['Code']} | 🏫 {cls['Type']}")
                        st.markdown("---")
            else:
                st.info("No classes scheduled")
            st.markdown("---")
    
    # Download option
    st.markdown("---")
    col_down1, col_down2 = st.columns([3, 1])
    with col_down1:
        with st.expander("View Schedule Table"):
            st.dataframe(timetable_df[['Day', 'Time', 'Subject', 'Class', 'Room', 'Type', 'Status']], 
                       use_container_width=True)
    with col_down2:
        csv = timetable_df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            f"faculty_schedule_{faculty_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )

# ================== MAIN APP ==================
def main():
    # Initialize session
    initialize_session_state()
    
    # Load all data
    courses_df = load_courses_data()
    rooms_df = load_rooms_config()
    time_df = load_time_config()
    days_list = load_days_config()
    
    # Show role selection if no role chosen
    if st.session_state.user_role is None:
        show_role_selection()
    else:
        # Header with role and back button
        col_header1, col_header2 = st.columns([4, 1])
        
        with col_header1:
            role_display = "Student" if st.session_state.user_role == 'student' else "Teacher"
            role_icon = "🎓" if st.session_state.user_role == 'student' else "👨‍🏫"
            
            st.title(f"📅 UniTimetable Pro")
            st.write(f"AI-Powered Clash-Free Timetable Scheduler | {role_icon} {role_display} Mode")
        
        with col_header2:
            if st.button("Switch Role", type="secondary", use_container_width=True):
                st.session_state.user_role = None
                st.session_state.selected_faculty = None
                st.session_state.selected_class = None
                st.session_state.show_timetable = False
                st.session_state.faculty_schedule = {}
                st.session_state.view_faculty_schedule = {}
                st.session_state.search_faculty_mode = False
                st.session_state.timetable_data = None
                st.rerun()
        
        # Show appropriate portal based on role
        if st.session_state.user_role == 'student':
            show_student_portal(courses_df, rooms_df, time_df, days_list)
        elif st.session_state.user_role == 'teacher':
            show_teacher_portal(courses_df, rooms_df, time_df, days_list)

    # Footer
    st.markdown("---")
    st.markdown("**🎓 Intelligent Timetable Scheduling System**")
    st.markdown("Muhammad Atif Qureshi (57230) | Jawad Ahmed Javed (56751)")
    st.markdown("BSCS-5B | Riphah International University")
    st.markdown("Submitted to: Mr. Muhammad Asif")
    st.markdown("*Powered by Advanced Clash-Free Scheduling Algorithm*")

if __name__ == "__main__":
    main()