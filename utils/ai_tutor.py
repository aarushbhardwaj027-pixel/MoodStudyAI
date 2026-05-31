import os
import json
import traceback
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = "llama-3.1-8b-instant"


# ================= SAFE JSON =================

def safe_parse_json(text):
    try:
        if not text:
            return None
        text = text.strip()
        if "```" in text:
            text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except:
            pass
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end != -1:
            return json.loads(text[start:end])
        return None
    except Exception as e:
        print("JSON ERROR:", e)
        return None


# ================= NORMALIZE ANSWER =================

def normalize_answer(ans):
    if not ans:
        return "A"
    ans = str(ans).strip().upper()
    if ans not in ["A", "B", "C", "D"]:
        return "A"
    return ans


# ================= CALL AI =================

def call_ai(prompt, system="Return ONLY valid JSON. No markdown. No explanation."):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.5
    )
    return response.choices[0].message.content


# ================= QA =================

def generate_qa(topic, intensity):
    prompt = f"""
Topic: {topic}
Intensity: {intensity}

Generate 3-5 important exam Q&A pairs. Match count and difficulty to intensity.

Return ONLY valid JSON:
{{
  "qa": [
    {{
      "question": "...",
      "answer": "..."
    }}
  ]
}}
"""
    try:
        text = call_ai(prompt)
        return safe_parse_json(text) or {"qa": []}
    except Exception as e:
        print("QA ERROR:", e)
        return {"qa": []}


# ================= MORE MCQS =================

def generate_more_mcqs(topic, intensity):
    prompt = f"""
Topic: {topic}
Intensity: {intensity}

Generate exactly 5 practice MCQs, different from basic ones.
Each must have 4 options. answer must be exactly A, B, C or D.
Match difficulty to intensity.

Return ONLY valid JSON:
{{
  "mcqs": [
    {{
      "question": "...",
      "options": ["option A", "option B", "option C", "option D"],
      "answer": "A"
    }}
  ]
}}
"""
    try:
        text = call_ai(prompt)
        data = safe_parse_json(text)
        if not data:
            return {"mcqs": []}
        for m in data.get("mcqs", []):
            m["answer"] = normalize_answer(m.get("answer"))
        return data
    except Exception as e:
        print("MORE MCQ ERROR:", e)
        return {"mcqs": []}


# ================= NOTES =================

def generate_notes(topic, intensity, mood):
    prompt = f"""
Topic: {topic}
Mood: {mood}
Intensity: {intensity}

Generate clean structured study notes.

Return ONLY valid JSON:
{{
  "summary": "3-4 line overview",
  "key_points": ["point 1", "point 2", "point 3"],
  "important_formulas": ["formula 1"],
  "remember": ["tip 1", "tip 2"],
  "quick_recap": "one paragraph revision"
}}

If no formulas exist return empty list for important_formulas.
"""
    try:
        text = call_ai(prompt)
        return safe_parse_json(text) or {}
    except Exception as e:
        print("NOTES ERROR:", e)
        return {}


# ================= MAIN TUTOR =================

def generate_ai_tutor_content(mood, topics, intensity):
    cleaned_topics = []
    for t in topics:
        if "::" in t:
            parts = t.split("::")
            cleaned_topics.append(f"{parts[0].strip()} - {parts[1].strip()}")
        else:
            cleaned_topics.append(t.strip())

    prompt = f"""
You are a strict JSON generator. Generate study content for every topic listed.

TOPICS: {cleaned_topics}
MOOD: {mood}
INTENSITY: {intensity}

RULES:
- Output ONLY valid JSON, no markdown, no explanation
- Cover ALL {len(cleaned_topics)} topics in the same order
- NEVER skip a topic
- explanation: 4-5 lines, match difficulty to intensity
- example: one short practical example or code snippet
- EXACTLY 3 MCQs per topic
- answer must be ONLY A, B, C or D

OUTPUT FORMAT:
{{
  "topics": [
    {{
      "name": "topic name",
      "explanation": "4-5 line explanation",
      "example": "short practical example",
      "mcqs": [
        {{
          "question": "question text",
          "options": ["option A text", "option B text", "option C text", "option D text"],
          "answer": "A"
        }}
      ]
    }}
  ]
}}
"""

    try:
        text = call_ai(prompt)
        data = safe_parse_json(text)

        if not data or "topics" not in data:
            print("TUTOR: bad or empty response")
            return {"topics": []}

        cleaned = []
        for t in data.get("topics", []):
            mcqs = t.get("mcqs", [])[:3]
            for m in mcqs:
                m["answer"] = normalize_answer(m.get("answer"))
            cleaned.append({
                "name":        t.get("name", "Unknown Topic"),
                "explanation": t.get("explanation", "No explanation provided."),
                "example":     t.get("example", "No example provided."),
                "mcqs":        mcqs
            })

        return {"topics": cleaned}

    except Exception:
        print("TUTOR ERROR:")
        traceback.print_exc()
        return {"topics": []}