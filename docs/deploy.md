# Putting CineMatch online with Render

This guide takes CineMatch from your laptop to a public web address. You do every step yourself in
your browser and one terminal window. Nothing here costs money on the free plans, and nothing in the
repository contains a password or key.

## What gets hosted

| Piece | Where it runs on Render | Where it comes from |
|---|---|---|
| Website and API | One **web service** built from the `Dockerfile` | Your GitHub repository (`main` branch) |
| Database | One **PostgreSQL** database | Created empty by Render |
| Film catalog (14,292 films, people, credits, keywords, awards) | Inside the database | Uploaded from your laptop (`catalog.dump`, about 14 MB) |
| Demo account (`demo@cinematch.local`, same password as on your laptop) | Inside the database | Uploaded from your laptop (`demo_user.json`) |
| Trained models and the Research Lab numbers | Inside the database, unpacked by the server at start | Uploaded from your laptop (`artifacts.tar.gz`, about 38 MB) |

Why the models travel through the database: the GitHub repository is public, and the models are built
from MovieLens ratings, which may not be redistributed. The database is private to your Render account,
so the models never become public.

Memory: with the same 512 MB limit as Render's free plan, the container peaked at about 380 MB while
serving the home page, film pages, search and the Research Lab (measured in Docker on the laptop). The
free plan fits. The database uses about 240 MB of the free plan's 1 GB.

## Before you start

- A Render account (you have one), signed in with GitHub so Render can see the repository.
- Docker Desktop running on the laptop (the upload uses it), and the local database started:
  `scripts\db.ps1 start`.
- All pull requests merged into `main` on GitHub. Render deploys `main`.

## Step 1: create the service and the database

1. Open <https://dashboard.render.com>, click **New**, then **Blueprint**.
2. Pick the `CINEMATCH` repository. Render finds `render.yaml` and shows two items:
   `cinematch` (web service) and `cinematch-db` (database).
3. Render asks for one value, `WEB_ORIGIN`. Type `https://cinematch.onrender.com`.
   (If Render gives the service a different address, change this value to that address in the
   service's **Environment** tab. The site works in the meantime.)
4. Click **Apply**. Render creates the database, builds the Docker image (about 5 to 10 minutes the
   first time), starts the service, and creates all the tables.
5. Wait until the web service shows **Live**. Open `https://<your address>/api/health`. You should see
   `{"status":"ok","db":"ok",...}`. The home page opens too, but has no films yet.

## Step 2: copy the catalog, demo account and models from the laptop

1. In Render, open **cinematch-db**, click **Connect**, choose **External**, and copy the
   **External Database URL**. Treat it like a password: do not paste it into chats, files or GitHub.
2. In a terminal in the `cinematch` folder, make the three upload files:

   ```powershell
   .\.venv\Scripts\python.exe scripts\deploy_data.py export
   ```

   It prints the sizes, for example `catalog.dump 14.3 MB` and `artifacts.tar.gz 38.0 MB`. The files go
   to `deploy-out\`, which git ignores.
3. Upload them:

   ```powershell
   .\.venv\Scripts\python.exe scripts\deploy_data.py upload
   ```

   Paste the External Database URL when it asks (the text stays hidden). It takes a minute or two and
   prints `1/3 Catalog`, `2/3 Demo account`, `3/3 Model bundle`, then `Done`.
4. In Render, open the **cinematch** service, click **Manual Deploy**, then **Restart service**.
5. Open the site. The home page now shows the hero and the rails. The first visit after a restart can
   take about 10 seconds while the recommender loads.

Running `upload` again is safe: it skips the catalog and the demo account if they are already there, and
replaces the model bundle.

## Updating the site later

- **Code changes**: merge into `main`. Render rebuilds and redeploys by itself (`autoDeploy`).
  Database changes (Alembic migrations) run automatically when the new version starts.
- **New models**: run the pipeline on the laptop, then `deploy_data.py export` and `upload` again, then
  **Restart service**.
- **New films in the catalog** (for example after the franchise update): `upload` skips a catalog that is
  already there. Ask for help before replacing it, because accounts' ratings point at the films.

## Things to know about the free plans

- The free web service **sleeps after 15 minutes without visitors**. The next visit wakes it, which takes
  about a minute. Open the site a few minutes before a demo.
- Render's free database has an **expiry date** (shown on the database page). Before it expires, either
  upgrade the database to a paid plan, or create a new Blueprint and repeat Step 2. Accounts made on the
  site live in this database, so they go with it.
- Sign-in lockout counters are kept in the server's memory, so a restart clears them.
- There is no email service, so the site cannot send password reset or verification emails.

## If something goes wrong

| What you see | What to do |
|---|---|
| Build fails on Render | Open the service's **Logs**. Most often a download timed out: click **Manual Deploy**, then **Deploy latest commit**. |
| `/api/health` shows `"db":"error"` | The database is still starting, or the service lost its `DATABASE_URL`. In the **Environment** tab, `DATABASE_URL` must come from `cinematch-db`. |
| `upload` says the database has no CineMatch tables | The service has not finished its first start. Wait for **Live**, then run `upload` again. |
| `upload` cannot connect | Use the **External** URL (not the Internal one) and check that Docker Desktop is running. |
| Home page shows no rails after the upload | Restart the service (Step 2.4). The logs should show `unpacked artifact bundle` and `recommender engine ready`. |
| Service restarts with "out of memory" | Move the web service to the paid Starter plan. Our measurement fits 512 MB, but this is the fix if real traffic needs more. |

## Trying the hosted setup on the laptop first (optional)

The same container can run locally against an empty database, which is how this setup was tested:

```powershell
docker build -t cinematch:local .
docker run --rm -p 8000:8000 --memory 512m -e DATABASE_URL=<a local test database URL> -e JWT_SECRET=<any long random text> cinematch:local
```

Then run `deploy_data.py upload` with that database's URL and open <http://localhost:8000>.
