import streamlit as st
import ollama

# Page settings
import streamlit as st
import ollama

# Page settings
st.set_page_config(
    page_title="AI Student Assistant",
    page_icon="🤖",
    layout="wide"
)

# Sidebar
with st.sidebar:

    st.title("🤖 AI Student Assistant")

    st.write(
        "Your personal AI-powered study assistant."
    )

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

# Main page
st.title("🤖 AI Student Assistant")

st.write(
    "Ask questions, generate study notes, and test your knowledge."
)

# Subject selection
subject = st.selectbox(
    "📚 Select your subject:",
    [
        "General",
        "Programming",
        "DBMS",
        "Computer Networks",
        "Operating Systems",
        "Software Testing",
        "Artificial Intelligence",
        "Machine Learning"
    ]
)
# Study Notes Generator
st.subheader("📝 Study Notes Generator")

topic = st.text_input("Enter a topic for notes:")

if st.button("Generate Notes"):
    if topic:

        with st.spinner("Generating notes..."):

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

            response = ollama.chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "user",
                        "content": notes_prompt
                    }
                ]
            )

            notes = response["message"]["content"]

            st.markdown("### 📚 Generated Notes")
            st.write(notes)

    else:
        st.warning("Please enter a topic first.")
        # Quiz Generator
# Interactive Quiz Generator
st.subheader("🧠 Interactive Quiz")

quiz_topic = st.text_input(
    "Enter a topic for quiz:",
    key="interactive_quiz_topic"
)

if st.button("Generate Quiz", key="interactive_generate_quiz"):

    if quiz_topic:

        with st.spinner("Generating quiz..."):

            quiz_prompt = f"""
            Create exactly 5 multiple choice questions.

            Subject: {subject}
            Topic: {quiz_topic}

            Return ONLY valid JSON in this format:

            [
                {{
                    "question": "Question here",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "answer": "Option A"
                }}
            ]

            Rules:
            - Create exactly 5 questions.
            - Each question must have exactly 4 options.
            - The answer must exactly match one option.
            - Do not add any extra text outside JSON.
            """

            response = ollama.chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "user",
                        "content": quiz_prompt
                    }
                ]
            )

            quiz_text = response["message"]["content"]

            try:
                import json

                quiz_data = json.loads(quiz_text)

                st.session_state.quiz_data = quiz_data

            except:
                st.error("Quiz format error. Please generate again.")

    else:
        st.warning("Please enter a topic first.")


# Display Quiz
if "quiz_data" in st.session_state:

    st.markdown("### 📝 Answer the Questions")

    user_answers = []

    for i, question in enumerate(st.session_state.quiz_data):

        st.write(f"### Question {i + 1}")
        st.write(question["question"])

        answer = st.radio(
            "Select your answer:",
            question["options"],
            key=f"question_{i}"
        )

        user_answers.append(answer)

    if st.button("✅ Submit Quiz", key="submit_quiz"):

        score = 0

        for i, question in enumerate(st.session_state.quiz_data):

            if user_answers[i] == question["answer"]:
                score += 1

        st.success(
            f"🎉 Your Score: {score}/5"
        )

        if score == 5:
            st.balloons()
            st.success("Excellent! 🎯")

        elif score >= 3:
            st.info("Good job! Keep practicing. 👍")

        else:
            st.warning("Keep learning and try again! 📚")
# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Clear chat button
if st.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
question = st.chat_input("Ask your question...")

if question:

    # Display user question
    with st.chat_message("user"):
        st.write(question)

    # Save user question
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    # Create instruction for AI
    system_prompt = f"""
    You are an AI Student Assistant.

    The student's selected subject is: {subject}

    Answer questions in simple and clear language.
    Explain difficult concepts step-by-step.
    Give examples wherever useful.
    If the question is related to programming, provide simple code examples.
    Focus on helping an engineering student understand the topic.
    """

    # Ask Ollama
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            messages_for_ai = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ] + st.session_state.messages

            response = ollama.chat(
                model="llama3.2",
                messages=messages_for_ai
            )

            answer = response["message"]["content"]

            st.write(answer)

    # Save AI answer
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })