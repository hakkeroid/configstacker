FROM alpine:3.8

ENV PYTHON_VERSIONS 2.7.15 3.4.10 3.5.7 3.6.9 3.7.4
ENV PYTHON_GLOBAL_VERSION 3.7.4
ENV PYTHON_PIP_VERSION 18.0

RUN apk --update add \
    bash \
    build-base \
    bzip2-dev \
    curl \
    git \
    libffi-dev \
    ncurses-dev \
    openssl-dev \
    linux-headers \
    readline-dev \
    sqlite-dev \
    tk-dev \
    xz-dev \
    zlib-dev

COPY install.sh /install.sh

RUN /bin/bash /install.sh \
    && rm /install.sh

ENV HOME /root
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

ENV CI_PROJECT_DIR /app

WORKDIR $CI_PROJECT_DIR
CMD tox
