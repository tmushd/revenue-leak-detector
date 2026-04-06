# Docker Run Guide

This repo is Docker-runnable out of the box.

## Fastest path (beginner-safe)

From the repo root, run:

```bash
bash docker/build-image.sh
bash docker/run-app.sh
```

Open: [http://localhost:8501](http://localhost:8501)

What happens automatically:
1. The container runs `python -m src.run_pipeline`.
2. Processed files are generated in `data/processed/` and model artifacts in `artifacts/`.
3. Streamlit launches on port `8501`.

## Manual Docker commands (advanced)

From the repo root:

```bash
docker build -t revenue-leak-detector .
docker run --rm -p 8501:8501 revenue-leak-detector
```

## Docker Compose option

```bash
docker compose up --build
```

Open: [http://localhost:8501](http://localhost:8501)

## Useful commands

Run only the pipeline:

```bash
docker run --rm revenue-leak-detector pipeline
```

or using helper script:

```bash
bash docker/run-pipeline.sh
```

Skip pipeline and launch Streamlit directly (uses existing processed files in image):

```bash
docker run --rm -p 8501:8501 -e RUN_PIPELINE_ON_START=false revenue-leak-detector
```

or with helper script:

```bash
RUN_PIPELINE_ON_START=false bash docker/run-app.sh
```

Open shell in container:

```bash
docker run --rm -it revenue-leak-detector bash
```

## Common errors and exact fixes

### 1) `docker: invalid reference format`
Cause: typo in run command, usually `-` instead of `-p`.

Wrong:
```bash
docker run --rm - 8501:8501 revenue-leak-detector
```

Correct:
```bash
docker run --rm -p 8501:8501 revenue-leak-detector
```

### 2) `Unable to find image 'revenue-leak-detector:latest' locally`
Cause: image was not built yet.

Fix:
```bash
bash docker/build-image.sh
```

### 3) `Usage: docker buildx build ...`
Cause: `buildx` command used without required args, or image not loaded locally.

Fix (preferred):
```bash
docker build -t revenue-leak-detector .
```

If using buildx:
```bash
docker buildx build --load -t revenue-leak-detector .
```

### 4) `Bind for 0.0.0.0:8501 failed: port is already allocated`
Cause: port `8501` already in use.

Fix:
```bash
PORT=8502 bash docker/run-app.sh
```
Then open `http://localhost:8502`.

## Copy/clone and run workflow

```bash
git clone https://github.com/tmushd/revenue-leak-detector.git
cd revenue-leak-detector
bash docker/build-image.sh
bash docker/run-app.sh
```

No local Python setup is required.
