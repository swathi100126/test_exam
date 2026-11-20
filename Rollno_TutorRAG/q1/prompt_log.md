# Prompt Log (Q1: TutorRAG web app)
Disclosure: Notes and question bank drafted with AI help (Claude), then edited and checked by me against my textbook.
App built with: Lovable

Prompt 2
"(paste the prompt above)"
Result: (fill in after testing)

Prompt 2b
"(paste the prompt above)"
Result: (fill in: did the two levels now differ clearly?)

Note: Lovable free credits ran out after Prompt 2.
I switched to Streamlit and used Cursor's AI to generate the code.
Prompts 3 onwards were given to Cursor (Grok), not to Lovable.

Prompt 3 (Cursor, Streamlit)
Feature: 1 Learner profile
"In Rollno_TutorRAG/q1, create a Streamlit app.py for TutorRAG, a study tutor for Class 10 Science: Life Processes. Build only the learner profile screen for now. Fields: nickname (required, 2 to 20 characters), level (beginner, intermediate or advanced), subject (fixed to Life Processes, read-only), current topic (Nutrition, Respiration, Transportation or Excretion) and preferred style (simple or exam-focused). Show a clear error under each invalid field and block continuing until all are valid. On a valid submit, save the profile in st.session_state and show a welcome message with the nickname. Keep the layout mobile friendly. Load the Groq key only from .env, never hardcode it."
What changed: (added groq dout chat with level-based answers.and session history)


Prompt 4 (Cursor, Streamlit)
Feature: 2 Doubt chat
"<In Rollno_TutorRAG/q1/app.py, add a doubt chat screen that opens after a valid profile is saved. Use the Groq API with a currently available Groq chat model, with the key loaded only from .env via python-dotenv. Use st.chat_input and st.chat_message, and keep the full conversation in st.session_state so it stays visible. Show the nickname and level at the top. Send the saved level and preferred style to the model with every question in the system prompt. Beginner: maximum 4 short sentences, simple everyday words, one real-life example, no technical terms. Intermediate: clear explanation with key terms defined, about 6 sentences. Advanced: detailed explanation with technical terms, the mechanism, and an exam-style point at the end. Show a friendly error message if the API call fails. Never hardcode the key.>"
What changed: (submitted profile as a beginer and answed my doubt)

Prompt 5 (Cursor, Streamlit)
Feature: 3 Cited answers
"<n Rollno_TutorRAG/q1/app.py, ground every answer in my course notes. Parse notes/notes.md: each note starts with "## Note N" and has Title, Topic, Section and Content lines. Split it into one chunk per note, keeping title, topic and section. Use scikit-learn TF-IDF with cosine similarity to retrieve the top 3 chunks for each question. Put only those chunks in the prompt to Groq and instruct the model to answer only from them, keep the level and style rules, and end with a citation line in this format: Source: [Note title, Section X.X]. If the best similarity score is below a threshold (start with 0.1, keep it in one variable), do not answer from general knowledge. Show "This question is outside the syllabus of the Life Processes notes" and suggest rephrasing. Also show the retrieved note titles and sections under each answer in an expander.>"
What changed: (What changed: Added retrieval from notes.md using TF-IDF (top 3 chunks). Answers now end with a source line (note title and section). The cricket question was flagged as outside the syllabus.)

Prompt 5b (Cursor, Streamlit)
"The cricket question was answered from general knowledge. Raise the similarity threshold to 0.2 and always show the outside-the-syllabus message when the score is lower."
What changed: Cricket question now flagged as outside the syllabus.

Prompt 6 (Cursor, Streamlit)
Feature: 4 Practice quiz
"<In Rollno_TutorRAG/q1/app.py, add academic integrity rules. Show a visible notice at the top of the chat: "TutorRAG helps you learn. It gives hints and steps, not full answers to graded homework or exams." Update the system prompt so that if the learner asks for homework-style help (for example "solve this", "write my answer", "complete my assignment", "write my essay" or "give me the answers to my test"), the tutor does not give the final solution. It gives 2 to 3 hints and step-by-step guidance and asks the learner to try the next step. If the learner asks the tutor to write graded work (an assignment, a lab report or an exam answer), the tutor politely refuses and offers to explain the concept instead. Keep the notes grounding and citation rules working.>"
What changed: (tested answering quiz giving right output)

Prompt 7 (Cursor, Streamlit)
Feature: 5 Academic integrity
"<In Rollno_TutorRAG/q1/app.py, improve usability. Use layout="centered" and make sure everything is readable on a phone screen. Keep the full chat history in st.session_state for the session. Add a sidebar with the saved profile (nickname, level, topic, style), an "Edit profile" button that returns to the profile form without losing the chat history, and a "Clear chat" button. Show a loading spinner while the model is answering. Show a friendly message instead of a crash if the API key is missing or the API fails. Check that every button works and nothing is broken.>"
What changed: ()

Prompt 8 (Cursor, Streamlit)
"<The "Clear chat" button in app.py does not work. Fix it: use a callback (on_click) that sets st.session_state.messages = [] (use the same session_state key the chat actually uses), and call st.rerun() afterwards if needed. Make sure the sidebar buttons have unique key values, and that the chat history is only initialised once with "if 'messages' not in st.session_state". Keep the profile and quiz state unchanged. Test it.>"
What changed: (checked all the buttons working,only clear chat not working )

Prompt 8b (Cursor, Streamlit)
feature :6 usability
"<In Rollno_TutorRAG/q1/app.py, improve usability. Use layout="centered" and make sure everything is readable on a phone screen. Keep the full chat history in st.session_state for the session. Add a sidebar with the saved profile (nickname, level, topic, style), an "Edit profile" button that returns to the profile form without losing the chat history, and a "Clear chat" button. Show a loading spinner while the model is answering. Show a friendly message instead of a crash if the API key is missing or the API fails. Check that every button works and nothing is broken.>"
What changed: Clear chat button now empties the conversation.





