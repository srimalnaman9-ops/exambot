import streamlit as st
import google.generativeai as genai
import sqlite3
import json
import pandas as pd
import plotly.express as px
import time
import datetime
import hashlib
from typing import List, Optional
from dataclasses import dataclass, asdict

# =============================================================================
# 1. PAGE & STYLE CONFIG
# =============================================================================
st.set_page_config(page_title="Exam Ascent AI", layout="wide", page_icon="🧪")

# Custom CSS for UI
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stButton>button { 
        background: linear-gradient(90deg, #4F46E5, #7C3AED); 
        color: white; border: none; font-weight: bold; height: 3.5em; width: 100%; border-radius: 12px;
    }
    .q-card { 
        background-color: #1e1e2f; padding: 30px; border-radius: 18px; 
        border-left: 8px solid #6366F1; margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .mark-scheme { 
        background-color: #064E3B; padding: 25px; border-radius: 12px; 
        border: 1px solid #10B981; margin-top: 20px; color: #ECFDF5;
    }
    .timetable-card {
        background-color: #f8fafc; color: #1e293b; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4F46E5;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. DATA MODELS & DATABASE
# =============================================================================
@dataclass
class Question:
    id: str
    subject: str
    topic: str
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty: str

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect("exam_data.db", check_same_thread=False)
        self.init_db()

    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS results (subject TEXT, topic TEXT, score INTEGER, date TIMESTAMP)')
        cursor.execute('CREATE TABLE IF NOT EXISTS saved (id TEXT PRIMARY KEY, subject TEXT, topic TEXT, data TEXT)')
        self.conn.commit()

    def save_score(self, sub, top, score):
        self.conn.execute("INSERT INTO results VALUES (?, ?, ?, ?)", (sub, top, score, datetime.datetime.now()))
        self.conn.commit()

    def save_question(self, q: Question):
        self.conn.execute("INSERT OR REPLACE INTO saved VALUES (?, ?, ?, ?)", (q.id, q.subject, q.topic, json.dumps(asdict(q))))
        self.conn.commit()

db = DatabaseManager()

# =============================================================================
# 3. AI ENGINE (AUTO-MODEL + NARRATIVE PROMPTING)
# =============================================================================
class AIEngine:
    def __init__(self):
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("API Key not found!")
            st.stop()
        genai.configure(api_key=api_key)
        self.model_name = self._detect_best_model()
        self.model = genai.GenerativeModel(self.model_name)

    def _detect_best_model(self):
        try:
            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            for target in ['models/gemini-1.5-flash', 'models/gemini-pro']:
                if target in available: return target
            return available[0]
        except:
            return "gemini-1.5-flash"

    def generate(self, subject, topic, level):
        level_label = "Standard Level (SL)" if subject == "Chemistry" else "Higher Level (HL)"
        
        # FIXED: Prompt explicitly demands multi-sentence narrative word problems
        prompt = f"""
        Act as an IB Senior Examiner. Research patterns from Revision Village and Save My Exams.
        Create a complex {level_label} {subject} exam question for the topic: {topic}.
        
        STRICT RULES:
        1. The 'question' must be a multi-sentence narrative word problem (like a real exam).
        2. Do NOT just output numbers. Describe a physical or mathematical scenario.
        3. Use LaTeX for ALL math symbols ($...$).
        4. Provide an IB-style Mark Scheme for the explanation.
        
        Return ONLY JSON:
        {{
            "question": "Narrative question text here...",
            "options": ["A", "B", "C", "D"],
            "answer": "correct string",
            "explanation": "Step-by-step marking guide..."
        }}
        """
        try:
            response = self.model.generate_content(prompt)
            clean_json = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(clean_json)
            return Question(
                id=hashlib.md5(data['question'].encode()).hexdigest()[:10],
                subject=subject, topic=topic,
                question_text=data['question'],
                options=data['options'],
                correct_answer=data['answer'],
                explanation=data['explanation'],
                difficulty=str(level)
            )
        except: return None

# =============================================================================
# 4. UI LOGIC (WITH TIMETABLE & CHECKLIST)
# =============================================================================
def main():
    st.sidebar.title("🚀 Exam Ascent AI")
    st.sidebar.info(f"Engine: {AIEngine().model_name}")
    
    # PDF TIMETABLE DATA 
    assessment_data = [
        {"Date": "25.03.2026", "Sub": "Physics P-I", "Portion": "A.1 to A.5", "Time": "2 hrs"},
        {"Date": "26.03.2026", "Sub": "Physics P-II", "Portion": "B.1 to B.5", "Time": "2.30 hrs"},
        {"Date": "28.03.2026", "Sub": "Chemistry P-I", "Portion": "Structure: 1, 2 & 3", "Time": "1.30 hrs"},
        {"Date": "06.04.2026", "Sub": "Maths P-I", "Portion": "Unit 1: Number & Algebra", "Time": "2 hrs"},
        {"Date": "07.04.2026", "Sub": "Maths P-II/III", "Portion": "Unit 2 & 3 (Trig)", "Time": "2 hrs/1.15 hrs"},
        {"Date": "09.04.2026", "Sub": "English P-I", "Portion": "Writing Tasks", "Time": "1.15 hrs"},
        {"Date": "10.04.2026", "Sub": "English P-II", "Portion": "Reading & Listening", "Time": "1.45 hrs"}
    ]

    page = st.sidebar.radio("Navigate", ["Dashboard", "Final Schedule", "Portion Checklist", "Practice Lab", "Revision Bank"])
    ai = AIEngine()

    if page == "Dashboard":
        st.title("Jain Vidyalaya Readiness")
        # Countdown to first exam
        days_left = (datetime.datetime(2026, 3, 25) - datetime.datetime.now()).days
        st.metric("Countdown to Physics", f"{days_left} Days")
        
        df = pd.read_sql("SELECT * FROM results", db.conn)
        if not df.empty:
            fig = px.line(df, x='date', y='score', color='subject', title="Score Trends")
            st.plotly_chart(fig, use_container_width=True)

    elif page == "Final Schedule":
        st.title("🗓️ Final Ascent Assessment 2025-26")
        for item in assessment_data:
            st.markdown(f"""
            <div class="timetable-card">
                <strong>{item['Date']}</strong> | {item['Sub']} ({item['Time']})<br>
                <small>Focus: {item['Portion']}</small>
            </div>
            """, unsafe_allow_html=True)

    elif page == "Portion Checklist":
        st.title("✅ Syllabus Checklist")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Physics & Chemistry")
            st.checkbox("A.1 to A.5 (Physics Paper I)") [cite: 6]
            st.checkbox("B.1 to B.5 (Physics Paper II)") [cite: 6]
            st.checkbox("Structure: 1, 2, 3 (Chemistry)") [cite: 6]
        with col2:
            st.subheader("Math & English")
            st.checkbox("Unit 1: Number & Algebra") [cite: 6]
            st.checkbox("Unit 2: Functions") [cite: 6]
            st.checkbox("Unit 3: Trigonometry") [cite: 6]
            st.checkbox("English Writing: Blog, Proposal, Essay, etc.") [cite: 6]

    elif page == "Practice Lab":
        st.title("🧪 Practice Lab")
        c1, c2, c3 = st.columns(3)
        sub = c1.selectbox("Subject", ["Mathematics", "Physics", "Chemistry", "English"])
        
        # Syllabus maps based on assessment schedule 
        syllabus = {
            "Physics": ["Mechanics A.1-A.5", "Fields & Thermal B.1-B.5"],
            "Chemistry": ["Structure 1: Particles", "Structure 2: Bonding", "Structure 3: Periodicity"],
            "Mathematics": ["Unit 1: Algebra", "Unit 2: Functions", "Unit 3: Trigonometry"],
            "English": ["Formal Letter", "Journal Entry", "Proposal", "Essay", "Blog"]
        }
        top = c2.selectbox("Focus Topic", syllabus[sub])
        lvl = c3.slider("Difficulty", 1, 5, 3)

        if st.button("Generate Exam Question"):
            with st.spinner("AI Generating Narrative Scenario..."):
                st.session_state.current_q = ai.generate(sub, top, lvl)
                st.session_state.submitted = False

        if "current_q" in st.session_state and st.session_state.current_q:
            q = st.session_state.current_q
            st.markdown(f"<div class='q-card'><h3>{q.question_text}</h3></div>", unsafe_allow_html=True)
            
            user_input = st.radio("Choose Answer:", q.options, index=None)
            
            if st.button("Check Answer"):
                st.session_state.submitted = True
                if user_input == q.correct_answer:
                    st.success("🎯 Correct!")
                    db.save_score(sub, top, 1)
                else:
                    st.error(f"❌ Incorrect. Answer: {q.correct_answer}")
                    db.save_score(sub, top, 0)

            if st.session_state.get('submitted'):
                st.markdown("---")
                st.markdown(f"<div class='mark-scheme'><strong>IB Mark Scheme:</strong><br>{q.explanation}</div>", unsafe_allow_html=True)

    elif page == "Revision Bank":
        st.title("🔖 Saved Bank")
        df_saved = pd.read_sql("SELECT * FROM saved", db.conn)
        for _, row in df_saved.iterrows():
            data = json.loads(row['data'])
            with st.expander(f"{row['subject']} - {row['topic']}"):
                st.write(data['question_text'])
                st.info(data['explanation'])

if __name__ == "__main__":
    main()
