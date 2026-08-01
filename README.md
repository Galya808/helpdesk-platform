# helpdesk-platform
Helpdesk platform built with FastAPI, PostgreSQL and Next.js

## Local database

Start PostgreSQL:

​```bash
docker compose up -d db
​```

Check the service status:

​```bash
docker compose ps
​```

View database logs:

​```bash
docker compose logs db
​```

Connect with psql:

​```bash
docker compose exec db psql -U helpdesk -d helpdesk
​```

Stop the services:

​```bash
docker compose down
​```