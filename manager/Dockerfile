FROM python:3.6.7-alpine
# Install Docker and dependencies
RUN apk --update add \
   bash \
   iptables \
   ca-certificates \
   e2fsprogs \
  docker \  
  && rm -rf /var/cache/apk/* \
  && pip install --upgrade pip 
  
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt && chmod 644 app.py
CMD ["python3", "app.py"]