# Task 2: CS Major Handbook Chatbot Evaluation

## Selected handbook and system

The selected knowledge source is `major_handbook_pdfs/CS_MajorHandbook.pdf`, the 19-page *Undergraduate Major Handbook: B.S. Computer Science*, Version 1.0 (May 2025). It covers program objectives and learning outcomes, degree and major requirements, course offerings and prerequisites, teaching and assessment, and the course catalogue. The existing PDF is indexed on its own, so results are not mixed with other majors' handbooks.

The chatbot uses `nomic-embed-text` for embeddings, Chroma for persistent vector storage, a 1,000-character chunk size with 200-character overlap, and the top 5 retrieved chunks per question. Its answer prompt instructs the language model to use only retrieved handbook context, preserve qualifications, and say when the answer is not present. Responses show the source PDF, page, and similarity score. The app supports an interactive command-line chat through `--interactive`.

The model comparison used `qwen2.5:0.5b` and `qwen2.5:1.5b` at temperature 0.0 with the same index, questions, and retrieval settings. Each of the 13 responses was manually checked against the handbook. The 1.5B model is the application's default because it performed better in this comparison.

## Test results

| Test question | Expected evidence | qwen2.5:0.5b | qwen2.5:1.5b | Handbook page(s) |
|---|---|---|---|---|
| How many credits are required for the CS major? | 56 credits | **Incorrect:** answered with the major declaration rule instead of total credits. | **Incomplete:** listed several 8- and 16-credit components but did not give the 56-credit total. | 7 |
| What must a student complete to declare the CS major? | Two CS courses; MATH 202 also counts. | **Correct.** | **Correct.** | 7 |
| What is required to enroll in CS 401 Capstone I? | Major GPA of at least 3.5 and approval of a successful application. | **Correct.** | **Correct.** | 9 |
| How often is CS 103 offered, and what are its prerequisites? | Twice a year; none. | **Incomplete:** gave the frequency only. | **Correct.** | 13-14 |
| What is the prerequisite for CS 201? | CS 101. | **Correct.** | **Correct.** | 7, 14 |
| What is the prerequisite for CS 311 Advanced Deep Learning? | CS 313. | **Correct.** | **Correct.** | 18 |
| What topics does the CS 311 course description cover? | Advanced deep learning topics including transfer learning, GANs, RL, attention/transformers, and GNNs. | **Incorrect:** returned a software engineering description. | **Incorrect:** returned programming-language topics. | 18 |
| What are the four Core courses or course groups? | Global Humanities; Modern Vietnamese Culture and Society; Design and Systems Thinking; and one QUEST course group. | **Incorrect:** substituted foundational CS courses. | **Incorrect:** also substituted foundational CS courses. | 6 |
| What is Major Learning Outcome 3? | Develop real-world applications using CS and other disciplines. | **Incorrect:** gave a Core Learning Outcome instead. | **Correct.** | 5 |
| Which teaching methods and assessment examples are listed for PLO 1? | Lecture, lab, worksheet, group discussion; programming test, quiz, exam, group presentation, capstone. | **Incorrect:** described learning outcomes rather than the methods and assessments. | **Correct.** | 12 |
| Is CS 303 guaranteed every year, and what prerequisite is listed? | Availability is stated as “On holding”; prerequisite is one 200-level CS course. | **Incorrect:** said it is guaranteed annually and omitted the prerequisite. | **Incorrect in part:** supplied the prerequisite but said it is guaranteed annually. | 13, 17 |
| What degree is awarded after Section 4 requirements? | The handbook conflicts: cover says B.S. Computer Science; page 6 says B.S. Applied Mathematics. | **Ambiguous/source conflict:** gave only Applied Mathematics. | **Ambiguous/source conflict:** gave only Applied Mathematics. | 1, 6 |
| What is the Fall 2026 application deadline for the CS major? | No deadline is stated in this handbook. | **Incorrect:** invented October 1, 2026. | **Correct:** said the handbook does not specify a deadline. | Not specified |

### Summary by model

| Model | Correct | Incomplete | Incorrect | Ambiguous because the source conflicts |
|---|---:|---:|---:|---:|
| qwen2.5:0.5b | 4/13 | 1/13 | 7/13 | 1/13 |
| qwen2.5:1.5b | 8/13 | 1/13 | 3/13 | 1/13 |

The larger model improved the total-credit response, the CS 103 multi-part response, MLO 3, PLO 1 teaching/assessment, and the question with no answer in the handbook. It still failed on retrieving the CS 311 topic description and Core curriculum section, and it misread the CS 303 availability status.

## Examples and failure analysis

### Correct answers

- Asked about CS 401 Capstone I, both models returned the minimum major GPA of 3.5 and the successful-application approval condition from page 9.
- Asked about declaring the CS major, both models correctly returned the two-course requirement and noted that MATH 202 counts, from page 7.
- The 1.5B model correctly answered the CS 103 offering frequency and lack of prerequisites, and the teaching/assessment examples for PLO 1.
- For the Fall 2026 deadline question, qwen2.5:1.5b said the handbook did not specify a deadline; qwen2.5:0.5b hallucinated a date.

### Incorrect and incomplete answers

- **CS 311 topics:** The embedding search ranked chunks from pages 16 and 14 above the CS 311 description on page 18. The language model then answered from the wrong retrieved course description. This is primarily a retrieval failure, compounded by the small model's weak ability to notice the mismatch.
- **Core curriculum:** Search returned the “Foundational Courses” section on page 8 rather than the Core-course list on page 6. Both models treated those foundational CS courses as the four Core courses.
- **Major credits:** The relevant page 7 chunks were retrieved, but neither model stated the total of 56 credits. The 0.5B model answered an adjacent declaration rule; the 1.5B model listed components without directly answering the total.
- **CS 303 availability:** The course catalogue says “On holding.” Both models interpreted this as a guaranteed annual offering. The 1.5B model did retrieve and correctly report the prerequisite, but it still overstated the availability information.
- **Unanswerable deadline:** The smaller model made up a specific date despite the grounded-answer prompt. The 1.5B model abstained correctly. This shows that the prompt reduces but does not eliminate hallucination.

### Ambiguous source content

The handbook cover identifies the degree as *B.S. Computer Science* (page 1), but the degree-requirements paragraph on page 6 says *Bachelor of Science in Applied Mathematics*. Both models returned only the latter statement and did not flag the contradiction. This is a source-document inconsistency, not a fact that the chatbot can resolve from this handbook alone.

## Limitations and next improvements

This evaluation uses 13 manually checked questions and one 19-page handbook. It is a qualitative baseline, not a claim of a general accuracy rate. Table extraction and similar section names can confuse semantic retrieval; a future version could add hybrid keyword/vector retrieval or course-code-aware reranking. Questions that combine multiple facts are more error-prone, and model size alone does not solve retrieval mistakes. Users should check the displayed source page for important program decisions.

## Reproduce the evaluation

From the `sample_code` folder, with Ollama running and the `nomic-embed-text`, `qwen2.5:0.5b`, and `qwen2.5:1.5b` models available:

```bash
python evaluate_handbook.py \
  --handbook major_handbook_pdfs/CS_MajorHandbook.pdf \
  --vector-store data_txt/cs_handbook_vector_store \
  --model qwen2.5:1.5b \
  --rebuild-index
```

Use `--model qwen2.5:0.5b` to repeat the smaller-model comparison. The test script prints one JSON record per question, including the expected fact, answer, fallback status, and retrieved pages.
