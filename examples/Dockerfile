# To run validation using a Docker environment:
#   docker container run $(docker image build -f examples/Dockerfile -q .)

FROM python:3.8-slim

COPY ./examples/requirements.txt /app/examples/requirements.txt
RUN pip install -r /app/examples/requirements.txt
ADD ./ /app

CMD ["python", "/app/examples/validate_examples.py"]
