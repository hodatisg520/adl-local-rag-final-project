# Task 4: Browser-based chatbot interface

The Streamlit application connects directly to the Task 2 RAG functions. It accepts questions in a browser, displays assistant responses and retrieved handbook pages, preserves the conversation within the current browser session, and provides a button to clear that history.

## Run in Docker

From the repository root, start Ollama as described in [`docker/README.md`](../docker/README.md), then run:

```bash
docker-compose up --build web
```

Open [http://localhost:8501](http://localhost:8501) in a browser. Stop the web server with `Ctrl+C` in the Terminal running Compose. The web container uses the same read-only CS handbook mount and persistent Chroma volume as the CLI chatbot.

## Run locally without Docker

From the `sample_code` folder, install the project requirements and start the app:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Ollama must be available at `http://127.0.0.1:11434` with `nomic-embed-text` and `qwen2.5:1.5b` downloaded. Set `OLLAMA_URL` if Ollama listens elsewhere.

## Interface behavior

- The sidebar identifies the selected handbook and the embedding and answer models.
- Questions and answers appear as chat messages.
- Each answer can show the three retrieved source passages, including PDF page and relevance score.
- The clear button resets the current session's conversation history.
- The handbook index is cached in the Docker volume or, for local runs, in `sample_code/data_txt/cs_handbook_vector_store`.

## Verification

Use questions with known handbook answers, for example:

1. `What is the prerequisite for CS 311 Advanced Deep Learning?` — expected: CS 313, handbook page 18.
2. `What must a student complete to declare the CS major?` — expected: two Computer Science courses, with MATH 202 also counting, handbook page 7.

The browser demo should show the answer, source pages, both turns in the conversation history, and the clear-chat control. The captured browser screenshot is saved in `screenshots/`.

The checked-in screenshot [`task4_answer_with_sources.png`](../screenshots/task4_answer_with_sources.png) shows the declaration-requirements answer and the collapsed panel indicating three retrieved sources. In the browser session, expanding the panel showed PDF pages 7, 7, and 4; the two-question history and clear-chat control were also confirmed.

The additional screenshot [`task4_two_question_history.jpg`](../screenshots/task4_two_question_history.jpg) shows both questions and answers in one session, with each answer's three-source panel and the clear-chat control visible.
