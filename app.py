import streamlit as st
from docx import Document
import random
from gtts import gTTS
import io

# ====================== UTILITY FUNCTIONS ======================
def text_to_speech(text):
    """Convert text to audio bytes using gTTS in Hindi"""
    try:
        tts = gTTS(text=text, lang='hi', slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        st.error(f"🔊 Audio error: {e}")
        return None

# ====================== LOAD FLASHCARDS ======================
def load_flashcards(doc_path):
    try:
        doc = Document(doc_path)
        cards = []
        question = None
        answer = None
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            if text.startswith("QUESTION:"):
                if question and answer:
                    cards.append((question, answer))
                question = text[len("QUESTION:"):].strip()
                answer = None
            elif text.startswith("ANSWER:") and question:
                answer = text[len("ANSWER:"):].strip()
        if question and answer:
            cards.append((question, answer))
        return cards
    except Exception as e:
        st.error(f"❌ Error loading document: {e}")
        return []

# ====================== INITIALIZE ======================
if "cards" not in st.session_state:
    st.session_state.cards = load_flashcards("Law Preparation.docx")
    if st.session_state.cards:
        st.session_state.deck = list(range(len(st.session_state.cards)))
        random.shuffle(st.session_state.deck)

if "current_index" not in st.session_state:
    st.session_state.current_index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False

if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []

if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}

if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0

# Audio state
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False

# ====================== FLASHCARDS ======================
def show_flashcards():
    st.title("📚 LLB फ्लैशकार्ड्स (हिंदी)")
    
    if not st.session_state.cards:
        st.warning("कोई फ्लैशकार्ड नहीं मिला।")
        st.info("आपके .docx में अपेक्षित प्रारूप:\n\nQUESTION: ...\nANSWER: ...")
        return

    idx = st.session_state.deck[st.session_state.current_index]
    question, answer = st.session_state.cards[idx]
    
    # Question section
    st.subheader(f"प्रश्न: {question}")
    
    # Question audio controls
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔊 प्रश्न सुनें"):
            with st.spinner("प्रश्न ऑडियो बन रहा है..."):
                st.session_state.audio_bytes = text_to_speech(question)
                st.session_state.is_playing = True
                st.rerun()
    with col2:
        if st.button("🛑 ऑडियो रोकें"):
            st.session_state.is_playing = False
            st.session_state.audio_bytes = None
            st.rerun()
    with col3:
        if st.session_state.is_playing:
            st.success("▶️ प्रश्न ऑडियो लूप पर चल रहा है...")

    # Show audio player if playing
    if st.session_state.is_playing and st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/mp3", loop=True)

    # Answer section
    if st.session_state.show_answer:
        st.markdown(
            f"""
            <div style="
                padding: 16px;
                background-color: #000000;
                border-left: 4px solid #ff5252;
                border-radius: 8px;
                margin: 14px 0;
                font-size: 18px;
                line-height: 1.6;
                word-wrap: break-word;
                white-space: pre-wrap;
                color: #ff5252;
                font-weight: bold;
            ">
                <strong>उत्तर:</strong><br>{answer}
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Answer audio controls
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔊 उत्तर सुनें"):
                with st.spinner("उत्तर ऑडियो बन रहा है..."):
                    st.session_state.audio_bytes = text_to_speech(answer)
                    st.session_state.is_playing = True
                    st.rerun()
        with col2:
            if st.button("🛑 ऑडियो रोकें", key="stop_answer"):
                st.session_state.is_playing = False
                st.session_state.audio_bytes = None
                st.rerun()
        with col3:
            if st.session_state.is_playing:
                st.success("▶️ उत्तर ऑडियो लूप पर चल रहा है...")

        # Show audio player for answer
        if st.session_state.is_playing and st.session_state.audio_bytes:
            st.audio(st.session_state.audio_bytes, format="audio/mp3", loop=True)

    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        st.button("👁️ उत्तर दिखाएं", on_click=lambda: st.session_state.update(show_answer=True))
    with col2:
        st.button("⏭️ अगला कार्ड", on_click=lambda: st.session_state.update(
            current_index=(st.session_state.current_index + 1) % len(st.session_state.deck),
            show_answer=False,
            is_playing=False,
            audio_bytes=None
        ))
    
    st.caption(f"कार्ड {st.session_state.current_index + 1} कुल {len(st.session_state.deck)} में से")

# ====================== QUIZ ======================
def start_quiz(num_questions):
    if len(st.session_state.cards) < 4:
        st.error("क्विज़ के लिए कम से कम 4 फ्लैशकार्ड चाहिए।")
        return
    selected = random.sample(st.session_state.cards, min(num_questions, len(st.session_state.cards)))
    quiz_q = []
    for q, a in selected:
        wrong_pool = [c[1] for c in st.session_state.cards if c[1] != a]
        wrong = random.sample(wrong_pool, k=min(3, len(wrong_pool)))
        options = [a] + wrong
        random.shuffle(options)
        quiz_q.append((q, a, options))
    st.session_state.quiz_questions = quiz_q
    st.session_state.user_answers = {}
    st.session_state.quiz_index = 0
    st.session_state.quiz_active = True

def show_quiz():
    st.title("📝 LLB क्विज़ (हिंदी)")
    
    if not st.session_state.cards:
        st.warning("कोई फ्लैशकार्ड लोड नहीं हुआ। पहले फ्लैशकार्ड टैब पर जाएं।")
        return

    if not st.session_state.quiz_active:
        st.write("अपने ज्ञान का परीक्षण करें!")
        num = st.slider("प्रश्नों की संख्या", 3, min(10, len(st.session_state.cards)), 5)
        if st.button("🚀 क्विज़ शुरू करें"):
            start_quiz(num)
    else:
        total = len(st.session_state.quiz_questions)
        idx = st.session_state.quiz_index
        if idx >= total:
            correct = 0
            for i, (q, correct_ans, opts) in enumerate(st.session_state.quiz_questions):
                if st.session_state.user_answers.get(i) == correct_ans:
                    correct += 1
            score = (correct / total) * 100
            st.balloons()
            st.success("🎉 क्विज़ पूर्ण हुआ!")
            st.metric("स्कोर", f"{score:.1f}%")
            if score >= 80:
                st.success("🏆 उत्कृष्ट!")
            elif score >= 60:
                st.info("👍 अच्छा काम!")
            else:
                st.warning("📚 अभ्यास जारी रखें!")
            if st.button("🔁 क्विज़ दोहराएं"):
                st.session_state.quiz_active = False
                st.rerun()
        else:
            q, correct_ans, options = st.session_state.quiz_questions[idx]
            st.subheader(f"प्रश्न {idx + 1} कुल {total} में से")
            st.write(f"**{q}**")
            choice = st.radio("अपना उत्तर चुनें:", options, index=None)
            if st.button("✅ जमा करें"):
                st.session_state.user_answers[idx] = choice
                if choice == correct_ans:
                    st.success("✅ सही!")
                else:
                    st.error("❌ गलत")
                    st.info(f"**सही उत्तर:** {correct_ans}")
                next_btn = "➡️ अगला" if idx + 1 < total else "🏁 समाप्त करें"
                st.button(next_btn, on_click=lambda: st.session_state.update(quiz_index=idx + 1))

# ====================== MAIN ======================
st.set_page_config(page_title="LLB फ्लैशकार्ड्स और क्विज़", page_icon="📚")

tab1, tab2 = st.tabs(["🎴 फ्लैशकार्ड्स", "📝 क्विज़"])

with tab1:
    show_flashcards()

with tab2:
    show_quiz()