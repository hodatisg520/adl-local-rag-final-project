FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY sample_code/requirements-docker.txt /tmp/requirements-docker.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements-docker.txt

COPY sample_code/run_txt.py /app/run_txt.py
COPY sample_code/streamlit_app.py /app/streamlit_app.py
RUN mkdir -p /app/data_txt /app/major_handbook_pdfs

ENTRYPOINT ["python", "/app/run_txt.py"]
