# Task 6 video demos

This folder contains the four separate video demos required for Tasks 1–4. Each is a narrated, four-scene walkthrough that explains the purpose, shows relevant implementation excerpts, and presents verified project results. Task 4 includes a screenshot from the tested Streamlit interface. English transcripts are included beside the videos.

| Task | Video | Transcript | Duration |
| --- | --- | --- | ---: |
| 1 — PDF support | `task1_pdf_support.mp4` | `task1_pdf_support_transcript.txt` | 53 sec |
| 2 — handbook chatbot | `task2_handbook_chatbot.mp4` | `task2_handbook_chatbot_transcript.txt` | 56 sec |
| 3 — Docker deployment | `task3_docker_deployment.mp4` | `task3_docker_deployment_transcript.txt` | 45 sec |
| 4 — web interface | `task4_web_interface.mp4` | `task4_web_interface_transcript.txt` | 52 sec |

All videos are 1920 × 1080 H.264 MP4 files with AAC narration. The combined video size is approximately 5.6 MB.

## Regenerate the videos

The source builder is `build_demos.py`. It was written for macOS and requires Python 3, FFmpeg (`ffmpeg` and `ffprobe`), the macOS `say` command, and Pillow. From the repository root:

```bash
python3 -m pip install -r demo_video/requirements.txt
python3 demo_video/build_demos.py
```

To rebuild only selected videos, add `--tasks` followed by one or more task numbers, such as `--tasks 3 4`. Use `--voice` to choose another installed macOS English voice. The script keeps temporary slides and audio in a temporary work directory and writes MP4s and transcripts to this folder.
