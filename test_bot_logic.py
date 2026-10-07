from bot_logic import (
    is_greeting,
    find_programs,
    recommend_program,
    is_likely_in_scope
)


def test_real_greeting():
    assert is_greeting("hi") is True
    assert is_greeting("Hello!") is True


def test_which_is_not_greeting():
    # Regression test for the bug found during development.
    assert is_greeting(
        "Which program should I choose?"
    ) is False


def test_find_artificial_intelligence():
    programs = find_programs(
        "Tell me about artificial intelligence."
    )

    assert "Artificial Intelligence" in programs


def test_find_two_programs_for_comparison():
    programs = find_programs(
        "Compare cybersecurity and data analysis."
    )

    assert "Cybersecurity" in programs
    assert "Data Analysis" in programs


def test_ai_recommendation():
    result = recommend_program(
        "I like machine learning and Python.",
        "I want to build AI tools and automate tasks."
    )

    assert result == "Artificial Intelligence"


def test_software_recommendation():
    result = recommend_program(
        "I enjoy coding and programming.",
        "I want to build apps and websites."
    )

    assert result == "Software Engineering"


def test_out_of_scope_detection():
    assert is_likely_in_scope(
        "What is the weather tomorrow?"
    ) is False


def test_in_scope_detection():
    assert is_likely_in_scope(
        "How long is the cybersecurity program?"
    ) is True