# app.py — outlines for info/uploader text + accept txt/pdf/docx + extract text

import streamlit as st
import pandas as pd
from pathlib import Path
import base64
import io

# NEW: libraries for reading PDF/DOCX
from PyPDF2 import PdfReader
from docx import Document

st.set_page_config(page_title="Smart Resume Analyzer", page_icon="✨", layout="wide")

# ---------- background helper ----------
def embed_bg(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return """
        <style>
          [data-testid="stAppViewContainer"]{
            background: linear-gradient(135deg,#ffe5ff 0%, #e6e9ff 50%, #ffd9f7 100%) fixed !important;
          }
          [data-testid="stHeader"]{ background: transparent; }
        </style>
        """
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"""
    <style>
      [data-testid="stAppViewContainer"]{{
        background: url("data:image/jpeg;base64,{b64}") no-repeat center center fixed !important;
        background-size: cover !important;
      }}
      [data-testid="stHeader"]{{ background: transparent; }}
    </style>
    """

st.markdown(embed_bg("assets/bg.jpg"), unsafe_allow_html=True)

# ---------- styles ----------
st.markdown("""
<style>
  .main > div { max-width: 1000px; margin: auto; }

  /* SIDE BORDERS — thicker */
  .stApp::before, .stApp::after{
    content:""; position:fixed; top:0; bottom:0; width:35px; pointer-events:none; z-index: 9998;
  }
  .stApp::before{
    left:0; background: linear-gradient(180deg,#ffd1ff,#c7b8ff,#ffd6f7);
    box-shadow: 3px 0 0 rgba(0,0,0,0.9), 0 0 30px rgba(199,184,255,0.6), 0 0 60px rgba(255,214,247,0.5);
  }
  .stApp::after{
    right:0; background: linear-gradient(180deg,#ffd6f7,#c7b8ff,#ffd1ff);
    box-shadow: -3px 0 0 rgba(0,0,0,0.9), 0 0 30px rgba(199,184,255,0.6), 0 0 60px rgba(255,214,247,0.5);
  }

  /* TITLE — thick outline + soft pulse */
  .title{
    text-align:center; font-weight:900; font-size:46px; position:relative;
    background: linear-gradient(90deg,#a18cd1,#fbc2eb,#a1c4fd,#f3a7f0);
    -webkit-background-clip:text; background-clip:text; color:transparent;
    letter-spacing:.4px; margin-bottom:6px;
    filter:
      drop-shadow(0 4px 0 rgba(0,0,0,1))
      drop-shadow(0 -4px 0 rgba(0,0,0,1))
      drop-shadow(4px 0 0 rgba(0,0,0,1))
      drop-shadow(-4px 0 0 rgba(0,0,0,1));
    animation: glowPulse 3.2s ease-in-out infinite;
  }
  @keyframes glowPulse {
    0%   { text-shadow:0 0 3px rgba(255,255,255,0.35), 0 0 8px rgba(243,167,240,0.25), 0 0 14px rgba(161,196,253,0.25); }
    50%  { text-shadow:0 0 6px rgba(255,255,255,0.55), 0 0 14px rgba(243,167,240,0.45), 0 0 22px rgba(161,196,253,0.45); }
    100% { text-shadow:0 0 3px rgba(255,255,255,0.35), 0 0 8px rgba(243,167,240,0.25), 0 0 14px rgba(161,196,253,0.25); }
  }

  .subtitle{
    text-align:center; color:#2f2640; font-size:20px; margin-top:-6px; margin-bottom:18px;
    text-shadow:-1px -1px 0 rgba(0,0,0,0.55), 1px -1px 0 rgba(0,0,0,0.55), -1px 1px 0 rgba(0,0,0,0.55), 1px 1px 0 rgba(0,0,0,0.55);
    position: relative; z-index: 1;
  }

  /* Cards */
  .card{
    background: rgba(255,255,255,0.95);
    border: 2px solid #f3c6ff;
    border-radius: 18px;
    padding: 22px 26px;
    box-shadow: 0 18px 40px rgba(164,120,255,0.18);
    color:#3a2d4f; position: relative; z-index: 1;
  }

  /* Text outlines globally (labels, small text, etc.) */
  h2, h3, label, .stMarkdown p, span, .stText{
    text-shadow:-1px -1px 0 rgba(0,0,0,0.45), 1px -1px 0 rgba(0,0,0,0.45), -1px 1px 0 rgba(0,0,0,0.45), 1px 1px 0 rgba(0,0,0,0.45);
  }
  h2{ font-size:1.9rem; color:#ffffff; }
  h3{ font-size:1.25rem; color:#ffffff; }

  /* Uploader: white box; FORCE readable text + outline */
  [data-testid="stFileUploaderDropzone"]{
    background:#ffffff !important; border:1.5px solid #e9d8ff !important; border-radius:12px !important; color:#2b1f42 !important;
  }
  [data-testid="stFileUploader"] *{
    color:#2b1f42 !important; 
    text-shadow:-1px -1px 0 rgba(0,0,0,0.45), 1px -1px 0 rgba(0,0,0,0.45), -1px 1px 0 rgba(0,0,0,0.45), 1px 1px 0 rgba(0,0,0,0.45) !important;
    filter:none !important;  /* avoid any accidental blur */
  }
  [data-testid="stFileUploader"] button{
    background: linear-gradient(90deg,#ffd1ff,#d8b4fe) !important; color:#2b1f42 !important; font-weight:700 !important;
    border:2px solid #e9d8ff !important; border-radius:999px !important; padding:8px 14px !important; box-shadow:0 8px 18px rgba(173,127,255,0.25) !important;
  }
  [data-testid="stFileUploader"] button:hover{ filter:brightness(1.05); transform:translateY(-1px); }

  /* Inputs & Buttons */
  .stTextArea textarea, .stTextInput input{ background:#fff !important; color:#3a2d4f !important; border-radius:12px !important; border:1.5px solid #e9d8ff !important; }
  .stButton > button{
    background: linear-gradient(90deg,#ffd1ff,#d8b4fe); color:#2b1f42; font-weight:700; border:2px solid #e9d8ff; border-radius:999px;
    padding:10px 18px; box-shadow:0 8px 18px rgba(173,127,255,0.25);
    text-shadow:-1px -1px 0 rgba(0,0,0,0.35), 1px -1px 0 rgba(0,0,0,0.35), -1px 1px 0 rgba(0,0,0,0.35), 1px 1px 0 rgba(0,0,0,0.35);
  }
  .stButton > button:hover{ filter:brightness(1.06); transform:translateY(-1px); }
  .stProgress > div > div > div{ background: linear-gradient(90deg,#b3c7ff,#f7c6ff) !important; }

  /* INFO / ALERT text — make readable with outline */
  [data-testid="stAlert"] *, [data-testid="stInfo"] *{
    color:#1b1b1b !important;
    text-shadow:-1px -1px 0 rgba(255,255,255,0.0), 1px -1px 0 rgba(255,255,255,0.0),
                -1px 1px 0 rgba(255,255,255,0.0), 1px 1px 0 rgba(255,255,255,0.0);
    /* switch to darker color; the global outline already applies elsewhere */
    text-shadow:
      -1px -1px 0 rgba(0,0,0,0.45),
       1px -1px 0 rgba(0,0,0,0.45),
      -1px  1px 0 rgba(0,0,0,0.45),
       1px  1px 0 rgba(0,0,0,0.45) !important;
  }

  .footer{
    text-align:center; color:#2f2640; font-size:14px;
    text-shadow:-1px -1px 0 rgba(0,0,0,0.45), 1px -1px 0 rgba(0,0,0,0.45), -1px 1px 0 rgba(0,0,0,0.45), 1px 1px 0 rgba(0,0,0,0.45);
    position: relative; z-index: 1;
  }

  /* Mobile tweaks */
  @media (max-width: 680px){
    .title{ font-size: 34px; }
    .stApp::before, .stApp::after{ width: 24px; }
    .main > div{ padding-left: 8px; padding-right: 8px; }
  }
</style>
""", unsafe_allow_html=True)

# ---------- content ----------
st.markdown('<div class="title">✨ Smart Resume Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">˖ ݁𖥔Analyze your resume efficiently˖ ݁𖥔</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📄 Upload Section")
    # ALLOW txt, pdf, docx
    uploaded = st.file_uploader("Upload your resume (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"], key="resume_upload")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("💼 Job Description (Optional)")
    jd = st.text_area("Paste a job description (optional)", height=140)
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("🔍 Analysis Results")

    keywords = ["python","sql","excel","power bi","machine learning","pandas","streamlit","git","communication","teamwork"]

    def extract_text(file) -> str:
        """Return plain text from txt/pdf/docx; fallback to empty string."""
        if not file:
            return ""
        name: str = file.name.lower()
        try:
            if name.endswith(".txt"):
                return file.read().decode("utf-8", errors="ignore")
            if name.endswith(".pdf"):
                # Read bytes first because Streamlit uploads as SpooledTemporaryFile
                data = file.read()
                reader = PdfReader(io.BytesIO(data))
                pages = [p.extract_text() or "" for p in reader.pages]
                return "\n".join(pages)
            if name.endswith(".docx"):
                data = file.read()
                doc = Document(io.BytesIO(data))
                return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            st.warning(f"Could not read file: {e}")
        return ""

    if uploaded:
        raw_text = extract_text(uploaded)
        text = raw_text.lower()

        if not text.strip():
            st.warning("File uploaded, but I couldn’t extract text. Try a .txt, .pdf, or .docx with selectable text.")
        else:
            found   = [k for k in keywords if k in text]
            missing = [k for k in keywords if k not in text]
            score = int(100 * len(found) / max(1, len(keywords)))

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("✅ Keywords Found")
                st.write(", ".join(found) if found else "-")
            with c2:
                st.subheader("❌ Keywords Missing")
                st.write(", ".join(missing) if missing else "-")

            st.subheader("📈 Match Score")
            st.progress(score/100)
            st.success(f"Overall match: {score}%")

            st.subheader("💡 Suggestions")
            if missing:
                for k in missing:
                    st.write(f"- Add a bullet for **{k}**.")
            else:
                st.write("Great coverage! Add impact metrics for stronger results.")
    else:
        st.info("Upload a .txt, .pdf, or .docx resume to see results.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown('<p class="footer">Made with 💜 by SashankPeddada</p>', unsafe_allow_html=True)
