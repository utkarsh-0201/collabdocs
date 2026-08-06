FROM postgres:16

ENV POSTGRES_DB=collabdocs
ENV POSTGRES_USER=collabdocs_user
ENV POSTGRES_PASSWORD=collabdocs_pass

EXPOSE 5432