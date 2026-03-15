import streamlit as st
import sqlite3
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import datetime
import hashlib
from typing import Dict, List, Tuple, Optional
import google.generativeai as genai
from dataclasses import dataclass, asdict
from enum import Enum
import random
import os

# =============================================================================
# DATA CLASSES & ENUMS
# =============================================================================

class Subject(Enum):
    MATHEMATICS = "Mathematics"
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    ENGLISH = "English"

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

@dataclass
class StudySession:
    user_id: str
    subject: str
    duration: int
    timestamp: str

# =============================================================================
# DATABASE MANAGER
# =============================================================================

class DatabaseManager:
    def __init__(self, db_path: str = "ibcp_exam_prep.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT)')
        cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_results (
            id TEXT PRIMARY KEY, user_id TEXT, subject TEXT, topic TEXT, 
            score INTEGER, total INTEGER, timestamp TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS saved_questions (
            id TEXT PRIMARY KEY, user_id TEXT, subject TEXT, topic TEXT, question_data TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS study_sessions (
            user_id TEXT, subject TEXT, duration INTEGER, timestamp TIMESTAMP)''')
        conn.commit()
        conn.close()

    def save_result(self, user_id, subject, topic, score, total):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        res_id = hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()[:8]
        cursor.execute("INSERT INTO quiz_results VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (res_id, user_id, subject, topic, score, total, datetime.datetime.now()))
        conn.commit()
        conn.close()

    def save_question(self, user_id, question: Question):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO saved_questions VALUES (?, ?, ?, ?, ?)",
                       (question.id, user_id, question.subject, question.topic, json.dumps(asdict(question))))
        conn.commit()
        conn.close()

db = DatabaseManager()

# =============================================================================
# AI ENGINE
# =============================================================================

class AIQuestionGenerator:
    def __init__(self):
        # Auto-detect API key from secrets
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")
            st.stop()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.syllabus = {
            "Mathematics": ["Algebra", "Functions", "Trigonometry", "Calculus"],
            "Physics": ["Mechanics", "Thermal", "Waves", "Electricity"],
            "Chemistry": ["Atomic Structure", "Bonding", "Organic", "Stoichiometry"],
            "English": ["Reading Analysis", "Essay Planning", "Formal Writing"]
        }

    def generate(self, subject, topic, level) -> Optional[Question]:
        prompt = f"""
        Generate a professional IB DP {subject} exam question.
        Topic: {topic}. Difficulty: Level {level}/5.
        Style: Modeled after Revision Village / Save My Exams.
        Return ONLY a JSON object with keys: 
        'question', 'options' (list of 4), 'answer' (exact string), 'explanation'.
        Use LaTeX for math symbols (e.g. $x^2$).
        """
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            return Question(
                id=hashlib.md5(data['question'].encode()).hexdigest()[:8],
                subject=subject, topic=topic,
                question_text=data['question'],
                options=data['options'],
                correct_answer=data['answer'],
                explanation=data['explanation'],
                difficulty=str(level)
            )
        except:
            return None

# =============================================================================
# UI COMPONENTS
# =============================================================================

def apply_styles():
    st.markdown("""
    <style>
    .metric-card { background: #1E293B; padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #334155; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background: linear-gradient(90deg, #4F46E5, #7C3AED); color: white; border: none; }
    .question-box { background: #0F172A; padding: 25px; border-radius: 15px; border-left: 5px solid #6366F1; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    apply_styles()
    st.sidebar.title("📚 Exam Ascent AI")
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "user_default"
    
    ai = AIQuestionGenerator()
    menu = st.sidebar.radio("Navigate", ["Dashboard", "AI Practice Lab", "Study Timer", "Saved Items"])

    if menu == "Dashboard":
        st.markdown("<h1 style='text-align: center;'>Exam Ascent AI Dashboard</h1>", unsafe_allow_html=True)
        
        # Analytics Query
        conn = sqlite3.connect("ibcp_exam_prep.db")
        df = pd.read_sql_query("SELECT * FROM quiz_results", conn)
        conn.close()
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='metric-card'><h3>{len(df)}</h3><p>Solved</p></div>", unsafe_allow_html=True)
        with c2: 
            acc = f"{int(df['score'].sum()/df['total'].sum()*100)}%" if not df.empty else "0%"
            st.markdown(f"<div class='metric-card'><h3>{acc}</h3><p>Accuracy</p></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>12</h3><p>Study Streak</p></div>", unsafe_allow_html=True)

        if not df.empty:
            st.subheader("Performance Trend")
            fig = px.line(df, x='timestamp', y='score', color='subject', markers=True, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "AI Practice Lab":
        st.title("🧪 Practice Lab")
        col1, col2, col3 = st.columns(3)
        sub = col1.selectbox("Subject", list(ai.syllabus.keys()))
        top = col2.selectbox("Topic", ai.syllabus[sub])
        lvl = col3.slider("Difficulty", 1, 5, 3)

        if st.button("Generate Question"):
            with st.spinner("AI is crafting your question..."):
                st.session_state.q = ai.generate(sub, top, lvl)
                st.session_state.answered = False

        if "q" in st.session_state and st.session_state.q:
            q = st.session_state.q
            st.markdown(f"<div class='question-box'><h4>{q.question_text}</h4></div>", unsafe_allow_html=True)
            
            choice = st.radio("Choose the correct answer:", q.options, index=None)
            
            if st.button("Submit Answer"):
                if choice == q.correct_answer:
                    st.success("✅ Correct! Excellent Work.")
                    db.save_result(st.session_state.user_id, sub, top, 1, 1)
                else:
                    st.error(f"❌ Incorrect. Correct answer was: {q.correct_answer}")
                    db.save_result(st.session_state.user_id, sub, top, 0, 1)
                
                with st.expander("View Full Marking Scheme"):
                    st.write(q.explanation)
                
                if st.button("Save Question to Revision Set"):
                    db.save_question(st.session_state.user_id, q)
                    st.toast("Saved!")

    elif menu == "Study Timer":
        st.title("⏲️ Focus Timer")
        col1, col2 = st.columns([1, 2])
        mins = col1.number_input("Focus Duration (mins)", 25)
        if col1.button("Start Pomodoro"):
            ph = col2.empty()
            for i in range(mins * 60, 0, -1):
                m, s = divmod(i, 60)
                ph.markdown(f"<h1 style='font-size: 100px; text-align: center;'>{m:02d}:{s:02d}</h1>", unsafe_allow_html=True)
                time.sleep(1)
            st.balloons()

    elif menu == "Saved Items":
        st.title("🔖 Revision Bank")
        conn = sqlite3.connect("ibcp_exam_prep.db")
        df = pd.read_sql_query("SELECT * FROM saved_questions", conn)
        conn.close()
        for _, row in df.iterrows():
            with st.expander(f"{row['subject']} - {row['topic']}"):
                data = json.loads(row['question_data'])
                st.write(data['question_text'])
                st.info(f"Correct Answer: {data['correct_answer']}")

if __name__ == "__main__":
    main()
