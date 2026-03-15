import streamlit as st
import sqlite3
import json
import pandas as pd
import plotly.express as px
import time
import datetime
import hashlib
from typing import Dict, List, Tuple, Optional
import google.generativeai as genai
from dataclasses import dataclass, asdict
import random

# =============================================================================
# 1. CONFIGURATION & DATA MODELS
# =============================================================================

st.set_page_config(page_title="Exam Ascent AI", layout="wide")

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

# =============================================================================
# 2. DATABASE ORCHESTRATION
# =============================================================================

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect("ib_prep.db", check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS results (
            subject TEXT, topic TEXT, score INTEGER, timestamp DATETIME)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS saved_questions (
            id TEXT PRIMARY KEY, subject TEXT, topic TEXT, data TEXT)''')
        self.conn.commit()

    def log_result(self, subject, topic, score):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO results VALUES (?, ?, ?, ?)",
                       (subject, topic, score, datetime.datetime.now()))
        self.conn.commit()

    def save_q(self, question: Question):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO saved_questions VALUES (?, ?, ?, ?)",
                       (question.id, question.subject, question.topic, json.dumps(asdict(question))))
        self.conn.commit()

db = DatabaseManager()

# =============================================================================
# 3. AI GENERATION ENGINE (REVISION VILLAGE & SAVE MY EXAMS STYLE)
# =============================================================================

class AIEngine:
    def __init__(self):
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("API Key missing! Add GEMINI_API_KEY to Streamlit Secrets.")
            st.stop()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_question(self, subject, topic, level):
        # LEVEL LOGIC: Chemistry is SL, others are HL as requested
        level_type = "Standard Level (SL)" if subject == "Chemistry" else "Higher Level (HL)"
        
        prompt = f"""
        Act as an IB Examiner. Research patterns from Revision Village and Save My Exams.
        Create a unique {level_type} {subject} question on '{topic}'.
        Difficulty: Level {level} of 5.
        
        Rules:
        - Use IB Command Terms ('Calculate', 'Deduce', 'Determine', 'Explain').
        - Use LaTeX for ALL math/science notation ($...$).
        - Provide a rigorous, step-by-step IB Marking Scheme in the explanation.
        
        Return ONLY valid JSON:
        {{
            "question": "text",
            "options": ["A", "B", "C", "D"],
            "answer": "exact string from options",
            "explanation": "Step-by-step breakdown"
        }}
        """
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            return Question(
                id=hashlib.md5(data['question'].encode()).hexdigest()[:10],
                subject=subject, topic=topic,
                question_text=data['question'],
                options=data['options'],
                correct_answer=data['answer'],
                explanation=data['explanation'],
                difficulty=str(level)
            )
        except Exception as e:
            st.error(f"AI Error: {e}")
            return None

# =============================================================================
# 4. MAIN USER INTERFACE
# =============================================================================

def main():
    st.markdown("""
        <style>
        .stButton>button { background: linear-gradient(90deg, #4F46E5, #7C3AED); color: white; border: none; font-weight: bold; height: 3em; }
        .q-card { background-color: #111827; padding: 25px; border-radius: 15px; border-left: 5px solid #6366F1; margin-bottom: 20px; }
        .ans-card { background-color: #064E3B; padding: 20px; border-radius: 10px; margin-top: 20px; }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("🚀 Exam Ascent AI")
    page = st.sidebar.radio("Navigation", ["Dashboard", "Practice Lab", "Saved Bank"])
    
    ai = AIEngine()

    if page == "Dashboard":
        st.title("Performance Overview")
        df = pd.read_sql("SELECT * FROM results", db.conn)
        
        if not df.empty:
            c1, c2 = st.columns(2)
            # Accuracy Bar Chart
            fig1 = px.bar(df.groupby('subject')['score'].mean().reset_index(), 
                          x='subject', y='score', title="Avg Accuracy by Subject", template="plotly_dark")
            c1.plotly_chart(fig1, use_container_width=True)
            
            # Study Trend
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            fig2 = px.line(df, x='timestamp', y='score', title="Study History", template="plotly_dark")
            c2.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No data yet. Start practicing in the Lab!")

    elif page == "Practice Lab":
        st.title("🧪 AI Practice Lab")
        
        col1, col2, col3 = st.columns(3)
        sub = col1.selectbox("Subject", ["Mathematics", "Physics", "Chemistry", "English"])
        
        # Display Level Badge
        lvl_tag = "IB HL" if sub != "Chemistry" else "IB SL"
        st.info(f"Currently generating: **{lvl_tag}** questions (Style: Revision Village)")

        topics_map = {
            "Mathematics": ["Algebra", "Functions", "Trigonometry", "Calculus", "Vectors"],
            "Physics": ["Mechanics", "Thermal", "Waves", "Electricity", "Atomic"],
            "Chemistry": ["Stoichiometry", "Atomic Structure", "Periodicity", "Bonding", "Organic"],
            "English": ["Reading Analysis", "Essay Planning", "Argumentation"]
        }
        
        top = col2.selectbox("Topic", topics_map[sub])
        lvl = col3.slider("Difficulty", 1, 5, 3)

        if st.button("Generate Exam Question", use_container_width=True):
            with st.spinner("AI is analyzing exam patterns..."):
                st.session_state.current_q = ai.generate_question(sub, top, lvl)
                st.session_state.show_ans = False

        if "current_q" in st.session_state and st.session_state.current_q:
            q = st.session_state.current_q
            
            # Question Card
            st.markdown(f"<div class='q-card'><h4>{q.question_text}</h4></div>", unsafe_allow_html=True)
            
            # Multiple Choice Logic
            user_choice = st.radio("Select the correct answer:", q.options, index=None)
            
            if st.button("Check Answer"):
                if user_choice:
                    st.session_state.show_ans = True
                    if user_choice == q.correct_answer:
                        st.success("Correct Answer!")
                        db.log_result(sub, top, 1)
                    else:
                        st.error(f"Incorrect. The answer is: {q.correct_answer}")
                        db.log_result(sub, top, 0)
                else:
                    st.warning("Please select an option.")

            # IB Marking Scheme Reveal
            if st.session_state.get('show_ans'):
                st.markdown("---")
                st.subheader("📝 Step-by-Step Marking Scheme")
                st.markdown(f"<div class='ans-card'>{q.explanation}</div>", unsafe_allow_html=True)
                
                if st.button("Save to Revision Bank"):
                    db.save_q(q)
                    st.toast("Question Saved!")

    elif page == "Saved Bank":
        st.title("🔖 Your Saved Questions")
        df_saved = pd.read_sql("SELECT * FROM saved_questions", db.conn)
        for _, row in df_saved.iterrows():
            data = json.loads(row['data'])
            with st.expander(f"{row['subject']} - {row['topic']}"):
                st.write(data['question_text'])
                st.write(f"**Answer:** {data['correct_answer']}")
                st.info(data['explanation'])

if __name__ == "__main__":
    main()
