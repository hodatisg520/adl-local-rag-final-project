# Task 3: Docker deployment

This setup packages the Python RAG chatbot in a Docker image and runs it through Docker Compose. The selected CS handbook is mounted read-only. Chroma's index is stored in a named Docker volume so it survives container restarts and rebuilds. The Dockerfile pins the Python base image by digest and installs the exact Python package versions listed in `sample_code/requirements-docker.txt`.

Ollama runs on the Mac host rather than inside Docker. [Ollama's official guidance](https://ollama.com/blog/ollama-is-now-available-as-an-official-docker-image) recommends running Ollama as a standalone Mac application because Docker Desktop on macOS does not provide GPU access to the Ollama container. The Python container connects to the host Ollama API through `host.docker.internal`.

## Prerequisites

- Docker Desktop or another Docker Engine with the Docker Compose plugin.
- Python dependencies are installed in the image from `sample_code/requirements-docker.txt`.
- Ollama installed on the Mac, with these models downloaded:

  ```bash
  ollama pull nomic-embed-text
  ollama pull qwen2.5:1.5b
  ```

On macOS, if Docker is not installed, the tested lightweight setup is:

```bash
brew install docker docker-compose colima
colima start --cpu 2 --memory 3 --disk 30
```

## Start Ollama for container access

Ollama normally listens only on the Mac's loopback interface. The container needs to reach its API through the host gateway. Quit any existing Ollama app/server, then start it in a Terminal window with:

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

Keep this Terminal window open while using the chatbot. The API is unauthenticated; stop this server after using the Docker chatbot if you do not need it available to other devices on your network.

If Ollama is running on another host, copy `.env.example` to `.env` and set `OLLAMA_URL` to that server's reachable API URL. On Linux, set it to an address the container can reach on the host; the default `host.docker.internal` name is supplied automatically by Docker Desktop and Colima on macOS, but may require host-specific network configuration on other engines.

## Build and run

From the repository root:

```bash
docker-compose build
docker-compose run --rm chatbot
```

On its first run, the app builds the handbook index in the `rag_index` volume. Enter questions in the prompt and type `quit` or `exit` to leave. Later runs reuse the saved index.

The compose file can also build and start the interactive container in one command:

```bash
docker-compose run --build --rm chatbot
```

## Rebuild the index

If the handbook changes or you want a clean index, use:

```bash
docker-compose run --rm chatbot \
  --data-dir major_handbook_pdfs/CS_MajorHandbook.pdf \
  --vector-store data_txt/cs_handbook_vector_store \
  --rebuild-index \
  --llm-model qwen2.5:1.5b \
  --interactive
```

## Data persistence and cleanup

- The handbook PDF is mounted read-only from `sample_code/major_handbook_pdfs/`.
- The vector database is stored in the `rag_index` named volume, outside the image.
- `docker-compose down` removes stopped containers but keeps the index volume.
- `docker-compose down --volumes` also deletes the saved index; the next run recreates it.

To use a different handbook, update the file bind mount and the `--data-dir` argument in `docker-compose.yml` to the selected PDF.

## Local verification

Verified on Apple Silicon with Colima:

- `docker-compose config` accepted the Compose configuration and `docker-compose build` built the image successfully.
- With a fresh volume, the container extracted the selected handbook and indexed 57 chunks.
- A later container reused the persisted index, answered that CS 313 is the prerequisite for CS 311, and cited page 18.
