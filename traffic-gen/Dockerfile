# WXO Traffic Generator
#
# Build context MUST be the repository root, not the traffic-gen/ directory.
# The COPY instructions below reach scenarios/, standalone/, and evaluation/
# which live at repo root — those directories contain the auto-discovered
# agent manifests and prompt data. A rebuild picks up any new scenarios or
# standalone agents automatically with no code changes.
#
# Build:
#   docker build -f traffic-gen/Dockerfile -t wxo-traffic-gen .
#
# Run:
#   docker run --rm \
#     -e WXO_API_KEY=<your-key> \
#     -e WXO_URL=https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<id> \
#     -e WXO_ENV_TYPE=ibm_iam \
#     -e CALL_INTERVAL_MINUTES=1 \
#     wxo-traffic-gen
#
# Optional extra users (CSV is mounted at runtime, never copied into the image):
#   docker run --rm ... \
#     -v "$(pwd)/api-keys.csv:/app/api-keys.csv:ro" \
#     -e WXO_API_KEYS_FILE=/app/api-keys.csv \
#     wxo-traffic-gen

FROM python:3.11-slim

# Unbuffered stdout so logs appear immediately in `docker logs`.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Application source and standalone prompt config.
COPY traffic-gen/app.py     /app/app.py
COPY traffic-gen/prompts.yaml /app/prompts.yaml

# Scenario manifests — app reads smoke_agent, flows, and agents[] from these.
# Every scenarios/*/scenario.yaml is included. Adding a new scenario and
# rebuilding the image is all that is required to pick it up.
COPY scenarios/ /app/scenarios/

# Standalone agent definitions — app reads the name: field from each agent.yaml.
COPY standalone/ /app/standalone/

# Evaluation ground truth — app reads smoke_prompts from ground_truth.json
# for each scenario agent.
COPY evaluation/ /app/evaluation/

CMD ["python", "app.py"]
