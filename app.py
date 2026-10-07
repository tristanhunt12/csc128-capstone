import streamlit as st
from groq import Groq

from program_data import PROGRAMS
from bot_logic import (
    is_greeting,
    find_programs,
    get_program_markdown,
    compare_programs_markdown,
    has_profile_detail,
    recommend_program,
    is_likely_in_scope,
    get_all_program_facts
)


GROQ_MODEL = "openai/gpt-oss-120b"


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="Central Piedmont Program & Career Path Assistant",
    page_icon="🎓",
    layout="centered"
)

st.title("🎓 Central Piedmont Program & Career Path Assistant")

st.caption(
    "This is a software-based chatbot created for a CSC-128 capstone project. "
    "It helps students explore selected Central Piedmont programs and career paths."
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! 👋 I'm the Central Piedmont Program & Career Path Assistant. "
                "I'm a software-based chatbot that can help you explore programs, "
                "compare options, look at career paths, or recommend a program "
                "based on your interests.\n\n"
                "What would you like help with?"
            )
        }
    ]

if "selected_program" not in st.session_state:
    st.session_state.selected_program = None

if "recommendation_active" not in st.session_state:
    st.session_state.recommendation_active = False

if "recommendation_slots" not in st.session_state:
    st.session_state.recommendation_slots = {
        "interest": None,
        "career_goal": None
    }


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.header("About")

    st.write(
        "This chatbot currently covers six Central Piedmont programs."
    )

    st.write(
        "- Artificial Intelligence\n"
        "- Cybersecurity\n"
        "- Data Analysis\n"
        "- Software Engineering\n"
        "- Cloud and Networking Technologies\n"
        "- Business Administration"
    )

    st.caption(
        "Program facts come from a curated local knowledge base. "
        "The language model is only used with grounded program information."
    )

    if st.button("Start Over"):
        st.session_state.messages = []
        st.session_state.selected_program = None
        st.session_state.recommendation_active = False
        st.session_state.recommendation_slots = {
            "interest": None,
            "career_goal": None
        }

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Hi! 👋 I'm the Central Piedmont Program & Career Path "
                    "Assistant. What would you like help with?"
                )
            }
        )

        st.rerun()


# --------------------------------------------------
# LLM
# --------------------------------------------------

def grounded_llm_response(user_question, facts):
    """
    Uses Groq for natural-language responses while strictly limiting
    the model to facts from the project's knowledge base.

    If the API is unavailable, the deterministic chatbot still works.
    """

    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return None

    if not api_key:
        return None

    try:
        client = Groq(
            api_key=api_key
        )

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a software-based college program assistant. "
                        "Answer ONLY from the supplied FACTS. "
                        "Do not use outside knowledge. "
                        "Do not invent tuition, salaries, credits, acceptance "
                        "rates, deadlines, rankings, percentages, statistics, "
                        "or any other numbers. "
                        "If the requested information is not contained in FACTS, "
                        "clearly say that the project's knowledge base does not "
                        "contain that information. "
                        "Do not guarantee employment or career outcomes. "
                        "Keep the response friendly, useful, and concise."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"FACTS:\n{facts}\n\n"
                        f"STUDENT QUESTION:\n{user_question}"
                    )
                }
            ]
        )

        answer = completion.choices[0].message.content

        if answer:
            return answer.strip()

    except Exception:
        return None

    return None


# --------------------------------------------------
# RECOMMENDATION / SLOT FILLING
# --------------------------------------------------

def reset_recommendation():
    st.session_state.recommendation_active = False

    st.session_state.recommendation_slots = {
        "interest": None,
        "career_goal": None
    }


def finish_recommendation():
    interest = st.session_state.recommendation_slots["interest"]
    career_goal = st.session_state.recommendation_slots["career_goal"]

    recommendation = recommend_program(
        interest,
        career_goal
    )

    if recommendation is None:

        reset_recommendation()

        return (
            "I don't have enough information to make a grounded recommendation "
            "from the programs in my knowledge base. Try again and mention "
            "something like coding, AI, data, cybersecurity, networking, "
            "business, or the type of work you want to do."
        )

    st.session_state.selected_program = recommendation

    program = PROGRAMS[recommendation]

    facts = (
        f"Recommended program: {recommendation}\n"
        f"Degree: {program['degree']}\n"
        f"Duration: {program['duration']}\n"
        f"Format: {program['format']}\n"
        f"Description: {program['description']}\n"
        f"Skills: {', '.join(program['skills'])}\n"
        f"Career directions: {', '.join(program['careers'])}\n"
        f"Student interest: {interest}\n"
        f"Student career goal: {career_goal}"
    )

    ai_explanation = grounded_llm_response(
        (
            "Briefly explain why this program could fit the student's "
            "stated interests and career goal. Do not add facts that are "
            "not provided."
        ),
        facts
    )

    response = (
        f"Based on the two things you told me, **{recommendation}** "
        f"looks like the strongest match in my current program set.\n\n"
    )

    if ai_explanation:
        response += (
            f"**AI-generated grounded explanation:**  \n"
            f"{ai_explanation}\n\n"
        )

    response += get_program_markdown(
        recommendation
    )

    reset_recommendation()

    return response


def handle_recommendation_slot(user_text):

    lowered = user_text.lower().strip()

    if lowered in [
        "cancel",
        "stop",
        "nevermind",
        "never mind"
    ]:
        reset_recommendation()

        return (
            "No problem — I canceled the recommendation. "
            "What else would you like to explore?"
        )

    slots = st.session_state.recommendation_slots

    # SLOT 1
    if slots["interest"] is None:

        slots["interest"] = user_text

        return (
            "Got it. **Second question:** what kind of work or career "
            "sounds interesting to you?\n\n"
            "For example, you could say you want to build apps, analyze "
            "data, protect networks, work with AI, manage computer systems, "
            "or lead a business team."
        )

    # SLOT 2
    if slots["career_goal"] is None:

        slots["career_goal"] = user_text

        return finish_recommendation()

    return finish_recommendation()


def start_recommendation(user_text):

    st.session_state.recommendation_active = True

    st.session_state.recommendation_slots = {
        "interest": None,
        "career_goal": None
    }

    # If the first message already contains an interest,
    # use it as slot 1.
    if has_profile_detail(user_text):

        st.session_state.recommendation_slots["interest"] = user_text

        return (
            "That gives me your **first piece of information: your interests.** "
            "Now I need one more thing.\n\n"
            "**What kind of work or career would you like to do?**"
        )

    return (
        "Absolutely. I'll ask you **two quick questions** so I can make "
        "a grounded recommendation.\n\n"
        "**First:** what subjects or activities interest you most?\n\n"
        "For example: coding, AI, data, cybersecurity, networking, "
        "business, statistics, or something similar."
    )


# --------------------------------------------------
# RESPONSE HELPERS
# --------------------------------------------------

def list_programs():

    names = "\n".join(
        f"- {program_name}"
        for program_name in PROGRAMS
    )

    return (
        "I currently have grounded information for these programs:\n\n"
        f"{names}\n\n"
        "You can ask me about one, compare two, or ask me to recommend one."
    )


def career_response(program_name):

    careers = PROGRAMS[program_name]["careers"]

    return (
        f"Possible career directions connected to **{program_name}** "
        f"in my knowledge base include:\n\n"
        + "\n".join(
            f"- {career}"
            for career in careers
        )
        + "\n\nThese are examples, not employment guarantees."
    )


def selected_program_followup(text, program_name):

    program = PROGRAMS[program_name]

    if any(
        phrase in text
        for phrase in [
            "career",
            "careers",
            "job",
            "jobs"
        ]
    ):
        return career_response(
            program_name
        )

    if any(
        phrase in text
        for phrase in [
            "skill",
            "skills",
            "learn",
            "study",
            "what do you learn"
        ]
    ):
        return (
            f"In **{program_name}**, the knowledge base lists these "
            f"skills and topics:\n\n"
            + "\n".join(
                f"- {skill}"
                for skill in program["skills"]
            )
        )

    if any(
        phrase in text
        for phrase in [
            "campus",
            "location",
            "locations",
            "online"
        ]
    ):
        return (
            f"**{program_name}** is listed for: "
            f"{', '.join(program['locations'])}.\n\n"
            f"Learning format: **{program['format']}**."
        )

    if any(
        phrase in text
        for phrase in [
            "how long",
            "duration",
            "timeline"
        ]
    ):
        return (
            f"The typical timeline listed for **{program_name}** is "
            f"**{program['duration']}**."
        )

    if any(
        phrase in text
        for phrase in [
            "tell me more",
            "more information",
            "more info",
            "what about it"
        ]
    ):
        return get_program_markdown(
            program_name
        )

    return None


# --------------------------------------------------
# MAIN MESSAGE HANDLER
# --------------------------------------------------

def handle_message(user_text):

    text = user_text.lower().strip()

    # Continue slot filling before processing other intents.
    if st.session_state.recommendation_active:
        return handle_recommendation_slot(
            user_text
        )

    # INTENT 1: GREETING
    if is_greeting(user_text):

        return (
            "Hi! 👋 I can help you explore programs, compare programs, "
            "look at careers, or recommend a program based on your interests."
        )

    # INTENT 2: LIST PROGRAMS
    if any(
        phrase in text
        for phrase in [
            "list programs",
            "what programs",
            "which programs",
            "programs do you cover",
            "programs can you help"
        ]
    ):
        return list_programs()

    # INTENT 3: COMPARE PROGRAMS
    if any(
        phrase in text
        for phrase in [
            "compare",
            "difference between",
            " versus ",
            " vs "
        ]
    ):

        programs = find_programs(
            user_text
        )

        if len(programs) >= 2:

            return compare_programs_markdown(
                programs[0],
                programs[1]
            )

        return (
            "I can compare two programs, but I need both program names. "
            "For example: **Compare Cybersecurity and Data Analysis.**"
        )

    # INTENT 4: RECOMMENDATION
    if any(
        phrase in text
        for phrase in [
            "recommend",
            "which program should",
            "what program should",
            "best program for me",
            "what should i study",
            "what should i major",
            "which major"
        ]
    ):
        return start_recommendation(
            user_text
        )

    detected_programs = find_programs(
        user_text
    )

    detected_program = (
        detected_programs[0]
        if detected_programs
        else None
    )

    if detected_program:
        st.session_state.selected_program = detected_program

    # INTENT 5: CAREER QUESTIONS
    if any(
        phrase in text
        for phrase in [
            "career",
            "careers",
            "job",
            "jobs"
        ]
    ):

        program_name = (
            detected_program
            or st.session_state.selected_program
        )

        if program_name:

            return career_response(
                program_name
            )

        return (
            "I can help with career directions, but I need to know which "
            "program you're asking about first."
        )

    # INTENT 6: SPECIFIC PROGRAM INFO
    if detected_program:

        return get_program_markdown(
            detected_program
        )

    # CONVERSATION STATE FOLLOW-UP
    if st.session_state.selected_program:

        followup = selected_program_followup(
            text,
            st.session_state.selected_program
        )

        if followup:
            return followup

    # GROUNDED LLM FALLBACK FOR IN-SCOPE QUESTIONS
    if is_likely_in_scope(
        user_text
    ):

        answer = grounded_llm_response(
            user_text,
            get_all_program_facts()
        )

        if answer:

            return (
                f"{answer}\n\n"
                "*This response was generated by the language model using "
                "only the project's Central Piedmont knowledge base.*"
            )

        return (
            "That question is related to Central Piedmont, but I don't have "
            "enough information in my current knowledge base to answer it "
            "reliably. I don't want to make up an answer."
        )

    # OUT-OF-SCOPE / GRACEFUL FAILURE
    return (
        "I'm not able to answer that because it's outside the scope of this "
        "chatbot. I'm designed specifically to help with the Central Piedmont "
        "programs in my knowledge base and their related career paths."
    )


# --------------------------------------------------
# DISPLAY CHAT HISTORY
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# --------------------------------------------------
# USER INPUT
# --------------------------------------------------

user_input = st.chat_input(
    "Ask about a program, career, comparison, or recommendation..."
)

if user_input:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    with st.chat_message(
        "user"
    ):

        st.markdown(
            user_input
        )

    response = handle_message(
        user_input
    )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )

    with st.chat_message(
        "assistant"
    ):

        st.markdown(
            response
        )