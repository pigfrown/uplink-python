
FROM python:3.8

RUN curl -O https://dl.google.com/go/go1.14.6.linux-amd64.tar.gz
RUN sha256sum go1.14.6.linux-amd64.tar.gz
RUN tar xvf go1.14.6.linux-amd64.tar.gz
RUN chown -R root:root ./go
RUN mv go /usr/local
ENV PATH=$PATH:/usr/local/go/bin

# ENV VIRTUAL_ENV=/opt/venv
# RUN python3 -m venv $VIRTUAL_ENV
# ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip --no-cache-dir install pylint
