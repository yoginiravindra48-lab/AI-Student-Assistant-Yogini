import json
import re

import ollama
import streamlit as st

# ---------------------------------------------------------------
# Page settings
# ---------------------------------------------------------------
st.set_page_config(
    page_title="AI Student Assistant",
    page_icon="🤖",
    layout="wide",
)

DEFAULT_MODEL = "llama3.2"
QUIZ_QUESTIONS = 5
MAX_HISTORY = 10          # how many past chat messages to send to the AI

SUBJECTS = [
    "General",
    "Programming",
    "DBMS",
    "Computer Networks",
    "Operating Systems",
    "Software Testing",
    "Artificial Intelligence",
    "Machine Learning",
]


# ---------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------
def get_installed_models():
    """Return the names of models installed in Ollama (empty list on error)."""
    try:
        res = ollama.list()
        models = getattr(res, "models", None)
        if models is None:
            models = res.get("models", [])
        names = []
        for m in models:
            name = getattr(m, "model", None)
            if name is None and isinstance(m, dict):
                name = m.get("model") or m.get("name")
            if name:
                names.append(name)
        return names
    except Exception:
        return []


def ollama_error(e):
    st.error(
        f"❌ Could not get a response from Ollama.\n\n"
        f"**Details:** {e}\n\n"
        f"Make sure Ollama is running and the model is installed:\n"
        f"`ollama pull {st.session_state.get('model', DEFAULT_MODEL)}`"
    )


def ask_ollama(messages, json_mode=False):
    """Ask Ollama and return the full reply text, or None on error."""
    try:
        kwargs = {"format": "json"} if json_mode else {}
        res = ollama.chat(
            model=st.session_state.model,
            messages=messages,
            **kwargs,
        )
        return res["message"]["content"]
    except Exception as e:
        ollama_error(e)
        return None


def stream_ollama(messages):
    """Generator that yields reply text piece by piece (for st.write_stream)."""
    stream = ollama.chat(
        model=st.session_state.model,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        yield chunk["message"]["content"]


def parse_quiz(text):
    """Turn the model's reply into a clean list of valid quiz questions."""
    text = text.strip()
    data = None

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Model added extra text or ```json fences - grab the JSON part
        match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                data = None

    if isinstance(data, dict):
        data = data.get("questions", [])

    if not isinstance(data, list):
        raise ValueError("No quiz list found in the AI reply.")

    valid = []
    for q in data:
        if not isinstance(q, dict):
            continue
        options = q.get("options")
        if (
            isinstance(q.get("question"), str)
            and isinstance(options, list)
            and len(options) == 4
            and q.get("answer") in options
        ):
            valid.append(
                {
                    "question": q["question"],
                    "options": options,
                    "answer": q["answer"],
                    "explanation": str(q.get("explanation", "")),
                }
            )

    if not valid:
        raise ValueError("The AI did not return any valid questions.")
    return valid


def score_quiz(quiz, answers):
    """Count correct answers. Unanswered (None) questions score 0."""
    return sum(1 for q, a in zip(quiz, answers) if a == q["answer"])


def generate_quiz(subject, topic, retries=2):
    """Ask the AI for a quiz, retrying if the format is wrong."""
    prompt = f"""
Create exactly {QUIZ_QUESTIONS} multiple choice questions for an engineering student.

Subject: {subject}
Topic: {topic}

Return ONLY valid JSON in exactly this format:

{{
  "questions": [
    {{
      "question": "Question here",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A",
      "explanation": "One short sentence explaining why the answer is correct"
    }}
  ]
}}

Rules:
- Create exactly {QUIZ_QUESTIONS} questions.
- Each question must have exactly 4 options.
- The "answer" must be copied exactly from one of the options.
- Do not add any text outside the JSON.
"""
    for _ in range(retries + 1):
        reply = ask_ollama([{"role": "user", "content": prompt}], json_mode=True)
        if reply is None:          # Ollama error already shown
            return None
        try:
            return parse_quiz(reply)
        except ValueError:
            continue
    st.error("Quiz format error. Please click Generate Quiz again.")
    return None


# ---------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------
DEFAULT_STATE = {
    "messages": [],
    "notes": "",
    "notes_title": "",
    "quiz_data": None,
    "quiz_result": None,
    "quiz_version": 0,
    "model": DEFAULT_MODEL,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------
with st.sidebar:
    st.title("🤖 AI Student Assistant")
    st.write("Your personal AI-powered study assistant.")

    st.divider()

    st.subheader("🧠 AI Model")
    installed = get_installed_models()
    if installed:
        default_index = next(
            (i for i, n in enumerate(installed) if n.startswith(DEFAULT_MODEL)), 0
        )
        st.session_state.model = st.selectbox(
            "Choose model:", installed, index=default_index
        )
    else:
        st.session_state.model = DEFAULT_MODEL
        st.warning(
            "Could not read the model list from Ollama. "
            "Is Ollama running?"
        )
        st.caption(f"Using default: `{DEFAULT_MODEL}`")

    st.divider()

    st.subheader("📌 Project Features")
    st.write("💬 AI Chatbot")
    st.write("📝 Study Notes Generator")
    st.write("🧠 Interactive Quiz")
    st.write("📚 Multiple Subjects")

    st.divider()

    st.subheader("⚙️ Technology")
    st.write("🐍 Python")
    st.write("🎨 Streamlit")
    st.write("🦙 Ollama")
    st.write("🧠 Llama 3.2")

    st.divider()

    st.caption("Developed as a Student AI Project")

# ---------------------------------------------------------------
# Main page
# ---------------------------------------------------------------
st.title("🤖 AI Student Assistant")
st.write("Ask questions, generate study notes, and test your knowledge.")

subject = st.selectbox("📚 Select your subject:", SUBJECTS)

tab_chat, tab_notes, tab_quiz = st.tabs(["💬 Chat", "📝 Study Notes", "🧠 Quiz"])

# ---------------------------------------------------------------
# TAB 1: Chat
# ---------------------------------------------------------------
with tab_chat:
    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    # Show previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    question = st.chat_input("Ask your question...")

    if question:
        with st.chat_message("user"):
            st.write(question)

        st.session_state.messages.append({"role": "user", "content": question})

        system_prompt = f"""
You are an AI Student Assistant.

The student's selected subject is: {subject}

Answer questions in simple and clear language.
Explain difficult concepts step-by-step.
Give examples wherever useful.
If the question is related to programming, provide simple code examples.
Focus on helping an engineering student understand the topic.
"""

        messages_for_ai = [
            {"role": "system", "content": system_prompt}
        ] + st.session_state.messages[-MAX_HISTORY:]

        with st.chat_message("assistant"):
            try:
                answer = st.write_stream(stream_ollama(messages_for_ai))
            except Exception as e:
                ollama_error(e)
                answer = None

        if answer:
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )
        else:
            # Remove the unanswered question so the history stays valid
            st.session_state.messages.pop()

# ---------------------------------------------------------------
# TAB 2: Study Notes Generator
# ---------------------------------------------------------------
with tab_notes:
    st.subheader("📝 Study Notes Generator")

    topic = st.text_input("Enter a topic for notes:", key="notes_topic")

    if st.button("Generate Notes"):
        if topic.strip():
            notes_prompt = f"""
You are an AI study assistant for engineering students.

Subject: {subject}
Topic: {topic}

Create short, exam-friendly notes.
Include:
1. Definition
2. Important points
3. Example
4. Advantages or applications if relevant

Use simple English and clear headings.
"""
            with st.spinner("Generating notes..."):
                notes = ask_ollama([{"role": "user", "content": notes_prompt}])

            if notes:
                st.session_state.notes = notes
                st.session_state.notes_title = topic.strip()
        else:
            st.warning("Please enter a topic first.")

    # Shown outside the button block so notes stay after other clicks
    if st.session_state.notes:
        st.markdown(f"### 📚 Notes: {st.session_state.notes_title}")
        st.markdown(st.session_state.notes)

        file_name = re.sub(r"\W+", "_", st.session_state.notes_title) or "notes"
        st.download_button(
            "⬇️ Download Notes",
            data=st.session_state.notes,
            file_name=f"{file_name}.md",
            mime="text/markdown",
        )

# ---------------------------------------------------------------
# TAB 3: Interactive Quiz
# ---------------------------------------------------------------
with tab_quiz:
    st.subheader("🧠 Interactive Quiz")

    quiz_topic = st.text_input(
        "Enter a topic for quiz:", key="interactive_quiz_topic"
    )

    if st.button("Generate Quiz", key="interactive_generate_quiz"):
        if quiz_topic.strip():
            with st.spinner("Generating quiz..."):
                quiz = generate_quiz(subject, quiz_topic.strip())

            if quiz:
                st.session_state.quiz_data = quiz
                st.session_state.quiz_result = None
                # New version => new radio keys => old answers are cleared
                st.session_state["quiz_version"] = (
                    st.session_state.get("quiz_version", 0) + 1
                )
        else:
            st.warning("Please enter a topic first.")

    quiz = st.session_state.quiz_data

    if quiz:
        st.markdown("### 📝 Answer the Questions")

        submitted = st.session_state.quiz_result is not None
        version = st.session_state.quiz_version

        for i, q in enumerate(quiz):
            st.markdown(f"**Question {i + 1}.** {q['question']}")
            st.radio(
                "Select your answer:",
                q["options"],
                index=None,              # nothing pre-selected
                key=f"quiz_{version}_{i}",
                disabled=submitted,
            )

        if not submitted:
            if st.button("✅ Submit Quiz", key="submit_quiz"):
                answers = [
                    st.session_state.get(f"quiz_{version}_{i}")
                    for i in range(len(quiz))
                ]

                if None in answers:
                    st.warning("Please answer all the questions before submitting.")
                else:
                    score = score_quiz(quiz, answers)
                    st.session_state.quiz_result = {
                        "score": score,
                        "total": len(quiz),
                        "answers": answers,
                    }
                    if score == len(quiz):
                        st.balloons()
                    st.rerun()

        # Result + review (kept in session_state so it survives reruns)
        result = st.session_state.quiz_result
        if result:
            score, total = result["score"], result["total"]
            st.success(f"🎉 Your Score: {score}/{total}")

            if score == total:
                st.success("Excellent! 🎯")
            elif score >= total * 0.6:
                st.info("Good job! Keep practicing. 👍")
            else:
                st.warning("Keep learning and try again! 📚")

            st.markdown("### 🔍 Review")
            for i, (q, given) in enumerate(zip(quiz, result["answers"])):
                if given == q["answer"]:
                    st.markdown(f"✅ **Q{i + 1}.** Correct — {q['answer']}")
                else:
                    st.markdown(
                        f"❌ **Q{i + 1}.** You chose *{given}*. "
                        f"Correct answer: **{q['answer']}**"
                    )
                if q["explanation"]:
                    st.caption(f"💡 {q['explanation']}")