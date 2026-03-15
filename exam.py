"""
╔══════════════════════════════════════════════════════════════╗
║           EXAM ASCENT AI — IB Exam Preparation Platform      ║
║           Powered by Google Gemini AI                        ║
║           Built with Python + Streamlit + SQLite + Plotly    ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import sqlite3
import json
import random
import time
import re
from datetime import datetime, date, timedelta
from typing import Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import google.generativeai as genai

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Exam Ascent AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

/* Dark background */
.stApp { background: #0d0f18; color: #e2e8f0; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #0d1220 100%);
    border-right: 1px solid #1e2a3a;
}

/* Cards */
.ea-card {
    background: linear-gradient(135deg, #1a2236 0%, #131929 100%);
    border: 1px solid #2a3a55;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    transition: transform .2s, box-shadow .2s;
}
.ea-card:hover { transform: translateY(-3px); box-shadow: 0 8px 30px rgba(99,179,237,0.12); }

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #1e2d45, #162133);
    border: 1px solid #2e4a6a;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
}
.metric-value { font-size: 2.2rem; font-weight: 700; color: #63b3ed; line-height: 1; }
.metric-label { font-size: 0.78rem; color: #8ba3be; margin-top: .4rem; letter-spacing: .05em; text-transform: uppercase; }

/* Countdown */
.countdown-box {
    background: linear-gradient(135deg, #1a3a5c 0%, #0f2540 100%);
    border: 1px solid #3182ce;
    border-radius: 16px;
    padding: 1.6rem 2rem;
    text-align: center;
}
.countdown-title { font-size: 1rem; color: #90cdf4; margin-bottom: .8rem; letter-spacing: .1em; }
.countdown-time  { font-size: 2.8rem; font-weight: 700; color: #bee3f8; font-family: 'JetBrains Mono', monospace; }
.countdown-sub   { font-size: 0.8rem; color: #63b3ed; margin-top: .5rem; }

/* Subject badges */
.badge-physics   { background: #1a365d; color: #90cdf4; border: 1px solid #2b6cb0; }
.badge-chemistry { background: #1c4532; color: #9ae6b4; border: 1px solid #276749; }
.badge-math      { background: #44337a; color: #d6bcfa; border: 1px solid #6b46c1; }
.badge-english   { background: #4a1942; color: #fbb6ce; border: 1px solid #97266d; }
.subject-badge {
    display: inline-block; padding: .25rem .75rem; border-radius: 20px;
    font-size: .75rem; font-weight: 600; letter-spacing: .04em;
}

/* Timetable card */
.exam-card {
    border-radius: 14px; padding: 1.2rem 1.5rem; margin-bottom: .75rem;
    border-left: 4px solid;
}
.exam-card.next { border-left-color: #f6ad55; background: #1a1505; }
.exam-card.today { border-left-color: #48bb78; background: #0a1f12; }
.exam-card.upcoming { border-left-color: #63b3ed; background: #0a1929; }
.exam-card.past { border-left-color: #4a5568; background: #111318; opacity: .6; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #1e40af);
    color: white; border: none; border-radius: 8px;
    font-family: 'Space Grotesk', sans-serif; font-weight: 600;
    padding: .6rem 1.5rem; transition: all .2s;
}
.stButton > button:hover { background: linear-gradient(135deg, #3b82f6, #2563eb); transform: translateY(-1px); }

/* Flashcard */
.flashcard {
    background: linear-gradient(135deg, #1e3a5f, #0f2540);
    border: 1px solid #2b6cb0; border-radius: 18px;
    min-height: 200px; display: flex; align-items: center;
    justify-content: center; padding: 2rem; text-align: center;
    cursor: pointer; transition: all .3s;
}
.flashcard:hover { border-color: #63b3ed; box-shadow: 0 0 30px rgba(99,179,237,.2); }
.flashcard-front { font-size: 1.3rem; font-weight: 600; color: #bee3f8; }
.flashcard-back  { font-size: 1rem; color: #90cdf4; font-family: 'JetBrains Mono', monospace; }

/* Progress bars */
.progress-bar-bg  { background: #1a2236; border-radius: 8px; height: 10px; overflow: hidden; }
.progress-bar-fill{ height: 100%; border-radius: 8px; transition: width .6s; }

/* Section headers */
.section-title {
    font-size: 1.6rem; font-weight: 700; color: #e2e8f0;
    border-bottom: 2px solid #2a3a55; padding-bottom: .5rem; margin-bottom: 1.4rem;
}
.section-subtitle { font-size: .9rem; color: #8ba3be; margin-top: -.8rem; margin-bottom: 1.4rem; }

/* Alert boxes */
.alert-success { background: #0a2518; border: 1px solid #276749; border-radius: 10px; padding: 1rem; color: #9ae6b4; }
.alert-error   { background: #250a0a; border: 1px solid #c53030; border-radius: 10px; padding: 1rem; color: #feb2b2; }
.alert-info    { background: #0a1929; border: 1px solid #2b6cb0; border-radius: 10px; padding: 1rem; color: #90cdf4; }
.alert-warn    { background: #1a1200; border: 1px solid #c07a10; border-radius: 10px; padding: 1rem; color: #f6ad55; }

/* Knowledge vault topics */
.topic-btn {
    background: #1a2236; border: 1px solid #2a3a55; border-radius: 10px;
    padding: .8rem 1rem; cursor: pointer; margin-bottom: .5rem;
    font-weight: 500; transition: all .2s;
}

/* MCQ option styles */
.mcq-option { border-radius: 10px; padding: .8rem 1.2rem; margin: .4rem 0; border: 1px solid #2a3a55; cursor: pointer; }
.mcq-correct { background: #0a2518 !important; border-color: #48bb78 !important; color: #9ae6b4 !important; }
.mcq-wrong   { background: #250a0a !important; border-color: #fc8181 !important; color: #feb2b2 !important; }

/* Weak topic alert */
.weak-topic { background: #1a0a0a; border-left: 4px solid #fc8181; border-radius: 8px; padding: .7rem 1rem; margin: .4rem 0; }
.strong-topic { background: #0a1a0a; border-left: 4px solid #48bb78; border-radius: 8px; padding: .7rem 1rem; margin: .4rem 0; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d0f18; }
::-webkit-scrollbar-thumb { background: #2a3a55; border-radius: 3px; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
EXAM_SCHEDULE = [
    {"date": date(2026, 3, 25), "subject": "Physics",   "paper": "Paper 1", "marks": 40, "duration": "1h",    "topics": ["Mechanics", "Waves", "Fields"]},
    {"date": date(2026, 3, 26), "subject": "Physics",   "paper": "Paper 2", "marks": 90, "duration": "2h 15m","topics": ["Electricity", "Thermal Physics", "Modern Physics"]},
    {"date": date(2026, 3, 28), "subject": "Chemistry", "paper": "Paper 1", "marks": 40, "duration": "1h",    "topics": ["Atomic Structure", "Bonding", "Periodic Trends"]},
    {"date": date(2026, 3, 30), "subject": "Chemistry", "paper": "Paper 2", "marks": 90, "duration": "2h 15m","topics": ["Organic Chemistry", "Energetics", "Kinetics"]},
    {"date": date(2026, 4, 6),  "subject": "Maths",     "paper": "Paper 1", "marks": 80, "duration": "2h",    "topics": ["Algebra", "Functions", "Calculus"]},
    {"date": date(2026, 4, 7),  "subject": "Maths",     "paper": "Paper 2 & 3", "marks": 130, "duration": "3h","topics": ["Trigonometry", "Statistics", "Proof"]},
    {"date": date(2026, 4, 9),  "subject": "English",   "paper": "Paper 1", "marks": 40, "duration": "1h 15m","topics": ["Essay Writing", "Article Writing", "Comprehension"]},
    {"date": date(2026, 4, 10), "subject": "English",   "paper": "Paper 2", "marks": 40, "duration": "1h 45m","topics": ["Speech", "Formal Letter", "Blog / Review"]},
]

SUBJECT_COLORS = {
    "Physics":   "#63b3ed",
    "Chemistry": "#68d391",
    "Maths":     "#d6bcfa",
    "English":   "#fbb6ce",
}

SUBJECT_EMOJI = {
    "Physics":   "⚡",
    "Chemistry": "⚗️",
    "Maths":     "📐",
    "English":   "📝",
}

KNOWLEDGE_VAULT = {
    "Mathematics": {
        "Number and Algebra": {
            "keywords": ["Arithmetic sequences", "Geometric sequences", "Sigma notation", "Binomial theorem", "Logarithms", "Exponents", "Complex numbers"],
            "formulas": [
                r"u_n = u_1 + (n-1)d \quad \text{(Arithmetic)}",
                r"u_n = u_1 \cdot r^{n-1} \quad \text{(Geometric)}",
                r"S_n = \frac{n}{2}(2u_1 + (n-1)d)",
                r"S_\infty = \frac{u_1}{1-r}, \quad |r| < 1",
                r"\log_a b = \frac{\ln b}{\ln a}",
                r"(a+b)^n = \sum_{k=0}^{n} \binom{n}{k} a^{n-k} b^k",
            ],
            "concept": "Number and Algebra forms the foundation of IB Mathematics. It bridges arithmetic patterns (sequences) with powerful algebraic tools (logarithms, binomial theorem) used throughout calculus and statistics.",
            "summary": "Master sequence formulas, log laws, and binomial expansion. These appear directly in Paper 1 and as sub-problems in Paper 2.",
            "worked_example": "Find the 15th term and sum of the first 15 terms of the arithmetic sequence 3, 7, 11, ...\n\nd = 4, u₁ = 3\nu₁₅ = 3 + 14(4) = 59\nS₁₅ = 15/2 × (3 + 59) = 465",
            "exam_tips": ["Always identify the type (AP vs GP) first.", "For infinite GP, check |r| < 1 before applying S∞.", "Binomial theorem: write out general term before substituting.", "Log change of base is frequently tested in Paper 1."],
        },
        "Functions": {
            "keywords": ["Domain", "Range", "Composite", "Inverse", "Transformation", "Asymptote", "Rational functions"],
            "formulas": [
                r"(f \circ g)(x) = f(g(x))",
                r"f^{-1}(f(x)) = x",
                r"y = a \cdot f(b(x-h)) + k",
                r"\text{Vertex of } ax^2+bx+c: \left(-\frac{b}{2a},\ c-\frac{b^2}{4a}\right)",
            ],
            "concept": "Functions describe relationships between variables. IB tests domain/range, transformations, composite/inverse functions, and graphs of rational, exponential and logarithmic functions.",
            "summary": "Understand how transformations affect graphs (stretch, shift, reflect). Know how to find inverses algebraically and graphically.",
            "worked_example": "f(x) = 2x+1, g(x) = x². Find (f∘g)(3).\ng(3) = 9, then f(9) = 2(9)+1 = 19.",
            "exam_tips": ["Swap x and y to find inverse, then solve for y.", "Asymptotes: vertical when denominator = 0, horizontal from degree comparison.", "Always state domain restrictions."],
        },
        "Trigonometry": {
            "keywords": ["Sine rule", "Cosine rule", "Radian", "Unit circle", "Identities", "Amplitude", "Period"],
            "formulas": [
                r"\frac{a}{\sin A} = \frac{b}{\sin B} = \frac{c}{\sin C}",
                r"c^2 = a^2 + b^2 - 2ab\cos C",
                r"\sin^2\theta + \cos^2\theta = 1",
                r"\sin 2\theta = 2\sin\theta\cos\theta",
                r"\cos 2\theta = \cos^2\theta - \sin^2\theta",
                r"\text{Area} = \frac{1}{2}ab\sin C",
            ],
            "concept": "Trigonometry in IB covers triangle geometry (sine/cosine rules), circular functions (radian measure, unit circle) and identities used in calculus and proof.",
            "summary": "Know all standard identities, be comfortable converting degrees ↔ radians, and understand graph transformations for trig functions.",
            "worked_example": "In triangle ABC: a=7, b=5, C=60°. Find c.\nc² = 49 + 25 - 2(7)(5)cos60° = 74 - 35 = 39 → c = √39 ≈ 6.24",
            "exam_tips": ["Label triangle sides opposite to angles.", "Use ambiguous case check for sine rule.", "Always work in radians for calculus questions."],
        },
    },
    "Physics": {
        "Mechanics": {
            "keywords": ["Displacement", "Velocity", "Acceleration", "SUVAT", "Newton's laws", "Momentum", "Energy"],
            "formulas": [
                r"v = u + at",
                r"s = ut + \frac{1}{2}at^2",
                r"v^2 = u^2 + 2as",
                r"F = ma",
                r"p = mv",
                r"E_k = \frac{1}{2}mv^2",
                r"E_p = mgh",
                r"W = Fs\cos\theta",
            ],
            "concept": "Mechanics describes how objects move and what causes that motion. It covers kinematics (describing motion) and dynamics (forces causing motion), linked by Newton's three laws.",
            "summary": "Master SUVAT equations, force diagrams, and energy conservation. These are the most frequently tested topics in Paper 1.",
            "worked_example": "A 2 kg ball is dropped from 20 m. Find velocity just before impact.\nUsing v² = u² + 2as: v² = 0 + 2(9.81)(20) = 392.4 → v = 19.8 m/s",
            "exam_tips": ["Always draw a free-body diagram.", "Energy conservation avoids kinematics complexity.", "Check sign conventions (up positive or down positive)."],
        },
        "Electricity": {
            "keywords": ["Current", "Voltage", "Resistance", "Ohm's law", "Kirchhoff", "Power", "EMF"],
            "formulas": [
                r"V = IR",
                r"P = IV = I^2R = \frac{V^2}{R}",
                r"R_{series} = R_1 + R_2 + \cdots",
                r"\frac{1}{R_{parallel}} = \frac{1}{R_1} + \frac{1}{R_2} + \cdots",
                r"Q = It",
                r"\varepsilon = V + Ir",
            ],
            "concept": "Electricity covers the behaviour of charge, current, and voltage in circuits. IB tests circuit analysis (Kirchhoff's laws), power calculations, and internal resistance.",
            "summary": "Be confident with Ohm's law, series/parallel rules, and internal resistance. Draw circuit diagrams neatly.",
            "worked_example": "Two 6Ω resistors in parallel: 1/R = 1/6 + 1/6 = 1/3 → R = 3Ω.\nConnected to 12V source: I = 12/3 = 4A.",
            "exam_tips": ["Redraw complex circuits step by step.", "Kirchhoff's voltage law: sum of EMFs = sum of voltage drops.", "Internal resistance drops terminal voltage under load."],
        },
        "Waves": {
            "keywords": ["Wavelength", "Frequency", "Amplitude", "Interference", "Diffraction", "Doppler", "Superposition"],
            "formulas": [
                r"v = f\lambda",
                r"T = \frac{1}{f}",
                r"f' = f\cdot\frac{v \pm v_o}{v \mp v_s} \quad \text{(Doppler)}",
                r"I \propto A^2",
                r"n_1 \sin\theta_1 = n_2 \sin\theta_2 \quad \text{(Snell's law)}",
            ],
            "concept": "Waves transfer energy without transferring matter. IB covers transverse/longitudinal waves, sound, light (optics), and quantum phenomena.",
            "summary": "Understand wave properties, interference patterns (double slit), and the Doppler effect. Connect mathematics to physical interpretation.",
            "worked_example": "Sound at 440 Hz, v=340 m/s. λ = v/f = 340/440 = 0.773 m",
            "exam_tips": ["Constructive interference: path difference = nλ.", "Destructive: path diff = (n+0.5)λ.", "Doppler: observer moving toward source → frequency increases."],
        },
        "Energy": {
            "keywords": ["Kinetic energy", "Potential energy", "Conservation", "Efficiency", "Power", "Thermal energy"],
            "formulas": [
                r"E_k = \frac{1}{2}mv^2",
                r"E_p = mgh",
                r"\eta = \frac{P_{useful}}{P_{input}} \times 100\%",
                r"P = \frac{W}{t} = Fv",
                r"Q = mc\Delta T",
            ],
            "concept": "Energy conservation is fundamental to IB Physics. Energy transforms between kinetic, potential, thermal, electrical, and chemical forms. Power measures energy transfer rate.",
            "summary": "Apply energy conservation in mechanics problems. Link thermal physics (Q = mcΔT) to energy transfer and efficiency.",
            "worked_example": "Car 1200 kg decelerates from 30 m/s to 0. Energy dissipated as heat:\nΔEk = ½(1200)(30²) = 540,000 J = 540 kJ",
            "exam_tips": ["Energy lost = Δ(Kinetic) in friction problems.", "Efficiency is always less than 100% — justify losses.", "Power = force × velocity for moving objects."],
        },
        "Forces": {
            "keywords": ["Normal force", "Friction", "Tension", "Weight", "Net force", "Free body diagram", "Equilibrium"],
            "formulas": [
                r"F_{net} = ma",
                r"W = mg",
                r"f = \mu N",
                r"\sum F = 0 \quad \text{(Equilibrium)}",
                r"F_G = \frac{Gm_1m_2}{r^2}",
            ],
            "concept": "Forces cause acceleration or maintain equilibrium. IB expects students to resolve forces, apply Newton's laws, and understand friction, gravity, and tension in connected systems.",
            "summary": "Draw FBDs before any calculation. Resolve all forces into components. Apply ΣF = ma for each direction.",
            "worked_example": "Block 10 kg on 30° incline, μ=0.3. Net force?\nW∥ = 10(9.81)sin30 = 49.05 N down slope\nN = 10(9.81)cos30 = 84.96 N\nf = 0.3(84.96) = 25.5 N (up slope)\nF_net = 49.05 - 25.5 = 23.55 N down slope",
            "exam_tips": ["Always resolve forces parallel and perpendicular to incline.", "Static friction ≤ μₛN; kinetic friction = μₖN.", "Tension is same throughout a massless string."],
        },
    },
    "Chemistry": {
        "Atomic Structure": {
            "keywords": ["Proton", "Neutron", "Electron", "Isotope", "Orbital", "Electronic configuration", "Ionisation energy"],
            "formulas": [
                r"A = Z + N \quad \text{(mass number = protons + neutrons)}",
                r"E = hf = \frac{hc}{\lambda}",
                r"\text{1st IE}: X(g) \rightarrow X^+(g) + e^-",
            ],
            "concept": "Atoms contain protons, neutrons, and electrons. Electrons occupy shells and subshells (s,p,d,f). Ionisation energy evidence supports orbital theory and periodic trends.",
            "summary": "Know electronic configurations up to Z=36, trends in ionisation energy, and how emission spectra relate to energy level transitions.",
            "worked_example": "Write the electron configuration of Fe (Z=26):\n[Ar] 3d⁶ 4s²\nFe²⁺: [Ar] 3d⁶ (loses 4s electrons first)",
            "exam_tips": ["3d fills before 4s but 4s is removed first in ions.", "Successive IE data: sudden jump indicates new inner shell.", "Emission spectrum → discrete energy levels (Bohr model evidence)."],
        },
        "Bonding": {
            "keywords": ["Ionic", "Covalent", "Metallic", "Polar", "VSEPR", "Electronegativity", "Intermolecular forces"],
            "formulas": [
                r"\Delta EN > 1.7 \Rightarrow \text{Ionic bond}",
                r"\text{Bond order} = \frac{(\text{bonding} - \text{antibonding})}{2}",
            ],
            "concept": "Chemical bonds arise from electrostatic attraction. Bond type depends on electronegativity difference. Molecular shape (VSEPR) determines polarity and physical properties.",
            "summary": "Use VSEPR to predict shape (linear, trigonal planar, tetrahedral, etc.). Link polarity to electronegativity and molecular symmetry.",
            "worked_example": "BF₃: 3 bonding pairs, 0 lone pairs → Trigonal planar, 120°, non-polar despite polar bonds (symmetrical cancellation)",
            "exam_tips": ["Lone pairs take more space → compress bond angles.", "Polar molecule ≠ polar bonds: check symmetry.", "Metallic bonding: sea of delocalised electrons explains conductivity."],
        },
        "Organic Chemistry": {
            "keywords": ["Homologous series", "Functional group", "Isomers", "Addition", "Substitution", "Elimination", "Condensation"],
            "formulas": [
                r"C_nH_{2n+2} \text{ (alkanes)}",
                r"C_nH_{2n} \text{ (alkenes)}",
                r"C_nH_{2n-2} \text{ (alkynes)}",
            ],
            "concept": "Organic chemistry studies carbon compounds. Functional groups determine reactivity. Reaction types (addition, substitution, elimination, condensation) link structure to mechanism.",
            "summary": "Know the key functional groups (alcohol, aldehyde, ketone, carboxylic acid, ester, amine, amide) and their reactions.",
            "worked_example": "Ethanol + ethanoic acid → ethyl ethanoate + water (Esterification/Condensation)\nCH₃CH₂OH + CH₃COOH → CH₃COOCH₂CH₃ + H₂O",
            "exam_tips": ["Name compounds systematically: longest chain → prefixes.", "Distinguish SN1 (tertiary) vs SN2 (primary) mechanisms.", "Know oxidation states: aldehyde → carboxylic acid; alcohol → aldehyde."],
        },
        "Periodic Trends": {
            "keywords": ["Electronegativity", "Atomic radius", "Ionisation energy", "Electron affinity", "Melting point", "Reactivity"],
            "formulas": [
                r"\text{Across period: radius } \downarrow, \text{ IE } \uparrow, \text{ EN } \uparrow",
                r"\text{Down group: radius } \uparrow, \text{ IE } \downarrow, \text{ EN } \downarrow",
            ],
            "concept": "The periodic table organises elements by increasing proton number, revealing repeating trends in physical and chemical properties linked to electronic structure.",
            "summary": "Explain all trends using nuclear charge, shielding, and atomic radius. Link trends to reactivity and bond type.",
            "worked_example": "Why does Na have lower IE than Mg?\nNa: [Ne]3s¹ — one electron in outer shell, easier to remove.\nMg: [Ne]3s² — greater nuclear charge pulls electrons more tightly.",
            "exam_tips": ["Anomalies: O < N (paired 2p electron repels); Be, Mg, Ca exceptions in IE.", "Shielding from inner shells is key to explaining all trend anomalies.", "Metallic character decreases across a period."],
        },
    },
    "English": {
        "Essay Writing": {
            "keywords": ["Thesis", "Argument", "Evidence", "Analysis", "Counter-argument", "Conclusion", "Coherence"],
            "formulas": ["Introduction: Hook → Context → Thesis", "Body: Point → Evidence → Explain → Link", "Conclusion: Restate thesis → Wider significance → Clincher"],
            "concept": "A well-structured essay presents a clear argument supported by evidence. IB rewards critical analysis, coherent structure, and precise language.",
            "summary": "Use the PEE (Point–Evidence–Explain) framework. Every paragraph must advance the central thesis. Avoid narration — analyse.",
            "worked_example": "Q: 'Education must prepare students for uncertainty.' Discuss.\nThesis: While traditional education values knowledge recall, modern education must prioritise adaptability and critical thinking to equip students for an unpredictable world.",
            "exam_tips": ["Underline key terms in the question — answer exactly what is asked.", "Avoid 'I think' — be assertive: 'Evidence suggests...'", "Leave 5 minutes to check spelling and coherence.", "One idea per paragraph — do not crowd arguments."],
        },
        "Speech Writing": {
            "keywords": ["Rhetorical devices", "Anaphora", "Ethos", "Pathos", "Logos", "Tricolon", "Audience"],
            "formulas": ["Opening: Address + Hook (rhetorical Q or anecdote)", "Body: 3 main arguments with evidence", "Close: Call to action + Memorable final line"],
            "concept": "Speeches are written to persuade, inspire, or inform a live audience. Unlike essays, speeches use rhetorical devices, direct address, and rhythm.",
            "summary": "Use 'Ladies and gentlemen' openings, vary sentence length for rhythm, and always end with a powerful call to action.",
            "worked_example": "Opening line: 'What if I told you that the greatest threat to your future sits in the palm of your hand?' — rhetorical question creating immediate engagement.",
            "exam_tips": ["Use parenthetical asides to sound natural: 'And believe me — I've seen this firsthand.'", "Tricolon creates rhythm: 'We must act now, act boldly, act together.'", "Direct address ('you', 'we') builds audience connection.", "Anaphora (repeating phrase) is highly examinable."],
        },
        "Formal Letter": {
            "keywords": ["Salutation", "Purpose", "Tone", "Formal register", "Sign-off", "Complaint", "Request"],
            "formulas": ["Sender's Address", "Date", "Recipient's Address", "Dear [Title Surname], / Dear Sir/Madam,", "Body paragraphs", "Yours sincerely / Yours faithfully"],
            "concept": "Formal letters follow strict conventions. 'Yours sincerely' when you know the name; 'Yours faithfully' when you don't. Purpose must be clear in the first paragraph.",
            "summary": "State purpose clearly, use formal vocabulary (no contractions), and maintain a respectful, professional tone throughout.",
            "worked_example": "First paragraph: 'I am writing to express my concern regarding the recent changes to the school library operating hours, which have significantly impacted students' ability to access essential resources.'",
            "exam_tips": ["Never use contractions in formal letters (don't → do not).", "End by requesting action: 'I trust this matter will receive your prompt attention.'", "Match tone to purpose: complaint = firm but polite; request = courteous.", "Check address format in the mark scheme rubric."],
        },
        "Article Writing": {
            "keywords": ["Headline", "Sub-heading", "Lead paragraph", "Audience", "Anecdote", "Feature article", "Opinion piece"],
            "formulas": ["Catchy Headline (alliteration / question)", "Deck (sub-headline, 1 sentence)", "Lead paragraph (who, what, when, where, why)", "Body: anecdotes, statistics, expert quotes", "Closing paragraph with reflection or call to action"],
            "concept": "Articles inform and engage a specific audience. IB distinguishes between news articles (factual), feature articles (narrative), and opinion pieces (persuasive).",
            "summary": "Adapt tone and language to audience. Feature articles use vivid description; opinion pieces use persuasive rhetoric. Headlines must hook the reader instantly.",
            "worked_example": "Headline: 'The Homework Trap: Why Less Can Mean More'\nDeck: As schools push for higher achievement, researchers ask whether mountains of homework are helping — or hindering.',",
            "exam_tips": ["Always include a headline — you lose marks without it.", "Use statistics as evidence: '74% of students report...'", "Feature articles may include sub-headings — check the question.", "Vary sentence structure for rhythm and readability."],
        },
    },
}

FLASHCARDS_DATA = {
    "Physics": [
        {"front": "Newton's Second Law", "back": "F = ma\n(Force = mass × acceleration)"},
        {"front": "Kinetic Energy", "back": "Eₖ = ½mv²"},
        {"front": "Wave Equation", "back": "v = fλ\n(speed = frequency × wavelength)"},
        {"front": "Ohm's Law", "back": "V = IR\n(Voltage = Current × Resistance)"},
        {"front": "Gravitational Potential Energy", "back": "Ep = mgh"},
        {"front": "Snell's Law", "back": "n₁sinθ₁ = n₂sinθ₂"},
        {"front": "Coulomb's Law", "back": "F = kq₁q₂/r²"},
        {"front": "Power", "back": "P = IV = I²R = V²/R"},
        {"front": "Doppler Effect (moving source)", "back": "f' = f × v/(v ± vₛ)"},
        {"front": "Internal Resistance", "back": "ε = V + Ir\n(EMF = terminal voltage + internal loss)"},
    ],
    "Chemistry": [
        {"front": "Rate of Reaction", "back": "Rate = k[A]^m[B]^n"},
        {"front": "Ideal Gas Law", "back": "PV = nRT"},
        {"front": "Hess's Law", "back": "ΔH reaction = ΣΔHf(products) − ΣΔHf(reactants)"},
        {"front": "pH Definition", "back": "pH = −log[H⁺]"},
        {"front": "Henderson–Hasselbalch", "back": "pH = pKₐ + log([A⁻]/[HA])"},
        {"front": "Empirical Formula", "back": "Simplest whole-number ratio of atoms in a compound"},
        {"front": "Bond Enthalpy", "back": "ΔH = Σ(bonds broken) − Σ(bonds formed)"},
        {"front": "Kw at 25°C", "back": "Kw = [H⁺][OH⁻] = 1×10⁻¹⁴"},
        {"front": "Avogadro's Number", "back": "Nₐ = 6.022 × 10²³ mol⁻¹"},
        {"front": "Hybridisation sp³", "back": "Tetrahedral, 109.5° (e.g. CH₄, H₂O, NH₃)"},
    ],
    "Maths": [
        {"front": "Quadratic Formula", "back": "x = (−b ± √(b²−4ac)) / 2a"},
        {"front": "Sum of Arithmetic Series", "back": "Sₙ = n/2 × (2u₁ + (n−1)d)"},
        {"front": "Sum of Geometric Series", "back": "Sₙ = u₁(rⁿ−1)/(r−1)"},
        {"front": "Sine Rule", "back": "a/sinA = b/sinB = c/sinC"},
        {"front": "Cosine Rule", "back": "c² = a² + b² − 2ab·cosC"},
        {"front": "Product Rule (Calculus)", "back": "d/dx[uv] = u'v + uv'"},
        {"front": "Chain Rule (Calculus)", "back": "dy/dx = (dy/du)(du/dx)"},
        {"front": "Integration by Parts", "back": "∫u dv = uv − ∫v du"},
        {"front": "Maclaurin Series for eˣ", "back": "eˣ = 1 + x + x²/2! + x³/3! + ..."},
        {"front": "Double Angle: sin2θ", "back": "sin2θ = 2sinθcosθ"},
    ],
    "English": [
        {"front": "Anaphora", "back": "Repetition of a word/phrase at the start of successive clauses\n(e.g. 'We shall fight...We shall never surrender')"},
        {"front": "Tricolon", "back": "A series of three parallel elements\n(e.g. 'Life, liberty, and the pursuit of happiness')"},
        {"front": "Ethos", "back": "Appeal to credibility/authority"},
        {"front": "Pathos", "back": "Appeal to emotion"},
        {"front": "Logos", "back": "Appeal to logic/reason"},
        {"front": "Epistrophe", "back": "Repetition at the END of clauses\n(e.g. '...of the people, by the people, for the people')"},
        {"front": "Hyperbole", "back": "Deliberate exaggeration for effect"},
        {"front": "PEE Framework", "back": "Point → Evidence → Explain/Evaluate"},
        {"front": "Formal Letter Sign-off", "back": "Known name → Yours sincerely\nUnknown → Yours faithfully"},
        {"front": "Feature Article Structure", "back": "Headline → Deck → Lead → Body (anecdotes + stats + quotes) → Reflection"},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE  CLASS
# ─────────────────────────────────────────────────────────────────────────────
class Database:
    """Handles all SQLite operations for the application."""

    def __init__(self, db_path: str = "exam_ascent.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        """Create all required tables if they don't exist."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS quiz_results (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject     TEXT NOT NULL,
                    topic       TEXT NOT NULL,
                    q_type      TEXT NOT NULL,
                    difficulty  TEXT NOT NULL,
                    correct     INTEGER NOT NULL,
                    total       INTEGER NOT NULL,
                    timestamp   TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS saved_questions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject     TEXT NOT NULL,
                    topic       TEXT NOT NULL,
                    question    TEXT NOT NULL,
                    answer      TEXT NOT NULL,
                    timestamp   TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS study_sessions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject     TEXT NOT NULL,
                    minutes     INTEGER NOT NULL,
                    timestamp   TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS weak_topics (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject     TEXT NOT NULL,
                    topic       TEXT NOT NULL,
                    accuracy    REAL NOT NULL,
                    updated_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS mock_results (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_name   TEXT NOT NULL,
                    score       INTEGER NOT NULL,
                    total       INTEGER NOT NULL,
                    time_taken  INTEGER NOT NULL,
                    timestamp   TEXT NOT NULL
                );
            """)

    # ── Quiz results ──────────────────────────────────────────────────────────
    def save_quiz_result(self, subject, topic, q_type, difficulty, correct, total):
        ts = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO quiz_results(subject,topic,q_type,difficulty,correct,total,timestamp) VALUES(?,?,?,?,?,?,?)",
                (subject, topic, q_type, difficulty, correct, total, ts),
            )
        self._update_weak_topics(subject, topic, correct, total)

    def get_quiz_results(self) -> pd.DataFrame:
        with self._connect() as conn:
            df = pd.read_sql("SELECT * FROM quiz_results ORDER BY timestamp DESC", conn)
        return df

    # ── Weak topics ───────────────────────────────────────────────────────────
    def _update_weak_topics(self, subject, topic, correct, total):
        if total == 0:
            return
        accuracy = (correct / total) * 100
        ts = datetime.now().isoformat()
        with self._connect() as conn:
            exists = conn.execute(
                "SELECT id FROM weak_topics WHERE subject=? AND topic=?", (subject, topic)
            ).fetchone()
            if exists:
                conn.execute(
                    "UPDATE weak_topics SET accuracy=?, updated_at=? WHERE subject=? AND topic=?",
                    (accuracy, ts, subject, topic),
                )
            else:
                conn.execute(
                    "INSERT INTO weak_topics(subject,topic,accuracy,updated_at) VALUES(?,?,?,?)",
                    (subject, topic, accuracy, ts),
                )

    def get_weak_topics(self) -> pd.DataFrame:
        with self._connect() as conn:
            df = pd.read_sql("SELECT * FROM weak_topics ORDER BY accuracy ASC", conn)
        return df

    # ── Study sessions ────────────────────────────────────────────────────────
    def log_study_session(self, subject, minutes):
        ts = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO study_sessions(subject,minutes,timestamp) VALUES(?,?,?)",
                (subject, minutes, ts),
            )

    def get_study_sessions(self) -> pd.DataFrame:
        with self._connect() as conn:
            df = pd.read_sql("SELECT * FROM study_sessions ORDER BY timestamp DESC", conn)
        return df

    # ── Saved questions ───────────────────────────────────────────────────────
    def save_question(self, subject, topic, question, answer):
        ts = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO saved_questions(subject,topic,question,answer,timestamp) VALUES(?,?,?,?,?)",
                (subject, topic, question, answer, ts),
            )

    def get_saved_questions(self) -> pd.DataFrame:
        with self._connect() as conn:
            df = pd.read_sql("SELECT * FROM saved_questions ORDER BY timestamp DESC", conn)
        return df

    # ── Mock results ──────────────────────────────────────────────────────────
    def save_mock_result(self, exam_name, score, total, time_taken):
        ts = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO mock_results(exam_name,score,total,time_taken,timestamp) VALUES(?,?,?,?,?)",
                (exam_name, score, total, time_taken, ts),
            )

    def get_mock_results(self) -> pd.DataFrame:
        with self._connect() as conn:
            df = pd.read_sql("SELECT * FROM mock_results ORDER BY timestamp DESC", conn)
        return df

    # ── Aggregates ────────────────────────────────────────────────────────────
    def get_total_questions(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COALESCE(SUM(total),0) FROM quiz_results").fetchone()
        return int(row[0])

    def get_overall_accuracy(self) -> float:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(correct),0), COALESCE(SUM(total),0) FROM quiz_results"
            ).fetchone()
        correct, total = row
        return round((correct / total) * 100, 1) if total > 0 else 0.0

    def get_study_streak(self) -> int:
        """Calculate consecutive days with study sessions."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT DATE(timestamp) as d FROM study_sessions ORDER BY d DESC"
            ).fetchall()
        if not rows:
            return 0
        streak, today = 0, date.today()
        for i, (d,) in enumerate(rows):
            day = date.fromisoformat(d)
            if (today - day).days == i:
                streak += 1
            else:
                break
        return streak

# ─────────────────────────────────────────────────────────────────────────────
# GEMINI  AI CLASS
# ─────────────────────────────────────────────────────────────────────────────
class GeminiAI:
    """Wrapper around Google Gemini API for all AI-generated content."""

    def __init__(self):
        self.model = None
        self._configured = False
        self._configure()

    def _configure(self):
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            self._configured = True
        except Exception as e:
            self._configured = False

    def is_ready(self) -> bool:
        return self._configured

    def _call(self, prompt: str, max_tokens: int = 2048) -> Optional[str]:
        """Low-level Gemini API call with error handling."""
        if not self._configured:
            return None
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                ),
            )
            return response.text
        except Exception as e:
            st.error(f"Gemini API error: {e}")
            return None

    def generate_mcq(self, subject: str, topic: str, difficulty: str) -> Optional[dict]:
        """Generate a single MCQ with 4 options, answer, and explanation."""
        prompt = f"""
You are a senior IB examiner with expertise in creating exam-standard questions.

Generate ONE challenging IB {subject} {difficulty}-level multiple choice question on the topic: {topic}.

The question must:
- Match the style of Save My Exams and Revision Village
- Be at IB Higher Level standard for {difficulty} difficulty
- Test conceptual understanding, not just recall
- Have exactly 4 options labeled A, B, C, D
- Have ONE clearly correct answer
- Include a detailed step-by-step mark scheme explanation (3–5 steps)

Return ONLY valid JSON in this exact structure:
{{
  "question": "...",
  "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "correct": "A",
  "explanation": "Step 1: ...\\nStep 2: ...\\nStep 3: ...",
  "marks": 1
}}
"""
        raw = self._call(prompt)
        if not raw:
            return None
        return self._parse_json(raw)

    def generate_structured_question(self, subject: str, topic: str, difficulty: str) -> Optional[dict]:
        """Generate a multi-part structured exam question with mark scheme."""
        prompt = f"""
You are a senior IB examiner.

Create ONE multi-part IB {subject} {difficulty} structured question on: {topic}.

The question must:
- Be in the style of an IB Paper 2 / Paper 3 exam question
- Have exactly 3 parts: (a), (b), (c)
- Total marks: 9–12 marks
- Each part must build on the previous (scaffolded)
- Part (c) should require higher-order thinking (synthesis/evaluation)

Return ONLY valid JSON:
{{
  "context": "Background scenario or data provided to the student...",
  "parts": [
    {{"part": "a", "question": "...", "marks": 3, "answer": "...", "mark_scheme": "..."}},
    {{"part": "b", "question": "...", "marks": 4, "answer": "...", "mark_scheme": "..."}},
    {{"part": "c", "question": "...", "marks": 4, "answer": "...", "mark_scheme": "..."}}
  ],
  "total_marks": 11
}}
"""
        raw = self._call(prompt)
        if not raw:
            return None
        return self._parse_json(raw)

    def generate_important_questions(self, subject: str, topic: str) -> Optional[list]:
        """Generate a list of likely high-value exam questions."""
        prompt = f"""
You are an IB expert coach who has analysed 10 years of past papers.

Generate 5 HIGH-PRIORITY exam questions for IB {subject} — {topic}.

These should be:
- Questions that frequently appear in IB exams (high probability)
- A mix of conceptual and calculation questions  
- At Higher Level standard
- Each with a concise model answer (2–4 sentences or steps)

Return ONLY valid JSON array:
[
  {{
    "question": "...",
    "type": "calculation | conceptual | definition",
    "difficulty": "Hard | Very Hard",
    "model_answer": "...",
    "why_important": "Why this question is likely to appear..."
  }}
]
"""
        raw = self._call(prompt)
        if not raw:
            return None
        result = self._parse_json(raw)
        return result if isinstance(result, list) else None

    def generate_study_plan(self, weak_topics: list, exam_schedule: list) -> Optional[str]:
        """Generate a personalized AI study plan."""
        today = date.today().isoformat()
        exams_str = "\n".join(
            f"- {e['date']} | {e['subject']} {e['paper']}" for e in exam_schedule
        )
        weak_str = ", ".join(weak_topics) if weak_topics else "None identified yet"

        prompt = f"""
You are an elite IB study coach specializing in high-performance exam preparation.

Today's date: {today}
Upcoming exams:
{exams_str}

Student's identified weak topics: {weak_str}

Generate a DETAILED, PERSONALIZED daily study plan from today until the last exam.

The plan must:
- Prioritize weak topics in early weeks
- Allocate more revision time to subjects with earlier exams
- Include daily breakdown (Monday–Sunday)
- Include specific activities: active recall, past paper practice, concept mapping
- Be realistic (2–4 hours study per day maximum)
- Include rest days and revision checkpoints
- Use clear formatting with days, subjects, and time blocks

Format as a structured, easy-to-follow markdown timetable.
"""
        return self._call(prompt, max_tokens=3000)

    def generate_mock_exam(self, subject: str, difficulty: str, num_questions: int = 10) -> Optional[list]:
        """Generate a full set of MCQ questions for a mock exam."""
        prompt = f"""
You are an IB chief examiner.

Generate {num_questions} IB {subject} multiple choice questions for a full mock exam paper.

Requirements:
- Mix of {difficulty} difficulty
- Cover different topics within {subject}
- Each question tests a different concept  
- IB exam style (command terms, scientific notation, units)
- 4 options each (A, B, C, D) with ONE correct answer
- Brief explanation for each correct answer

Return ONLY valid JSON array:
[
  {{
    "question": "...",
    "topic": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct": "B",
    "explanation": "..."
  }}
]
"""
        raw = self._call(prompt, max_tokens=4096)
        if not raw:
            return None
        result = self._parse_json(raw)
        return result if isinstance(result, list) else None

    @staticmethod
    def _parse_json(raw: str) -> Optional[any]:
        """Extract and parse JSON from Gemini response."""
        try:
            # Strip markdown code fences if present
            clean = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            # Attempt to find JSON block within text
            match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
        return None

# ─────────────────────────────────────────────────────────────────────────────
# HELPER  UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
def days_until(target: date) -> int:
    return max(0, (target - date.today()).days)

def get_next_exam() -> Optional[dict]:
    today = date.today()
    future = [e for e in EXAM_SCHEDULE if e["date"] >= today]
    return future[0] if future else None

def subject_badge(subject: str) -> str:
    cls = f"badge-{subject.lower()}"
    emoji = SUBJECT_EMOJI.get(subject, "📚")
    return f'<span class="subject-badge {cls}">{emoji} {subject}</span>'

def color_for(subject: str) -> str:
    return SUBJECT_COLORS.get(subject, "#90cdf4")

def accuracy_color(acc: float) -> str:
    if acc >= 80:
        return "#48bb78"
    if acc >= 60:
        return "#f6ad55"
    return "#fc8181"

def render_card(content_html: str, extra_class: str = ""):
    st.markdown(f'<div class="ea-card {extra_class}">{content_html}</div>', unsafe_allow_html=True)

def render_metric(value, label: str, color: str = "#63b3ed"):
    st.markdown(
        f"""<div class="metric-card">
          <div class="metric-value" style="color:{color}">{value}</div>
          <div class="metric-label">{label}</div>
        </div>""",
        unsafe_allow_html=True,
    )

def render_progress_bar(pct: float, color: str = "#63b3ed"):
    st.markdown(
        f"""<div class="progress-bar-bg">
          <div class="progress-bar-fill" style="width:{min(pct,100):.1f}%;background:{color}"></div>
        </div>""",
        unsafe_allow_html=True,
    )

def render_section_header(title: str, subtitle: str = ""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def page_dashboard(db: Database):
    render_section_header("🚀 Dashboard", "Your IB exam preparation overview at a glance")

    next_exam = get_next_exam()
    total_q   = db.get_total_questions()
    accuracy  = db.get_overall_accuracy()
    streak    = db.get_study_streak()

    # Countdown + Metrics
    col_cd, col_m1, col_m2, col_m3 = st.columns([2, 1, 1, 1])

    with col_cd:
        if next_exam:
            days = days_until(next_exam["date"])
            st.markdown(
                f"""<div class="countdown-box">
                  <div class="countdown-title">⏳ NEXT EXAM COUNTDOWN</div>
                  <div class="countdown-time">{days} days</div>
                  <div class="countdown-sub">
                    {SUBJECT_EMOJI.get(next_exam['subject'],'📚')} {next_exam['subject']} — {next_exam['paper']}<br>
                    {next_exam['date'].strftime('%A, %d %B %Y')}
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="countdown-box"><div class="countdown-title">🎉 All exams completed!</div></div>', unsafe_allow_html=True)

    with col_m1:
        render_metric(total_q, "Questions Solved", "#63b3ed")
    with col_m2:
        render_metric(f"{accuracy}%", "Overall Accuracy", accuracy_color(accuracy))
    with col_m3:
        render_metric(f"🔥 {streak}", "Day Streak", "#f6ad55")

    st.markdown("---")

    # Exam Countdown Cards
    render_section_header("📅 Upcoming Exams", "Countdowns to each paper")

    cols = st.columns(4)
    today = date.today()
    upcoming = [e for e in EXAM_SCHEDULE if e["date"] >= today][:4]
    for i, exam in enumerate(upcoming):
        days = days_until(exam["date"])
        color = color_for(exam["subject"])
        with cols[i % 4]:
            st.markdown(
                f"""<div class="ea-card" style="border-left:4px solid {color}; text-align:center">
                  <div style="font-size:2rem;font-weight:700;color:{color}">{days}</div>
                  <div style="font-size:.7rem;color:#8ba3be;text-transform:uppercase;letter-spacing:.06em">days</div>
                  <div style="font-size:.95rem;font-weight:600;margin-top:.5rem">{exam['subject']}</div>
                  <div style="font-size:.8rem;color:#8ba3be">{exam['paper']}</div>
                  <div style="font-size:.75rem;color:#4a6a8a;margin-top:.3rem">{exam['date'].strftime('%d %b')}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Performance Charts
    col_l, col_r = st.columns(2)

    with col_l:
        render_section_header("📊 Accuracy by Subject")
        df = db.get_quiz_results()
        if not df.empty:
            agg = df.groupby("subject").apply(
                lambda x: round(x["correct"].sum() / x["total"].sum() * 100, 1)
            ).reset_index()
            agg.columns = ["Subject", "Accuracy"]
            fig = px.bar(
                agg, x="Subject", y="Accuracy",
                color="Accuracy",
                color_continuous_scale=["#fc8181", "#f6ad55", "#68d391"],
                range_color=[0, 100],
                template="plotly_dark",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0", showlegend=False, height=280,
                margin=dict(l=0, r=0, t=20, b=0),
                coloraxis_showscale=False,
            )
            fig.update_traces(marker_line_color="#0d0f18", marker_line_width=1)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<div class="alert-info">📝 Complete some practice questions to see your accuracy chart.</div>', unsafe_allow_html=True)

    with col_r:
        render_section_header("📈 Questions Over Time")
        df = db.get_quiz_results()
        if not df.empty:
            df["date"] = pd.to_datetime(df["timestamp"]).dt.date
            daily = df.groupby("date")["total"].sum().reset_index()
            fig2 = px.area(
                daily, x="date", y="total",
                template="plotly_dark",
                color_discrete_sequence=["#63b3ed"],
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0", height=280,
                margin=dict(l=0, r=0, t=20, b=0),
                xaxis_title="", yaxis_title="Questions",
            )
            fig2.update_traces(fillcolor="rgba(99,179,237,0.15)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.markdown('<div class="alert-info">📝 Start practicing to see your progress.</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Weak Topics
    render_section_header("⚠️ Weak Topics Detected", "Topics where your accuracy is below 60%")
    weak_df = db.get_weak_topics()
    if not weak_df.empty:
        for _, row in weak_df.iterrows():
            acc = row["accuracy"]
            style = "weak-topic" if acc < 60 else "strong-topic"
            icon = "🔴" if acc < 60 else "🟢"
            st.markdown(
                f'<div class="{style}">{icon} <strong>{row["subject"]} — {row["topic"]}</strong>: {acc:.1f}% accuracy</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<div class="alert-info">✅ No weak topics identified yet. Complete practice questions to get insights.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: EXAM TIMETABLE
# ─────────────────────────────────────────────────────────────────────────────
def page_timetable():
    render_section_header("📅 Exam Timetable", "Your complete IB exam schedule with countdowns")

    today = date.today()
    next_exam = get_next_exam()

    # Live Countdown
    if next_exam:
        days = days_until(next_exam["date"])
        hours_rem = days * 24
        color = color_for(next_exam["subject"])
        st.markdown(
            f"""<div class="countdown-box" style="margin-bottom:1.5rem;border-color:{color}">
              <div class="countdown-title" style="color:{color}">
                {SUBJECT_EMOJI.get(next_exam['subject'],'📚')} NEXT EXAM: {next_exam['subject'].upper()} — {next_exam['paper'].upper()}
              </div>
              <div class="countdown-time" style="color:{color}">{days} Days  {hours_rem % 24:02d}h remaining</div>
              <div class="countdown-sub" style="color:{color}">
                {next_exam['date'].strftime('%A, %d %B %Y')} &nbsp;|&nbsp;
                {next_exam['marks']} marks &nbsp;|&nbsp; {next_exam['duration']}
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

    # Timeline
    for exam in EXAM_SCHEDULE:
        days   = days_until(exam["date"])
        color  = color_for(exam["subject"])
        is_past   = exam["date"] < today
        is_next   = next_exam and exam["date"] == next_exam["date"] and not is_past

        if is_past:
            cls, label = "past", "✅ Completed"
        elif is_next:
            cls, label = "next", f"🔥 NEXT — {days} days"
        elif days == 0:
            cls, label = "today", "📌 TODAY"
        else:
            cls, label = "upcoming", f"⏳ {days} days"

        topics_html = " ".join(
            f'<span style="background:#1a2a3a;border:1px solid #2a3a55;border-radius:6px;padding:.2rem .6rem;font-size:.75rem;margin:.2rem">{t}</span>'
            for t in exam["topics"]
        )

        st.markdown(
            f"""<div class="exam-card {cls}" style="border-left-color:{color}">
              <div style="display:flex;justify-content:space-between;align-items:start;flex-wrap:wrap;gap:.5rem">
                <div>
                  <div style="font-size:1.1rem;font-weight:700;color:{color}">
                    {SUBJECT_EMOJI.get(exam['subject'],'📚')} {exam['subject']} — {exam['paper']}
                  </div>
                  <div style="font-size:.85rem;color:#8ba3be;margin-top:.25rem">
                    📅 {exam['date'].strftime('%A, %d %B %Y')} &nbsp;|&nbsp;
                    ⏱ {exam['duration']} &nbsp;|&nbsp;
                    📊 {exam['marks']} marks
                  </div>
                  <div style="margin-top:.6rem">{topics_html}</div>
                </div>
                <div style="text-align:right">
                  <span style="background:#0d0f18;border:1px solid {color};color:{color};
                    border-radius:8px;padding:.3rem .8rem;font-size:.8rem;font-weight:600">{label}</span>
                </div>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

    # Summary table
    st.markdown("---")
    render_section_header("📋 Schedule Summary")
    summary_data = []
    for e in EXAM_SCHEDULE:
        d = days_until(e["date"])
        summary_data.append({
            "Date": e["date"].strftime("%d %b %Y"),
            "Subject": f"{SUBJECT_EMOJI.get(e['subject'],'')} {e['subject']}",
            "Paper": e["paper"],
            "Marks": e["marks"],
            "Duration": e["duration"],
            "Days Away": d if e["date"] >= today else "Done ✅",
        })
    st.dataframe(
        pd.DataFrame(summary_data),
        use_container_width=True,
        hide_index=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: KNOWLEDGE VAULT
# ─────────────────────────────────────────────────────────────────────────────
def page_knowledge_vault():
    render_section_header("📚 Knowledge Vault", "Structured notes, formulas, and examples for every topic")

    subject = st.selectbox("Select Subject", list(KNOWLEDGE_VAULT.keys()))
    if not subject:
        return

    topics = KNOWLEDGE_VAULT[subject]
    topic  = st.selectbox("Select Topic", list(topics.keys()))
    if not topic:
        return

    data = topics[topic]

    # ── Keywords ──────────────────────────────────────────────────────────────
    with st.expander("🔑 Key Words", expanded=True):
        kw_html = " ".join(
            f'<span style="background:#1a2a45;border:1px solid #2b6cb0;color:#90cdf4;border-radius:20px;padding:.25rem .75rem;font-size:.8rem;margin:.2rem;display:inline-block">{k}</span>'
            for k in data["keywords"]
        )
        st.markdown(kw_html, unsafe_allow_html=True)

    # ── Formulas ──────────────────────────────────────────────────────────────
    with st.expander("📐 Formula Sheet"):
        for formula in data["formulas"]:
            if subject == "English":
                st.info(formula)
            else:
                st.latex(formula)

    # ── Concept ───────────────────────────────────────────────────────────────
    with st.expander("💡 Concept Explanation"):
        st.markdown(
            f'<div class="ea-card"><p style="line-height:1.8;color:#cbd5e0">{data["concept"]}</p></div>',
            unsafe_allow_html=True,
        )

    # ── Summary ───────────────────────────────────────────────────────────────
    with st.expander("📋 Quick Summary"):
        st.markdown(
            f'<div class="alert-info"><strong>🎯 Summary:</strong> {data["summary"]}</div>',
            unsafe_allow_html=True,
        )

    # ── Worked Example ────────────────────────────────────────────────────────
    with st.expander("✏️ Worked Example"):
        st.markdown(
            f"""<div class="ea-card">
              <pre style="color:#90cdf4;font-family:'JetBrains Mono',monospace;white-space:pre-wrap;line-height:1.8;font-size:.9rem">{data['worked_example']}</pre>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Exam Tips ─────────────────────────────────────────────────────────────
    with st.expander("💎 Exam Tips"):
        for tip in data["exam_tips"]:
            st.markdown(
                f'<div style="background:#0a1929;border-left:3px solid #f6ad55;padding:.6rem 1rem;margin:.4rem 0;border-radius:4px;color:#f6ad55">💡 {tip}</div>',
                unsafe_allow_html=True,
            )

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: PRACTICE LAB
# ─────────────────────────────────────────────────────────────────────────────
def page_practice_lab(db: Database, ai: GeminiAI):
    render_section_header("🧪 Practice Lab", "AI-generated IB-style questions tailored to your needs")

    if not ai.is_ready():
        st.markdown('<div class="alert-warn">⚠️ Gemini API key not found. Add GEMINI_API_KEY to Streamlit secrets (.streamlit/secrets.toml).</div>', unsafe_allow_html=True)
        return

    # Controls
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        subject = st.selectbox("Subject", ["Mathematics", "Physics", "Chemistry", "English"], key="pl_subject")
    with col2:
        subject_topics = list(KNOWLEDGE_VAULT.get(subject, {}).keys())
        topic = st.selectbox("Topic", subject_topics, key="pl_topic")
    with col3:
        q_type = st.selectbox("Question Type", ["MCQ", "Structured Question"], key="pl_qtype")
    with col4:
        difficulty = st.selectbox("Difficulty", ["Standard", "Hard", "Very Hard"], key="pl_diff")

    col_gen, col_save = st.columns([1, 3])
    with col_gen:
        generate = st.button("⚡ Generate Question", use_container_width=True)

    st.markdown("---")

    # Generate question
    if generate:
        with st.spinner("🤖 Gemini is generating your IB question..."):
            if q_type == "MCQ":
                q_data = ai.generate_mcq(subject, topic, difficulty)
                if q_data:
                    st.session_state["current_mcq"] = q_data
                    st.session_state["mcq_answered"] = False
                    st.session_state["mcq_subject"] = subject
                    st.session_state["mcq_topic"] = topic
                    st.session_state["mcq_difficulty"] = difficulty
                else:
                    st.markdown('<div class="alert-error">❌ Failed to generate question. Check API key and try again.</div>', unsafe_allow_html=True)
            else:
                q_data = ai.generate_structured_question(subject, topic, difficulty)
                if q_data:
                    st.session_state["current_struct"] = q_data
                    st.session_state["struct_revealed"] = False
                    st.session_state["struct_subject"] = subject
                    st.session_state["struct_topic"] = topic
                    st.session_state["struct_difficulty"] = difficulty
                else:
                    st.markdown('<div class="alert-error">❌ Failed to generate question. Try again.</div>', unsafe_allow_html=True)

    # Display MCQ
    if "current_mcq" in st.session_state and st.session_state.get("current_mcq"):
        q = st.session_state["current_mcq"]
        st.markdown(
            f"""<div class="ea-card">
              <div style="font-size:.75rem;color:#8ba3be;margin-bottom:.5rem">
                MCQ &nbsp;|&nbsp; {st.session_state.get('mcq_subject','')} — {st.session_state.get('mcq_topic','')} &nbsp;|&nbsp; {st.session_state.get('mcq_difficulty','')} &nbsp;|&nbsp; {q.get('marks',1)} mark(s)
              </div>
              <div style="font-size:1.05rem;font-weight:500;line-height:1.7;color:#e2e8f0">{q.get('question','')}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        options = q.get("options", {})
        user_answer = st.radio(
            "Select your answer:",
            list(options.keys()),
            format_func=lambda k: f"{k}. {options[k]}",
            key="mcq_user_ans",
            index=None,
        )

        col_sub, col_clr = st.columns([1, 3])
        with col_sub:
            submit = st.button("✅ Submit Answer", use_container_width=True)

        if submit and user_answer:
            correct_key = q.get("correct", "A")
            is_correct = user_answer == correct_key
            st.session_state["mcq_answered"] = True

            if is_correct:
                st.markdown('<div class="alert-success">🎉 Correct! Well done.</div>', unsafe_allow_html=True)
                db.save_quiz_result(
                    st.session_state.get("mcq_subject", ""),
                    st.session_state.get("mcq_topic", ""),
                    "MCQ", st.session_state.get("mcq_difficulty", ""),
                    1, 1,
                )
            else:
                st.markdown(
                    f'<div class="alert-error">❌ Incorrect. The correct answer is <strong>{correct_key}. {options.get(correct_key,"")}</strong></div>',
                    unsafe_allow_html=True,
                )
                db.save_quiz_result(
                    st.session_state.get("mcq_subject", ""),
                    st.session_state.get("mcq_topic", ""),
                    "MCQ", st.session_state.get("mcq_difficulty", ""),
                    0, 1,
                )

            with st.expander("📖 Full Explanation", expanded=True):
                st.markdown(
                    f"""<div class="ea-card">
                      <div style="color:#90cdf4;font-family:'JetBrains Mono',monospace;white-space:pre-wrap;line-height:1.8">
                      {q.get('explanation','')}
                      </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            if st.button("💾 Save Question"):
                db.save_question(
                    st.session_state.get("mcq_subject", ""),
                    st.session_state.get("mcq_topic", ""),
                    q.get("question", ""),
                    q.get("explanation", ""),
                )
                st.success("Question saved to your collection!")

    # Display Structured Question
    if "current_struct" in st.session_state and st.session_state.get("current_struct"):
        q = st.session_state["current_struct"]
        st.markdown(
            f"""<div class="ea-card">
              <div style="font-size:.75rem;color:#8ba3be;margin-bottom:.5rem">
                Structured Question &nbsp;|&nbsp; {st.session_state.get('struct_subject','')} — {st.session_state.get('struct_topic','')} &nbsp;|&nbsp; Total: {q.get('total_marks',0)} marks
              </div>
              <div style="font-size:.95rem;color:#8ba3be;margin-bottom:1rem;font-style:italic">{q.get('context','')}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        for part in q.get("parts", []):
            with st.expander(f"Part ({part['part']}) — {part['marks']} marks", expanded=True):
                st.markdown(
                    f'<div style="font-size:1rem;color:#e2e8f0;margin-bottom:.7rem"><strong>({part["part"]})</strong> {part["question"]}</div>',
                    unsafe_allow_html=True,
                )
                st.text_area(f"Your answer ({part['part']}):", key=f"struct_ans_{part['part']}", height=100)

        if st.button("🔍 Reveal Model Answers & Mark Scheme"):
            for part in q.get("parts", []):
                st.markdown(
                    f"""<div class="ea-card">
                      <div style="color:#f6ad55;font-weight:600;margin-bottom:.5rem">Part ({part['part']}) — Model Answer</div>
                      <div style="color:#e2e8f0;margin-bottom:.8rem">{part['answer']}</div>
                      <div style="color:#68d391;font-size:.85rem"><strong>Mark Scheme:</strong> {part['mark_scheme']}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            db.save_quiz_result(
                st.session_state.get("struct_subject", ""),
                st.session_state.get("struct_topic", ""),
                "Structured", st.session_state.get("struct_difficulty", ""),
                0, q.get("total_marks", 0),
            )

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: IMPORTANT QUESTIONS
# ─────────────────────────────────────────────────────────────────────────────
def page_important_questions(ai: GeminiAI):
    render_section_header("⭐ Important Questions", "High-priority questions most likely to appear in IB exams")

    if not ai.is_ready():
        st.markdown('<div class="alert-warn">⚠️ Gemini API key required for this feature.</div>', unsafe_allow_html=True)
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        subject = st.selectbox("Subject", list(KNOWLEDGE_VAULT.keys()), key="iq_subject")
    with col2:
        topics = list(KNOWLEDGE_VAULT.get(subject, {}).keys())
        topic = st.selectbox("Topic", topics, key="iq_topic")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        generate = st.button("🎯 Generate Important Questions", use_container_width=True)

    if generate:
        with st.spinner("🤖 Analysing past paper patterns..."):
            questions = ai.generate_important_questions(subject, topic)

        if questions:
            st.markdown(
                f'<div class="alert-info">✅ Generated {len(questions)} high-priority questions for <strong>{subject} — {topic}</strong></div>',
                unsafe_allow_html=True,
            )
            for i, q in enumerate(questions, 1):
                difficulty_color = {"Hard": "#f6ad55", "Very Hard": "#fc8181"}.get(q.get("difficulty", "Hard"), "#f6ad55")
                with st.expander(f"Question {i}: {q.get('question', '')[:80]}...", expanded=(i == 1)):
                    st.markdown(
                        f"""<div class="ea-card">
                          <div style="display:flex;gap:.5rem;margin-bottom:.8rem;flex-wrap:wrap">
                            <span style="background:#1a2236;border:1px solid {difficulty_color};color:{difficulty_color};border-radius:6px;padding:.2rem .6rem;font-size:.75rem">{q.get('difficulty','')}</span>
                            <span style="background:#1a2236;border:1px solid #4a6a8a;color:#8ba3be;border-radius:6px;padding:.2rem .6rem;font-size:.75rem">{q.get('type','')}</span>
                          </div>
                          <div style="font-size:1rem;color:#e2e8f0;margin-bottom:1rem;line-height:1.7">{q.get('question','')}</div>
                          <div style="background:#0a1929;border-radius:8px;padding:1rem;margin-bottom:.8rem">
                            <div style="font-size:.8rem;color:#63b3ed;font-weight:600;margin-bottom:.4rem">MODEL ANSWER</div>
                            <div style="color:#90cdf4;font-family:'JetBrains Mono',monospace;font-size:.9rem;line-height:1.7">{q.get('model_answer','')}</div>
                          </div>
                          <div style="background:#0a0f1a;border-left:3px solid #f6ad55;padding:.6rem .9rem;border-radius:4px">
                            <div style="font-size:.8rem;color:#f6ad55;font-weight:600">WHY IS THIS IMPORTANT?</div>
                            <div style="font-size:.85rem;color:#d69e2e;margin-top:.3rem">{q.get('why_important','')}</div>
                          </div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown('<div class="alert-error">❌ Failed to generate questions. Please try again.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: MOCK EXAMS
# ─────────────────────────────────────────────────────────────────────────────
def page_mock_exams(db: Database, ai: GeminiAI):
    render_section_header("📝 Mock Exams", "Timed full exam simulations with score reports")

    if not ai.is_ready():
        st.markdown('<div class="alert-warn">⚠️ Gemini API key required for mock exams.</div>', unsafe_allow_html=True)
        return

    # Previous results
    past = db.get_mock_results()
    if not past.empty:
        st.markdown("**📊 Your Recent Mock Exam Results:**")
        display = past.head(5).copy()
        display["Score %"] = (display["score"] / display["total"] * 100).round(1)
        display["Date"] = pd.to_datetime(display["timestamp"]).dt.strftime("%d %b %Y")
        st.dataframe(
            display[["Date", "exam_name", "score", "total", "Score %", "time_taken"]].rename(
                columns={"exam_name": "Exam", "score": "Score", "total": "Total", "time_taken": "Time (s)"}
            ),
            use_container_width=True, hide_index=True,
        )
        st.markdown("---")

    # Exam Setup
    if "mock_active" not in st.session_state:
        st.session_state["mock_active"] = False

    if not st.session_state["mock_active"]:
        render_section_header("⚙️ Set Up Mock Exam")
        col1, col2, col3 = st.columns(3)
        with col1:
            mock_subject = st.selectbox("Subject", ["Physics", "Chemistry", "Mathematics", "English"], key="mock_subj")
        with col2:
            mock_difficulty = st.selectbox("Difficulty", ["Mixed", "Standard", "Hard"], key="mock_diff")
        with col3:
            mock_num = st.slider("Number of Questions", 5, 20, 10, key="mock_num")

        col_start, _ = st.columns([1, 2])
        with col_start:
            if st.button("🚀 Start Mock Exam", use_container_width=True):
                with st.spinner(f"Generating {mock_num} {mock_subject} questions..."):
                    questions = ai.generate_mock_exam(mock_subject, mock_difficulty, mock_num)
                if questions:
                    st.session_state["mock_active"] = True
                    st.session_state["mock_questions"] = questions
                    st.session_state["mock_answers"] = {}
                    st.session_state["mock_start_time"] = time.time()
                    st.session_state["mock_name"] = f"{mock_subject} {mock_difficulty} Mock"
                    st.session_state["mock_submitted"] = False
                    st.rerun()
                else:
                    st.markdown('<div class="alert-error">❌ Failed to generate mock exam. Try again.</div>', unsafe_allow_html=True)
    else:
        # Active mock exam
        questions = st.session_state.get("mock_questions", [])
        elapsed = int(time.time() - st.session_state.get("mock_start_time", time.time()))
        elapsed_str = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
        total_q = len(questions)

        col_timer, col_progress = st.columns([1, 3])
        with col_timer:
            st.markdown(
                f'<div class="countdown-box" style="padding:.8rem 1.2rem"><div class="countdown-title">⏱ Time</div><div class="countdown-time" style="font-size:1.8rem">{elapsed_str}</div></div>',
                unsafe_allow_html=True,
            )
        with col_progress:
            answered = len(st.session_state.get("mock_answers", {}))
            st.markdown(f"**Progress: {answered}/{total_q} answered**")
            render_progress_bar(answered / total_q * 100 if total_q else 0, "#63b3ed")

        st.markdown("---")

        if not st.session_state.get("mock_submitted", False):
            for i, q in enumerate(questions):
                opts = q.get("options", {})
                st.markdown(
                    f'<div style="font-size:.8rem;color:#8ba3be;margin-bottom:.3rem">Q{i+1} | {q.get("topic","")}</div>'
                    f'<div style="font-size:1rem;font-weight:500;color:#e2e8f0;margin-bottom:.5rem">{q.get("question","")}</div>',
                    unsafe_allow_html=True,
                )
                ans = st.radio(
                    f"Answer Q{i+1}:",
                    list(opts.keys()),
                    format_func=lambda k, opts=opts: f"{k}. {opts[k]}",
                    key=f"mock_q_{i}",
                    index=None,
                    label_visibility="collapsed",
                )
                if ans:
                    st.session_state["mock_answers"][i] = ans
                st.markdown('<hr style="border-color:#1a2236">', unsafe_allow_html=True)

            col_submit, col_quit = st.columns([1, 1])
            with col_submit:
                if st.button("📊 Submit & See Results", use_container_width=True):
                    st.session_state["mock_submitted"] = True
                    st.rerun()
            with col_quit:
                if st.button("❌ Quit Mock Exam", use_container_width=True):
                    for key in ["mock_active", "mock_questions", "mock_answers", "mock_submitted", "mock_name"]:
                        st.session_state.pop(key, None)
                    st.rerun()
        else:
            # Results
            questions = st.session_state.get("mock_questions", [])
            answers = st.session_state.get("mock_answers", {})
            score = sum(1 for i, q in enumerate(questions) if answers.get(i) == q.get("correct"))
            total = len(questions)
            time_taken = int(time.time() - st.session_state.get("mock_start_time", time.time()))
            pct = score / total * 100 if total else 0

            db.save_mock_result(st.session_state.get("mock_name", "Mock"), score, total, time_taken)

            grade_color = "#48bb78" if pct >= 70 else "#f6ad55" if pct >= 50 else "#fc8181"
            st.markdown(
                f"""<div class="countdown-box" style="border-color:{grade_color}">
                  <div class="countdown-title" style="color:{grade_color}">MOCK EXAM COMPLETE</div>
                  <div class="countdown-time" style="color:{grade_color}">{score}/{total} ({pct:.1f}%)</div>
                  <div class="countdown-sub" style="color:{grade_color}">Time taken: {time_taken//60}m {time_taken%60}s</div>
                </div>""",
                unsafe_allow_html=True,
            )

            st.markdown("---")
            st.markdown("**📋 Question Review:**")
            for i, q in enumerate(questions):
                user_ans = answers.get(i, "Not answered")
                correct_ans = q.get("correct", "")
                is_correct = user_ans == correct_ans
                icon = "✅" if is_correct else "❌"
                opts = q.get("options", {})
                with st.expander(f"{icon} Q{i+1}: {q.get('question','')[:60]}..."):
                    st.markdown(
                        f"""<div>
                          <div>Your answer: <strong style="color:{'#68d391' if is_correct else '#fc8181'}">{user_ans}. {opts.get(user_ans,'')}</strong></div>
                          <div>Correct: <strong style="color:#68d391">{correct_ans}. {opts.get(correct_ans,'')}</strong></div>
                          <div style="margin-top:.5rem;color:#8ba3be;font-size:.9rem">{q.get('explanation','')}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

            if st.button("🔄 New Mock Exam"):
                for key in ["mock_active", "mock_questions", "mock_answers", "mock_submitted", "mock_name"]:
                    st.session_state.pop(key, None)
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: FLASHCARDS
# ─────────────────────────────────────────────────────────────────────────────
def page_flashcards():
    render_section_header("🃏 Flashcards", "Master key formulas, identities, and concepts")

    col1, col2 = st.columns([1, 3])
    with col1:
        subject = st.selectbox("Subject", list(FLASHCARDS_DATA.keys()), key="fc_subject")

    cards = FLASHCARDS_DATA.get(subject, [])
    if not cards:
        st.info("No flashcards for this subject yet.")
        return

    if "fc_index" not in st.session_state:
        st.session_state["fc_index"] = 0
    if "fc_flipped" not in st.session_state:
        st.session_state["fc_flipped"] = False
    if "fc_subject_prev" not in st.session_state:
        st.session_state["fc_subject_prev"] = subject

    # Reset if subject changed
    if st.session_state["fc_subject_prev"] != subject:
        st.session_state["fc_index"] = 0
        st.session_state["fc_flipped"] = False
        st.session_state["fc_subject_prev"] = subject

    idx = st.session_state["fc_index"] % len(cards)
    card = cards[idx]
    flipped = st.session_state["fc_flipped"]

    # Progress
    st.markdown(f"**Card {idx + 1} of {len(cards)}**")
    render_progress_bar((idx + 1) / len(cards) * 100)
    st.markdown("")

    # Card display
    if not flipped:
        st.markdown(
            f"""<div class="flashcard">
              <div>
                <div style="font-size:.75rem;color:#4a7a9a;margin-bottom:1rem;letter-spacing:.1em">FRONT — CLICK FLIP TO SEE ANSWER</div>
                <div class="flashcard-front">{card['front']}</div>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        back_text = card["back"].replace("\n", "<br>")
        st.markdown(
            f"""<div class="flashcard" style="background:linear-gradient(135deg,#0f3d2a,#072618)">
              <div>
                <div style="font-size:.75rem;color:#276749;margin-bottom:1rem;letter-spacing:.1em">BACK — ANSWER</div>
                <div class="flashcard-front" style="color:#9ae6b4;font-size:1.1rem">{card['front']}</div>
                <div class="flashcard-back" style="margin-top:1rem;font-size:1rem">{back_text}</div>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("")
    col_prev, col_flip, col_next, col_shuffle = st.columns(4)
    with col_prev:
        if st.button("⬅️ Previous", use_container_width=True):
            st.session_state["fc_index"] = (idx - 1) % len(cards)
            st.session_state["fc_flipped"] = False
            st.rerun()
    with col_flip:
        if st.button("🔄 Flip Card", use_container_width=True):
            st.session_state["fc_flipped"] = not st.session_state["fc_flipped"]
            st.rerun()
    with col_next:
        if st.button("➡️ Next", use_container_width=True):
            st.session_state["fc_index"] = (idx + 1) % len(cards)
            st.session_state["fc_flipped"] = False
            st.rerun()
    with col_shuffle:
        if st.button("🔀 Shuffle", use_container_width=True):
            st.session_state["fc_index"] = random.randint(0, len(cards) - 1)
            st.session_state["fc_flipped"] = False
            st.rerun()

    # All cards grid
    st.markdown("---")
    render_section_header("📋 All Cards", f"{len(cards)} flashcards for {subject}")
    cols = st.columns(3)
    for i, c in enumerate(cards):
        with cols[i % 3]:
            st.markdown(
                f"""<div class="ea-card" style="cursor:pointer;min-height:100px">
                  <div style="font-size:.7rem;color:#4a6a8a;margin-bottom:.4rem">#{i+1}</div>
                  <div style="font-weight:600;color:#90cdf4;margin-bottom:.4rem">{c['front']}</div>
                  <div style="font-size:.8rem;color:#4a6a8a;font-family:'JetBrains Mono',monospace">{c['back'][:60]}...</div>
                </div>""",
                unsafe_allow_html=True,
            )

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: PROGRESS ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────
def page_analytics(db: Database):
    render_section_header("📊 Progress Analytics", "Deep dive into your performance trends")

    df = db.get_quiz_results()

    if df.empty:
        st.markdown(
            '<div class="alert-info">📝 No data yet. Complete practice questions, mock exams, and flashcards to see your analytics.</div>',
            unsafe_allow_html=True,
        )
        return

    # Top KPIs
    total_q = int(df["total"].sum())
    total_correct = int(df["correct"].sum())
    overall_acc = round(total_correct / total_q * 100, 1) if total_q else 0
    subjects_done = df["subject"].nunique()
    sessions = len(df)

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric(total_q, "Total Questions", "#63b3ed")
    with c2: render_metric(f"{overall_acc}%", "Accuracy", accuracy_color(overall_acc))
    with c3: render_metric(subjects_done, "Subjects Covered", "#d6bcfa")
    with c4: render_metric(sessions, "Practice Sessions", "#68d391")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("🎯 Accuracy by Subject")
        subj_acc = df.groupby("subject").apply(
            lambda x: round(x["correct"].sum() / x["total"].sum() * 100, 1)
        ).reset_index()
        subj_acc.columns = ["Subject", "Accuracy"]
        fig1 = go.Figure(go.Bar(
            x=subj_acc["Accuracy"], y=subj_acc["Subject"],
            orientation="h",
            marker_color=[accuracy_color(a) for a in subj_acc["Accuracy"]],
            text=subj_acc["Accuracy"].astype(str) + "%",
            textposition="outside",
        ))
        fig1.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
            height=250, margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(range=[0, 110]),
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_r:
        st.subheader("📈 Accuracy by Topic")
        top_acc = df.groupby("topic").apply(
            lambda x: round(x["correct"].sum() / x["total"].sum() * 100, 1)
        ).reset_index()
        top_acc.columns = ["Topic", "Accuracy"]
        top_acc = top_acc.sort_values("Accuracy")
        fig2 = go.Figure(go.Bar(
            x=top_acc["Accuracy"], y=top_acc["Topic"],
            orientation="h",
            marker_color=[accuracy_color(a) for a in top_acc["Accuracy"]],
        ))
        fig2.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
            height=max(200, len(top_acc) * 30),
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(range=[0, 110]),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🔵 Questions by Difficulty")
        diff_counts = df.groupby("difficulty")["total"].sum().reset_index()
        fig3 = px.pie(
            diff_counts, names="difficulty", values="total",
            color_discrete_map={"Standard": "#63b3ed", "Hard": "#f6ad55", "Very Hard": "#fc8181"},
            template="plotly_dark",
        )
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
            height=250, margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        st.subheader("📅 Daily Study Trend")
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        daily = df.groupby("date").agg(questions=("total", "sum"), accuracy=("correct", lambda x: round(x.sum() / df.loc[x.index, "total"].sum() * 100, 1))).reset_index()
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(x=daily["date"], y=daily["questions"], name="Questions", marker_color="#1e3a5f"))
        fig4.add_trace(go.Scatter(x=daily["date"], y=daily["accuracy"], name="Accuracy %", line=dict(color="#f6ad55", width=2), yaxis="y2"))
        fig4.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
            height=250, margin=dict(l=0, r=0, t=10, b=0),
            yaxis2=dict(overlaying="y", side="right", range=[0, 110]),
            legend=dict(orientation="h", y=-0.3),
        )
        st.plotly_chart(fig4, use_container_width=True)

    # Weak topics
    st.markdown("---")
    st.subheader("⚠️ Topics Needing Attention")
    weak_df = db.get_weak_topics()
    if not weak_df.empty:
        fig5 = go.Figure(go.Bar(
            x=weak_df["topic"], y=weak_df["accuracy"],
            marker_color=[accuracy_color(a) for a in weak_df["accuracy"]],
            text=weak_df["accuracy"].round(1).astype(str) + "%",
            textposition="outside",
        ))
        fig5.add_hline(y=60, line_dash="dash", line_color="#f6ad55", annotation_text="60% Threshold")
        fig5.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
            height=300, margin=dict(l=0, r=0, t=10, b=0),
            yaxis=dict(range=[0, 110]),
            xaxis_title="", yaxis_title="Accuracy %",
        )
        st.plotly_chart(fig5, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: STUDY PLAN GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def page_study_plan(db: Database, ai: GeminiAI):
    render_section_header("🗓️ Smart Study Plan", "AI-generated personalised revision schedule")

    if not ai.is_ready():
        st.markdown('<div class="alert-warn">⚠️ Gemini API key required to generate study plans.</div>', unsafe_allow_html=True)
        return

    weak_df = db.get_weak_topics()
    weak_topics = weak_df[weak_df["accuracy"] < 60]["topic"].tolist() if not weak_df.empty else []

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📌 Detected Weak Topics (< 60% accuracy):**")
        if weak_topics:
            for t in weak_topics:
                st.markdown(f'<div class="weak-topic">🔴 {t}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-info">✅ No weak topics yet. Complete practice questions first.</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("**📅 Exam Schedule:**")
        for e in EXAM_SCHEDULE[:4]:
            days = days_until(e["date"])
            st.markdown(
                f'<div style="background:#1a2236;border-radius:8px;padding:.5rem .9rem;margin:.3rem 0;font-size:.85rem">'
                f'{SUBJECT_EMOJI.get(e["subject"],"📚")} {e["subject"]} {e["paper"]} — {e["date"].strftime("%d %b")} ({days}d)</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    extra_weak = st.text_input(
        "➕ Additional weak topics (comma-separated):",
        placeholder="e.g. Calculus, Organic Reactions, Vectors",
        key="sp_extra",
    )

    if extra_weak:
        extra_list = [t.strip() for t in extra_weak.split(",") if t.strip()]
        weak_topics.extend(extra_list)

    col_gen, _ = st.columns([1, 2])
    with col_gen:
        generate = st.button("🤖 Generate My Study Plan", use_container_width=True)

    if generate:
        with st.spinner("🧠 Gemini AI is creating your personalised study plan..."):
            plan = ai.generate_study_plan(weak_topics, EXAM_SCHEDULE)

        if plan:
            st.markdown("---")
            st.markdown(
                '<div class="alert-success">✅ Your personalised AI study plan is ready!</div>',
                unsafe_allow_html=True,
            )
            st.markdown("")
            st.markdown(plan)
            db.log_study_session("Study Plan", 5)
        else:
            st.markdown('<div class="alert-error">❌ Failed to generate study plan. Check API key and try again.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR  NAVIGATION
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        # Logo / Branding
        st.markdown(
            """<div style="text-align:center;padding:1rem 0 1.5rem">
              <div style="font-size:2.5rem">🚀</div>
              <div style="font-size:1.3rem;font-weight:700;color:#e2e8f0">Exam Ascent AI</div>
              <div style="font-size:.75rem;color:#4a6a8a;letter-spacing:.1em">IB EXAM PREPARATION</div>
            </div>""",
            unsafe_allow_html=True,
        )

        pages = {
            "🏠 Dashboard":            "Dashboard",
            "📅 Exam Timetable":       "Timetable",
            "📚 Knowledge Vault":      "Knowledge Vault",
            "🧪 Practice Lab":         "Practice Lab",
            "⭐ Important Questions":  "Important Questions",
            "📝 Mock Exams":           "Mock Exams",
            "🃏 Flashcards":           "Flashcards",
            "📊 Progress Analytics":   "Analytics",
            "🗓️ Study Plan":           "Study Plan",
        }

        if "page" not in st.session_state:
            st.session_state["page"] = "Dashboard"

        for label, key in pages.items():
            active = st.session_state["page"] == key
            btn_style = "background:linear-gradient(135deg,#1e3a5f,#162133);border:1px solid #2b6cb0;" if active else ""
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state["page"] = key
                st.rerun()

        st.markdown("---")

        # Next exam in sidebar
        next_exam = get_next_exam()
        if next_exam:
            days = days_until(next_exam["date"])
            color = color_for(next_exam["subject"])
            st.markdown(
                f"""<div style="background:#0a1929;border:1px solid {color};border-radius:10px;padding:.8rem;text-align:center">
                  <div style="font-size:.7rem;color:{color};letter-spacing:.08em">NEXT EXAM IN</div>
                  <div style="font-size:1.8rem;font-weight:700;color:{color}">{days}d</div>
                  <div style="font-size:.75rem;color:#8ba3be">{next_exam['subject']} {next_exam['paper']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;font-size:.7rem;color:#2a3a55">Powered by Google Gemini AI<br>© 2026 Exam Ascent AI</div>',
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# MAIN  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def main():
    """Main application entry point."""
    # Initialise singletons (cached for session)
    if "db" not in st.session_state:
        st.session_state["db"] = Database()
    if "ai" not in st.session_state:
        st.session_state["ai"] = GeminiAI()

    db: Database = st.session_state["db"]
    ai: GeminiAI = st.session_state["ai"]

    render_sidebar()

    page = st.session_state.get("page", "Dashboard")

    if page == "Dashboard":
        page_dashboard(db)
    elif page == "Timetable":
        page_timetable()
    elif page == "Knowledge Vault":
        page_knowledge_vault()
    elif page == "Practice Lab":
        page_practice_lab(db, ai)
    elif page == "Important Questions":
        page_important_questions(ai)
    elif page == "Mock Exams":
        page_mock_exams(db, ai)
    elif page == "Flashcards":
        page_flashcards()
    elif page == "Analytics":
        page_analytics(db)
    elif page == "Study Plan":
        page_study_plan(db, ai)
    else:
        page_dashboard(db)


if __name__ == "__main__":
    main()
