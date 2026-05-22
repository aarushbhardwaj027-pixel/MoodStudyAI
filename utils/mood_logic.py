def get_study_mode(mood, day_plan):

    mood = mood.lower()

    # ================= HAPPY / ENERGETIC =================

    if mood in ["happy", "excited", "good"]:

        return {
            "intensity": "high",
            "topics": day_plan,
            "study_time": 50,
            "break_time": 10,
            "style": "fast + practice heavy",
            "message": "High energy day! Let’s crush it 🚀",
            "max_cycles": 3
        } 

    # ================= NORMAL =================

    elif mood in ["normal", "okay", "fine"]:

        return {
            "intensity": "medium",
            "topics": day_plan,
            "study_time": 45,
            "break_time": 15,
            "style": "balanced learning",
            "message": "Steady focus mode 📘",
            "max_cycles": 3
        }

    # ================= LOW ENERGY =================

    elif mood in ["sad", "low", "tired"]:

        return {
            "intensity": "low",
            "topics": day_plan,
            "study_time": 30,
            "break_time": 20,
            "style": "simple explanations + slow pace",
            "message": "Easy mode today. Small progress is still progress 🌿",
            "max_cycles": 2
        }

    # ================= STRESSED =================

    elif mood in ["angry", "stressed", "anxious"]:

        return {
            "intensity": "very_low",
            "topics": day_plan,
            "study_time": 35,
            "break_time": 15,
            "style": "calm + revision only",
            "message": "First relax, then study 🧘",
            "max_cycles": 3
        }

    # ================= DEFAULT =================

    else:

        return {
            "intensity": "medium",
            "topics": day_plan,
            "study_time": 45,
            "break_time": 15,
            "style": "normal learning",
            "message": "Let’s begin 👍",
            "max_cycles": 3
        }