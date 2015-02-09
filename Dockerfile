FROM gliderlabs/alpine:3.1

RUN apk-install python py-pip openssl ca-certificates procps openvpn

WORKDIR /pritunl

COPY . /pritunl

RUN apk-install --virtual build python-dev build-base wget \
  && pip install -r requirements.txt \
  && python setup.py install \
  && apk del --purge -r build

CMD pritunl start
