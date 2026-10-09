"""ChapterLens - local chapter readability analyzer."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Iterable

import streamlit as st

try:
    import textstat
except ImportError:  # pragma: no cover - exercised when dependency is unavailable
    textstat = None


SAMPLE_CHAPTER = """Mara had always believed that the lighthouse was empty. Every evening, she watched its lantern turn across the bay, painting the dark water with a patient, silver rhythm. No one had tended it since the old keeper vanished during a winter storm.

On the first night of October, a light appeared in the lower window. Mara crossed the dunes with a borrowed coat wrapped tightly around her shoulders. The door opened before she touched the handle, and a warm breath of candle smoke drifted into the cold.

Inside, the stairs rose through darkness. Somewhere above her, a clock began to count the seconds. Mara climbed anyway, because the light had not appeared by accident, and because the sea below was already calling her name."""


@dataclass(frozen=True)
class Sentence:
    text: str
    start: int
    end: int
    words: int
    syllables: int
    complexity: float
    difficulty: float


def _fallback_syllables(word: str) -> int:
    """Estimate syllables without external services or APIs."""
    cleaned = re.sub(r"[^a-z]", "", word.lower())
    if not cleaned:
        return 0
    if len(cleaned) <= 3:
        return 1
    groups = len(re.findall(r"[aeiouy]+", cleaned))
    if cleaned.endswith("e") and not cleaned.endswith(("le", "ye")) and groups > 1:
        groups -= 1
    if cleaned.endswith("ed") and len(cleaned) > 4 and groups > 1:
        groups -= 1
    return max(1, groups)


def syllables(word: str) -> int:
    if textstat is not None:
        try:
            return max(1, int(textstat.syllable_count(word)))
        except (TypeError, ValueError):
            pass
    return _fallback_syllables(word)


def words_in(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*", text)


def split_sentences(text: str) -> list[tuple[str, int, int]]:
    """Split on terminal punctuation while preserving exact source positions."""
    matches = list(re.finditer(r".+?(?:[.!?]+(?=\s|$)|$)", text, flags=re.S))
    return [
        (match.group().strip(), match.start() + len(match.group()) - len(match.group().lstrip()), match.end())
        for match in matches
        if match.group().strip()
    ]


def flesch_score(text: str) -> float:
    if textstat is not None:
        try:
            return round(float(textstat.flesch_reading_ease(text)), 1)
        except (ValueError, ZeroDivisionError):
            pass
    word_list = words_in(text)
    sentence_count = max(1, len(split_sentences(text)))
    if not word_list:
        return 0.0
    total_syllables = sum(syllables(word) for word in word_list)
    return round(206.835 - 1.015 * (len(word_list) / sentence_count) - 84.6 * (total_syllables / len(word_list)), 1)


def score_label(score: float) -> tuple[str, str]:
    if score >= 70:
        return "Easy to read", "Clear, accessible prose for most readers."
    if score >= 50:
        return "Moderate", "Some longer or more complex passages may need a second read."
    return "Difficult", "Dense sentence structure or word choice may slow readers down."


def analyze_sentences(text: str) -> list[Sentence]:
    analyzed: list[Sentence] = []
    for sentence_text, start, end in split_sentences(text):
        sentence_words = words_in(sentence_text)
        if not sentence_words:
            continue
        sentence_syllables = sum(syllables(word) for word in sentence_words)
        long_words = sum(len(re.sub(r"[^A-Za-z]", "", word)) >= 8 for word in sentence_words)
        avg_word_length = sum(len(re.sub(r"[^A-Za-z]", "", word)) for word in sentence_words) / len(sentence_words)
        complexity = min(100.0, (long_words / len(sentence_words)) * 100 + max(0, avg_word_length - 5) * 10)
        length_factor = min(100.0, len(sentence_words) / 35 * 100)
        syllable_factor = min(100.0, sentence_syllables / max(1, len(sentence_words)) / 3 * 100)
        difficulty = round(length_factor * 0.4 + complexity * 0.3 + syllable_factor * 0.3, 1)
        analyzed.append(Sentence(sentence_text, start, end, len(sentence_words), sentence_syllables, complexity, difficulty))
    return analyzed


def difficulty_label(score: float) -> str:
    if score >= 70:
        return "Very challenging"
    if score >= 45:
        return "Challenging"
    return "Watch this sentence"


def suggestions(sentence: Sentence) -> list[str]:
    ideas: list[str] = []
    if sentence.words > 25:
        ideas.append("Try dividing it into two sentences to give the main idea more breathing room.")
    if sentence.complexity >= 35:
        ideas.append("Swap one or two abstract or long words for shorter, more concrete alternatives.")
    if sentence.syllables / max(1, sentence.words) >= 1.8:
        ideas.append("Read it aloud and simplify any phrase that feels difficult to say in one breath.")
    if not ideas:
        ideas.append("The sentence is broadly balanced; a quick read-aloud pass may still reveal small edits.")
    return ideas


def highlighted_html(text: str, hardest: Iterable[Sentence]) -> str:
    highlights = sorted(hardest, key=lambda item: item.start)
    chunks: list[str] = []
    cursor = 0
    for index, sentence in enumerate(highlights):
        if sentence.start < cursor:
            continue
        chunks.append(html.escape(text[cursor:sentence.start]).replace("\n", "<br>"))
        label = difficulty_label(sentence.difficulty)
        chunks.append(
            f'<mark class="sentence-highlight" title="{html.escape(label)}">'
            f"{html.escape(text[sentence.start:sentence.end])}</mark>"
        )
        cursor = sentence.end
    chunks.append(html.escape(text[cursor:]).replace("\n", "<br>"))
    return "".join(chunks)


def render_score_card(score: float) -> None:
    label, description = score_label(score)
    st.markdown(
        f"""<div class="score-card">
          <div><span class="eyebrow">Flesch Reading Ease</span>
          <div class="score-number">{score:.1f}<span>/100</span></div>
          <div class="score-label">{label}</div>
          <p>{description}</p></div>
          <div class="score-ring"><span>{round(score):.0f}</span></div>
        </div>""",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="ChapterLens", page_icon="📖", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(
        """<style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Libre+Baskerville:wght@400;700&display=swap');
        :root { --ink:#24231f; --muted:#716d64; --paper:#f7f4ed; --card:#fffdf8; --accent:#b56d4d; --line:#e6dfd2; }
        .stApp { background:var(--paper); color:var(--ink); font-family:'DM Sans',sans-serif; }
        [data-testid="stTextAreaRootElement"],
        [data-testid="stTextAreaRootElement"] > div,
        [data-testid="stTextArea"] textarea,
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="textarea"] textarea {
            background-color:var(--card) !important;
            color:var(--ink) !important;
            -webkit-text-fill-color:var(--ink) !important;
            caret-color:var(--accent) !important;
            border-color:var(--line) !important;
        }
        [data-testid="stTextArea"] textarea::selection,
        div[data-baseweb="textarea"] textarea::selection {
            background-color:#f2cdbd !important;
            color:var(--ink) !important;
        }
        h1,h2,h3 { font-family:'Libre Baskerville',serif !important; color:var(--ink); }
        .block-container { max-width:1180px; padding:3rem 2rem 5rem; }
        .brand { font:700 1.15rem 'DM Sans'; letter-spacing:.04em; color:var(--accent); }
        .hero h1 { font-size:clamp(2.4rem,5vw,4.6rem); line-height:1.05; margin:.7rem 0 .8rem; }
        .hero p { color:var(--muted); font-size:1.12rem; max-width:650px; }
        .eyebrow { text-transform:uppercase; letter-spacing:.13em; font-size:.73rem; font-weight:700; color:var(--accent); }
        .score-card,.stat-card,.analysis-card,.chapter-card { background:var(--card); border:1px solid var(--line); border-radius:20px; padding:1.5rem; box-shadow:0 8px 24px rgba(70,55,35,.04); }
        .score-card { display:flex; justify-content:space-between; align-items:center; min-height:188px; }
        .score-number { font:700 3.4rem 'Libre Baskerville'; margin:.35rem 0; }
        .score-number span { font:400 1rem 'DM Sans'; color:var(--muted); }
        .score-label { font-weight:700; font-size:1.05rem; }
        .score-card p { color:var(--muted); margin:.35rem 0 0; max-width:360px; }
        .score-ring { width:90px; height:90px; border:9px solid #e8d3c7; border-top-color:var(--accent); border-right-color:var(--accent); border-radius:50%; display:grid; place-items:center; font-weight:700; color:var(--accent); }
        .stat-card { min-height:112px; } .stat-value { font:700 1.7rem 'Libre Baskerville'; margin-top:.4rem; } .stat-label { color:var(--muted); font-size:.85rem; }
        .sentence-row { border-top:1px solid var(--line); padding:1rem 0; } .sentence-row:first-child { border-top:0; }
        .sentence-text { font:1.02rem/1.65 'Libre Baskerville'; } .sentence-meta { color:var(--muted); font-size:.83rem; margin-top:.45rem; }
        .pill { display:inline-block; border-radius:99px; padding:.28rem .65rem; font-size:.74rem; font-weight:700; background:#f2dfd5; color:#85452d; margin-right:.35rem; }
        .chapter-preview { line-height:1.9; font:1.04rem/1.9 'Libre Baskerville'; color:#403d36; }
        .sentence-highlight { background:#f2cdbd; color:inherit; padding:.08rem .18rem; border-radius:4px; box-shadow:0 0 0 2px #e7b39d; }
        .note { color:var(--muted); font-size:.82rem; font-style:italic; }
        div.stButton > button { background:var(--accent); color:white; border:0; border-radius:10px; font-weight:700; padding:.65rem 1.2rem; }
        div.stButton > button:hover { background:#955337; color:white; }
        </style>""",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="brand">CHAPTERLENS</div><div class="hero"><h1>See where your chapter<br>asks readers to slow down.</h1><p>A calm, local readability check for authors. Find dense sentences, understand why they feel heavy, and revise with confidence.</p></div>', unsafe_allow_html=True)

    if "sample_chapter_pending" in st.session_state:
        st.session_state["chapter_input"] = st.session_state.pop("sample_chapter_pending")
    if "chapter_input" not in st.session_state:
        st.session_state["chapter_input"] = ""

    with st.container():
        input_col, options_col = st.columns([3, 1])
        with input_col:
            st.markdown("### Paste your chapter")
            chapter = st.text_area(
                "Chapter text",
                height=300,
                placeholder="Paste a chapter or a scene here...",
                label_visibility="collapsed",
                key="chapter_input",
            )
        with options_col:
            st.markdown("### Start quickly")
            if st.button("Use sample chapter", use_container_width=True):
                st.session_state["sample_chapter_pending"] = SAMPLE_CHAPTER
                st.rerun()
            st.markdown('<p class="note">Your text stays in this browser session. No account or API key required.</p>', unsafe_allow_html=True)
        analyze = st.button("Analyze chapter  →", type="primary", use_container_width=False)

    if analyze or "analysis" in st.session_state:
        if analyze:
            chapter = st.session_state["chapter_input"]
        if not chapter.strip():
            st.warning("Paste some chapter text or load the sample chapter to begin.")
            return
        sentence_data = analyze_sentences(chapter)
        if not sentence_data:
            st.warning("I couldn't find complete sentences. Add punctuation such as periods, question marks, or exclamation marks.")
            return
        score = flesch_score(chapter)
        st.session_state["analysis"] = (chapter, sentence_data, score)
        st.divider()
        render_score_card(score)
        word_count = len(words_in(chapter))
        sentence_count = len(sentence_data)
        average = word_count / sentence_count
        read_time = max(1, round(word_count / 220))
        cols = st.columns(4)
        for col, value, label in zip(cols, [word_count, sentence_count, f"{average:.1f}", f"{read_time} min"], ["Words", "Sentences", "Avg. sentence length", "Estimated reading time"]):
            with col:
                st.markdown(f'<div class="stat-card"><div class="stat-value">{value}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)
        st.markdown("### Five hardest sentences")
        st.caption("These are rule-based estimates using sentence length, word complexity, and syllable density—not a judgment of your writing.")
        hardest = sorted(sentence_data, key=lambda item: item.difficulty, reverse=True)[:5]
        left, right = st.columns([1.15, 1])
        with left:
            st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
            for number, sentence in enumerate(hardest, 1):
                st.markdown(f'<div class="sentence-row"><span class="eyebrow">#{number} · {difficulty_label(sentence.difficulty)}</span><div class="sentence-text">{html.escape(sentence.text)}</div><div class="sentence-meta"><span class="pill">{sentence.words} words</span><span class="pill">Difficulty {sentence.difficulty:.0f}/100</span></div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with right:
            st.markdown("### Gentle revision ideas")
            for number, sentence in enumerate(hardest, 1):
                with st.expander(f"Sentence {number}: {sentence.text[:55]}{'…' if len(sentence.text) > 55 else ''}"):
                    for idea in suggestions(sentence):
                        st.markdown(f"- {idea}")
        st.markdown("### Chapter map")
        st.markdown('<div class="chapter-card"><div class="chapter-preview">' + highlighted_html(chapter, hardest) + "</div></div>", unsafe_allow_html=True)
        st.markdown('<p class="note">Highlighted passages are the five highest-scoring sentences by our local heuristic. Readability scores are estimates, not definitive judgments of writing quality.</p>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
