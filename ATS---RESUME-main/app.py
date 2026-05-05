import streamlit as st
import pdfplumber
import docx
import tempfile
import os
from datetime import datetime
from groq import Groq

# Page configuration
st.set_page_config(
    page_title="ATS Resume Scanner Pro",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 2rem;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #3B82F6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3B82F6 0%, #1D4ED8 100%);
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #3B82F6 0%, #1D4ED8 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.75rem;
        border-radius: 8px;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #2563EB 0%, #1E40AF 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown('<h1 class="main-header">📄 ATS Resume Scanner Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Optimize your resume for Applicant Tracking Systems</p>', unsafe_allow_html=True)

# Initialize session state
if 'ats_feedback' not in st.session_state:
    st.session_state.ats_feedback = None
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""

# Sidebar for API Configuration
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/resume.png", width=100)
    st.title("⚙️ Configuration")
    
    api_key = st.text_input("Enter Groq API Key:", type="password", 
                           placeholder="gsk_xxxxxxxxxxxxxxxxxxxxxxxxxx",
                           help="Get your API key from https://console.groq.com")
    
    model = st.selectbox(
        "Select AI Model:",
        ["llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma-7b-it"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 📊 How it works:")
    st.markdown("""
    1. Upload your resume
    2. Paste job description
    3. Get ATS score & feedback
    4. Improve your resume
    
    **ATS systems look for:**
    - Keywords from job description
    - Relevant skills & experience
    - Proper formatting
    - Quantifiable achievements
    """)
    
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit & Groq AI")

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📤 Upload Resume")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose your resume file", 
        type=['pdf', 'docx', 'txt'],
        help="Supported formats: PDF, DOCX, TXT"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Extract text based on file type
        resume_text = ""
        try:
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(tmp_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            resume_text += text + "\n"
            
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(tmp_path)
                for para in doc.paragraphs:
                    if para.text.strip():
                        resume_text += para.text + "\n"
            
            elif uploaded_file.type == "text/plain":
                resume_text = uploaded_file.getvalue().decode("utf-8")
            
            st.session_state.resume_text = resume_text
            
            # Show preview
            with st.expander("📄 Resume Preview", expanded=False):
                st.text_area("Extracted Text", resume_text[:2000] + "...", height=200)
            
            st.success(f"✅ Successfully extracted {len(resume_text.split())} words")
            
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
        finally:
            os.unlink(tmp_path)
    
    st.markdown("### 📝 Job Description")
    job_description = st.text_area(
        "Paste the job description here:",
        height=200,
        placeholder="Paste the complete job description here...",
        help="Copy and paste the entire job description for accurate analysis"
    )

with col2:
    st.markdown("### 🎯 Analysis Results")
    
    if st.button("🚀 Scan Resume with ATS", type="primary"):
        if not api_key:
            st.error("Please enter your Groq API key in the sidebar")
        elif not st.session_state.resume_text:
            st.error("Please upload your resume first")
        elif not job_description.strip():
            st.error("Please enter the job description")
        else:
            with st.spinner("🔍 Analyzing resume with AI..."):
                try:
                    # Initialize Groq client
                    client = Groq(api_key=api_key)
                    
                    # Prepare enhanced prompt
                    prompt = f"""You are an expert ATS (Applicant Tracking System) analyst. Analyze this resume against the job description.

RESUME:
{st.session_state.resume_text}

JOB DESCRIPTION:
{job_description}

Please provide a comprehensive analysis with the following sections:

1. **ATS COMPATIBILITY SCORE** (0-100): Give a numerical score only, then explain.

2. **KEYWORD MATCHING**:
   - Matched Keywords (found in resume)
   - Missing Keywords (from job description but not in resume)
   - Keyword Density Analysis

3. **SKILLS ANALYSIS**:
   - Skills Present
   - Skills Missing
   - Skills to Highlight

4. **EXPERIENCE ALIGNMENT**:
   - How well experience matches requirements
   - Gaps to address

5. **FORMATTING & STRUCTURE**:
   - ATS-friendly formatting issues
   - Structural improvements

6. **TOP 5 ACTIONABLE RECOMMENDATIONS**:
   - Specific, actionable items to improve score

7. **OPTIMIZED RESUME SUGGESTIONS**:
   - Specific phrases to add
   - Sections to reorganize

Format the response clearly with bullet points and brief explanations.
Remove any special characters from the response."""
                    
                    # Call Groq API
                    completion = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=4096
                    )
                    
                    ats_feedback = completion.choices[0].message.content
                    st.session_state.ats_feedback = ats_feedback
                    
                    # Extract score from feedback (looking for number 0-100)
                    import re
                    score_match = re.search(r'(\d{1,3})/100|\b(\d{1,3})\s*(?:score|rating|%)', ats_feedback, re.IGNORECASE)
                    if score_match:
                        for group in score_match.groups():
                            if group and group.isdigit():
                                st.session_state.score = int(group)
                                break
                    
                except Exception as e:
                    st.error(f"Error analyzing resume: {str(e)}")
    
    # Display results
    if st.session_state.ats_feedback:
        # Score Card
        col_score, col_grade = st.columns([2, 1])
        
        with col_score:
            st.markdown(f"""
            <div class="score-card">
                <h2 style="margin:0;">ATS Score</h2>
                <h1 style="font-size: 4rem; margin:0;">{st.session_state.score}/100</h1>
            </div>
            """, unsafe_allow_html=True)
        
        with col_grade:
            if st.session_state.score >= 80:
                st.markdown("### 🏆 Excellent")
                st.success("High chance of passing ATS")
            elif st.session_state.score >= 60:
                st.markdown("### 👍 Good")
                st.info("Good match, some improvements needed")
            elif st.session_state.score >= 40:
                st.markdown("### ⚠️ Fair")
                st.warning("Needs significant improvements")
            else:
                st.markdown("### ❌ Poor")
                st.error("Major revisions required")
        
        # Progress bar
        st.progress(st.session_state.score / 100)
        
        # Feedback in tabs
        tab1, tab2, tab3 = st.tabs(["📋 Full Analysis", "🎯 Key Recommendations", "💬 AI Chat"])
        
        with tab1:
            st.markdown("### Detailed Analysis")
            st.markdown(st.session_state.ats_feedback)
            
            # Download button for results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_text = f"ATS Resume Analysis Report\nDate: {datetime.now()}\nScore: {st.session_state.score}/100\n\n{st.session_state.ats_feedback}"
            
            st.download_button(
                label="📥 Download Analysis Report",
                data=result_text,
                file_name=f"ats_analysis_{timestamp}.txt",
                mime="text/plain"
            )
        
        with tab2:
            # Extract key recommendations (simplified version)
            lines = st.session_state.ats_feedback.split('\n')
            recommendations = [line for line in lines if any(word in line.lower() for word in ['recommend', 'suggest', 'add', 'improve', 'include', 'should'])]
            
            if recommendations:
                for i, rec in enumerate(recommendations[:10], 1):
                    st.markdown(f"""
                    <div class="metric-card">
                        <b>Recommendation {i}:</b> {rec}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No specific recommendations extracted. Check Full Analysis tab.")
        
        with tab3:
            st.markdown("### 💬 Ask AI About Your Resume")
            
            # Simple chat interface
            user_query = st.text_input("Ask a question about your resume analysis:")
            
            if user_query and st.session_state.resume_text:
                if st.button("Ask AI"):
                    with st.spinner("Thinking..."):
                        try:
                            chat_prompt = f"""
                            Based on this resume analysis:
                            
                            Resume: {st.session_state.resume_text[:2000]}
                            
                            Previous ATS Feedback: {st.session_state.ats_feedback[:1000]}
                            
                            User Question: {user_query}
                            
                            Please provide a helpful, specific answer.
                            """
                            
                            chat_client = Groq(api_key=api_key)
                            chat_response = chat_client.chat.completions.create(
                                model=model,
                                messages=[{"role": "user", "content": chat_prompt}],
                                temperature=0.7,
                                max_tokens=1000
                            )
                            
                            st.session_state.chat_history.append({"user": user_query, "ai": chat_response.choices[0].message.content})
                        
                        except Exception as e:
                            st.error(f"Chat error: {str(e)}")
            
            # Display chat history
            for chat in reversed(st.session_state.chat_history[-5:]):
                with st.chat_message("user"):
                    st.write(chat["user"])
                with st.chat_message("assistant"):
                    st.write(chat["ai"])

# Footer
st.markdown("---")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.markdown("**💡 Tips for ATS Success:**")
    st.markdown("""
    - Use standard headings
    - Include keywords from JD
    - Use bullet points
    - Avoid images/tables
    - Save as PDF
    """)
with col_f2:
    st.markdown("**📈 Improve Your Score:**")
    st.markdown("""
    - Match job title
    - Add quantifiable results
    - Include specific skills
    - Use industry keywords
    - Keep formatting simple
    """)
with col_f3:
    st.markdown("**🛠️ Tools Used:**")
    st.markdown("""
    - Streamlit
    - Groq AI
    - PDF Plumber
    - Python-docx
    """)

