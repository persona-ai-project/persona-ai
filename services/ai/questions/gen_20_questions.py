import time
from services.ai.questions.question_engine import next_question

# 20 different personas with different gaps
personas = [
    {"name": "Ali", "profession": "", "hobbies": ["cricket"], "goals": [], "personality": "", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Sara", "profession": "Doctor", "hobbies": [], "goals": [], "personality": "", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Bilal", "profession": "Student", "hobbies": ["reading"], "goals": [], "personality": "", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Zara", "profession": "Teacher", "hobbies": ["painting"], "goals": ["travel the world"], "personality": "", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Hassan", "profession": "", "hobbies": [], "goals": [], "personality": "", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Fatima", "profession": "Engineer", "hobbies": ["cooking"], "goals": [], "personality": "introverted", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Omar", "profession": "Designer", "hobbies": [], "goals": ["start a business"], "personality": "creative", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Ayesha", "profession": "", "hobbies": ["music"], "goals": [], "personality": "", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Kamran", "profession": "Manager", "hobbies": ["football"], "goals": [], "personality": "", "background": "", "updated_at": "2026-01-01T00:00:00+00:00"},
    {"name": "Nadia", "profession": "Nurse", "hobbies": [], "goals": ["buy a house"], "personality": "caring", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Tariq", "profession": "", "hobbies": ["gaming"], "goals": [], "personality": "competitive", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Hina", "profession": "Accountant", "hobbies": ["yoga"], "goals": [], "personality": "", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Usman", "profession": "Developer", "hobbies": ["chess"], "goals": ["learn AI"], "personality": "", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Maryam", "profession": "", "hobbies": [], "goals": [], "personality": "", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Faisal", "profession": "Freelancer", "hobbies": ["photography"], "goals": [], "personality": "adventurous", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Sana", "profession": "Student", "hobbies": [], "goals": ["become a doctor"], "personality": "", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Raza", "profession": "Lawyer", "hobbies": ["reading"], "goals": [], "personality": "analytical", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Amna", "profession": "", "hobbies": ["dancing"], "goals": [], "personality": "", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Waqar", "profession": "Chef", "hobbies": ["traveling"], "goals": [], "personality": "", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
    {"name": "Lubna", "profession": "Researcher", "hobbies": ["writing"], "goals": ["publish a book"], "personality": "curious", "background": "", "updated_at": "2026-05-23T00:00:00+00:00"},
]

print("=== 20 Generated Questions for Team Review ===\n")
for i, persona in enumerate(personas):
    result = next_question(f"user-{i}", persona)
    print(f"{i+1}. Name: {persona['name']} | Gap: {result['gap_field']} ({result['gap_type']})")
    print(f"   Question: {result['question']}")
    print()
    time.sleep(13)  # 13 second wait between each call