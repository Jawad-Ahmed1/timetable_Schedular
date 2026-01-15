import random
import pandas as pd
from src.utils import generate_time_slots, generate_classrooms, load_data

class GeneticAlgorithmTimetable:
    def __init__(self, csv_file="timetable_data.csv"):
        self.df = load_data(csv_file)
        self.time_slots = generate_time_slots()
        self.classrooms = generate_classrooms()
        
    def get_lecture_blocks(self, hours):
        """Convert total hours to lecture blocks (1 hour = 1 slot)"""
        blocks = []
        if hours <= 0:
            return blocks
        
        # For 4-hour courses: 2 lectures of 2 hours each
        if hours == 4:
            blocks = [2, 2]  # Two 2-hour lectures
        elif hours == 3:
            blocks = [3]     # One 3-hour lecture
        elif hours == 2:
            blocks = [2]     # One 2-hour lecture
        elif hours == 1:
            blocks = [1]     # One 1-hour lecture
        else:
            # For other values, split into reasonable blocks
            while hours > 0:
                if hours >= 3:
                    blocks.append(3)
                    hours -= 3
                elif hours >= 2:
                    blocks.append(2)
                    hours -= 2
                else:
                    blocks.append(1)
                    hours -= 1
        
        return blocks
    
    def find_consecutive_slots(self, day, duration, used_slots):
        """Find consecutive time slots for a lecture"""
        available_slots = []
        
        # Define time slot mapping
        time_mapping = {
            '08:00-09:00': 1,
            '09:00-10:00': 2,
            '10:00-11:00': 3,
            '11:00-12:00': 4,
            '12:00-13:00': 5,
            '13:00-14:00': 6,
            '14:00-15:00': 7,
            '15:00-16:00': 8
        }
        
        reverse_mapping = {v: k for k, v in time_mapping.items()}
        
        # Check all possible starting slots
        for start_slot in range(1, 9 - duration + 1):
            consecutive = True
            slots_needed = []
            
            # Check if all needed slots are available
            for i in range(duration):
                slot_num = start_slot + i
                time_slot = reverse_mapping[slot_num]
                key = (day, time_slot)
                if key in used_slots:
                    consecutive = False
                    break
                slots_needed.append(time_slot)
            
            if consecutive:
                available_slots.append({
                    'start': reverse_mapping[start_slot],
                    'slots': slots_needed,
                    'duration': duration
                })
        
        return available_slots
    
    def create_individual(self):
        """Create a random timetable with proper durations and STRICT conflict checking."""
        timetable = []
        used_slots = set()  # Track (day, time_slot_str, room) combinations
        used_faculty_slots = set()  # Track (day, time_slot_str, faculty) combinations
        used_class_slots = set()  # Track (day, time_slot_str, class) combinations
        daily_class_hours = {}  # Track hours per class per day (max 4)
        daily_faculty_hours = {}  # Track hours per faculty per day (max 5)
        
        # Define available time slots
        available_times = ['08:00-09:00', '09:00-10:00', '10:00-11:00', 
                          '11:00-12:00', '12:00-13:00', '14:00-15:00', '15:00-16:00']
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        # Process each course
        for _, row in self.df.iterrows():
            try:
                hours = int(row['Hours']) if pd.notna(row['Hours']) else 0
            except:
                hours = 0
            
            if hours <= 0:
                continue
            
            # Get lecture blocks for this course
            lecture_blocks = self.get_lecture_blocks(hours)
            
            for block_duration in lecture_blocks:
                placed = False
                max_attempts = 100  # Increased from 50
                
                for attempt in range(max_attempts):
                    # Select a random day
                    day = random.choice(days)
                    
                    # Find consecutive slots for this duration
                    available_slots = self.find_consecutive_slots(day, block_duration, used_slots)
                    
                    if not available_slots:
                        continue  # Try another day
                    
                    # Select a random available slot
                    slot_info = random.choice(available_slots)
                    start_time = slot_info['start']
                    
                    # Calculate time range
                    start_hour = int(start_time.split(':')[0])
                    end_hour = start_hour + block_duration
                    time_range = f"{start_hour:02d}:00-{end_hour:02d}:00"
                    
                    # Select appropriate room
                    if 'Type' in row and 'Lab' in str(row['Type']):
                        available_rooms = [r for r in self.classrooms if 'Lab' in r]
                    else:
                        available_rooms = [r for r in self.classrooms if 'Lab' not in r]
                    
                    if not available_rooms:
                        continue
                    
                    room = random.choice(available_rooms)
                    
                    # Parse faculty (handle multiple faculty for labs)
                    faculties = [f.strip() for f in str(row['FacultyID']).split(';')]
                    class_name = str(row['Class'])
                    
                    # STRICT CONFLICT CHECK
                    conflict = False
                    
                    # Check all slots in the block
                    for slot in slot_info['slots']:
                        # 1. Room conflict
                        if (day, slot, room) in used_slots:
                            conflict = True
                            break
                        
                        # 2. Faculty conflicts
                        for faculty in faculties:
                            if (day, slot, faculty) in used_faculty_slots:
                                conflict = True
                                break
                        
                        # 3. Class conflict
                        if (day, slot, class_name) in used_class_slots:
                            conflict = True
                            break
                        
                        if conflict:
                            break
                    
                    if conflict:
                        continue
                    
                    # Check daily hour limits
                    daily_class_key = (class_name, day)
                    daily_faculty_key = tuple([(f, day) for f in faculties])
                    
                    class_hours_today = daily_class_hours.get(daily_class_key, 0)
                    if class_hours_today + block_duration > 4:  # Max 4 hours per day per class
                        continue
                    
                    # Check faculty hour limits
                    faculty_conflict = False
                    for faculty in faculties:
                        faculty_hours_today = daily_faculty_hours.get((faculty, day), 0)
                        if faculty_hours_today + block_duration > 5:  # Max 5 hours per day per faculty
                            faculty_conflict = True
                            break
                    
                    if faculty_conflict:
                        continue
                    
                    # If all checks pass, schedule the lecture
                    entry = {
                        'Class': class_name,
                        'Subject': str(row['Subject']),
                        'Faculty': str(row['Faculty']),
                        'Code': str(row['Code']) if 'Code' in row else '',
                        'Type': str(row['Type']) if 'Type' in row else 'Theory',
                        'Day': day,
                        'Start Time': f"{start_hour:02d}:00",
                        'End Time': f"{end_hour:02d}:00",
                        'Duration': f"{block_duration} hour{'s' if block_duration > 1 else ''}",
                        'Time Slot': time_range,
                        'Room': room,
                        'Total Hours': hours
                    }
                    
                    timetable.append(entry)
                    
                    # Mark slots as used
                    for slot in slot_info['slots']:
                        used_slots.add((day, slot, room))
                        
                        # Mark faculty slots
                        for faculty in faculties:
                            used_faculty_slots.add((day, slot, faculty))
                        
                        # Mark class slots
                        used_class_slots.add((day, slot, class_name))
                    
                    # Update daily hour counters
                    daily_class_hours[daily_class_key] = class_hours_today + block_duration
                    for faculty in faculties:
                        faculty_key = (faculty, day)
                        daily_faculty_hours[faculty_key] = daily_faculty_hours.get(faculty_key, 0) + block_duration
                    
                    placed = True
                    break
                
                if not placed:
                    # Force placement only if really necessary - respects constraints
                    for day in days:
                        for time_slot in available_times:
                            faculties = [f.strip() for f in str(row['Faculty']).split(';')]
                            class_name = str(row['Class'])
                            
                            # Quick conflict check
                            conflict = False
                            for faculty in faculties:
                                if (day, time_slot, faculty) in used_faculty_slots:
                                    conflict = True
                                    break
                            if (day, time_slot, class_name) in used_class_slots:
                                conflict = True
                            
                            if not conflict:
                                if 'Type' in row and 'Lab' in str(row['Type']):
                                    room = random.choice([r for r in self.classrooms if 'Lab' in r])
                                else:
                                    room = random.choice([r for r in self.classrooms if 'Lab' not in r])
                                
                                entry = {
                                    'Class': class_name,
                                    'Subject': str(row['Subject']),
                                    'Faculty': str(row['Faculty']),
                                    'Code': str(row['Code']) if 'Code' in row else '',
                                    'Type': str(row['Type']) if 'Type' in row else 'Theory',
                                    'Day': day,
                                    'Start Time': time_slot.split('-')[0],
                                    'End Time': time_slot.split('-')[1],
                                    'Duration': '1 hour',
                                    'Time Slot': time_slot,
                                    'Room': room,
                                    'Total Hours': hours
                                }
                                timetable.append(entry)
                                
                                # Mark as used
                                used_class_slots.add((day, time_slot, class_name))
                                for faculty in faculties:
                                    used_faculty_slots.add((day, time_slot, faculty))
                                
                                placed = True
                                break
                        if placed:
                            break
        
        return timetable
    
    def calculate_fitness(self, timetable):
        """Calculate fitness score with STRICT clash penalties."""
        if not timetable:
            return 0
        
        fitness = 1000  # Increased base fitness
        penalty = 0
        
        # Track conflicts with strict detection
        room_slots = {}
        faculty_slots = {}
        class_slots = {}
        subject_per_day = {}  # (class, subject, day) -> count
        daily_class_hours = {}  # (class, day) -> hours
        daily_faculty_hours = {}  # (faculty, day) -> hours
        
        for entry in timetable:
            # ROOM CLASH DETECTION
            key = (entry['Day'], entry['Time Slot'], entry['Room'])
            if key in room_slots:
                penalty += 100  # HEAVY penalty for room clash
            room_slots[key] = entry
            
            # FACULTY CLASH DETECTION
            faculties = [f.strip() for f in str(entry['Faculty']).split(';')]
            for faculty in faculties:
                fkey = (entry['Day'], entry['Time Slot'], faculty)
                if fkey in faculty_slots:
                    penalty += 75  # HEAVY penalty for faculty clash
                faculty_slots[fkey] = entry
            
            # CLASS CLASH DETECTION
            ckey = (entry['Day'], entry['Time Slot'], entry['Class'])
            if ckey in class_slots:
                penalty += 80  # HEAVY penalty for class clash
            class_slots[ckey] = entry
            
            # Check subject per day (max 1 per class per day)
            subject_key = (entry['Class'], entry['Subject'], entry['Day'])
            subject_per_day[subject_key] = subject_per_day.get(subject_key, 0) + 1
            if subject_per_day[subject_key] > 1:
                penalty += 50  # Penalty for multiple same subjects per day
            
            # Check daily hours per class (max 4 hours)
            class_day_key = (entry['Class'], entry['Day'])
            try:
                duration = int(entry['Duration'].split()[0])
            except:
                duration = 1
            daily_class_hours[class_day_key] = daily_class_hours.get(class_day_key, 0) + duration
            if daily_class_hours[class_day_key] > 4:
                penalty += 40  # Penalty for exceeding 4 hours per class per day
            
            # Check daily hours per faculty (max 5 hours)
            for faculty in faculties:
                faculty_day_key = (faculty, entry['Day'])
                daily_faculty_hours[faculty_day_key] = daily_faculty_hours.get(faculty_day_key, 0) + duration
                if daily_faculty_hours[faculty_day_key] > 5:
                    penalty += 30  # Penalty for exceeding 5 hours per faculty per day
        
        # Check if total hours match requirements
        total_required_hours = 0
        total_scheduled_hours = 0
        
        for _, row in self.df.iterrows():
            try:
                required_hours = int(row['Hours']) if pd.notna(row['Hours']) else 0
            except:
                required_hours = 0
            
            if required_hours > 0:
                total_required_hours += required_hours
                scheduled_hours = sum(1 for entry in timetable 
                                    if str(entry['Class']) == str(row['Class']) 
                                    and str(entry['Subject']) == str(row['Subject']))
                
                total_scheduled_hours += scheduled_hours
                
                if scheduled_hours < required_hours:
                    penalty += (required_hours - scheduled_hours) * 10
        
        fitness -= penalty
        return max(fitness, 1)
    
    def run(self, generations=150, population_size=100):
        """Run genetic algorithm with STRICT constraint satisfaction."""
        # Create initial population
        population = []
        for _ in range(population_size):
            population.append(self.create_individual())
        
        best_individual = None
        best_fitness = 0
        generations_without_improvement = 0
        
        for gen in range(generations):
            # Evaluate fitness for all individuals
            fitness_scores = []
            for individual in population:
                fitness = self.calculate_fitness(individual)
                fitness_scores.append(fitness)
                
                if fitness > best_fitness:
                    best_fitness = fitness
                    best_individual = individual
                    generations_without_improvement = 0
            
            # Early stopping if no improvement
            generations_without_improvement += 1
            if generations_without_improvement > 20 and best_fitness > 500:
                # We have a good solution, apply repairs
                if best_individual:
                    best_individual = self.repair_clashes(best_individual)
                break
            
            # Selection (elitism + tournament)
            if len(population) > 2:
                # Keep top 10% as elite
                elite_count = max(2, population_size // 10)
                indexed_fitness = [(i, fitness_scores[i]) for i in range(len(fitness_scores))]
                indexed_fitness.sort(key=lambda x: x[1], reverse=True)
                
                elite_indices = [idx for idx, _ in indexed_fitness[:elite_count]]
                new_population = [population[i] for i in elite_indices]
                
                # Tournament selection for rest
                while len(new_population) < population_size:
                    tournament_size = min(5, len(population))
                    tournament_indices = random.sample(range(len(population)), tournament_size)
                    tournament_fitness = [(idx, fitness_scores[idx]) for idx in tournament_indices]
                    tournament_fitness.sort(key=lambda x: x[1], reverse=True)
                    
                    winner_idx = tournament_fitness[0][0]
                    new_population.append(population[winner_idx])
                
                population = new_population[:population_size]
            
            # Mutation (lower rate to preserve good solutions)
            for i in range(1, len(population)):
                if random.random() < 0.05:  # 5% mutation rate
                    population[i] = self.create_individual()
        
        # Apply final repair to best solution
        if best_individual:
            best_individual = self.repair_clashes(best_individual)
            best_fitness = self.calculate_fitness(best_individual)
        
        return best_individual, best_fitness
    
    def get_statistics(self, timetable):
        """Get statistics about generated timetable."""
        if not timetable:
            return {}
        
        df_timetable = pd.DataFrame(timetable)
        
        stats = {
            'total_classes': len(timetable),
            'unique_classes': df_timetable['Class'].nunique(),
            'unique_faculty': df_timetable['Faculty'].nunique(),
            'rooms_used': df_timetable['Room'].nunique(),
            'total_hours_scheduled': df_timetable['Total Hours'].sum() if 'Total Hours' in df_timetable.columns else 0,
        }
        
        # Calculate duration distribution
        if 'Duration' in df_timetable.columns:
            duration_counts = df_timetable['Duration'].value_counts()
            stats['duration_distribution'] = dict(duration_counts)
        
        # Calculate room utilization
        room_usage = df_timetable['Room'].value_counts().to_dict()
        stats['room_utilization'] = room_usage
        
        return stats