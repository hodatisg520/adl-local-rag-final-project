#!/usr/bin/env python3
"""Build the Canvas folder and, once user-recorded videos exist, its ZIP."""

from __future__ import annotations

import argparse
import re
import shutil
import zipfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
VIDEO_NAMES = (
    "task1_pdf_support.mp4",
    "task2_handbook_chatbot.mp4",
    "task3_docker_deployment.mp4",
    "task4_web_interface.mp4",
)
APP_FILES = (
    "run_txt.py",
    "streamlit_app.py",
    "evaluate_handbook.py",
    "requirements.txt",
    "requirements-docker.txt",
    "TASK1_PDF_SUPPORT.md",
    "TASK2_EVALUATION.md",
    "TASK4_UI.md",
)
REPORT_FILES = (
    "final_project_report.pdf",
    "final_project_report.md",
    "build_report.py",
    "requirements.txt",
)


def copy_required(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Required project file is missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def check_videos(video_dir: Path) -> None:
    for name in VIDEO_NAMES:
        video = video_dir / name
        if not video.is_file() or video.stat().st_size == 0:
            raise FileNotFoundError(f"Missing or empty video: {video}")


def prepare_source(package: Path) -> None:
    source_root = package / "source_code"
    app_root = source_root / "sample_code"

    for name in APP_FILES:
        copy_required(REPO / "sample_code" / name, app_root / name)

    for path in sorted((REPO / "sample_code" / "data_txt").glob("*.txt")):
        copy_required(path, app_root / "data_txt" / path.name)
    for path in sorted((REPO / "sample_code" / "major_handbook_pdfs").glob("*.pdf")):
        copy_required(path, app_root / "major_handbook_pdfs" / path.name)

    for name in ("Final-project-ADL.pdf", "Final-project-ADL-pptx.pdf"):
        copy_required(REPO / name, source_root / name)
    for suffix in ("*.png", "*.jpg"):
        for path in sorted((REPO / "screenshots").glob(suffix)):
            copy_required(path, source_root / "screenshots" / path.name)

    # Task 4's relative Docker link changes when the code moves under source_code/.
    task4 = app_root / "TASK4_UI.md"
    task4.write_text(
        task4.read_text(encoding="utf-8").replace(
            "(../docker/README.md)", "(../../docker/README.md)"
        ),
        encoding="utf-8",
    )


def prepare_docker(package: Path) -> None:
    docker_root = package / "docker"
    docker_root.mkdir(parents=True, exist_ok=True)

    dockerfile = (REPO / "docker" / "Dockerfile").read_text(encoding="utf-8")
    docker_root.joinpath("Dockerfile").write_text(
        dockerfile.replace("COPY sample_code/", "COPY source_code/sample_code/"),
        encoding="utf-8",
    )

    compose = (REPO / "docker-compose.yml").read_text(encoding="utf-8")
    (package / "docker-compose.yml").write_text(
        compose.replace("./sample_code/", "./source_code/sample_code/"),
        encoding="utf-8",
    )
    docker_root.joinpath("docker-compose.yml").write_text(
        compose.replace("context: .", "context: ..").replace(
            "./sample_code/", "../source_code/sample_code/"
        ),
        encoding="utf-8",
    )
    copy_required(REPO / ".env.example", docker_root / ".env.example")

    (package / ".dockerignore").write_text(
        "\n".join(
            (
                ".git",
                ".venv/",
                "**/.DS_Store",
                "**/__pycache__/",
                "**/*.py[cod]",
                "**/vector_store*/",
                "**/*_vector_store/",
                "source_code/sample_code/data_txt/",
                "source_code/sample_code/major_handbook_pdfs/",
                "source_code/Final-project-ADL*.pdf",
                "source_code/screenshots/",
                "report/",
                "demo_video/",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    docker_root.joinpath("README.md").write_text(
        """# Docker deployment

From the submission folder root, start Ollama on the Mac host in a separate
terminal with `OLLAMA_HOST=0.0.0.0:11434 ollama serve`, then run:

```bash
docker-compose build
docker-compose run --rm chatbot
```

For the Streamlit interface, run `docker-compose up --build web` and open
http://localhost:8501. The selected CS handbook is mounted read-only from
`source_code/sample_code/major_handbook_pdfs/CS_MajorHandbook.pdf`, and the
Chroma index persists in the `rag_index` Docker volume. If Ollama runs at
another address, set `OLLAMA_URL` in your shell; `docker/.env.example` shows
the default. The equivalent Compose file inside this folder can be used with
`docker-compose -f docker/docker-compose.yml` from the submission root.
""",
        encoding="utf-8",
    )


def prepare_report(package: Path) -> None:
    for name in REPORT_FILES:
        copy_required(REPO / "report" / name, package / "report" / name)


def prepare_videos(package: Path, videos_dir: Path | None) -> None:
    target = package / "demo_video"
    target.mkdir(parents=True, exist_ok=True)
    if videos_dir is not None:
        for name in VIDEO_NAMES:
            copy_required(videos_dir / name, target / name)
    message = (
        "These four Task 1–4 videos were supplied when the ZIP was built.\n"
        if videos_dir is not None
        else "Add your own Task 1–4 screen-recorded demos here, then rebuild the ZIP.\n"
    )
    target.joinpath("README.md").write_text(
        message + "Required filenames:\n"
        + "\n".join(f"- {name}" for name in VIDEO_NAMES)
        + "\n",
        encoding="utf-8",
    )


def prepare_readme(package: Path, videos_included: bool) -> None:
    status = (
        "All four user-recorded videos are included."
        if videos_included
        else "Add your own four videos, then rebuild with --videos-dir to create the final ZIP."
    )
    package.joinpath("README.md").write_text(
        f"""# CS311 final project submission

GitHub: https://github.com/hodatisg520/adl-local-rag-final-project

This folder follows the required `source_code/`, `docker/`, `report/`, and
`demo_video/` structure. {status}

## Local application

Start the Ollama desktop app, or run `ollama serve` in a separate terminal.
Then, from this submission folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r source_code/sample_code/requirements.txt
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
ollama pull qwen2.5:0.5b
cd source_code/sample_code
python run_txt.py --data-dir .. --vector-store data_txt/task1_pdf_demo_store \\
  --rebuild-index --question "How many main tasks does this final project have?"
```

The Task 1 PDFs are in `source_code/`. The selected Task 2 handbook is
`source_code/sample_code/major_handbook_pdfs/CS_MajorHandbook.pdf`.
Task-specific notes are beside the Python source files.

## Docker and report

From this submission folder, follow `docker/README.md` for CLI and web
deployment. The final report is `report/final_project_report.pdf`.
""",
        encoding="utf-8",
    )


def create_zip(package: Path, archive: Path) -> None:
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(package.rglob("*")):
            output.write(path, path.relative_to(package.parent))
    with zipfile.ZipFile(archive) as check:
        if check.testzip() is not None:
            raise OSError(f"ZIP integrity check failed: {archive}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-id", required=True, help="Exact student ID")
    parser.add_argument(
        "--output-dir", type=Path, default=REPO.parent / "submission_output"
    )
    parser.add_argument(
        "--videos-dir", type=Path, help="Folder containing your four recorded MP4s"
    )
    parser.add_argument("--force", action="store_true", help="Replace prior output")
    args = parser.parse_args()

    if re.fullmatch(r"[A-Za-z0-9]+", args.student_id) is None:
        parser.error("--student-id must contain only letters and numbers")

    output_dir = args.output_dir.expanduser().resolve()
    package = output_dir / f"ADL-{args.student_id}-project"
    archive = package.with_suffix(".zip")
    videos_dir = args.videos_dir.expanduser().resolve() if args.videos_dir else None

    if videos_dir is not None:
        if not videos_dir.is_dir():
            parser.error(f"Video directory does not exist: {videos_dir}")
        if videos_dir == package / "demo_video" or package in videos_dir.parents:
            parser.error("The video source must be outside the generated package")
        check_videos(videos_dir)

    if package.exists() or archive.exists():
        if not args.force:
            parser.error("Output already exists; pass --force to replace it")
        if package.exists():
            shutil.rmtree(package)
        if archive.exists():
            archive.unlink()

    package.mkdir(parents=True)
    prepare_source(package)
    prepare_docker(package)
    prepare_report(package)
    prepare_videos(package, videos_dir)
    prepare_readme(package, videos_dir is not None)

    print(f"Submission folder: {package}")
    if videos_dir is None:
        print("Video demos are pending; final ZIP was not created.")
    else:
        create_zip(package, archive)
        print(f"Submission ZIP: {archive}")


if __name__ == "__main__":
    main()
