ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION}

ARG BUILD_DATE
ARG BUILD_REPO
ARG BUILD_HASH

ARG APP_VERSION

ENV BUILD_DATE=${BUILD_DATE}
ENV BUILD_REPO=${BUILD_REPO}
ENV BUILD_HASH=${BUILD_HASH}

ENV APP_VERSION=${APP_VERSION}

RUN apt update && \
    apt install -y gosu && \
    rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# create the container user
RUN useradd -ms /bin/bash deploy

COPY dist/* /usr/local/src/
RUN pip install /usr/local/src/*.whl

WORKDIR /tmp
ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]
