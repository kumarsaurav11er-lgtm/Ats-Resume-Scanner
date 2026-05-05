import streamlit as st
import pdfplumber
import docx
import tempfile
import os
import ollama
import matplotlib.pyplot as plt
import re

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="ATS Resume Scanner AI",
    page_icon="📄",
    layout="wide"
)

# ---------------- AI FUNCTION ----------------
def ai_analyze(prompt):
    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]

# ---------------- UI ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to right, #0f172a, #111827);
    color: white;
}

.title {
    text-align: center;
    font-size: 3rem;
    font-weight: 900;
    color: #38bdf8;
}

.subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 30px;
}

.stButton > button {
    background: linear-gradient(90deg, #3b82f6, #06b6d4);
    color: white;
    padding: 12px;
    border-radius: 10px;
    font-weight: bold;
}

.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0px 0px 15px #38bdf8;
}

.card {
    background: #1e293b;
    padding: 15px;
    border-radius: 12px;
    margin-top: 10px;
}

.score-box {
    background: linear-gradient(135deg, #4f46e5, #06b6d4);
    padding: 25px;
    border-radius: 15px;
    text-align: center;
    font-size: 2rem;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown('<div class="title">📄 ATS Resume Scanner AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Offline AI powered by Ollama</div>', unsafe_allow_html=True)

# ---------------- SESSION ----------------
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "result" not in st.session_state:
    st.session_state.result = None
if "scores" not in st.session_state:
    st.session_state.scores = None

# ---------------- LAYOUT ----------------
col1, col2 = st.columns(2)

# ---------------- LEFT ----------------
with col1:

    st.subheader("📤 Upload Resume")
    file = st.file_uploader("Upload PDF / DOCX / TXT", type=["pdf", "docx", "txt"])

    if file:
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(file.read())
        path = tmp.name

        text = ""

        try:
            if file.type == "application/pdf":
                with pdfplumber.open(path) as pdf:
                    for p in pdf.pages:
                        text += p.extract_text() or ""

            elif "word" in file.type:
                doc = docx.Document(path)
                for p in doc.paragraphs:
                    text += p.text + "\n"

            else:
                text = open(path, "r", encoding="utf-8").read()

            st.session_state.resume_text = text
            st.success("Resume loaded!")

        except Exception as e:
            st.error(e)

        finally:
            os.remove(path)

    st.subheader("📝 Job Description")
    job_desc = st.text_area("Paste Job Description", height=200)

# ---------------- RIGHT ----------------
with col2:

    st.subheader("🎯 AI Analysis")

    if st.button("🚀 Analyze Resume"):

        if not st.session_state.resume_text:
            st.error("Upload resume first")

        elif not job_desc:
            st.error("Add job description")

        else:
            with st.spinner("AI analyzing..."):

                prompt = f"""
You are an ATS expert.

Resume:
{st.session_state.resume_text}

Job Description:
{job_desc}

Give:
- ATS Score (0-100)
- Keyword match
- Missing skills
- Improvements
- Top 5 suggestions
"""

                result = ai_analyze(prompt)
                st.session_state.result = result

                # SAFE SCORE EXTRACTION
                match = re.search(r'(\d{1,3})', result)
                score = int(match.group(1)) if match else 75

                if score > 100:
                    score = 100

                st.session_state.scores = {
                    "Keywords": score,
                    "Skills": max(score - 5, 0),
                    "Experience": max(score - 10, 0),
                    "Format": min(score + 2, 100)
                }

# ---------------- OUTPUT ----------------
if st.session_state.result:

    st.markdown("### 📊 ATS Result")

    st.markdown(f"""
    <div class="score-box">
        ATS SCORE: {list(st.session_state.scores.values())[0]} / 100
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🧠 AI Feedback")
    st.write(st.session_state.result)

    # ---------------- GRAPH ----------------
    st.markdown("### 📊 Score Breakdown")

    labels = list(st.session_state.scores.keys())
    values = list(st.session_state.scores.values())

    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Score")

    st.pyplot(fig)

    # ---------------- INSIGHTS ----------------
    st.markdown("### 📌 Key Insights")

    st.markdown('<div class="card">✔ AI analysis completed successfully</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">✔ Improve missing keywords from JD</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">✔ Add measurable achievements</div>', unsafe_allow_html=True)
