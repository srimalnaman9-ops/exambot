import streamlit as st
import google.generativeai as genai
import sqlite3
import json
import pandas as pd
import plotly.express as px
import datetime
import hashlib
from typing import List, Optional
from dataclasses import dataclass, asdict

# =============================================================================
# 1. PAGE CONFIG & STYLING
# =============================================================================
st.set_page_config(page_title="Exam Ascent AI", layout="wide", page_icon="🧪")

st.markdown("""
    <style>
    .stButton>button { 
        background: linear-gradient(90deg, #4F46E5, #7C3AED); 
        color: white; border-radius: 12px; font-weight: bold; height: 3.5em; width: 100%;
    }
    .q-card { 
        background-color: #1e1e2f; padding: 30px; border-radius: 18px; 
        border-left: 8px solid #6366F1; margin-bottom: 25px; color: #ffffff;
    }
    .mark-scheme { 
        background-color: #064E3B; padding: 25px; border-radius: 12px; color: #ECFDF5; border: 1px solid #10B981;
    }
    .formula-card {
        background-color: #0f172a; border: 1px solid #334155; padding: 15px; border-radius: 10px; margin-bottom: 10px;
    }
    .timetable-card {
        background-color: #f8fafc; color: #1e293b; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4F46E5;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. DATABASE & MODELS
# =============================================================================
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

# =============================================================================
# 3. AI ENGINE (MCQ & STRUCTURED LOGIC)
# =============================================================================
class AIEngine:
    def __init__(self):
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("API Key missing! Add GEMINI_API_KEY to Streamlit Secrets.")
            st.stop()
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self._detect_model())

    def _detect_model(self):
        try:
            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            return "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available else "models/gemini-pro"
        except: return "gemini-1.5-flash"

    def generate(self, subject, topic, q_type):
        level = "Standard Level (SL)" if subject == "Chemistry" else "Higher Level (HL)"
        
        format_instruction = ""
        if q_type == "MCQ":
            format_instruction = "Return ONLY JSON with: 'question' (narrative), 'options' (list of 4), 'answer' (exact string), 'explanation' (step-by-step)."
        else:
            format_instruction = "Create a multi-part structured question (Part a, b, c). Return ONLY JSON with: 'question' (narrative with parts), 'answer' (Full model answer), 'explanation' (Detailed mark scheme with point allocation)."

        prompt = f"""
        Act as an IB Senior Examiner. Research patterns from Revision Village and Save My Exams.
        Create a {level} {subject} {q_type} on '{topic}'.
        Use LaTeX for all math ($...$). Ensure a complex narrative scenario.
        {format_instruction}
        """
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            return data
        except: return None

# =============================================================================
# 4. MAIN APP
# =============================================================================
def main():
    db = DatabaseManager()
    ai = AIEngine()

    st.sidebar.title("🚀 Exam Ascent AI")
    page = st.sidebar.radio("Navigate", ["Dashboard", "Final Schedule", "Portion Checklist", "IB Formula Vault", "Practice Lab"])

    # SCHEDULE FROM PDF 
    schedule = [
        {"Date": "25.03.2026", "Sub": "Physics P-I", "Portion": "A.1 to A.5", "Dur": "2 hrs"},
        {"Date": "26.03.2026", "Sub": "Physics P-II", "Portion": "B.1 to B.5", "Dur": "2.30 hrs"},
        {"Date": "28.03.2026", "Sub": "Chemistry P-I", "Portion": "Structure: 1, 2 & 3", "Dur": "1.30 hrs"},
        {"Date": "30.03.2026", "Sub": "Chemistry P-II", "Portion": "Structure: 1, 2 & 3", "Dur": "1.30 hrs"},
        {"Date": "06.04.2026", "Sub": "Maths P-I", "Portion": "Unit 1 Number & Algebra", "Dur": "2 hrs"},
        {"Date": "07.04.2026", "Sub": "Maths P-II", "Portion": "Unit 2 & 3 (Trig)", "Dur": "2 hrs"},
        {"Date": "09.04.2026", "Sub": "English P-I", "Portion": "Writing Task", "Dur": "1.15 hrs"},
        {"Date": "10.04.2026", "Sub": "English P-II", "Portion": "Reading & Listening", "Dur": "1.45 hrs"}
    ]

    if page == "Dashboard":
        st.title("Jain Vidyalaya: Ready for Final Ascent?")
        exam_date = datetime.datetime(2026, 3, 25)
        days = (exam_date - datetime.datetime.now()).days
        st.metric("Countdown to Physics", f"{days} Days")
        
        df = pd.read_sql("SELECT * FROM results", db.conn)
        if not df.empty:
            st.plotly_chart(px.line(df, x='date', y='score', color='subject', title="Your Progress Trend"))

    elif page == "Final Schedule":
        st.title("🗓️ Final Ascent Assessment 2025-26")
        for s in schedule:
            st.markdown(f"""<div class='timetable-card'><strong>{s['Date']}</strong>: {s['Sub']} ({s['Dur']})<br><small>Focus: {s['Portion']}</small></div>""", unsafe_allow_html=True)

    elif page == "Portion Checklist":
        st.title("✅ Syllabus Checklist")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Physics & Chemistry")
            st.checkbox("A.1 to A.5 (Mechanics) ")
            st.checkbox("B.1 to B.5 (Energy/Fields) ")
            st.checkbox("Chemistry Structure 1, 2, 3 ")
        with c2:
            st.subheader("Math & English")
            st.checkbox("Unit 1: Number & Algebra ")
            st.checkbox("Unit 2: Functions ")
            st.checkbox("Unit 3: Trigonometry ")
            st.checkbox("English Writing: Blog, Proposal, Essay ")

    elif page == "IB Formula Vault":
        st.title("🔢 IB Formula Vault")
        sub_vault = st.selectbox("Select Subject", ["Mathematics HL", "Physics HL", "Chemistry SL"])
        
        if sub_vault == "Mathematics HL":
            with st.expander("Unit 1: Number & Algebra "):
                st.latex(r"n^{th} \text{ term of arithmetic sequence: } u_n = u_1 + (n-1)d")
                st.latex(r"\text{Sum of arithmetic series: } S_n = \frac{n}{2}(2u_1 + (n-1)d)")
                st.latex(r"\text{Compound Interest: } FV = PV \times (1 + \frac{r}{100k})^{kn}")
            with st.expander("Unit 3: Trigonometry "):
                st.latex(r"\text{Sine Rule: } \frac{a}{\sin A} = \frac{b}{\sin B} = \frac{c}{\sin C}")
                st.latex(r"\text{Cosine Rule: } c^2 = a^2 + b^2 - 2ab\cos C")
                st.latex(r"\text{Area of Triangle: } A = \frac{1}{2}ab\sin C")

        elif sub_vault == "Physics HL":
            with st.expander("A.1 - A.5: Mechanics "):
                st.latex(r"v = u + at \quad ; \quad s = ut + \frac{1}{2}at^2")
                st.latex(r"F = ma \quad ; \quad p = mv")
                st.latex(r"E_k = \frac{1}{2}mv^2 \quad ; \quad \Delta E_p = mg\Delta h")
            with st.expander("B.1 - B.5: Energy & Fields "):
                st.latex(r"P = \frac{\Delta E}{\Delta t} \quad ; \quad \text{Efficiency} = \frac{\text{useful work}}{\text{total work}}")

        elif sub_vault == "Chemistry SL":
            with st.expander("Structure 1, 2 & 3 "):
                st.latex(r"n = \frac{m}{M} \quad ; \quad n = cV")
                st.latex(r"PV = nRT \quad (\text{Ideal Gas Law})")
                st.latex(r"\text{Percentage Yield} = \frac{\text{Experimental}}{\text{Theoretical}} \times 100")

    elif page == "Practice Lab":
        st.title("🧪 Practice Lab")
        sub = st.selectbox("Subject", ["Mathematics", "Physics", "Chemistry", "English"])
        
        topics = {
            "Physics": ["Mechanics A.1-A.5 ", "Electricity B.1-B.5 "],
            "Chemistry": ["Atomic Structure ", "Bonding ", "Periodicity "],
            "Mathematics": ["Unit 1: Algebra ", "Unit 2: Functions ", "Unit 3: Trigonometry "],
            "English": ["Proposal ", "Blog ", "Journal Entry ", "Formal Letter "]
        }
        top = st.selectbox("Portion Focus", topics[sub])
        q_style = st.radio("Question Style", ["MCQ", "Structured (Written)"])

        if st.button("Generate Question"):
            with st.spinner("Analyzing IB patterns..."):
                st.session_state.current_q = ai.generate(sub, top, q_style)
                st.session_state.submitted = False

        if "current_q" in st.session_state and st.session_state.current_q:
            q = st.session_state.current_q
            st.markdown(f"<div class='q-card'><h3>{q['question']}</h3></div>", unsafe_allow_html=True)
            
            if q_style == "MCQ":
                ans = st.radio("Options:", q['options'], index=None)
                if st.button("Check Answer"):
                    st.session_state.submitted = True
                    if ans == q['answer']: st.success("Correct!")
                    else: st.error(f"Incorrect. Answer: {q['answer']}")
            else:
                st.info("Write your solution. Click below to compare with the IB Mark Scheme.")
                if st.button("Reveal Model Answer"): st.session_state.submitted = True

            if st.session_state.get('submitted'):
                st.markdown("---")
                if q_style == "Structured (Written)":
                    st.markdown(f"<div class='mark-scheme'><strong>Model Answer:</strong><br>{q['answer']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='mark-scheme'><strong>IB Mark Scheme:</strong><br>{q['explanation']}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
