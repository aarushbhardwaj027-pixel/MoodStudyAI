import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_plan(syllabus_text, days):

    prompt = f"""
You are an expert AI study planner.

Your job:
- Divide syllabus into {days} study days only no random number of days only given days
- Create SMALL detailed subtopics
- Arrange from easy → difficult
- Keep topics beginner friendly but detailed
- Each topic should feel like a checklist item
- Add a short one-line explanation
- Also make sure you names topics nicley for eg: if a user uplaoded python syllabus
  you divide syllabus in parts and name topics like varibale,operators they are not detailed
  nicley even c++ and js have variables but we are doing python so name topic like Python-Variable 
  to make it simple, no need to do everywhere only that places where there is mutliple subjects
  having same topics like if we r doing c++ and topic is pointer only c++ and c has pointers 
  but still write c++ - pointer to make it clear

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
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5,
        max_tokens=4000
    )

    plan_text = response.choices[0].message.content

    plan = []

    current_day = None
    current_topics = []

    for line in plan_text.split("\n"):

        line = line.strip()

        if line.startswith("Day"):

            if current_day is not None:

                plan.append({
                    "day": current_day,
                    "topics": current_topics
                })

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

    if current_day is not None:

        plan.append({
            "day": current_day,
            "topics": current_topics
        })

    return plan