FROM python:3.6.5-alpine3.7 AS python_build

ARG DEVELOPMENT=
COPY pip.conf /etc/pip.conf
COPY Pipfile Pipfile.lock pipenv.txt /usr/src/app/
WORKDIR /usr/src/app

RUN apk add --no-cache \
    gcc \
    git \
    linux-headers \
    lua5.2-dev \
    musl-dev \
    postgresql-dev
RUN pip install --no-deps -r pipenv.txt
RUN pipenv lock -r --keep-outdated > requirements.txt
RUN [ -z ${DEVELOPMENT} ] || pipenv lock -d -r --keep-outdated >> requirements.txt
RUN pip wheel -r requirements.txt -w /wheels


FROM alpine:3.7 AS lua_build

COPY hunts/runtimes/lua/luarocks/config.lua /etc/luarocks/config-5.2.lua

RUN apk add --no-cache \
    curl \
    gcc \
    imlib2-dev \
    lua5.2-dev \
    luarocks5.2 \
    musl-dev
RUN luarocks-5.2 install lua-cjson 2.1.0-1
RUN luarocks-5.2 install lua-imlib2 dev-2


FROM python:3.6.5-alpine3.7

COPY --from=python_build /wheels /wheels

WORKDIR /usr/src/app

RUN apk add --no-cache \
    lua5.2 \
    postgresql-client \
    postgresql-libs \
    imlib2
RUN python -m wheel install --force /wheels/*.whl
COPY --from=lua_build /opt/hunter2 /opt/hunter2

COPY . .

RUN addgroup -g 500 -S django \
 && adduser -h /usr/src/app -s /sbin/nologin -G django -S -u 500 django \
 && install -d -g django -o django /config /static /uploads/events /uploads/puzzles
USER django

VOLUME ["/config", "/static", "/uploads/events", "/uploads/puzzles"]

EXPOSE 3031
CMD ["uwsgi", "--ini", "/usr/src/app/uwsgi.ini"]
