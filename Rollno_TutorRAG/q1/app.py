import json
import os
import random
import re
from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SUBJECT = "Life Processes"
LEVELS = ("beginner", "intermediate", "advanced")
TOPICS = ("Nutrition", "Respiration", "Transportation", "Excretion")
STYLES = ("simple", "exam-focused")
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
CHAT_ERROR = "I couldn't answer that just now. Please try again in a moment."
OUTSIDE_SYLLABUS = (
    "This question is outside the syllabus of the Life Processes notes. "
    "Try rephrasing it with words from those notes."
)
NOTES_PATH = Path(__file__).resolve().parent / "notes" / "notes.md"
QUESTIONS_PATH = Path(__file__).resolve().parent / "questions_bank.csv"
SIMILARITY_THRESHOLD = 0.1
TOP_NOTES = 3
QUIZ_SIZE = 5
QUIZ_ERROR = "I couldn't mark the quiz just now. Please try again."
LEVEL_DIFFICULTY = {
    "beginner": "easy",
    "intermediate": "medium",
    "advanced": "hard",
}
QUIZ_POINTS = {
    "correct": 1.0,
    "partly correct": 0.5,
    "incorrect": 0.0,
}
QUIZ_LEVEL_RULES = {
    "beginner": "Use simple everyday words and no technical terms.",
    "intermediate": "Use clear wording and define any key term you use.",
    "advanced": "Technical terms are fine.",
}

LEVEL_LABELS = {
    "beginner": "Beginner",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
}
STYLE_LABELS = {
    "simple": "Simple",
    "exam-focused": "Exam-focused",
}
LEVEL_RULES = {
    "beginner": (
        "Use at most 4 short sentences. Use simple everyday words. "
        "Include one real-life example. Do not use technical terms."
    ),
    "intermediate": (
        "Give a clear explanation in about 6 sentences. "
        "Define each key term in everyday words."
    ),
    "advanced": (
        "Give a detailed explanation. Use the correct technical terms, "
        "explain the mechanism, and end with one exam-style point."
    ),
}
STYLE_RULES = {
    "simple": "Use friendly Class 10 wording.",
    "exam-focused": (
        "Use wording the student can reuse in a Class 10 exam, "
        "while still following the level rules."
    ),
}

NICKNAME_ERROR = "Enter a nickname of 2 to 20 characters."
LEVEL_ERROR = "Choose beginner, intermediate, or advanced."
TOPIC_ERROR = "Choose Nutrition, Respiration, Transportation, or Excretion."
STYLE_ERROR = "Choose simple or exam-focused."


def _load_groq_settings() -> tuple[str, str]:
    """Load Groq settings from .env. The key is never shown or stored."""
    app_dir = Path(__file__).resolve().parent
    repo_root = app_dir.parents[1]
    load_dotenv(app_dir / ".env")
    load_dotenv(repo_root / ".env")
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", "").strip() or DEFAULT_GROQ_MODEL
    return api_key, model


def _mark_profile_attempted() -> None:
    st.session_state.profile_attempted = True


def _open_profile_form() -> None:
    saved = st.session_state.learner_profile
    if saved:
        st.session_state.nickname = saved["nickname"]
        st.session_state.level = saved["level"]
        st.session_state.current_topic = saved["current_topic"]
        st.session_state.preferred_style = saved["preferred_style"]
    st.session_state.profile_attempted = False
    st.session_state.profile_ready = False


def _clear_chat() -> None:
    st.session_state.messages = []
    st.session_state.chat_error = False


def _nickname_error(value: str) -> str | None:
    cleaned = value.strip()
    if len(cleaned) < 2 or len(cleaned) > 20:
        return NICKNAME_ERROR
    return None


def _choice_error(value: str | None, allowed: tuple[str, ...], message: str) -> str | None:
    if value not in allowed:
        return message
    return None


def _parse_notes(notes_text: str) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    blocks = re.split(r"(?=^## Note \d+\s*$)", notes_text, flags=re.MULTILINE)
    for block in blocks:
        if not block.strip().startswith("## Note"):
            continue

        def field(name: str, source: str = block) -> str:
            match = re.search(rf"^{name}: (.+)$", source, flags=re.MULTILINE)
            return match.group(1).strip() if match else ""

        chunks.append(
            {
                "title": field("Title"),
                "topic": field("Topic"),
                "section": field("Section"),
                "content": field("Content"),
            }
        )
    return chunks


def _chunk_text(chunk: dict[str, str]) -> str:
    return "\n".join(
        [chunk["title"], chunk["topic"], chunk["section"], chunk["content"]]
    )


def _format_chunks(chunks: list[dict[str, str]]) -> str:
    blocks = []
    for chunk in chunks:
        blocks.append(
            "\n".join(
                [
                    f"Title: {chunk['title']}",
                    f"Topic: {chunk['topic']}",
                    f"Section: {chunk['section']}",
                    f"Content: {chunk['content']}",
                ]
            )
        )
    return "\n\n".join(blocks)


@st.cache_resource
def _note_index(notes_text: str):
    chunks = _parse_notes(notes_text)
    if not chunks:
        return chunks, None, None
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform([_chunk_text(chunk) for chunk in chunks])
    return chunks, vectorizer, matrix


def _retrieve(question: str) -> list[tuple[dict[str, str], float]]:
    notes_text = NOTES_PATH.read_text(encoding="utf-8")
    chunks, vectorizer, matrix = _note_index(notes_text)
    if not chunks or vectorizer is None or matrix is None:
        return []
    scores = cosine_similarity(vectorizer.transform([question]), matrix).ravel()
    scores[scores != scores] = 0.0
    ranking = scores.argsort()[::-1][:TOP_NOTES]
    return [(chunks[int(index)], float(scores[int(index)])) for index in ranking]


def _system_prompt(profile: dict[str, str], chunks: list[dict[str, str]]) -> str:
    level = profile["level"]
    style = profile["preferred_style"]
    return (
        "You are TutorRAG, a Class 10 Science tutor for Life Processes. "
        "Answer the student's latest doubt.\n\n"
        f"The student's level is {level}. "
        f"Their preferred style is {style}.\n"
        "Level rules always win if they conflict with the style.\n"
        "Integrity rules override a request for a complete final answer. "
        "They do not override the notes or the citation.\n"
        "If the learner asks for homework-style help, including \"solve this\", "
        "\"write my answer\", \"complete my assignment\", \"write my essay\", "
        "or \"give me the answers to my test\", do not give the final solution. "
        "Give 2 to 3 hints and step-by-step guidance in the learner's level of "
        "language, then ask the learner to try the next step.\n"
        "If the learner asks you to write graded work, such as an assignment, "
        "a lab report, or an exam answer, politely refuse and offer to explain "
        "the concept instead.\n"
        "Answer only from the notes below. Do not use general knowledge.\n"
        "The citation line is extra and does not count toward the sentence limit.\n"
        "End with one line in this exact form: "
        "Source: [Photosynthesis, Section 1.2]\n"
        "Use the title and section of the note that best supports the answer.\n\n"
        f"Level rules: {LEVEL_RULES[level]}\n"
        f"Style: {STYLE_RULES[style]}\n\n"
        f"Notes:\n{_format_chunks(chunks)}"
    )


def _reply_text(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            else:
                text = part.get("text") if isinstance(part, dict) else getattr(part, "text", None)
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()
    return ""


def _ask_tutor(
    profile: dict[str, str],
    messages: list[dict[str, str]],
    chunks: list[dict[str, str]],
) -> str:
    api_key, model = _load_groq_settings()
    if not api_key:
        raise RuntimeError("missing groq key")
    client = Groq(api_key=api_key)
    history = [
        {"role": message["role"], "content": message["content"]}
        for message in messages
    ]
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _system_prompt(profile, chunks)},
            *history,
        ],
        reasoning_effort="low",
        reasoning_format="hidden",
    )
    reply = _reply_text(completion.choices[0].message.content)
    if not reply:
        raise RuntimeError("empty tutor reply")
    return reply


@st.cache_data
def _load_questions(csv_text: str) -> list[dict[str, str]]:
    frame = pd.read_csv(StringIO(csv_text))
    return [
        {
            "topic": str(row.topic),
            "difficulty": str(row.difficulty),
            "question": str(row.question),
            "answer": str(row.answer),
        }
        for row in frame.itertuples(index=False)
    ]


def _question_bank() -> list[dict[str, str]]:
    return _load_questions(QUESTIONS_PATH.read_text(encoding="utf-8"))


def _select_quiz(topic: str, level: str) -> list[dict[str, str]]:
    difficulty = LEVEL_DIFFICULTY[level]
    bank = _question_bank()
    primary = [
        row for row in bank if row["topic"] == topic and row["difficulty"] == difficulty
    ]
    other = [
        row for row in bank if row["topic"] == topic and row["difficulty"] != difficulty
    ]
    random.shuffle(primary)
    random.shuffle(other)
    chosen = primary[:QUIZ_SIZE]
    if len(chosen) < QUIZ_SIZE:
        chosen.extend(other[: QUIZ_SIZE - len(chosen)])
    return chosen


def _start_quiz(profile: dict[str, str]) -> None:
    st.session_state.quiz_id = st.session_state.get("quiz_id", 0) + 1
    st.session_state.quiz_questions = _select_quiz(
        profile["current_topic"],
        profile["level"],
    )
    st.session_state.quiz_topic = profile["current_topic"]
    st.session_state.quiz_level = profile["level"]
    st.session_state.quiz_results = None
    st.session_state.quiz_score = None
    st.session_state.quiz_error = False


def _ensure_quiz(profile: dict[str, str]) -> None:
    if (
        st.session_state.get("quiz_questions")
        and st.session_state.get("quiz_topic") == profile["current_topic"]
        and st.session_state.get("quiz_level") == profile["level"]
    ):
        return
    _start_quiz(profile)


def _parse_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise RuntimeError("quiz response was not an object")
    return parsed


def _format_score(score: float) -> str:
    shown = str(int(score)) if float(score).is_integer() else f"{score:.1f}"
    return f"Score: {shown} out of {QUIZ_SIZE}"


def _mark_quiz(
    profile: dict[str, str],
    questions: list[dict[str, str]],
    student_answers: list[str],
) -> tuple[float, list[dict[str, str]]]:
    api_key, model = _load_groq_settings()
    if not api_key:
        raise RuntimeError("missing groq key")
    payload = [
        {
            "number": index,
            "question": question["question"],
            "stored_answer": question["answer"],
            "student_answer": answer.strip(),
        }
        for index, (question, answer) in enumerate(
            zip(questions, student_answers, strict=True),
            start=1,
        )
    ]
    instructions = (
        "You mark a Class 10 Life Processes quiz. "
        f"The learner's level is {profile['level']}. "
        f"{QUIZ_LEVEL_RULES[profile['level']]} "
        "Compare each student answer with the stored answer. "
        "The verdict must be exactly one of: correct, partly correct, incorrect. "
        "For a correct answer, set explanation to an empty string. "
        "For a partly correct or incorrect answer, explain what was wrong "
        "in 1 to 2 sentences. "
        "Return only JSON with this shape: "
        '{"results": [{"verdict": "correct", "explanation": ""}]} '
        "The results array must have one item per question, in the same order."
    )
    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": json.dumps(payload)},
        ],
        reasoning_effort="low",
        reasoning_format="hidden",
        response_format={"type": "json_object"},
    )
    parsed = _parse_json_object(_reply_text(completion.choices[0].message.content))
    raw_results = parsed.get("results")
    if not isinstance(raw_results, list) or len(raw_results) != len(questions):
        raise RuntimeError("quiz result count")
    cleaned: list[dict[str, str]] = []
    for item in raw_results:
        if not isinstance(item, dict):
            raise RuntimeError("quiz result item")
        verdict = str(item.get("verdict", "")).strip().lower()
        if verdict not in QUIZ_POINTS:
            raise RuntimeError("quiz verdict")
        explanation = "" if verdict == "correct" else str(item.get("explanation", "")).strip()
        cleaned.append({"verdict": verdict, "explanation": explanation})
    score = sum(QUIZ_POINTS[item["verdict"]] for item in cleaned)
    return score, cleaned


st.set_page_config(page_title="TutorRAG", layout="centered")

st.session_state.setdefault("profile_attempted", False)
st.session_state.setdefault("profile_ready", False)
st.session_state.setdefault("learner_profile", None)
if "messages" not in st.session_state:
    st.session_state.messages = []
st.session_state.setdefault("chat_error", False)
st.session_state.setdefault("quiz_id", 0)
st.session_state.setdefault("quiz_questions", None)
st.session_state.setdefault("quiz_results", None)
st.session_state.setdefault("quiz_score", None)
st.session_state.setdefault("quiz_error", False)

st.title("TutorRAG")
st.caption("Class 10 Science: Life Processes")

api_key, _groq_model = _load_groq_settings()
if not api_key:
    st.warning(
        "The tutor cannot connect yet. Add your Groq key to the .env file, then try again."
    )

profile = st.session_state.learner_profile
chat_open = st.session_state.profile_ready and profile is not None

if profile is not None:
    with st.sidebar:
        st.subheader("Your profile")
        st.markdown(f"**Nickname**  \n{profile['nickname']}")
        st.markdown(f"**Level**  \n{LEVEL_LABELS[profile['level']]}")
        st.markdown(f"**Topic**  \n{profile['current_topic']}")
        st.markdown(f"**Style**  \n{STYLE_LABELS[profile['preferred_style']]}")
        if chat_open and st.button(
            "Edit profile",
            key="edit_profile",
            width="stretch",
        ):
            _open_profile_form()
            st.rerun()
        if st.button(
            "Clear chat",
            key="clear_chat",
            on_click=_clear_chat,
            width="stretch",
        ):
            st.rerun()

if not chat_open:
    with st.form("learner_profile_form"):
        st.subheader("Learner profile")

        nickname_raw = st.text_input(
            "Nickname",
            max_chars=20,
            placeholder="2 to 20 characters",
            key="nickname",
        )
        nickname_error = None
        if st.session_state.profile_attempted:
            nickname_error = _nickname_error(nickname_raw)
            if nickname_error:
                st.error(nickname_error)

        level = st.segmented_control(
            "Level",
            LEVELS,
            format_func=lambda value: LEVEL_LABELS[value],
            key="level",
            width="stretch",
            wrap=True,
        )
        level_error = None
        if st.session_state.profile_attempted:
            level_error = _choice_error(level, LEVELS, LEVEL_ERROR)
            if level_error:
                st.error(level_error)

        st.text_input("Subject", value=SUBJECT, disabled=True)

        topic = st.segmented_control(
            "Current topic",
            TOPICS,
            key="current_topic",
            width="stretch",
            wrap=True,
        )
        topic_error = None
        if st.session_state.profile_attempted:
            topic_error = _choice_error(topic, TOPICS, TOPIC_ERROR)
            if topic_error:
                st.error(topic_error)

        style = st.segmented_control(
            "Preferred style",
            STYLES,
            format_func=lambda value: STYLE_LABELS[value],
            key="preferred_style",
            width="stretch",
            wrap=True,
        )
        style_error = None
        if st.session_state.profile_attempted:
            style_error = _choice_error(style, STYLES, STYLE_ERROR)
            if style_error:
                st.error(style_error)

        submitted = st.form_submit_button(
            "Continue",
            type="primary",
            icon=":material/arrow_forward:",
            on_click=_mark_profile_attempted,
            width="stretch",
        )

        if submitted:
            field_errors = (nickname_error, level_error, topic_error, style_error)
            if any(field_errors):
                st.session_state.profile_ready = False
            else:
                st.session_state.learner_profile = {
                    "nickname": nickname_raw.strip(),
                    "level": level,
                    "subject": SUBJECT,
                    "current_topic": topic,
                    "preferred_style": style,
                }
                st.session_state.profile_ready = True
                st.rerun()
else:
    st.caption(f"{profile['nickname']} · {LEVEL_LABELS[profile['level']]}")
    doubt_tab, quiz_tab = st.tabs(["Doubt chat", "Practice quiz"])

    with doubt_tab:
        st.info(
            "TutorRAG helps you learn. It gives hints and steps, "
            "not full answers to graded homework or exams."
        )
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                sources = message.get("sources") or []
                if sources:
                    with st.expander("Notes used"):
                        for source in sources:
                            st.markdown(f"{source['title']}, Section {source['section']}")

        if st.session_state.chat_error:
            st.error(CHAT_ERROR)

        prompt = st.chat_input(
            "Ask a doubt about Life Processes",
            submit_mode="disable",
        )
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            try:
                matches = _retrieve(prompt)
                best_score = matches[0][1] if matches else 0.0
                if best_score < SIMILARITY_THRESHOLD:
                    st.session_state.messages.append(
                        {"role": "assistant", "content": OUTSIDE_SYLLABUS}
                    )
                else:
                    chunks = [chunk for chunk, _score in matches]
                    with st.spinner("Thinking..."):
                        reply = _ask_tutor(profile, st.session_state.messages, chunks)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": reply,
                            "sources": [
                                {"title": chunk["title"], "section": chunk["section"]}
                                for chunk in chunks
                            ],
                        }
                    )
                st.session_state.chat_error = False
            except Exception:
                st.session_state.chat_error = True
            st.rerun()

    with quiz_tab:
        _ensure_quiz(profile)
        questions = st.session_state.quiz_questions
        difficulty = LEVEL_DIFFICULTY[profile["level"]]
        st.caption(f"{profile['current_topic']} · {difficulty}")

        with st.form("practice_quiz"):
            student_answers = []
            for index, question in enumerate(questions):
                student_answers.append(
                    st.text_area(
                        question["question"],
                        key=f"quiz_answer_{st.session_state.quiz_id}_{index}",
                    )
                )
            marked = st.form_submit_button(
                "Mark quiz",
                type="primary",
                width="stretch",
            )
        if marked:
            try:
                with st.spinner("Marking..."):
                    score, results = _mark_quiz(profile, questions, student_answers)
                st.session_state.quiz_score = score
                st.session_state.quiz_results = results
                st.session_state.quiz_error = False
            except Exception:
                st.session_state.quiz_score = None
                st.session_state.quiz_results = None
                st.session_state.quiz_error = True
            st.rerun()

        if st.session_state.quiz_error:
            st.error(QUIZ_ERROR)
        elif st.session_state.quiz_results:
            st.success(_format_score(st.session_state.quiz_score))
            for question, result in zip(questions, st.session_state.quiz_results, strict=True):
                st.markdown(f"**{question['question']}**")
                st.markdown(result["verdict"].capitalize())
                if result["explanation"]:
                    st.markdown(result["explanation"])
                st.caption(f"Stored answer: {question['answer']}")

        if st.button("New quiz", icon=":material/refresh:", width="stretch"):
            _start_quiz(profile)
            st.rerun()
