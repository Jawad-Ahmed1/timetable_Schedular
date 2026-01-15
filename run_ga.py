from src.ga_timetable import GeneticAlgorithmTimetable
import pandas as pd

def main():
    print("======================================================================")
    print("INTELLIGENT TIMETABLE SCHEDULING SYSTEM")
    print("Using Genetic Algorithm with Clash Resolution")
    print("======================================================================\n")
    
    ga = GeneticAlgorithmTimetable(csv_file="timetable_data.csv")
    
    print("📂 Loading data from timetable_data.csv...")
    print(f"Columns loaded: {ga.df.columns.tolist()}\n")
    
    print("🧬 Running Genetic Algorithm...")
    timetable, fitness = ga.run(generations=150, population_size=50)
    
    if timetable:
        print(f"\n✅ Timetable generated successfully! Fitness Score: {fitness}")
        df_tt = pd.DataFrame(timetable)
        df_tt.to_csv("final_timetable.csv", index=False)
        print("📄 Timetable saved as final_timetable.csv\n")
        
        # Show timetable per class
        print("📊 Daily Timetable per Class:\n")
        classes = df_tt['Class'].unique()
        for cls in classes:
            print(f"--- {cls} ---")
            cls_tt = df_tt[df_tt['Class'] == cls].sort_values(['Day', 'Start Time'])
            print(cls_tt[['Day', 'Time Slot', 'Subject', 'Faculty', 'Room']].to_string(index=False))
            print("\n")
    else:
        print("❌ Failed to generate a timetable!")

if __name__ == "__main__":
    main()
