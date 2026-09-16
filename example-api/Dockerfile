# Builds on top of the toolbox-container image itself, rather than
# standalone - this is the point being demonstrated: the toolbox CLI is a
# reusable dependency another service's image can install and call from its
# own entrypoint, not just something you `docker run` in isolation.
FROM toolbox-container:latest

USER root
WORKDIR /app

COPY app.py entrypoint.sh ./
RUN chmod +x entrypoint.sh \
    && chown -R toolbox:toolbox /app

USER toolbox

# Overrides the base image's ENTRYPOINT (["toolbox"]) with this service's
# own startup sequence, which itself calls `toolbox wait-for` internally.
ENTRYPOINT ["./entrypoint.sh"]
