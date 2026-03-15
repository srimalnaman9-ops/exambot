import streamlit as st
import google.generativeai as genai
import sqlite3
import pandas as pd
import plotly.express as px
import json
import time
from datetime import datetime

# ==========================================
# 1. API & AUTO-MODEL DETECTION
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")

def get_best_model():
    """Dynamically finds the best available Gemini model."""
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Prefer Flash for speed/cost, fallback to Pro
        for target in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if target in models:
                return target
        return models[0] if models else "gemini-pro"
    except:
        return "gemini-1.5-flash"

AVAILABLE_MODEL = get_best_model()

# ==========================================
# 2. DATABASE ARCHITECTURE
# ==========================================
class ExamDatabase:
    def __init__(self):
        self.conn = sqlite3.connect("exam_ascent.db", check_same_thread=False)
        self.init_db()

    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS results 
            (id INTEGER PRIMARY KEY, subject TEXT, topic TEXT, score INTEGER, total INTEGER, date TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS profiles 
            (id INTEGER PRIMARY KEY, xp INTEGER, level INTEGER)''')
        cursor.execute("SELECT COUNT(*) FROM profiles")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO profiles VALUES (1, 0, 1)")
        self.conn.commit()

    def add_score(self, sub, top, score, total):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO results (subject, topic, score, total, date) VALUES (?,?,?,?,?)",
                       (sub, top, score, total, datetime.now().strftime("%Y-%m-%d")))
        cursor.execute("UPDATE profiles SET xp = xp + ? WHERE id = 1", (score * 15,))
        self.conn.commit()

db = ExamDatabase()

# ==========================================
# 3. AI CORE
# ==========================================
def generate_ib_question(subject, topic, level):
    model = genai.GenerativeModel(AVAILABLE_MODEL)
    prompt = f"""
    Generate an IB-style {subject} question. 
    Topic: {topic}. Difficulty: {level} (1-5).
    Format: JSON only.
    Keys: "question", "options" (list of 4), "answer" (string), "explanation".
    Ensure the explanation is pedagogical and step-by-step.
    """
    try:
        response = model.generate_content(prompt)
        # Clean markdown
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except Exception as e:
        return {"error": str(e)}

# ==========================================
# 4. APP INTERFACE
# ==========================================
def main():
    st.sidebar.title("🚀 Exam Ascent AI")
    
    # Progress Tracker in Sidebar
    cursor = db.conn.cursor()
    cursor.execute("SELECT xp, level FROM profiles WHERE id = 1")
    xp, lvl = cursor.fetchone()
    st.sidebar.metric("Your Level", f"Lv. {lvl}")
    st.sidebar.progress(min((xp % 1000) / 1000, 1.0), text=f"{xp} XP")

    menu = ["Dashboard", "Practice Lab", "Analytics", "Study Timer"]
    choice = st.sidebar.selectbox("Navigate", menu)

    if choice == "Dashboard":
        st.title("Exam Ascent AI Dashboard")
        col1, col2, col3 = st.columns(3)
        df = pd.read_sql("SELECT * FROM results", db.conn)
        
        col1.metric("Questions Solved", len(df))
        col2.metric("Total XP", xp)
        col3.metric("Accuracy", f"{int(df['score'].sum()/df['total'].sum()*100) if not df.empty else 0}%")
        
        st.subheader("Recent Activity")
        st.dataframe(df.tail(5), use_container_width=True)

    elif choice == "Practice Lab":
        st.title("🧪 AI Practice Lab")
        c1, c2, c3 = st.columns(3)
        sub = c1.selectbox("Subject", ["Physics", "Chemistry", "Mathematics", "English"])
        top = c2.selectbox("Topic", ["Mechanics", "Organic Chem", "Trigonometry", "Essay Writing"])
        diff = c3.slider("Difficulty", 1, 5, 3)

        if st.button("Generate Question"):
            with st.spinner("AI is thinking..."):
                q = generate_ib_question(sub, top, diff)
                if "error" not in q:
                    st.session_state.current_q = q
                else:
                    st.error("API Limit reached or error occurred.")

        if "current_q" in st.session_state:
            q = st.session_state.current_q
            st.write(f"### {q['question']}")
            user_choice = st.radio("Select Answer:", q['options'])
            
            if st.button("Check Answer"):
                if user_choice == q['answer']:
                    st.success("Correct! +15 XP")
                    db.add_score(sub, top, 1, 1)
                else:
                    st.error(f"Incorrect. Correct answer: {q['answer']}")
                    db.add_score(sub, top, 0, 1)
                st.info(f"**Explanation:** {q['explanation']}")

    elif choice == "Analytics":
        st.title("📊 Performance Insights")
        df = pd.read_sql("SELECT * FROM results", db.conn)
        if not df.empty:
            fig = px.bar(df.groupby('subject')['score'].sum().reset_index(), 
                         x='subject', y='score', color='subject', title="Score per Subject")
            st.plotly_chart(fig)
        else:
            st.write("No data to display yet.")

    elif choice == "Study Timer":
        st.title("⏲️ Pomodoro Focus")
        mins = st.number_input("Minutes", 25)
        if st.button("Start Timer"):
            ph = st.empty()
            for i in range(mins * 60, 0, -1):
                m, s = divmod(i, 60)
                ph.subheader(f"Time Remaining: {m:02d}:{s:02d}")
                time.sleep(1)
            st.balloons()

if __name__ == "__main__":
    main()
