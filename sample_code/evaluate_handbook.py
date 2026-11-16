#!/usr/bin/env python3
"""Run a repeatable question set against the selected handbook RAG system."""

import argparse
import json

from langchain_ollama import OllamaEmbeddings, OllamaLLM

import run_txt


TEST_CASES = [
    {
        "id": "degree_credits",
        "question": "How many credits are required for the Computer Science major?",
        "expected": "56 credits",
        "topic": "program requirements",
    },
    {
        "id": "declare_major",
        "question": "What must a student complete to formally declare Computer Science as a major?",
        "expected": "At least two Computer Science courses; MATH 202 also counts.",
        "topic": "academic requirements",
    },
    {
        "id": "capstone_eligibility",
        "question": "What are the eligibility criteria for CS 401 Capstone I?",
        "expected": "Minimum major GPA 3.5 and approval of a successful application.",
        "topic": "academic requirements",
    },
    {
        "id": "cs103_catalogue",
        "question": "How often is CS 103 offered, and what are its prerequisites?",
        "expected": "Twice a year; no prerequisites.",
        "topic": "course catalogue",
    },
    {
        "id": "cs201_prerequisite",
        "question": "What is the prerequisite for CS 201 Data Structures and Algorithms?",
        "expected": "CS 101.",
        "topic": "course catalogue",
    },
    {
        "id": "cs311_prerequisite",
        "question": "What is the prerequisite for CS 311 Advanced Deep Learning?",
        "expected": "CS 313 Deep Learning for AI.",
        "topic": "course catalogue",
    },
    {
        "id": "cs311_topics",
        "question": "What topics does the CS 311 course description say it covers?",
        "expected": "Transfer learning, GANs, reinforcement learning, attention/transformers, and GNNs; applications include NLP, robotics, autonomous driving, and time series.",
        "topic": "course description",
    },
    {
        "id": "core_curriculum",
        "question": "What are the four Core courses or course groups required by the handbook?",
        "expected": "Global Humanities; Modern Vietnamese Culture and Society; Design and Systems Thinking; and one QUEST course (chosen from the four listed options).",
        "topic": "curriculum",
    },
    {
        "id": "major_learning_outcome",
        "question": "What is Major Learning Outcome 3?",
        "expected": "Develop real-world applications using Computer Science and other disciplines.",
        "topic": "learning outcomes",
    },
    {
        "id": "teaching_assessment",
        "question": "Which teaching methods and assessment examples are listed for PLO 1?",
        "expected": "Teaching: lecture, lab, worksheet, group discussion. Assessment: programming test, quiz, exam, group presentation, capstone.",
        "topic": "teaching and assessment",
    },
    {
        "id": "cs303_availability",
        "question": "Is CS 303 guaranteed to run every year, and what prerequisite is listed?",
        "expected": "It is listed as 'On holding', not as an annual offering; prerequisite: one 200-level CS course.",
        "topic": "course availability",
    },
    {
        "id": "degree_inconsistency",
        "question": "According to the handbook, what degree is awarded after completing the requirements in Section 4?",
        "expected": "The handbook is inconsistent: the cover identifies B.S. Computer Science, while page 6 says B.S. Applied Mathematics.",
        "topic": "document ambiguity",
    },
    {
        "id": "not_in_handbook",
        "question": "What is the application deadline for admission to the Computer Science major in Fall 2026?",
        "expected": "The handbook does not specify an admission deadline.",
        "topic": "unanswerable question",
    },
]


def main():
    parser = argparse.ArgumentParser(description="Evaluate the CS handbook chatbot")
    parser.add_argument(
        "--handbook", default="major_handbook_pdfs/CS_MajorHandbook.pdf",
        help="One handbook PDF or a folder of documents"
    )
    parser.add_argument(
        "--vector-store", default="data_txt/cs_handbook_vector_store",
        help="Folder where the handbook's Chroma index is stored"
    )
    parser.add_argument(
        "--model", default="qwen2.5:1.5b",
        help="Ollama language model to evaluate"
    )
    parser.add_argument(
        "--rebuild-index", action="store_true",
        help="Rebuild the Chroma index from the handbook"
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Run only the first N test cases (0 means all)"
    )
    args = parser.parse_args()

    embeddings = OllamaEmbeddings(
        model=run_txt.EMBED_MODEL,
        base_url=run_txt.OLLAMA_URL
    )
    db = run_txt.load_and_index(
        embeddings,
        data_dir=args.handbook,
        vector_store=args.vector_store,
        rebuild_index=args.rebuild_index
    )
    llm = OllamaLLM(
        model=args.model,
        base_url=run_txt.OLLAMA_URL,
        temperature=0.0
    )

    cases = TEST_CASES[:args.limit] if args.limit > 0 else TEST_CASES
    for case in cases:
        result = run_txt.ask(case["question"], db, llm)
        print(json.dumps({
            **case,
            "model": args.model,
            "answer": result["answer"],
            "used_fallback": result["used_fallback"],
            "sources": [
                {
                    "source": source["source"],
                    "page": source.get("page"),
                    "score": source["score"],
                }
                for source in result["sources"][:3]
            ],
        }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
