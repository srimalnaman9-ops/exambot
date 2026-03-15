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
# 3. AI ENGINE WITH AUTO-MODEL DETECTION
# =============================================================================
class AIEngine:
    def __init__(self):
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("API Key not found! Please add GEMINI_API_KEY to your Streamlit Secrets.")
            st.stop()
        genai.configure(api_key=api_key)
        self.model_name = self._detect_best_model()
        self.model = genai.GenerativeModel(self.model_name)

    def _detect_best_model(self):
        """Automatically detects available models and selects the most efficient one."""
        try:
            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Preference order: 1.5 Flash (Fast/High Quota) -> 1.5 Pro -> Pro 1.0
            for target in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
                if target in available: return target
            return available[0]
        except:
            return "gemini-1.5-flash" # Default fallback

    def generate(self, subject, topic, level):
        # Curriculum Logic: Chemistry is SL, others are HL
        level_label = "Standard Level (SL)" if subject == "Chemistry" else "Higher Level (HL)"
        
        prompt = f"""
        Act as an IB Examiner specialized in {subject} {level_label}. 
        Research typical questions from Revision Village and Save My Exams.
        
        Task: Create one {level_label} multiple-choice question.
        Topic: {topic}
        Difficulty: Level {level}/5
        
        Constraints:
        1. Use IB Command Terms (Calculate, Deduce, Explain).
        2. Use LaTeX for ALL math/science notation (e.g., $H_2O$, $x^2$).
        3. Provide a rigorous 'Mark Scheme' style explanation.
        
        Output ONLY JSON:
        {{
            "question": "Question text here...",
            "options": ["A", "B", "C", "D"],
            "answer": "The exact correct option string",
            "explanation": "Step-by-step IB marking guide..."
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
        except Exception as e:
            st.error(f"Generation failed: {e}")
            return None

# =============================================================================
# 4. UI LOGIC
# =============================================================================
def main():
    st.sidebar.title("🚀 Exam Ascent AI")
    st.sidebar.info(f"Using AI Engine: {AIEngine().model_name}")
    
    page = st.sidebar.radio("Navigate", ["Dashboard", "Practice Lab", "Revision Bank"])
    ai = AIEngine()

    if page == "Dashboard":
        st.title("Your Exam Readiness")
        df = pd.read_sql("SELECT * FROM results", db.conn)
        if not df.empty:
            col1, col2 = st.columns(2)
            fig1 = px.pie(df, names='subject', values='score', title="Score Distribution", hole=0.4)
            col1.plotly_chart(fig1)
            df['date'] = pd.to_datetime(df['date'])
            fig2 = px.line(df, x='date', y='score', color='subject', title="Performance Over Time")
            col2.plotly_chart(fig2)
        else:
            st.info("No data yet. Head to the Practice Lab to begin!")

    elif page == "Practice Lab":
        st.title("🧪 Practice Lab")
        
        c1, c2, c3 = st.columns(3)
        sub = c1.selectbox("Subject", ["Mathematics", "Physics", "Chemistry", "English"])
        
        # Display Level Info
        curric = "IB HL" if sub != "Chemistry" else "IB SL"
        st.caption(f"Curriculum Mode: **{curric}** | Style: **Revision Village**")

        topics = {
            "Mathematics": ["Calculus", "Vectors", "Complex Numbers", "Trigonometry"],
            "Physics": ["Fields", "Quantum Physics", "Mechanics", "Waves"],
            "Chemistry": ["Stoichiometry", "Bonding", "Periodicity", "Organic"],
            "English": ["Literary Analysis", "Paper 1 Strategies"]
        }
        top = c2.selectbox("Topic", topics[sub])
        lvl = c3.slider("Difficulty Level", 1, 5, 3)

        if st.button("Generate New Question"):
            with st.spinner("AI is researching exam patterns..."):
                st.session_state.current_q = ai.generate(sub, top, lvl)
                st.session_state.answered = False
                st.session_state.submitted = False

        if "current_q" in st.session_state and st.session_state.current_q:
            q = st.session_state.current_q
            st.markdown(f"<div class='q-card'><h3>{q.question_text}</h3></div>", unsafe_allow_html=True)
            
            user_input = st.radio("Choose one:", q.options, index=None, key="user_ans")
            
            if st.button("Check Answer"):
                if user_input:
                    st.session_state.submitted = True
                    if user_input == q.correct_answer:
                        st.success("🎯 Correct!")
                        db.save_score(sub, top, 1)
                    else:
                        st.error(f"❌ Incorrect. Correct answer: {q.correct_answer}")
                        db.save_score(sub, top, 0)
                else:
                    st.warning("Please select an option first.")

            # REVEAL marking scheme only after checking
            if st.session_state.get('submitted'):
                st.markdown("---")
                st.subheader("📝 IB Step-by-Step Marking Scheme")
                st.markdown(f"<div class='mark-scheme'>{q.explanation}</div>", unsafe_allow_html=True)
                
                if st.button("Save to Revision Bank"):
                    db.save_question(q)
                    st.toast("Question Saved!")

    elif page == "Revision Bank":
        st.title("🔖 Saved Questions")
        df_saved = pd.read_sql("SELECT * FROM saved", db.conn)
        for _, row in df_saved.iterrows():
            data = json.loads(row['data'])
            with st.expander(f"{row['subject']} - {row['topic']} (Level {data['difficulty']})"):
                st.write(data['question_text'])
                st.success(f"Answer: {data['correct_answer']}")
                st.info(data['explanation'])

if __name__ == "__main__":
    main()
