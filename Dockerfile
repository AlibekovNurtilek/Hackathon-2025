FROM continuumio/miniconda3

WORKDIR /app
COPY . /app

RUN conda env create -f environment.yml
RUN echo "source activate fastapi_env" > ~/.bashrc
ENV PATH /opt/conda/envs/fastapi_env/bin:$PATH

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
