import os
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Function to generate all quiz questions in one API call
def generate_quiz(topic, num_questions):
    try:
        # Specify the prompt to get multiple questions in the desired format
        prompt = (
            f"Create {num_questions} multiple-choice questions about {topic}. "
            "Each question should have exactly four options, and after each question, specify the correct answer. "
            "For example: \n"
            "Q1. What is the capital of Jordan?\n"
            "Amman\nBaghdad\nJerusalem\nDemascus\n\nThe correct answer is Amman\n\n"
            "Q2. What country is to the west of Jordan?\n"
            "Syria\nEgypt\nPalestine\nSaudi Arabia\n\nCorrect answer is Palestine"
        )
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        # Return the generated content if successful
        if completion.choices and completion.choices[0].message:
            return completion.choices[0].message.content
        else:
            return "No response generated."
    except Exception as e:
        # Handle any errors and return the error message
        return f"An error occurred: {e}"

# Function to parse multiple questions, their options, and correct answers from API response
def parse_questions(content):
    questions = []
    # Split the content into lines and process each question block
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    i = 0
    while i < len(lines):
        if lines[i].startswith("Q"):
            question = lines[i]
            options = lines[i + 1:i + 5]
            correct_answer = lines[i + 5].split('is ')[-1]
            questions.append((question, options, correct_answer))
            i += 6
        else:
            i += 1
    return questions

# Function to reset all session state variables related to the quiz
def reset_quiz_state():
    st.session_state.current_question = 0  # Tracks the current question index
    st.session_state.user_answers = []  # Stores whether each answer is correct or not
    st.session_state.questions = []  # Stores all parsed questions with options and correct answers
    st.session_state.scores = []  # Tracks scores for each question
    st.session_state.quiz_ready = False  # Flag to indicate if the quiz is ready
    st.session_state.submitted = False  # Tracks whether the current question has been submitted
    st.session_state.next_enabled = False  # Ensures smooth transition to next question

# Initialize session state if it is not already set
if 'current_question' not in st.session_state:
    reset_quiz_state()

# Streamlit UI Title
st.title('MCQ Quiz Application')

# Input for the quiz topic
topic = st.text_input('Enter a Quiz Topic:').strip()

# Input for the number of questions
default_questions = 1  # Default number of questions if none is selected
num_questions = st.number_input('Enter Number of Questions:', min_value=1, max_value=10, step=1, value=default_questions)

# Button to generate the quiz
if st.button('Generate Quiz'):
    reset_quiz_state()  # Reset the quiz state before generating new questions
    response = generate_quiz(topic, num_questions)
    st.session_state.questions = parse_questions(response)
    st.session_state.quiz_ready = True  # Mark the quiz as ready to display

# Check if the quiz is ready and there are questions to display
if st.session_state.quiz_ready and st.session_state.questions:
    # Get the current question, options, and correct answer
    current_question, options, correct_answer = st.session_state.questions[st.session_state.current_question]

    # Display the current question
    st.write(f"{current_question}")
    # Display answer choices using radio buttons
    selected_answer = st.radio("Select an answer:", options, key=f"answer_{st.session_state.current_question}")

    # Submit button behavior
    if st.session_state.current_question == len(st.session_state.questions) - 1:
        if st.button('Submit Quiz'):
            if not st.session_state.submitted:
                # Check if the selected answer is correct
                is_correct = selected_answer.strip() == correct_answer.strip()
                # Append the result to session state
                st.session_state.user_answers.append(is_correct)
                st.session_state.scores.append(1 if is_correct else 0)
                st.session_state.submitted = True

                # Calculate and display the final score
                score = sum(st.session_state.scores)
                st.write(f"Your score is: {score}/{len(st.session_state.questions)}")

                # Provide feedback for each question
                for i, (question, _, correct) in enumerate(st.session_state.questions):
                    correctness = "Correct" if st.session_state.user_answers[i] else "Incorrect"
                    st.write(f"{question} - {correctness}")

                # Reset the quiz state for a new quiz
                reset_quiz_state()
    else:
        # Display submit button for individual questions
        if st.button('Submit Answer', key=f'submit_{st.session_state.current_question}'):
            if not st.session_state.submitted:
                # Check if the selected answer is correct
                is_correct = selected_answer.strip() == correct_answer.strip()
                # Append the result to session state
                st.session_state.user_answers.append(is_correct)
                st.session_state.scores.append(1 if is_correct else 0)
                st.session_state.submitted = True
                st.session_state.next_enabled = True

        if st.session_state.submitted and st.session_state.next_enabled:
            if st.button('Next Question', key=f'next_{st.session_state.current_question}'):
                st.session_state.current_question += 1
                st.session_state.submitted = False
                st.session_state.next_enabled = False