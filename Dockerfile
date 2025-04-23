# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.13

# Set the working directory in the container
WORKDIR /app
COPY . /app

# Update package lists and install zlib
RUN apt-get update && apt-get install -y libjpeg-dev zlib1g-dev

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt



# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

#Expose port for app to run on
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

#Run
ENTRYPOINT ["streamlit", "run", "/app/code/StreamlitUI.py", "--server.port=8501", "--server.address=0.0.0.0"]
# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
#CMD ["python", "-m", "streamlit", "run", "FrontEndStreamlit.py", "--server-port", "8000", "--server.address", "0.0.0.0"]