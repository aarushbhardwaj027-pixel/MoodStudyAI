import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise Exception("API key not found. Check .env file")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

def generate_plan(syllabus_text, days=30):

    prompt = f"""
You are an expert AI study planner.

Your job:
- Divide syllabus into {days} study days
- Create SMALL detailed subtopics
- Arrange from easy → difficult
- Keep topics beginner friendly
- Each topic should feel like a checklist item
- Add a short one-line explanation

STRICT OUTPUT FORMAT:

Day 1
- Variables :: storing data values
- Data Types :: int, string, float basics
- Print Statements :: displaying output
- Input Function :: taking user input

Day 2
- Conditions :: if else basics
- Loops :: repeating tasks
- Functions :: reusable blocks of code

IMPORTANT:
- NO paragraphs
- NO markdown
- NO extra text
- ONLY follow format exactly

Syllabus:
{syllabus_text}
"""

    response = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5
    )

    plan_text = response.choices[0].message.content

    plan = []

    current_day = None
    current_topics = []

    for line in plan_text.split("\n"):

        line = line.strip()

        if line.startswith("Day"):

            # save previous day
            if current_day is not None:

                plan.append({
                    "day": current_day,
                    "topics": current_topics
                })

            # start new day
            try:
                current_day = int(
                    line.replace("Day", "").strip()
                )

                current_topics = []

            except:
                continue

        elif line.startswith("-"):

            topic = line.replace("-", "").strip()

            current_topics.append(topic)

    # save last day
    if current_day is not None:

        plan.append({
            "day": current_day,
            "topics": current_topics
        })

    return plan