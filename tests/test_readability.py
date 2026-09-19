from truthcast.readability import count_sentences, count_syllables, grade_level, hard_words


def test_syllables_handle_silent_e_and_short_words():
    assert count_syllables("make") == 1
    assert count_syllables("the") == 1
    assert count_syllables("cat") == 1
    assert count_syllables("water") == 2
    assert count_syllables("beautiful") == 3


def test_empty_text_scores_zero():
    assert grade_level("") == 0.0
    assert count_sentences("") == 0


def test_simple_text_scores_lower_than_dense_text():
    simple = "The sun is a big star. It gives us light. Plants need it to grow."
    dense = (
        "Notwithstanding the epistemological ramifications, the constitutional "
        "adjudication process necessitates considerable deliberation among "
        "institutional stakeholders."
    )
    assert grade_level(simple) < 5.0 < grade_level(dense)


def test_lines_without_periods_still_count_as_sentences():
    # Headlines rarely end in a period; treating them as one long sentence
    # would wrongly inflate the grade.
    assert count_sentences("Sleep matters\nCoffee is fine\nSugar is not") == 3


def test_hard_words_finds_the_long_ones():
    found = hard_words("The epistemological ramifications are considerable today.")
    assert "epistemological" in found
    assert "the" not in found
