from app import analyze_sentences, flesch_score, highlighted_html, split_sentences


def test_flesch_score_is_correct_for_known_formula():
    text = "The cat sat on the mat."
    assert round(flesch_score(text), 1) == 116.1


def test_short_and_unpunctuated_text_are_handled():
    assert len(split_sentences("A short chapter")) == 1
    assert analyze_sentences("A short chapter")[0].words == 3


def test_highlighting_preserves_original_sentence_text():
    text = "A tiny sentence. This is a considerably longer sentence with complicated vocabulary."
    sentences = analyze_sentences(text)
    result = highlighted_html(text, sentences[-1:])
    assert "A tiny sentence." in result
    assert "This is a considerably longer sentence with complicated vocabulary." in result
    assert "sentence-highlight" in result


def test_fewer_than_five_sentences_still_analyze():
    assert len(analyze_sentences("One sentence. Two sentences?")) == 2
