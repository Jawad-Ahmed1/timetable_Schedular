class TimetableConstraints:
    def __init__(self):
        self.fixed_slots = {
            'Math': ('Monday', '08:00-09:00'),
            'ESC': ('Friday', '10:00-11:00'),
        }
    
    def check_clashes(self, timetable):
        """Check for any clashes in timetable."""
        clashes = []
        
        # Check for same room same time
        room_time = {}
        for i, entry in enumerate(timetable):
            key = (entry['Day'], entry['Time'], entry['Room'])
            if key in room_time:
                clashes.append(f"Room clash: {entry['Room']} at {entry['Day']} {entry['Time']}")
            room_time[key] = entry
        
        # Check for same faculty same time
        faculty_time = {}
        for i, entry in enumerate(timetable):
            key = (entry['Day'], entry['Time'], entry['Faculty'])
            if key in faculty_time:
                clashes.append(f"Faculty clash: {entry['Faculty']} at {entry['Day']} {entry['Time']}")
            faculty_time[key] = entry
        
        return clashes
    
    def calculate_fitness(self, timetable):
        """Calculate fitness score."""
        fitness = 100
        
        # Penalize clashes
        clashes = self.check_clashes(timetable)
        fitness -= len(clashes) * 10
        
        # Check room utilization
        room_usage = {}
        for entry in timetable:
            room = entry['Room']
            room_usage[room] = room_usage.get(room, 0) + 1
        
        # Penalize underutilized rooms
        for usage in room_usage.values():
            if usage < 2:
                fitness -= 5
        
        return max(fitness, 1)