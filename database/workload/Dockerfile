# Custom PostgreSQL 16 image with HypoPG hypothetical index extension
FROM postgres:16

# Install HypoPG extension for PostgreSQL 16
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-16-hypopg \
    && rm -rf /var/lib/apt/lists/*

LABEL maintainer="QueryGuard AI Team"
LABEL description="PostgreSQL 16 with HypoPG extension and pg_stat_statements for what-if index simulation"
