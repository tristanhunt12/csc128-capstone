import re
from program_data import PROGRAMS


def contains_phrase(text, phrase):
    """
    Checks for a complete word or phrase instead of matching letters
    inside another word.

    Example:
    'hi' will match 'hi' but will NOT match 'which'.
    """
    text = text.lower()
    phrase = phrase.lower()

    pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
    return re.search(pattern, text) is not None


def is_greeting(text):
    text = text.lower().strip()

    return re.fullmatch(
        r"(hi|hello|hey|hi there|hello there|hey there)[!?. ]*",
        text
    ) is not None


def find_programs(text):
    """
    Finds all Central Piedmont programs mentioned by the user.
    """
    matches = []

    aliases = []

    for program_name, program in PROGRAMS.items():
        for alias in program["aliases"]:
            aliases.append(
                (alias, program_name)
            )

    aliases.sort(
        key=lambda item: len(item[0]),
        reverse=True
    )

    for alias, program_name in aliases:
        if contains_phrase(text, alias):
            if program_name not in matches:
                matches.append(program_name)

    return matches


def get_program_markdown(program_name):
    """
    Returns deterministic program facts from the local knowledge base.
    """
    program = PROGRAMS[program_name]

    return f"""
### {program_name}

**Degree:** {program['degree']}

**Typical timeline:** {program['duration']}

**Learning format:** {program['format']}

**Locations:** {", ".join(program['locations'])}

**About the program:**  
{program['description']}

**Skills covered:**  
{", ".join(program['skills'])}

**Possible career directions:**  
{", ".join(program['careers'])}

*Program information is grounded in the project's curated Central Piedmont knowledge base.*
"""


def compare_programs_markdown(first_name, second_name):
    """
    Creates a deterministic comparison between two programs.
    """
    first = PROGRAMS[first_name]
    second = PROGRAMS[second_name]

    return f"""
### {first_name} vs. {second_name}

#### {first_name}

- **Degree:** {first['degree']}
- **Typical timeline:** {first['duration']}
- **Format:** {first['format']}
- **Skills:** {", ".join(first['skills'])}
- **Career directions:** {", ".join(first['careers'])}

#### {second_name}

- **Degree:** {second['degree']}
- **Typical timeline:** {second['duration']}
- **Format:** {second['format']}
- **Skills:** {", ".join(second['skills'])}
- **Career directions:** {", ".join(second['careers'])}

The better choice depends on the kind of subjects and work you enjoy.
"""


def has_profile_detail(text):
    """
    Determines whether a recommendation request already includes
    useful information about the student's interests.
    """
    for program in PROGRAMS.values():

        terms = (
            program["interests"]
            + program["skills"]
            + program["work_styles"]
        )

        for term in terms:
            if contains_phrase(text, term):
                return True

    return False


def recommend_program(interest, career_goal):
    """
    Scores programs using the two recommendation slots:
    1. student interest
    2. career/work goal
    """
    profile = f"{interest} {career_goal}".lower()

    scores = {}

    for program_name, program in PROGRAMS.items():
        score = 0

        for term in program["interests"]:
            if contains_phrase(profile, term):
                score += 3

        for skill in program["skills"]:
            if contains_phrase(profile, skill):
                score += 2

        for work_style in program["work_styles"]:
            if contains_phrase(profile, work_style):
                score += 3

        for career in program["careers"]:
            if contains_phrase(profile, career):
                score += 2

        scores[program_name] = score

    best_program = max(
        scores,
        key=scores.get
    )

    if scores[best_program] == 0:
        return None

    return best_program


def is_likely_in_scope(text):
    """
    Used before sending an unmatched question to the LLM.
    This helps prevent unrelated questions from being answered.
    """
    scope_terms = [
        "central piedmont",
        "cpcc",
        "program",
        "degree",
        "major",
        "career",
        "job",
        "study",
        "college",
        "campus",
        "online",
        "class",
        "course",
        "skill",
        "learn",
        "format",
        "duration",
        "how long",
        "cost",
        "tuition",
        "salary",
        "financial aid",
        "compare"
    ]

    for term in scope_terms:
        if contains_phrase(text, term):
            return True

    if find_programs(text):
        return True

    return False


def get_all_program_facts():
    """
    Converts the local knowledge base into text that can safely be
    supplied to the language model.
    """
    sections = []

    for program_name, program in PROGRAMS.items():

        section = (
            f"PROGRAM: {program_name}\n"
            f"Degree: {program['degree']}\n"
            f"Duration: {program['duration']}\n"
            f"Format: {program['format']}\n"
            f"Locations: {', '.join(program['locations'])}\n"
            f"Description: {program['description']}\n"
            f"Skills: {', '.join(program['skills'])}\n"
            f"Career directions: {', '.join(program['careers'])}"
        )

        sections.append(section)

    return "\n\n".join(sections)