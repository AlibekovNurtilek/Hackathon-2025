FROM continuumio/miniconda3

WORKDIR /app

# Копируем только environment.yml для кеширования зависимостей
COPY environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml

# Копируем код после установки зависимостей (чтобы кеш не сбрасывался)
COPY . /app

# Настраиваем переменные среды для правильной работы Conda
ENV CONDA_ENV hackathon_env
ENV PATH /opt/conda/envs/${CONDA_ENV}/bin:$PATH

# Активируем Conda-среду и запускаем FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
