FROM python:3.8-alpine

# set python to use utf-8 rather than ascii.
ENV PYTHONIOENCODING="UTF-8"

# hard set UTC in case the user does not define it
ENV TZ="Etc/UTC"

RUN apk add --update --no-cache git py3-pip && \
    git clone -b master --single-branch https://github.com/morpheus65535/tesla_preheat.git /tesla && \
    pip3 install -r /tesla/requirements.txt

CMD ["python", "/tesla/tesla.py"]