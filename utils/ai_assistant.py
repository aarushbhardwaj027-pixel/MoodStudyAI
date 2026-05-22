import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# ========================= WELCOME MESSAGE =========================

def generate_welcome_message(day, topics):

    topics_text = ", ".join(topics)

    return f"""
    🚀 Welcome to Study Session Day {day}

    Today's topics:
    {topics_text}

    I'm your Moody AI Assistant 🤖

    Ask me doubts, explanations, examples, code help,
    revision questions, or topic summaries anytime.
    """

# ========================= ASK AI =========================

def ask_study_ai(day, topics, question):

        topics_text = ", ".join(topics)

        prompt = f"""
    You are Moody Study AI.

    Current Study Day: {day}

    Today's Topics:
    {topics_text}

    RULES:

    1. If the question is directly related to today's topics:
    - Answer normally
    - Explain simply
    - Use examples

    2. If question is related to education/studies but NOT today's topic:
    - Still answer it
    - Start answer with:
    "This is not directly related to today's topic, but to enrich your knowledge 📘"
    - End with:
    "Now let's get back to today's topic: {topics_text}"

    Examples:
    - science
    - math
    - programming
    - history
    - geography
    - physics
    - chemistry
    - biology
    - computers
    - school subjects

    3. If question is completely unrelated, random, or distracting:
    Refuse politely.

    Examples:
    - celebrity gossip
    - wars
    - politics
    - net worth
    - random heights/weights
    - viral drama
    - sports gossip
    - unrelated entertainment

    For unrelated questions reply ONLY:
    "Let's stay focused on studying 📚 Ask me something educational or related to today's topic."

    4. Keep answers:
    - short
    - beginner friendly
    - motivating
    - clean formatting

    Student Question:
    {question}
    """

        try:

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            print("AI ERROR:", e)
            return "AI is currently unavailable."