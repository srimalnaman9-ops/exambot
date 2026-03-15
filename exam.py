import streamlit as st
import google.generativeai as genai
import sqlite3
import json
import pandas as pd
import plotly.express as px
import datetime
import hashlib
import random
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

# =============================================================================
# 1. PAGE CONFIG & THEME
# =============================================================================
st.set_page_config(page_title="Exam Ascent AI", layout="wide", page_icon="🎓")

# Professional Dark UI Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stButton>button { 
        background: linear-gradient(90deg, #4F46E5, #7C3AED); 
        color: white; border-radius: 12px; font-weight: 600; height: 3.5em; width: 100%; border: none;
    }
    .main-card { 
        background-color: #1e1e2f; padding: 25px; border-radius: 18px; 
        border-left: 8px solid #6366F1; margin-bottom: 20px; color: #ffffff;
    }
    .mark-scheme { 
        background-color: #064E3B; padding: 20px; border-radius: 12px; 
        border: 1px solid #10B981; margin-top: 15px; color: #ECFDF5;
    }
    .timetable-card {
        background-color: #111827; border: 1px solid #374151; padding: 15px; 
        border-radius: 12px; margin-bottom: 10px; border-top: 4px solid #F59E0B;
    }
    .formula-box {
        background-color: #0f172a; padding: 15px; border-radius: 8px; border: 1px dashed #38bdf8;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. DATABASE ORCHESTRATION
# =============================================================================
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect("exam_vault.db", check_same_thread=False)
        self.init_db()

    def init_db(self):
        cursor = self.conn.cursor()
        # Table for results
        cursor.execute('CREATE TABLE IF NOT EXISTS results (subject TEXT, topic TEXT, score INTEGER, total INTEGER, type TEXT, date TIMESTAMP)')
        # Table for saved/weak topics
        cursor.execute('CREATE TABLE IF NOT EXISTS progress (subject TEXT, topic TEXT, mastery REAL, PRIMARY KEY(subject, topic))')
        self.conn.commit()

    def save_result(self, sub, top, score, total, q_type):
        self.conn.execute("INSERT INTO results VALUES (?, ?, ?, ?, ?, ?)", 
                          (sub, top, score, total, q_type, datetime.datetime.now()))
        self.conn.commit()

db = DatabaseManager()

# =============================================================================
# 3. AI EXAM ENGINE (GEMINI PRO / FLASH)
# =============================================================================
class AIEngine:
    def __init__(self):
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("API Key not found in Streamlit Secrets!")
            st.stop()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self._detect_model())

    def _detect_model(self):
        try:
            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            return "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available else "models/gemini-pro"
        except: return "gemini-1.5-flash"

    def generate_question(self, subject, topic, q_type, difficulty="HL"):
        # Chemistry logic: Force SL, others HL
        curriculum = "IB SL" if subject == "Chemistry" else f"IB {difficulty}"
        
        prompt = f"""
        Act as an IB examiner. Create an original {curriculum} {subject} question on '{topic}'.
        Style: Inspired by Revision Village and Save My Exams.
        Type: {q_type} (MCQ or Multi-part Structured).
        
        Constraint: Use LaTeX for ALL math ($...$). 
        For MCQ: Provide 4 options, 1 correct answer, and explanation.
        For Structured: Provide parts (a, b, c), full model answer, and detailed mark scheme.
        
        Return ONLY valid JSON:
        {{
            "question": "Scenario-based narrative question...",
            "options": ["A", "B", "C", "D"],
            "answer": "Correct string",
            "explanation": "IB Mark Scheme showing point allocation (M1, A1, R1)..."
        }}
        """
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            return data
        except: return None

# =============================================================================
# 4. MODULES: KNOWLEDGE VAULT & SCHEDULE
# =============================================================================

ASSESSMENT_SCHEDULE = [
    {"Date": "2026-03-25", "Sub": "Physics", "Paper": "I", "Focus": "Mechanics A.1-A.5", "Dur": "2.0 hrs", "Marks": 60},
    {"Date": "2026-03-26", "Sub": "Physics", "Paper": "II", "Focus": "Thermal/Waves B.1-B.5", "Dur": "2.5 hrs", "Marks": 90},
    {"Date": "2026-03-28", "Sub": "Chemistry", "Paper": "I", "Focus": "Structure: 1, 2 & 3", "Dur": "1.5 hrs", "Marks": 30},
    {"Date": "2026-04-06", "Sub": "Mathematics", "Paper": "I", "Focus": "Unit 1: Number & Algebra", "Dur": "2.0 hrs", "Marks": 110},
    {"Date": "2026-04-07", "Sub": "Mathematics", "Paper": "II", "Focus": "Unit 2: Functions, Unit 3: Trig", "Dur": "2.0 hrs", "Marks": 110},
]

def render_vault(subject):
    st.header(f"📚 {subject} Knowledge Vault")
    
    if subject == "Mathematics":
        with st.expander("🔢 Unit 1: Number & Algebra", expanded=True):
            st.subheader("Key Terms")
            st.write("Arithmetic Sequence, Geometric Progression, Logarithm, Binomial Expansion.")
            st.subheader("Formula Sheet")
            st.markdown("""<div class='formula-box'>
            $u_n = u_1 + (n-1)d$ <br>
            $S_n = \\frac{n}{2}(u_1 + u_n)$ <br>
            $FV = PV \\times (1 + \\frac{r}{100k})^{kn}$
            </div>""", unsafe_allow_html=True)
            st.subheader("Exam Tips")
            st.warning("Ensure your GDC is in Radians mode for Trigonometry questions unless specified otherwise!")

    elif subject == "Physics":
        with st.expander("⚛️ Mechanics (A.1 - A.5)", expanded=True):
            st.subheader("Concept Summary")
            st.write("Dynamics and Kinematics. Understanding forces, SUVAT, and projectile motion.")
            
            st.subheader("Worked Example")
            st.info("Calculate the displacement of a ball thrown at $20 ms^{-1}$ at an angle of $30^{\circ}$ after 2 seconds.")
            st.markdown("**IB Tip:** Always resolve vectors into horizontal and vertical components before applying SUVAT.")

# =============================================================================
# 5. MAIN UI NAVIGATION
# =============================================================================
def main():
    ai = AIEngine()
    
    st.sidebar.title("🚀 Exam Ascent AI")
    page = st.sidebar.radio("Navigation", 
        ["Dashboard", "Exam Timetable", "Knowledge Vault", "Practice Lab", "Mock Exams", "Progress Analytics"])

    if page == "Dashboard":
        st.title("Welcome back, Candidate!")
        # Countdown
        next_exam = datetime.datetime.strptime(ASSESSMENT_SCHEDULE[0]['date'], "%Y-%m-%d")
        delta = (next_exam - datetime.datetime.now()).days
        st.metric("Countdown to First Exam (Physics)", f"{delta} Days")
        
        # Recent Performance
        df = pd.read_sql("SELECT * FROM results", db.conn)
        if not df.empty:
            st.subheader("Recent Activity")
            st.table(df.tail(3))

    elif page == "Exam Timetable":
        st.title("🗓️ Final Ascent Assessment 2025-26")
        for exam in ASSESSMENT_SCHEDULE:
            st.markdown(f"""
            <div class='timetable-card'>
                <div style='display: flex; justify-content: space-between;'>
                    <strong>{exam['Date']}</strong>
                    <span style='color: #6366F1;'>{exam['Dur']}</span>
                </div>
                <h3 style='margin: 5px 0;'>{exam['Sub']} (Paper {exam['Paper']})</h3>
                <p>Focus: {exam['Focus']} | <strong>Marks: {exam['Marks']}</strong></p>
            </div>
            """, unsafe_allow_html=True)

    elif page == "Knowledge Vault":
        sub = st.selectbox("Select Subject", ["Mathematics", "Physics", "Chemistry"])
        render_vault(sub)

    elif page == "Practice Lab":
        st.title("🧪 Practice Lab")
        c1, c2 = st.columns(2)
        sub = c1.selectbox("Subject", ["Mathematics", "Physics", "Chemistry", "English"])
        q_type = c2.radio("Question Style", ["MCQ", "Structured Question (SQ)"])
        
        # Portion Selection based on Schedule
        topics = {
            "Mathematics": ["Algebra", "Functions", "Trigonometry"],
            "Physics": ["Mechanics A.1-A.5", "Fields B.1-B.5"],
            "Chemistry": ["Structure 1, 2 & 3"],
            "English": ["Proposal Writing", "Journal Entry", "Blog Analysis"]
        }
        topic = st.selectbox("Topic Focus", topics[sub])

        if st.button("Generate Exam Scenario"):
            with st.spinner("AI is researching patterns from Revision Village..."):
                st.session_state.current_q = ai.generate_question(sub, topic, q_type)
                st.session_state.answered = False

        if "current_q" in st.session_state and st.session_state.current_q:
            q = st.session_state.current_q
            st.markdown(f"<div class='main-card'><h3>{q['question']}</h3></div>", unsafe_allow_html=True)
            
            if q_type == "MCQ":
                user_ans = st.radio("Choose Option:", q['options'], index=None)
                if st.button("Submit Answer"):
                    st.session_state.answered = True
                    if user_ans == q['answer']:
                        st.success("🎯 Correct! Well done.")
                        db.save_result(sub, topic, 1, 1, "MCQ")
                    else:
                        st.error(f"❌ Incorrect. The correct answer is: {q['answer']}")
                        db.save_result(sub, topic, 0, 1, "MCQ")
            else:
                st.info("Write your solution. Click below to reveal the mark scheme.")
                if st.button("Reveal Model Answer"):
                    st.session_state.answered = True
            
            if st.session_state.get('answered'):
                st.markdown("---")
                st.markdown(f"<div class='mark-scheme'><strong>IB Mark Scheme & Explanation:</strong><br>{q['explanation']}</div>", unsafe_allow_html=True)

    elif page == "Progress Analytics":
        st.title("📊 Progress Analytics")
        df = pd.read_sql("SELECT * FROM results", db.conn)
        if not df.empty:
            # Accuracy Chart
            acc_df = df.groupby('subject').apply(lambda x: (x['score'].sum() / x['total'].sum()) * 100).reset_index(name='Accuracy')
            fig = px.bar(acc_df, x='subject', y='Accuracy', color='subject', title="Accuracy by Subject (%)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Trend Chart
            df['date'] = pd.to_datetime(df['date'])
            fig2 = px.line(df, x='date', y='score', color='subject', title="Performance Trend")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Complete some Practice Lab questions to see your analytics!")

if __name__ == "__main__":
    main()
