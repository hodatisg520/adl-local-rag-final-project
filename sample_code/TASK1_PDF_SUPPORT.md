# Task 1: PDF file support

The RAG sample now reads `.txt` and `.pdf` files from one folder. PDF text is extracted page by page, split with the existing chunk size and overlap settings, embedded by the configured Ollama embedding model, and stored in Chroma. Each PDF chunk keeps its source filename and page number so retrieved evidence can be traced back to the PDF.

## Run it

Follow the virtual-environment setup in the repository README. Start Ollama in Terminal 1 (or open its desktop app), then leave it running:

```bash
ollama serve
```

In Terminal 2, with the virtual environment activated, download the models:

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
```

Keep Ollama running while you run the chatbot. Run the command below from the `sample_code` folder.

To index PDFs in the project folder and ask a question covered by the supplied assignment PDFs:

```bash
python run_txt.py \
  --data-dir .. \
  --vector-store data_txt/task1_pdf_demo_store \
  --rebuild-index \
  --question "How many main tasks does this final project have?"
```

The expected answer is **seven main tasks**. Verified locally against the two supplied assignment PDFs: the command indexed 41 chunks and returned “The project comprises seven (07) main tasks.” Retrieved sources included `Final-project-ADL-pptx.pdf` page 6 and `Final-project-ADL.pdf` pages 12 and 7.

For your own documents, put `.pdf` and `.txt` files together in `data_txt`, or pass another folder with `--data-dir /path/to/documents`. On the first run, the program extracts and indexes supported files automatically. If you add, remove, or change files later, run with `--rebuild-index` so the Chroma index reflects the current folder.

## Scope and limitation

Text extraction works for selectable text in PDFs. Scanned pages and text inside images require OCR; this implementation reports when it finds no selectable text and does not perform OCR. The assignment brief identifies OCR as an optional processing step for those PDFs.

The Task 1 demo uses the assignment PDFs in the project folder only as sample inputs; it does not select a major handbook for Task 2.
