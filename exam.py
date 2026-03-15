import streamlit as st
import google.generativeai as genai
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import random
import time
from datetime import datetime, timedelta

# ==========================================
# CONFIGURATION & API SETUP
# ==========================================
st.set_page_config(page_title="Exam Ascent AI", layout="wide", initial_sidebar_state="expanded")

# Initialize Gemini API
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Please set GEMINI_API_KEY in your Streamlit secrets.")

# ==========================================
# DATABASE ORCHESTRATION
# ==========================================
class DatabaseManager:
    def __init__(self, db_name="exam_ascent.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Results table
        cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT, topic TEXT, difficulty INTEGER, 
            score INTEGER, total INTEGER, timestamp DATETIME)''')
        # Saved Questions
        cursor.execute('''CREATE TABLE IF NOT EXISTS saved_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT, topic TEXT, question_data TEXT)''')
        # Study Sessions (Pomodoro)
        cursor.execute('''CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            duration INTEGER, date DATE)''')
        # User Profile/XP
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY, xp INTEGER, level INTEGER)''')
        
        # Initialize profile if empty
        cursor.execute("SELECT COUNT(*) FROM user_profile")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO user_profile (id, xp, level) VALUES (1, 0, 1)")
        
        self.conn.commit()

    def add_result(self, subject, topic, difficulty, score, total):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO quiz_results (subject, topic, difficulty, score, total, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                       (subject, topic, difficulty, score, total, datetime.now()))
        # Update XP: 10 XP per correct answer
        xp_gain = score * 10
        cursor.execute("UPDATE user_profile SET xp = xp + ? WHERE id = 1", (xp_gain,))
        self.conn.commit()

    def save_question(self, subject, topic, q_json):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO saved_questions (subject, topic, question_data) VALUES (?, ?, ?)",
                       (subject, topic, json.dumps(q_json)))
        self.conn.commit()

db = DatabaseManager()

# ==========================================
# AI CORE ENGINE
# ==========================================
class AIEngine:
    @staticmethod
    def generate_question(subject, topic, level):
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Generate a professional IB-style {subject} question on the topic of {topic}.
        Difficulty Level: {level} (out of 5, where 5 is IB HL/Revision Village style).
        Return ONLY a JSON object with the following keys:
        - question: (The text of the question)
        - options: (A list of 4 strings)
        - answer: (The exact string from the options that is correct)
        - explanation: (A detailed step-by-step IB-style marking scheme explanation)
        """
        
        try:
            response = model.generate_content(prompt)
            # Cleaning potential markdown code blocks from Gemini
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(raw_text)
        except Exception as e:
            st.error(f"AI Generation Error: {e}")
            return None

# ==========================================
# UI COMPONENTS & PAGES
# ==========================================

def render_sidebar():
    st.sidebar.title("🚀 Exam Ascent AI")
    # XP and Level
    cursor = db.conn.cursor()
    cursor.execute("SELECT xp, level FROM user_profile WHERE id = 1")
    xp, level = cursor.fetchone()
    
    st.sidebar.metric("Your Level", f"Lvl {level}")
    st.sidebar.progress(min((xp % 1000) / 1000, 1.0), text=f"{xp} XP")
    
    menu = ["Dashboard", "AI Quiz Lab", "Mock Exams", "Flashcards", "Study Timer", "Saved Questions", "Analytics"]
    return st.sidebar.radio("Navigate", menu)

def show_dashboard():
    st.title("Welcome back, Scholar!")
    
    # Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    df = pd.read_sql("SELECT * FROM quiz_results", db.conn)
    
    with col1:
        st.metric("Questions Solved", len(df))
    with col2:
        acc = (df['score'].sum() / df['total'].sum() * 100) if not df.empty else 0
        st.metric("Avg. Accuracy", f"{acc:.1f}%")
    with col3:
        st.metric("Study Streak", "5 Days") # Logic can be expanded
    with col4:
        st.metric("Target Exam", "45 Days")

    st.markdown("---")
    
    # Quick Subjects
    st.subheader("Quick Start by Subject")
    sc1, sc2, sc3, sc4 = st.columns(4)
    subjects = [("Physics", "⚛️"), ("Chemistry", "🧪"), ("Mathematics", "🔢"), ("English", "📚")]
    for i, (sub, icon) in enumerate(subjects):
        with [sc1, sc2, sc3, sc4][i]:
            if st.button(f"{icon} {sub}", use_container_width=True):
                st.session_state.page = "AI Quiz Lab"
                st.session_state.selected_subject = sub

def show_quiz_lab():
    st.title("🧪 AI Quiz Lab")
    
    col1, col2, col3 = st.columns(3)
    subject = col1.selectbox("Subject", ["Mathematics", "Physics", "Chemistry", "English"])
    
    topics = {
        "Mathematics": ["Number & Algebra", "Functions", "Trigonometry"],
        "Physics": ["Mechanics", "Electricity", "Thermal Physics", "Waves"],
        "Chemistry": ["Atomic Structure", "Periodic Table", "Organic Chemistry"],
        "English": ["Reading Comprehension", "Writing Formats"]
    }
    
    topic = col2.selectbox("Topic", topics[subject])
    level = col3.slider("Difficulty Level", 1, 5, 3)

    if st.button("Generate AI Question", type="primary"):
        with st.spinner("Gemini is crafting a custom IB question..."):
            q_data = AIEngine.generate_question(subject, topic, level)
            if q_data:
                st.session_state.current_q = q_data
                st.session_state.answered = False

    if "current_q" in st.session_state:
        q = st.session_state.current_q
        st.info(f"**Question:** {q['question']}")
        
        choice = st.radio("Select your answer:", q['options'], index=None)
        
        if st.button("Submit Answer"):
            if choice == q['answer']:
                st.success("Correct! +10 XP")
                db.add_result(subject, topic, level, 1, 1)
            else:
                st.error(f"Incorrect. The correct answer was: {q['answer']}")
                db.add_result(subject, topic, level, 0, 1)
            
            with st.expander("See Step-by-Step Explanation"):
                st.write(q['explanation'])
            
            if st.button("Save to Revision Set"):
                db.save_question(subject, topic, q)
                st.toast("Question Saved!")

def show_flashcards():
    st.title("🗂️ Interactive Flashcards")
    # Concept for Physics Formulas
    cards = [
        {"q": "Newton's Second Law", "a": "$F = ma$"},
        {"q": "Ideal Gas Law", "a": "$PV = nRT$"},
        {"q": "Quadratic Formula", "a": "$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$"}
    ]
    
    idx = st.session_state.get("card_idx", 0)
    card = cards[idx % len(cards)]
    
    st.container(border=True)
    with st.container():
        st.markdown(f"### {card['q']}")
        if st.button("Flip Card"):
            st.write(card['a'])
    
    if st.button("Next Card"):
        st.session_state.card_idx = idx + 1
        st.rerun()

def show_timer():
    st.title("⏲️ Pomodoro Study Timer")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        minutes = st.number_input("Set focus time (mins)", value=25)
        if st.button("Start Session"):
            placeholder = st.empty()
            for t in range(minutes * 60, 0, -1):
                m, s = divmod(t, 60)
                placeholder.header(f"⏳ {m:02d}:{s:02d}")
                time.sleep(1)
            st.balloons()
            st.success("Session Complete! Take a break.")

def show_analytics():
    st.title("📊 Progress Analytics")
    df = pd.read_sql("SELECT * FROM quiz_results", db.conn)
    
    if df.empty:
        st.warning("No data yet. Solve some questions to see analytics!")
        return

    # Accuracy over time
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    fig = px.line(df, x='timestamp', y='score', title="Performance History", markers=True)
    st.plotly_chart(fig, use_container_width=True)
    
    # Subject breakdown
    sub_df = df.groupby('subject')['score'].mean().reset_index()
    fig2 = px.bar(sub_df, x='subject', y='score', color='subject', title="Accuracy by Subject")
    st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# MAIN ROUTING
# ==========================================
def main():
    selection = render_sidebar()
    
    if selection == "Dashboard":
        show_dashboard()
    elif selection == "AI Quiz Lab":
        show_quiz_lab()
    elif selection == "Flashcards":
        show_flashcards()
    elif selection == "Study Timer":
        show_timer()
    elif selection == "Analytics":
        show_analytics()
    elif selection == "Saved Questions":
        st.title("🔖 Saved Questions")
        df = pd.read_sql("SELECT * FROM saved_questions", db.conn)
        st.table(df[['subject', 'topic']])
    elif selection == "Mock Exams":
        st.title("📝 Full Mock Exams")
        st.info("Simulating Paper 1 Environment... (60 Minutes)")
        if st.button("Start Physics Paper 1 Mock"):
            st.session_state.mock_active = True
            st.write("Feature coming soon in v2.0!")

if __name__ == "__main__":
    main()
