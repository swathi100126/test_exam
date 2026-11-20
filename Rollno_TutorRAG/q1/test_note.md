# Test note

Checked locally with `streamlit run Rollno_TutorRAG/q1/app.py`. The Groq key was loaded from the environment. It is not in the code.

Profile used after the validation check: Riya, Beginner, Nutrition, Simple.

## Profile

Nickname `A`, with level, topic, and style left unset, stayed on the form. The page showed:

- Enter a nickname of 2 to 20 characters.
- Choose beginner, intermediate, or advanced.
- Choose Nutrition, Respiration, Transportation, or Excretion.
- Choose simple or exam-focused.

A valid profile opened the tutor. Screenshot: `screenshots/01_profile_validation.png` (nickname error at the top of the form).

## Doubt chat

Asked "What is photosynthesis?" The reply used short everyday words, a houseplant-by-the-window example, and ended with `Source: [Photosynthesis, Section 1.2]`. The Notes used expander listed Photosynthesis, Section 1.2; Common mistakes, Section 1.12; and Transpiration, Section 1.10. The chat notice was visible: TutorRAG helps you learn and gives hints, not full answers to graded work. Screenshot: `screenshots/02_doubt_chat.png`.

## Outside syllabus

Asked "Who won the cricket world cup?" The reply was: "This question is outside the syllabus of the Life Processes notes. Try rephrasing it with words from those notes." Screenshot: `screenshots/03_outside_syllabus.png`.

## Practice quiz

Nutrition, easy, five questions. Answers entered: Salivary amylase; In the chloroplasts; Chlorophyll; In the mouth; `6CO2 + 6H2O -> C6H12O6 + 6O2`. Result: Score: 4 out of 5. The mouth answer was marked Incorrect, with an explanation that protein digestion starts in the stomach. The other four were Correct, each with the stored answer. Screenshot: `screenshots/04_practice_quiz.png`.

## Sidebar

The sidebar showed Nickname Riya, Level Beginner, Topic Nutrition, Style Simple, Edit profile, and Clear chat. Screenshot: `screenshots/05_sidebar.png`.

Edit profile returned to the form with those values filled in. Continuing again kept both chat messages. Clear chat removed them. The profile and the quiz score stayed.
