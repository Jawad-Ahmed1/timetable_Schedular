import pandas as pd
import random
import os
from datetime import datetime

def load_data(filepath="timetable_data.csv"):
    """Load timetable data from CSV file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"❌ File not found: {filepath}")
    
    df = pd.read_csv(filepath)
    df = df.fillna('')
    return df

def get_unique_values(df):
    """Get unique values from dataset."""
    return {
        'classes': sorted(df['Class'].unique()),
        'subjects': sorted(df['Subject'].unique()),
        'faculty': sorted(df['Faculty'].unique()),
        'types': sorted(df['Type'].unique()),
    }

def generate_time_slots():
    """Generate time slots for timetable."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['08:00-09:00', '09:00-10:00', '10:00-11:00', 
               '11:00-12:00', '12:00-13:00', '14:00-15:00', '15:00-16:00']
    
    slots = []
    for day in days:
        for period in periods:
            slots.append(f"{day} {period}")
    
    return slots

def generate_classrooms():
    """Generate classroom list."""
    rooms = []
    
    # Theory rooms
    for i in range(1, 16):
        rooms.append(f'Room-{i:02d}')
    
    # Lab rooms
    for i in range(1, 8):
        rooms.append(f'Lab-{i:02d}')
    
    return rooms

def calculate_workload(df):
    """Calculate workload per faculty."""
    workload = {}
    for _, row in df.iterrows():
        faculty = row['Faculty']
        hours = int(row['Hours']) if row['Hours'] else 0
        
        if ';' in str(faculty):  # Multiple faculty for labs
            faculties = [f.strip() for f in str(faculty).split(';')]
            for f in faculties:
                workload[f] = workload.get(f, 0) + hours
        else:
            workload[faculty] = workload.get(faculty, 0) + hours
    
    return workload

def save_timetable(timetable, filename=None):
    """Save timetable to CSV."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_timetables/timetable_{timestamp}.csv"
    
    # Create directory if it doesn't exist
    os.makedirs("generated_timetables", exist_ok=True)
    
    df = pd.DataFrame(timetable)
    df.to_csv(filename, index=False)
    return filename