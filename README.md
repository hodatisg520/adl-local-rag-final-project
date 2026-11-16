# CS311 Advanced Deep Learning — Final Project

This repository contains the starter code and ongoing work for a local Retrieval-Augmented Generation (RAG) system. The system uses Ollama for local embedding and answer-generation models, LangChain for document processing, and Chroma for vector storage.

## Project structure

- `sample_code/run_txt.py` — command-line RAG application for TXT and PDF documents.
- `sample_code/requirements.txt` — Python dependencies.
- `sample_code/data_txt/` — sample TXT knowledge-base documents.
- `sample_code/major_handbook_pdfs/` — course-provided major handbooks for Task 2.
- `sample_code/TASK1_PDF_SUPPORT.md` — Task 1 implementation notes and verified demo command.
- `sample_code/evaluate_handbook.py` — repeatable question set for the selected CS handbook.
- `sample_code/TASK2_EVALUATION.md` — Task 2 evaluation and failure analysis.
- `docker/` — Task 3 Docker image and deployment instructions.
- `docker-compose.yml` — chatbot container configuration and persistent index volume.
- `sample_code/streamlit_app.py` — browser-based chat interface for Task 4.
- `sample_code/TASK4_UI.md` — Task 4 usage and UI verification notes.

Generated Chroma indexes, Python cache files, macOS metadata, and temporary Word lock files are excluded from version control.

## Setup

From the `sample_code` folder, create and activate a Python environment, install the requirements, and start Ollama:

```bash
conda create -n rag python=3.10
conda activate rag
pip install -r requirements.txt
ollama pull nomic-embed-text
ollama pull qwen2.5:0.5b
ollama pull qwen2.5:1.5b
ollama serve
```

Keep Ollama running in its terminal while you run the Python application in another terminal.

## Run the sample RAG application

```bash
cd sample_code
python run_txt.py --question "How many students are there at Fulbright?"
```

The default knowledge base is `sample_code/data_txt/`. You can point the application at another folder containing `.txt` and/or `.pdf` files with `--data-dir`.

## Task 2: CS major handbook chatbot

The selected handbook is `sample_code/major_handbook_pdfs/CS_MajorHandbook.pdf`. Start an interactive chatbot grounded in that single handbook with:

```bash
cd sample_code
python run_txt.py \
  --data-dir major_handbook_pdfs/CS_MajorHandbook.pdf \
  --vector-store data_txt/cs_handbook_vector_store \
  --rebuild-index \
  --llm-model qwen2.5:1.5b \
  --interactive
```

Enter `quit` or `exit` to close the chat. The chatbot shows the source PDF and page for retrieved passages. See `sample_code/TASK2_EVALUATION.md` for the questions, model comparison, observed failures, and inconsistencies in the handbook.

## Task 3: Docker deployment

The Python RAG application is packaged as a Docker image. It connects to Ollama running on the host Mac, where Ollama can use the machine's Apple GPU. The Compose configuration mounts the selected handbook read-only and keeps the Chroma index in a persistent Docker volume. See [`docker/README.md`](docker/README.md) for setup, build, run, re-index, and cleanup instructions.

## Task 4: Web chat interface

The Streamlit interface supports question input, browser-session conversation history, source pages, and a clear-chat control. Start it with `docker-compose up --build web`, then open `http://localhost:8501`. See [`sample_code/TASK4_UI.md`](sample_code/TASK4_UI.md) for screenshots, local setup, and verification details.

## Task 1: PDF support

The application extracts selectable text page by page from PDFs, splits it into chunks, embeds those chunks, and indexes them in Chroma. Retrieved PDF sources include page numbers. Scanned PDFs containing only images require OCR, which is outside the current implementation.

To repeat the verified demo using the assignment PDFs in the repository root:

```bash
cd sample_code
python run_txt.py \
  --data-dir .. \
  --vector-store data_txt/task1_pdf_demo_store \
  --rebuild-index \
  --question "How many main tasks does the project comprise?"
```

Expected answer: **The project comprises seven (07) main tasks.** The output includes the source PDF and page number. See `sample_code/TASK1_PDF_SUPPORT.md` for the verified result and details.

When documents change, add `--rebuild-index` so the saved index is refreshed.

## Progress

- Task 1: PDF ingestion and retrieval implemented and demonstrated.
- Task 2: CS handbook chatbot implemented, evaluated, and documented.
- Task 3: Docker image and Compose deployment implemented and verified locally.
- Task 4: Streamlit web interface implemented, tested with two handbook questions, and documented with a browser screenshot.
- Tasks 5–7: work in progress.
