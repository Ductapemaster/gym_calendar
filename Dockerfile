FROM python:3.7-alpine

# Go grab our repo
RUN apk add --update git && \
    git clone https://github.com/Ductapemaster/gym_calendar.git /app/gym_calendar && \
    rm -rf gym_calendar/.git && \
    apk del git && \
    rm -rf /var/cache/apk/*

# Install python requirements
RUN pip install -r /app/gym_calendar/requirements.txt

# Copy our credentials file into the container
COPY service.json /app/gym_calendar/service.json
COPY secrets.py /app/gym_calendar/secrets.py

# Set up working directory
WORKDIR /app/gym_calendar

# Run it!
CMD ["python", "main.py"]
