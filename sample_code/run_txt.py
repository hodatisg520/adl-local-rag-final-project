#!/usr/bin/env python3

"""
Sample local RAG system for TXT and PDF documents.

Usage: python run_txt.py
       python run_txt.py --question "Your question here"
       python run_txt.py --data-dir ../sample_documents --rebuild-index
"""

# IMPORT LIBRARIES
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from pypdf import PdfReader

# RAG SETTINGS
DATA_DIR = "data_txt" # Folder that contains .txt and .pdf files.
# Keep the original text-only index intact; this index supports both file types.
VECTOR_STORE = DATA_DIR + "/vector_store_pdf"
COLLECTION = "rag_documents" # Name of the Chroma collection.
CHUNK_SIZE = 1000 # Maximum characters per text chunk.
CHUNK_OVERLAP = 200 # Number of characters shared between nearby chunks.
EMBED_MODEL = "nomic-embed-text" # Ollama embedding model used to convert text to vectors (Remember to pull the embedding model by running the command: ollama pull nomic-embed-text)
LLM_MODEL = "qwen2.5:0.5b" # Ollama model name for generating answers (Remember to pull the LLM model by running the command: ollama pull qwen2.5:0.5b).
TEMPERATURE = 0.7 # Controls how random or creative the model response is (the higher, the more creative; 0.0: deterministic).
OLLAMA_URL = "http://127.0.0.1:11434" # URL of local (127.0.0.1) Ollama server. Its default port is 11434
TOP_K = 5 # Number of top-matched chunks to retrieve.
SCORE_THRESHOLD = 0.3 # Minimum average relevance score before trusting retrieved context.
SAMPLE_QUESTION = "How many students are there at Fulbright?" # Default question if user does not pass --question.

# FINAL PROMPT SENT TO THE MODEL: Replacing {context} and {question} with the actual values.
# Without this instruction, the model might rely entirely on its pretrained knowledge.
# {context} is a variable that will be replaced by retrieved chunks from the vector database.
# 1. If the retrieved documents contain the answer, use them.
# 2. If the vector database does not contain the answer, use the model’s own knowledge.
# 3. Keep answers short.
# 4. This is a useful RAG trick. It helps distinguish: Answer from retrieved documents vs. Answer from model knowledge. Note: some small models might not understand this trick.
# Answer from retrieved documents
PROMPT_TEMPLATE = """You are a helpful AI assistant that answers questions based on provided documents.

CONTEXT FROM DOCUMENTS:
{context}
---
QUESTION: {question}

INSTRUCTIONS:
1. If the context contains relevant information, answer based on that.
2. If the context is insufficient, use your general knowledge.
3. Be concise - 2-4 sentences unless more detail is needed.

ANSWER:"""

# FIND SUPPORTED DOCUMENTS IN A FOLDER
def find_document_files(directory: str):
    folder = Path(directory)
    if not folder.is_dir():
        raise FileNotFoundError("Document folder not found: " + str(folder))

    # Search only the top level so files inside the vector store are ignored.
    return sorted(
        (
            path for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in {".txt", ".pdf"}
        ),
        key=lambda path: path.name.lower()
    )

# LOAD TXT FILES AND EXTRACT SELECTABLE TEXT FROM PDF PAGES
def load_documents(directory: str):
    documents = []

    for file_path in find_document_files(directory):
        print("  Loading: " + file_path.name)

        if file_path.suffix.lower() == ".txt":
            content = file_path.read_text(encoding="utf-8")
            if content.strip():
                documents.append(Document(
                    page_content=content,
                    metadata={"source": file_path.name, "file_type": "txt"}
                ))
            continue

        try:
            pdf = PdfReader(str(file_path))
            if pdf.is_encrypted and pdf.decrypt("") == 0:
                raise ValueError("the PDF is encrypted and requires a password")

            pages_with_text = 0
            for page_number, page in enumerate(pdf.pages, start=1):
                content = page.extract_text() or ""
                if not content.strip():
                    continue
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "source": file_path.name,
                        "file_type": "pdf",
                        "page": page_number
                    }
                ))
                pages_with_text += 1

            if pages_with_text == 0:
                print(
                    "  Warning: no selectable text found in " + file_path.name
                    + "; scanned/image-only PDFs need OCR."
                )
        except Exception as error:
            raise ValueError(
                "Could not read PDF '" + file_path.name + "': " + str(error)
            ) from error

    return documents

# LOAD AN EXISTING VECTOR STORE OR CREATE IT FROM TXT/PDF SOURCES
def load_and_index(
    embeddings,
    data_dir: str = DATA_DIR,
    vector_store: str = VECTOR_STORE,
    rebuild_index: bool = False
) -> Chroma:
    document_files = find_document_files(data_dir)
    if not document_files:
        raise FileNotFoundError(
            "No .txt or .pdf documents found in '" + str(data_dir) + "'."
        )

    vector_store_path = Path(vector_store)
    if vector_store_path.exists() and not rebuild_index:
        print("Loading existing vector store...")
        return Chroma(
            collection_name=COLLECTION,
            embedding_function=embeddings,
            persist_directory=str(vector_store_path)
        )

    if vector_store_path.exists():
        print("Rebuilding vector store from current TXT/PDF files...")
        shutil.rmtree(vector_store_path)

    print("No vector store found. Indexing documents...")
    documents = load_documents(data_dir)
    if not documents:
        raise ValueError(
            "No readable text was extracted from the documents in '"
            + str(data_dir) + "'. For scanned PDFs, add OCR before indexing."
        )

    chunks = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    ).split_documents(documents)
    print("  Indexing " + str(len(chunks)) + " chunks...")

    vector_store_path.parent.mkdir(parents=True, exist_ok=True)
    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION,
        persist_directory=str(vector_store_path)
    )

# FUNCTION TO RETRIEVE RELEVANT CHUNKS AND GENERATE AN ANSWER
def ask(question: str, db: Chroma, llm: OllamaLLM) -> Dict[str, Any]:
    # Retrieve top-K similar chunks with distance scores.
    raw_results = db.similarity_search_with_score(question, k=TOP_K)
    # Convert raw retrieval output into easier dictionaries.
    sources = [
        {
            # Source file name from metadata.
            'source': str(doc.metadata.get('source', 'Unknown')),
            # PDF page number, when this result came from a PDF.
            'page': doc.metadata.get('page'),
            # Convert distance to similarity score.
            'score': round(1 / (1 + score), 4),
            # Text content of retrieved chunk.
            'content': doc.page_content
        }
        # Build one source dict per retrieved result.
        for doc, score in raw_results
    ]
    # Compute average relevance score (0 if no sources).
    avg_score = sum(float(s['score']) for s in sources) / len(sources) if sources else 0
    # Use fallback if no sources or relevance is too low.
    used_fallback = not sources or avg_score < SCORE_THRESHOLD
    # Fallback branch: retrieval is not good enough.
    if used_fallback:
        # Tell model to use general knowledge.
        context = "No sufficiently relevant documents found. Use your general knowledge."
    # Retrieval branch: build context from matched chunks.
    else:
        # Join chunks with separators for readability.
        context = "\n\n---\n\n".join(
            # Include source and PDF page so the model can use traceable context.
            "[" + str(s['source'])
            + (", page " + str(s['page']) if s.get('page') is not None else "")
            + "]\n" + str(s['content']) for s in sources
        )
    # Fill prompt template placeholders with actual values.
    prompt = PROMPT_TEMPLATE.replace("{context}", context).replace("{question}", question)
    # Ask model and trim whitespace from response.
    answer = llm.invoke(prompt).strip()
    # Return answer, evidence sources, and fallback status.
    return {'answer': answer, 'sources': sources, 'used_fallback': used_fallback}

# MAIN FUNCTION
def main():
    parser = argparse.ArgumentParser(
        description="Local RAG Q&A for TXT and PDF documents"
    )
    parser.add_argument('--question', '-q', default=SAMPLE_QUESTION, help='Question to ask')
    parser.add_argument(
        '--data-dir', default=DATA_DIR,
        help='Folder containing .txt and .pdf documents (default: data_txt)'
    )
    parser.add_argument(
        '--vector-store', default=VECTOR_STORE,
        help='Folder for the Chroma index (default: data_txt/vector_store_pdf)'
    )
    parser.add_argument(
        '--rebuild-index', action='store_true',
        help='Recreate the index to include newly added or changed documents'
    )
    args = parser.parse_args()

    # Load embeddings and LLM
    print("Loading Ollama embeddings: " + EMBED_MODEL)
    # Initialize Ollama embedding model.
    embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_URL)
    # Load the existing index or build one from the selected source folder.
    try:
        db = load_and_index(
            embeddings,
            data_dir=args.data_dir,
            vector_store=args.vector_store,
            rebuild_index=args.rebuild_index
        )
    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))
    # Show which LLM is being used.
    print("Connecting to Ollama (" + LLM_MODEL + ")...")
    # Initialize Ollama LLM client.
    llm = OllamaLLM(model=LLM_MODEL, base_url=OLLAMA_URL, temperature=TEMPERATURE)

    # Print user question.
    print("Q: " + args.question)
    # Get answer from RAG pipeline.
    result = ask(args.question, db, llm)
    # Print answer text.
    print("\nA: " + result['answer'] + "\n")
    # If fallback happened, show note.
    if result['used_fallback']:
        # Fallback note for transparency.
        print("(answered from model knowledge — no relevant documents found)")
    # If retrieval was relevant, show top sources.
    else:
        # # Show first 3 sources
        print("Sources:")
        for s in result['sources'][:3]:
            # Print source file, PDF page (when available), and similarity score.
            page_label = ""
            if s.get('page') is not None:
                page_label = "  page=" + str(s['page'])
            print(
                "   " + str(s['source']) + page_label
                + "  score=" + str(s['score'])
            )

# RUN PROGRAM IF THIS FILE IS EXECUTED DIRECTLY.
if __name__ == "__main__":
    main()
