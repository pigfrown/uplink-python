
FROM python:latest
LABEL MAINTAINER marcin.niemira@gmail.com

RUN pip3 --no-cache-dir install pylint

ENTRYPOINT ["pylint"]
