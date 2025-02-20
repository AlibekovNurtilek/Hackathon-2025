FROM continuumio/miniconda3

WORKDIR /app
COPY . /app

# Устанавливаем зависимости из environment.yml
RUN conda env create -f environment.yml

# Настраиваем переменные среды для правильной работы Conda
ENV CONDA_ENV hackathon_env
ENV PATH /opt/conda/envs/${CONDA_ENV}/bin:$PATH

# Активируем Conda-среду и запускаем FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
