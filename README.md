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
| `demo_video/` | Four Task 1–4 demo videos, transcripts, and rebuild instructions |
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
| Local RAG app and evaluation | `sample_code/requirements.txt` | Python 3.10; [Ollama](https://ollama.com/download) with `nomic-embed-text` and `qwen2.5:1.5b` |
| Docker app | `sample_code/requirements-docker.txt` (locked versions) | [Docker with Compose](https://docs.docker.com/compose/install/); Ollama reachable from the container |
| Rebuild the report | `report/requirements.txt` | Python and ReportLab |
| Rebuild the demo videos | `demo_video/requirements.txt` | macOS, FFmpeg (`ffmpeg` and `ffprobe`), and the macOS `say` command |

The Task 2 model comparison also uses `qwen2.5:0.5b`. The demo MP4 files and report PDF are already included, so their build-only dependencies are needed only when regenerating them.

## Local setup

From the repository root, create an environment and install the application dependencies:

```bash
cd sample_code
conda create -n rag python=3.10
conda activate rag
python -m pip install -r requirements.txt
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
ollama pull qwen2.5:0.5b
```

Install [Ollama](https://ollama.com/download) if needed and make sure it is running locally. If it is not already running as an application or service, start it in a terminal:

```bash
ollama serve
```

Keep the Ollama terminal open. In another terminal, from the repository root, run the sample question:

```bash
cd sample_code
conda activate rag
python run_txt.py --question "How many students are there at Fulbright?"
```

The default input folder is `sample_code/data_txt/`. Pass `--data-dir` to use another folder or PDF file. Use `--rebuild-index` after changing the input documents.

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

Four separate 1080p walkthrough videos cover Tasks 1–4. Each explains the task purpose, shows relevant implementation excerpts, and presents verified results. The videos have English narration and matching transcripts; Task 4 includes a screenshot from the tested browser interface.

- [Task 1 — PDF support](demo_video/task1_pdf_support.mp4) · [transcript](demo_video/task1_pdf_support_transcript.txt)
- [Task 2 — handbook chatbot](demo_video/task2_handbook_chatbot.mp4) · [transcript](demo_video/task2_handbook_chatbot_transcript.txt)
- [Task 3 — Docker deployment](demo_video/task3_docker_deployment.mp4) · [transcript](demo_video/task3_docker_deployment_transcript.txt)
- [Task 4 — browser interface](demo_video/task4_web_interface.mp4) · [transcript](demo_video/task4_web_interface_transcript.txt)

See [`demo_video/README.md`](demo_video/README.md) for video specifications and regeneration instructions.

## Known limitations

- PDF extraction covers selectable text, not scanned images; OCR is not included.
- A grounded prompt and citations do not guarantee a correct answer. The evaluation documents incorrect, incomplete, and source-conflict cases; verify important answers against the cited handbook page.
- The Docker container expects Ollama to be running on a reachable host endpoint. The default macOS/Colima address is `host.docker.internal:11434`; other setups may need `OLLAMA_URL` configured.

## Task 7: GitHub repository and README

The project repository is [`hodatisg520/adl-local-rag-final-project`](https://github.com/hodatisg520/adl-local-rag-final-project). It contains the source code, dependency lists, Docker configuration, handbook and example data, report, screenshots, and video demos. The linked task notes provide implementation details and evidence for reproducing and reviewing the project.
