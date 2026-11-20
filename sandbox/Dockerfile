FROM mcr.microsoft.com/playwright/python:v1.58.0-noble
ARG AGENT_UID=1000
RUN pip install --no-cache-dir playwright==1.58.0 && useradd --uid ${AGENT_UID} --non-unique -m agent && mkdir /workspace && chown agent /workspace
LABEL workbench.agent.uid=${AGENT_UID}
COPY action.py /opt/action.py
COPY browser_service.py /opt/browser_service.py
USER agent
WORKDIR /workspace
CMD ["python", "/opt/browser_service.py"]
