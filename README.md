# CS311 Advanced Deep Learning — Final Project

This repository contains a local Retrieval-Augmented Generation (RAG) chatbot built around the course-provided sample code. It indexes text and selectable-text PDF documents with LangChain and Chroma, creates embeddings and answers questions with Ollama, and exposes both a command-line interface and a Streamlit web app. The Task 2 knowledge source is the B.S. Computer Science major handbook.

## Repository contents

| Path | Contents |
| --- | --- |
| `sample_code/run_txt.py` | RAG ingestion, retrieval, answer generation, and CLI |
| `sample_code/streamlit_app.py` | Browser chat interface using the shared RAG backend |
| `sample_code/data_txt/` | Small text documents for the starter example |
| `sample_code/major_handbook_pdfs/` | Course-provided major handbooks, including the selected CS handbook |
| `docker/`, `docker-compose.yml` | Container build and CLI/web deployment configuration; Docker's locked Python dependencies are in `sample_code/requirements-docker.txt` |
| `report/` | Final report PDF, editable source, and build script |
| `demo_video/` | User-recorded combined demo currently covering Tasks 1–4 |
| `screenshots/` | Verified Task 4 interface screenshot |
| `Final-project-ADL*.pdf` | Assignment documents used as Task 1 sample PDFs |

Task-specific notes and evidence are in `sample_code/TASK1_PDF_SUPPORT.md`, `sample_code/TASK2_EVALUATION.md`, `docker/README.md`, and `sample_code/TASK4_UI.md`. Generated Chroma indexes are intentionally excluded from Git; the application creates them on first run and reuses them on later runs.

## Get the repository

Clone the project and move into its folder:

```bash
git clone https://github.com/hodatisg520/adl-local-rag-final-project.git
cd adl-local-rag-final-project
```

## Requirements

| Workflow | Requirements file | Additional requirements |
| --- | --- | --- |
| Local RAG app and evaluation | `sample_code/requirements.txt` | Python 3.12 (tested); [Ollama](https://ollama.com/download) with `nomic-embed-text` and `qwen2.5:1.5b` |
| Docker app | `sample_code/requirements-docker.txt` (locked versions) | [Docker with Compose](https://docs.docker.com/compose/install/); Ollama reachable from the container |
| Rebuild the report | `report/requirements.txt` | Python and ReportLab |

The Task 2 model comparison also uses `qwen2.5:0.5b`. The report PDF and the current user-recorded demo MP4 are already included.

## Local setup

In Terminal 1, start Ollama and leave it running. If the Ollama desktop app is already open and serving requests, skip `ollama serve`:

```bash
ollama serve
```

In Terminal 2, from the repository root, create a Python virtual environment, install dependencies, and download the models. `ollama pull` requires the Ollama server to be running:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r sample_code/requirements.txt
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
ollama pull qwen2.5:0.5b
```

With the virtual environment still active in Terminal 2, run the sample question:

```bash
cd sample_code
python run_txt.py --question "How many students are there at Fulbright?"
```

For a new Terminal session, run `source .venv/bin/activate` from the repository root before using Python. The default input folder is `sample_code/data_txt/`. Pass `--data-dir` to use another folder or PDF file. Use `--rebuild-index` after changing the input documents.

## Task 1: PDF support

The loader extracts selectable text page by page and preserves each PDF filename and page number in the indexed chunks. From the `sample_code` folder, reproduce the assignment-PDF example with:

```bash
python run_txt.py \
  --data-dir .. \
  --vector-store data_txt/task1_pdf_demo_store \
  --rebuild-index \
  --question "How many main tasks does this final project have?"
```

Expected answer: **The project comprises seven (07) main tasks.** Sources should include the assignment PDFs and page numbers. This example indexes the PDFs in the repository root; it does not use the major handbook selected for Task 2. Scanned PDFs and text embedded in images require OCR, which is not implemented.

## Task 2: CS handbook chatbot

The selected document is `sample_code/major_handbook_pdfs/CS_MajorHandbook.pdf`. Start an interactive chatbot grounded in that handbook alone:

```bash
cd sample_code
python run_txt.py \
  --data-dir major_handbook_pdfs/CS_MajorHandbook.pdf \
  --vector-store data_txt/cs_handbook_vector_store \
  --rebuild-index \
  --llm-model qwen2.5:1.5b \
  --interactive
```

Type `quit` or `exit` to close the chat. To repeat the 13-question evaluation, run `python evaluate_handbook.py --handbook major_handbook_pdfs/CS_MajorHandbook.pdf --vector-store data_txt/cs_handbook_vector_store --model qwen2.5:1.5b --rebuild-index`. See `sample_code/TASK2_EVALUATION.md` for the manual scoring, model comparison, and failure analysis.

## Task 3: Docker deployment

The Docker image runs the Python app, while Ollama runs on the host computer. Docker Compose mounts the CS handbook read-only and stores Chroma data in a named persistent volume. From the repository root, the CLI can be started with:

```bash
docker-compose build
docker-compose run --rm chatbot
```

For prerequisites, starting Ollama so the container can reach it, rebuilding the index, and volume cleanup, follow [`docker/README.md`](docker/README.md). A local configuration template is provided in `.env.example`.

## Task 4: Browser interface

Start the Streamlit service with Docker Compose:

```bash
docker-compose up --build web
```

Then open [http://localhost:8501](http://localhost:8501). The interface keeps conversation history for the browser session, displays source pages and retrieval scores, and has a clear-chat control. See [`sample_code/TASK4_UI.md`](sample_code/TASK4_UI.md) for local setup, verification questions, and the checked-in screenshot.

## Task 5: Final report

The report is available as [`report/final_project_report.pdf`](report/final_project_report.pdf), with its editable Markdown source and ReportLab build script in the same folder. To rebuild it, install `report/requirements.txt` and run `python report/build_report.py` from the repository root.

## Task 6: Video demos

The user-recorded [VideoDemo.mp4](demo_video/VideoDemo.mp4) is a 3-minute-32-second, 1080p recording that shows Tasks 1–4 in one combined video. The assignment requires four separate video files, one for each task, so this combined recording still needs to be split or re-recorded as separate deliverables before final submission.

The submission builder expects these filenames: `task1_pdf_support.mp4`, `task2_handbook_chatbot.mp4`, `task3_docker_deployment.mp4`, and `task4_web_interface.mp4`.

## Known limitations

- PDF extraction covers selectable text, not scanned images; OCR is not included.
- A grounded prompt and citations do not guarantee a correct answer. The evaluation documents incorrect, incomplete, and source-conflict cases; verify important answers against the cited handbook page.
- The Docker container expects Ollama to be running on a reachable host endpoint. The default macOS/Colima address is `host.docker.internal:11434`; other setups may need `OLLAMA_URL` configured.

## Task 7: GitHub repository and README

The project repository is [`hodatisg520/adl-local-rag-final-project`](https://github.com/hodatisg520/adl-local-rag-final-project). It contains the source code, dependency lists, Docker configuration, handbook and example data, report, screenshots, and current video demo. The linked task notes provide implementation details and evidence for reproducing and reviewing the project.

## Canvas submission package

Run `python3 scripts/build_submission.py --student-id YOUR_ID --output-dir /path/to/output` to create the `ADL-YOUR_ID-project/` folder with `source_code/`, `docker/`, `report/`, and `demo_video/`. The script leaves the package's `demo_video/` folder empty until the four separate task videos are ready. The combined `VideoDemo.mp4` does not meet the builder's four-file requirement. After preparing the four expected filenames in a separate directory, rerun the command with `--videos-dir /path/to/your/videos --force` to create the matching ZIP file. Add the repository URL to your Canvas submission comment.
