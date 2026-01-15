import streamlit as st
import pandas as pd
from src.ga_timetable import GeneticAlgorithmTimetable

# Set page config
st.set_page_config(page_title="Timetable Scheduler", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
    <style>
        .main-header {
            font-size: 3em;
            color: #2E86AB;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: bold;
        }
        .sub-header {
            font-size: 1.5em;
            color: #A23B72;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #A23B72;
            padding-bottom: 0.5rem;
        }
        .fitness-box {
            background-color: #C6DE41;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        .section-title {
            background-color: #F18F01;
            color: white;
            padding: 0.8rem;
            border-radius: 0.5rem;
            font-weight: bold;
            margin-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">📚 INTELLIGENT TIMETABLE GA SYSTEM</div>', unsafe_allow_html=True)

# Sidebar controls
st.sidebar.header("⚙️ Configuration")
generations = st.sidebar.slider("Generations", 10, 100, 50)
population_size = st.sidebar.slider("Population Size", 5, 50, 20)

# Generate timetable button
if st.sidebar.button("🚀 Generate Timetable", key="generate"):
    with st.spinner("Generating timetable..."):
        ga = GeneticAlgorithmTimetable(csv_file="timetable_data.csv")
        timetable, fitness = ga.run(generations=generations, population_size=population_size)
        
        if timetable:
            df_tt = pd.DataFrame(timetable)
            df_tt.to_csv("final_timetable.csv", index=False)
            
            # Store in session state
            st.session_state.df_timetable = df_tt
            st.session_state.fitness = fitness
            st.success("✅ Timetable generated successfully!")
        else:
            st.error("❌ Failed to generate timetable!")

# Check if timetable exists in session
if 'df_timetable' in st.session_state:
    df_tt = st.session_state.df_timetable
    fitness = st.session_state.fitness
    
    # Display fitness
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f'<div class="fitness-box">Fitness Score: {fitness}</div>', unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Daily Schedule", "📚 Subjects", "🏫 By Section", "👨‍🏫 By Faculty", "📥 Download"])
    
    # Tab 1: Daily Schedule
    with tab1:
        st.markdown('<div class="sub-header">Complete Timetable by Day</div>', unsafe_allow_html=True)
        
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        for day in days_order:
            day_tt = df_tt[df_tt['Day'] == day].sort_values(['Start Time'])
            if len(day_tt) > 0:
                st.markdown(f'<div class="section-title">{day}</div>', unsafe_allow_html=True)
                
                # Select columns to display
                display_cols = ['Time Slot', 'Class', 'Subject', 'Faculty', 'Room', 'Type']
                st.dataframe(
                    day_tt[display_cols],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Time Slot": st.column_config.TextColumn("⏰ Time Slot"),
                        "Class": st.column_config.TextColumn("👥 Class"),
                        "Subject": st.column_config.TextColumn("📖 Subject"),
                        "Faculty": st.column_config.TextColumn("👨‍🏫 Faculty"),
                        "Room": st.column_config.TextColumn("🏛️ Room"),
                        "Type": st.column_config.TextColumn("📝 Type"),
                    }
                )
    
    # Tab 2: Subjects by Section
    with tab2:
        st.markdown('<div class="sub-header">Subjects by Section</div>', unsafe_allow_html=True)
        
        sections = sorted(df_tt['Class'].unique())
        
        for section in sections:
            section_tt = df_tt[df_tt['Class'] == section]
            subjects = section_tt[['Subject', 'Code', 'Type']].drop_duplicates().sort_values(['Subject'])
            
            with st.expander(f"📚 {section} ({len(subjects)} Subjects)"):
                st.dataframe(
                    subjects,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Subject": st.column_config.TextColumn("📖 Subject"),
                        "Code": st.column_config.TextColumn("🔢 Code"),
                        "Type": st.column_config.TextColumn("📝 Type"),
                    }
                )
    
    # Tab 3: Section-wise Timetable
    with tab3:
        st.markdown('<div class="sub-header">Timetable by Section</div>', unsafe_allow_html=True)
        
        sections = sorted(df_tt['Class'].unique())
        selected_section = st.selectbox("Select Section", sections, key="section_select")
        
        section_tt = df_tt[df_tt['Class'] == selected_section]
        
        st.markdown(f'<div class="section-title">{selected_section}</div>', unsafe_allow_html=True)
        
        # Show subjects first
        st.write("**Subjects Offered:**")
        subjects = section_tt[['Subject', 'Code', 'Type']].drop_duplicates().sort_values(['Subject'])
        st.dataframe(subjects, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Show timetable by day
        st.write("**Weekly Schedule:**")
        
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        for day in days_order:
            day_tt = section_tt[section_tt['Day'] == day].sort_values(['Start Time'])
            if len(day_tt) > 0:
                st.markdown(f'<div class="section-title">{day}</div>', unsafe_allow_html=True)
                
                display_cols = ['Time Slot', 'Subject', 'Faculty', 'Room', 'Type']
                st.dataframe(
                    day_tt[display_cols],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Time Slot": st.column_config.TextColumn("⏰ Time"),
                        "Subject": st.column_config.TextColumn("📖 Subject"),
                        "Faculty": st.column_config.TextColumn("👨‍🏫 Faculty"),
                        "Room": st.column_config.TextColumn("🏛️ Room"),
                        "Type": st.column_config.TextColumn("📝 Type"),
                    }
                )
            else:
                st.info(f"No classes scheduled on {day}")
    
    # Tab 4: Faculty-wise Timetable
    with tab4:
        st.markdown('<div class="sub-header">Timetable by Faculty</div>', unsafe_allow_html=True)
        
        # Get unique faculty members
        faculty_list = sorted(df_tt['Faculty'].unique())
        selected_faculty = st.selectbox("Select Faculty Member", faculty_list, key="faculty_select")
        
        # Filter timetable for selected faculty
        faculty_tt = df_tt[df_tt['Faculty'] == selected_faculty]
        
        st.markdown(f'<div class="section-title">👨‍🏫 {selected_faculty}</div>', unsafe_allow_html=True)
        
        # Show teaching summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Classes", len(faculty_tt))
        with col2:
            st.metric("Sections", len(faculty_tt['Class'].unique()))
        with col3:
            st.metric("Subjects", len(faculty_tt['Subject'].unique()))
        with col4:
            st.metric("Rooms", len(faculty_tt['Room'].unique()))
        
        st.divider()
        
        # Show subjects taught
        st.write("**Subjects Taught:**")
        subjects_taught = faculty_tt[['Subject', 'Code', 'Class', 'Type']].drop_duplicates().sort_values(['Subject'])
        st.dataframe(subjects_taught, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Show weekly schedule
        st.write("**Weekly Schedule:**")
        
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        for day in days_order:
            day_tt = faculty_tt[faculty_tt['Day'] == day].sort_values(['Start Time'])
            if len(day_tt) > 0:
                st.markdown(f'<div class="section-title">{day}</div>', unsafe_allow_html=True)
                
                display_cols = ['Time Slot', 'Subject', 'Class', 'Room', 'Type']
                st.dataframe(
                    day_tt[display_cols],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Time Slot": st.column_config.TextColumn("⏰ Time"),
                        "Subject": st.column_config.TextColumn("📖 Subject"),
                        "Class": st.column_config.TextColumn("👥 Class"),
                        "Room": st.column_config.TextColumn("🏛️ Room"),
                        "Type": st.column_config.TextColumn("📝 Type"),
                    }
                )
            else:
                st.info(f"No classes scheduled on {day}")
    
    # Tab 5: Download
    with tab5:
        st.markdown('<div class="sub-header">Download Timetable</div>', unsafe_allow_html=True)
        
        # CSV download
        csv = df_tt.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="timetable.csv",
            mime="text/csv"
        )
        
        # Excel download
        try:
            excel_buffer = pd.ExcelWriter("temp_timetable.xlsx", engine='openpyxl')
            df_tt.to_excel(excel_buffer, sheet_name='Timetable', index=False)
            excel_buffer.close()
            
            with open("temp_timetable.xlsx", "rb") as f:
                st.download_button(
                    label="📊 Download as Excel",
                    data=f.read(),
                    file_name="timetable.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except:
            st.warning("Excel export not available")
        
        # Display stats
        st.divider()
        st.write("**📊 Timetable Statistics:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Classes", len(df_tt))
        with col2:
            st.metric("Sections", len(df_tt['Class'].unique()))
        with col3:
            st.metric("Faculty Members", len(df_tt['Faculty'].unique()))
        with col4:
            st.metric("Rooms Used", len(df_tt['Room'].unique()))

else:
    st.info("👈 Click 'Generate Timetable' button in the sidebar to get started!")
    
    # Show sample data info
    st.markdown('<div class="sub-header">About This System</div>', unsafe_allow_html=True)
    st.write("""
    This intelligent timetable scheduling system uses **Genetic Algorithm** to:
    
    ✅ Avoid scheduling conflicts (rooms, faculty, classes)
    ✅ Distribute lectures and labs across different days
    ✅ Respect faculty and class workload limits
    ✅ Optimize classroom utilization
    
    **Features:**
    - 📊 Interactive dashboard with multiple views
    - 🔍 Search and filter by section
    - 📥 Download results as CSV or Excel
    - 📈 Real-time fitness score tracking
    """)
