# Production deployment

The production setup uses Render for PostgreSQL and the FastAPI Docker service,
and Vercel for the Next.js frontend.

## 1. Deploy the backend on Render

1. In Render, choose **New > Blueprint**.
2. Connect `Galya808/helpdesk-platform`.
3. Render detects the root `render.yaml` file.
4. Apply the Blueprint and wait for the database and `helpdesk-api` service.
5. Open `https://<render-service>.onrender.com/health` and confirm the response
   is `{"status":"ok"}`.

The Blueprint generates the JWT secret, connects the database through Render's
private network, applies Alembic migrations, and configures `/health` as the
service health check.

## 2. Deploy the frontend on Vercel

1. Import `Galya808/helpdesk-platform` as a new Vercel project.
2. Set **Root Directory** to `frontend`.
3. Keep the detected Next.js build settings.
4. Add `NEXT_PUBLIC_API_URL` with the Render service URL, without a trailing
   slash.
5. Add the variable to Production and Preview environments.
6. Deploy and copy the generated Vercel URL.

## 3. Allow the Vercel origin

In the Render `helpdesk-api` environment settings, add:

```text
HELPDESK_CORS_ORIGINS=["https://<vercel-project>.vercel.app"]
```

Replace the placeholder with the exact Vercel production URL, save the setting,
and redeploy the backend.

## 4. Verify production

- open the frontend;
- confirm that the backend status is online;
- register a test customer;
- sign in;
- create and open a ticket;
- add a comment;
- inspect `/docs`, `/health`, and `/metrics` on the Render service.

Do not commit production secrets or database URLs to the repository.
