# Final Project Report
## A Local Retrieval-Augmented Generation System for Computer Science Handbook Q&A

**Course:** CS311 Advanced Deep Learning, Fall 2026
**Deliverable:** Task 5 report
**Repository:** https://github.com/hodatisg520/adl-local-rag-final-project
**Prepared:** November 2026

[[PAGEBREAK]]

## Abstract

This project develops a local Retrieval-Augmented Generation (RAG) system for questions about Computer Science program requirements. The system reads text files and selectable-text PDFs, divides their content into overlapping chunks, embeds the chunks with Ollama's `nomic-embed-text` model, and stores them in Chroma. For a question, it retrieves the five most similar chunks and asks a local `qwen2.5:1.5b` model to answer using the retrieved handbook context. Source filenames and PDF page numbers are carried through to the answer display. A command-line interface supports document-level experiments, while a Streamlit interface makes the selected CS handbook available in a browser. Docker Compose packages both interfaces and persists the vector index while Ollama remains on the host machine.

The evaluation compared two small local language models on 13 manually reviewed questions. The `qwen2.5:1.5b` model produced eight fully correct answers, compared with four for `qwen2.5:0.5b`. This improvement did not eliminate retrieval errors, incomplete answers, hallucinations, or a contradiction in the source handbook. The project therefore treats citations and conservative prompts as safeguards that help users inspect answers, not as proof that every answer is correct. The report describes the design, implementation, observed behavior, deployment, limitations, and practical next steps.

## 1. Project objective and scope

The project brief asks for a complete RAG workflow that supports PDF input, answers questions about a selected major handbook, can run in Docker, and provides a browser interface. Task 5 asks for a report of at least 1,500 words about the design, implementation, evaluation, observations, limitations, and future improvements. This report covers the work for Tasks 1 through 4 and interprets their results as evidence about one specific local system, rather than claiming that the system generalizes to every handbook or question type.

The selected knowledge base is the 19-page *Undergraduate Major Handbook: B.S. Computer Science*, Version 1.0, May 2025. The chatbot is intended to help a student locate program and course information in that handbook. It is not an official advising system and does not resolve disagreements inside the document. Local inference was chosen to keep the language model and embedding requests on the user's machine and to avoid making a hosted model API a prerequisite for the demo.

## 2. System design

### 2.1 Document ingestion and indexing

The ingestion layer accepts `.txt` and `.pdf` files. Text files are read as UTF-8. PDFs are opened with `pypdf`, and each page with selectable text becomes a separate LangChain document. The document metadata records its source filename, file type, and, for PDFs, the one-based page number. Keeping each page separate makes it possible to show a page citation after a chunk is retrieved. Encrypted or unreadable PDFs produce an error; a PDF with no selectable text produces a warning because scanned images require OCR, which is outside the implemented scope.

`RecursiveCharacterTextSplitter` creates chunks of up to 1,000 characters with 200 characters of overlap. Overlap reduces the chance that a fact split at a boundary loses useful neighboring context. The fixed character-based setting is simple and repeatable, but it does not understand section headings, course records, or table structure. The resulting chunks are embedded with Ollama's `nomic-embed-text` model and stored in a persistent Chroma collection. The index can be reused on later runs or explicitly rebuilt when source documents change.

### 2.2 Retrieval and answer generation

For each question, the system performs vector similarity search and retrieves the top five chunks. The code converts Chroma's distance into a distance-derived similarity value using `1 / (1 + distance)`, then averages the retrieved values. If there are no results or the average is below 0.30, the system sends a fallback context that tells the model that sufficiently relevant passages were not found. These values are a practical heuristic, not a calibrated probability that an answer is correct.

The answer prompt tells the model to use only the supplied handbook context, avoid filling gaps with general knowledge, preserve qualifications, and say when the handbook does not contain the answer. Retrieved source names and page numbers are included in the prompt. Answer generation uses `qwen2.5:1.5b` at temperature 0.0. The interactive command-line program and browser interface both call the same retrieval and answer function, which keeps the evidence and prompt behavior consistent across the two user interfaces.

[[ARCHITECTURE_DIAGRAM]]

**Figure 1.** Document indexing and question-answer flow. The lower path queries the persistent index built by the upper path.

### 2.3 User interfaces and deployment

The command-line interface supports a single question or an interactive session. It prints the generated answer and the top three retrieved sources with page numbers and distance-derived scores. This interface was useful for repeatable development and evaluation because it exposed the evidence associated with each answer.

The Streamlit interface reuses the Task 2 backend. It stores questions and answers in browser-session state, offers a control to clear the current conversation, and puts retrieved references in an expandable source panel. The panel shows the PDF name, page, and score for up to three results. Streamlit caches the loaded embedding, vector store, and language-model objects so the app does not need to rebuild them on each interaction.

The Docker image uses a digest-pinned Python 3.12 slim base and a locked dependency file. Compose defines both the interactive CLI service and the web service. The selected handbook is mounted read-only, and a named volume keeps the Chroma index outside the disposable container. Ollama runs on the host Mac and the container connects to it through `host.docker.internal`; this design uses the host's local Ollama installation instead of trying to provide Apple GPU access from inside a Linux container. The web port is bound to the host loopback interface.

## 3. Implementation across Tasks 1-4

Task 1 extended the starter program from text-only input to selectable-text PDF support. A documented demonstration indexed 41 chunks from the supplied assignment PDFs and answered a question about the number of project tasks with the expected answer of seven. Retrieved results included filenames and page references. This demonstration verifies the ingestion path for those documents; it does not establish accuracy for arbitrary PDFs or scanned documents.

Task 2 selected the CS major handbook as a standalone knowledge source. The recorded Docker indexing run extracted its content into 57 chunks. A repeatable evaluation script contains 13 questions spanning credit requirements, declaring the major, prerequisites, course descriptions, learning outcomes, teaching and assessment, course availability, conflicting source statements, and a question not answered by the handbook. The 1.5B model became the default after the model comparison.

Task 3 packaged the existing RAG program in Docker. A fresh named volume was used to verify that the container could extract and index the handbook; a later run reused the saved index and answered the CS 311 prerequisite question with a page 18 citation. Docker Compose configuration and image building were verified on Apple Silicon using Colima. Keeping Ollama on the host also keeps the inference model outside the image and avoids downloading model weights during every container build.

Task 4 added a browser-based interface and a separate Compose service for it. The service uses the same image, handbook mount, vector volume, and Ollama endpoint as the CLI. Browser verification covered two questions: the prerequisite for CS 311 Advanced Deep Learning, answered as CS 313 with a page 18 source; and the conditions to declare the CS major, answered as two Computer Science courses with MATH 202 also counted. The second answer displayed three retrieved references from pages 7, 7, and 4. The two turns remained visible in the conversation, and the clear-history control was available.

## 4. Evaluation methodology and results

The project compared `qwen2.5:0.5b` with `qwen2.5:1.5b`. Both models used the same handbook index, retrieval settings, questions, and temperature of 0.0. The 13 answers from each model were manually checked against the expected handbook evidence. Results were assigned to four categories: correct, incomplete, incorrect, or ambiguous because the source document conflicts with itself. This is a small qualitative evaluation, not a broad benchmark or a statistical estimate of real-world accuracy.

| Model | Fully correct | Incomplete | Incorrect | Source conflict |
|---|---:|---:|---:|---:|
| qwen2.5:0.5b | 4/13 (30.8%) | 1/13 | 7/13 | 1/13 |
| qwen2.5:1.5b | 8/13 (61.5%) | 1/13 | 3/13 | 1/13 |

On this question set, the larger model improved five outcomes: the total-credit question, the multi-part CS 103 question, Major Learning Outcome 3, teaching and assessment examples for PLO 1, and the question about an unspecified deadline. It did not fix every failure. Both models gave the wrong CS 311 course topics and confused Core courses with foundational CS courses. Both also failed to report the contradiction between the handbook cover, which says B.S. Computer Science, and a page 6 passage that says B.S. Applied Mathematics.

The CS 311 topics error is primarily a retrieval problem. The top results ranked chunks from pages 16 and 14 above the course description on page 18, so the language model received evidence about other courses. The Core curriculum error has the same broad pattern: search returned the foundational-course section on page 8 instead of the Core-course list on page 6. Increasing the language-model size alone cannot reliably repair missing or wrongly ranked evidence.

Other errors arose after relevant evidence was retrieved. For total major credits, page 7 evidence appeared in the retrieved chunks, but neither model stated the required total of 56 credits. The smaller model answered an adjacent declaration rule; the larger model listed component values without giving the requested total. For CS 303, both models overstated the availability entry “On holding” as a guaranteed yearly offering. The 1.5B model supplied the prerequisite but still misread the qualification. These examples show why answer quality depends on retrieval, reading of qualifications, and direct response to the exact question.

The unanswerable deadline question illustrates the role and limit of the grounded prompt. The smaller model invented October 1, 2026, while the 1.5B model said the handbook did not specify a deadline. The larger model followed the instruction to abstain in this example, but one success does not establish reliable abstention in general. Likewise, the source conflict is an information-quality problem that the chatbot cannot resolve without an authoritative clarification from the handbook owner.

## 5. Observations and lessons learned

First, a correct answer requires both useful evidence and careful generation. A fluent answer can be wrong when the top five chunks omit the relevant section, and a retrieved chunk can still be summarized incompletely. Evaluation should therefore inspect both the answer and its retrieved pages. The source panel makes that review possible, but it does not automatically detect that a citation is irrelevant or contradictory.

Second, model size affected this particular 13-question set, but it was not a substitute for improving retrieval. The 1.5B model more often handled multi-part questions and abstained on the deadline question, while both models failed on the same two retrieval-sensitive questions. Choosing a default from a measured local comparison was more defensible than assuming the larger model would always be better.

Third, narrow source scope improves traceability. Indexing only the selected handbook avoids mixing policies from other majors. Page metadata is useful in both interfaces because a student can open the original page and verify program rules. This is especially important where the source is ambiguous or where a course's availability has a qualification.

Finally, local deployment creates operational tradeoffs. It avoids hosted model APIs and permits the Mac host to run Ollama, but the user must install Ollama, download the embedding and answer models, and keep the service available while the container is running. Docker simplifies packaging and preserves the index, but it does not remove the need to manage the host model service.

## 6. Limitations and future improvements

The first limitation is document coverage. The PDF loader depends on selectable text and does not perform OCR. Page-level extraction may also represent a table as linear text, which can weaken associations among course names, availability, and prerequisites. The current folder scan is limited to files directly in the selected directory, and the evaluation uses only one handbook.

The second limitation is retrieval design. A fixed 1,000-character chunk size can split a course record or place a question's key term in a neighboring chunk. Dense vector search may favor semantically similar but structurally incorrect sections. The average distance-derived score and 0.30 threshold have not been calibrated on a labeled relevance set. A displayed score should not be interpreted as answer confidence.

The third limitation is evaluation scope. Thirteen questions are too few to characterize all handbook topics, paraphrases, multi-hop queries, or document revisions. Outcomes were manually classified, and the project did not run a blinded multi-reviewer process or compute retrieval metrics such as recall at five or mean reciprocal rank. The current results are useful for identifying failure examples, but they should not be generalized as benchmark performance.

Several improvements follow directly. A larger evaluation set should include paraphrases, table lookups, questions requiring facts from multiple pages, unanswerable questions, and explicit contradiction checks. Retrieval should be assessed separately from answer generation using page-level relevance labels. Hybrid lexical and vector search could better preserve exact course codes, while a reranker could reorder the candidate chunks. Chunking by handbook headings and course-record boundaries, plus table-aware extraction, could keep related fields together. These changes should be compared against the current fixed-chunk baseline rather than adopted without measurement.

The answer layer could also be strengthened by requiring an answer checklist: identify the requested fact, verify that a retrieved passage supports it, preserve any qualifier, and abstain when support is missing. A contradiction-aware response could report both conflicting passages instead of selecting one. If resources permit, a larger local model could be evaluated for answer completeness and latency, but retrieval improvements should be tested independently so their effect is visible. OCR can be added as an explicit preprocessing path for scanned PDFs. Finally, user-interface work could label the source score as a retrieval similarity heuristic and make the source preview easier to inspect.

## 7. Conclusion

The project delivers a functioning local RAG pipeline from document ingestion through retrieval, generation, browser interaction, and Docker deployment. Its strongest practical features are local model execution, reusable indexing, PDF page traceability, and a repeatable question set that exposed concrete failure modes. The 1.5B model outperformed the 0.5B model on the small manual evaluation, but the tests also show that retrieval and source interpretation remain important sources of error. The next development priority should be a better measured retrieval pipeline and a broader evaluation set, while retaining page citations and clear abstention behavior for student review.

[[PAGEBREAK]]

## Project evidence and reproducibility references

1. `sample_code/run_txt.py` - ingestion, chunking, retrieval, prompt, and CLI implementation.
2. `sample_code/TASK1_PDF_SUPPORT.md` - PDF support demonstration and scope.
3. `sample_code/evaluate_handbook.py` and `sample_code/TASK2_EVALUATION.md` - repeatable questions and manually reviewed model comparison.
4. `docker/Dockerfile`, `docker-compose.yml`, and `docker/README.md` - image, deployment, and local verification notes.
5. `sample_code/streamlit_app.py` and `sample_code/TASK4_UI.md` - browser interface, run instructions, and UI verification.
6. `sample_code/major_handbook_pdfs/CS_MajorHandbook.pdf` - selected source handbook.

The Task 2 evaluation can be repeated from `sample_code/` with Ollama running and the required models downloaded by invoking `python evaluate_handbook.py --handbook major_handbook_pdfs/CS_MajorHandbook.pdf --vector-store data_txt/cs_handbook_vector_store --model qwen2.5:1.5b --rebuild-index`. Use `--model qwen2.5:0.5b` for the smaller-model comparison. The Task 4 browser interface is started from the repository root with `docker-compose up --build web` after starting Ollama for container access; it is then available at `http://localhost:8501`.
