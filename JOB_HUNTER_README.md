# Restaurant Job Hunter

This repo includes a focused job-search assistant for serving, lead server, shift lead, bartender, and restaurant supervisor jobs around the San Fernando Valley, Thousand Oaks, Westlake Village, and nearby areas.

The fastest way to use it is **not** to wait for API keys. Generate a private profile, open the first batch of target links, apply manually, and track every follow-up.

## What it does

- Creates a private `job_profile.yaml` pre-filled for Dylan's restaurant search, including the iCloud resume path from the shared resume file.
- Builds `job_leads/applications.csv` so you can track every application, status, follow-up date, interview date, and notes.
- Writes tailored draft cover notes in `job_leads/drafts/` for each target or job lead.
- Writes `job_leads/today_application_plan.md` with a one-hour application sprint, phone script, and follow-up script.
- Opens high-priority application/search links in your browser so you can start applying immediately.
- Optionally searches current job posts through the Adzuna Jobs API when credentials are available.

## What it will not do automatically

It does **not** submit applications without you reviewing them. Fully automated job applications can violate job-board terms, submit inaccurate answers, and hurt your chances. This tool gets you to the apply links quickly with tailored notes and a tracking system so you can apply fast but still stay accurate.


## No-Terminal Mac launcher

If Terminal is confusing, double-click:

```text
RUN_JOB_HUNTER.command
```

If macOS blocks it, right-click the file, choose **Open**, then choose **Open** again. The launcher installs requirements, creates `job_profile.yaml` if needed, opens it so you can add your email/phone, then opens the first 10 application/search links and the tracker files.

See `QUICK_START_FOR_DYLAN.md` for the simplest step-by-step version.

## Fast start: get applications out today

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create your private profile:

   ```bash
   python job_hunter.py --init-profile
   ```

3. Open `job_profile.yaml` and fill in your real email and phone number. The template already points to:

   ```text
   /Users/dylanzimmerman/Library/Mobile Documents/com~apple~CloudDocs/RESUME copy.docx
   ```

4. Export your resume as a PDF too. Most application sites accept PDFs more reliably than `.docx` files.

5. Generate today's application packet and open the first 10 links:

   ```bash
   python job_hunter.py --source targets --open 10
   ```

6. Apply to real openings from those links, then update `job_leads/applications.csv` after every submission.

## Run options

Generate target/search links without API keys:

```bash
python job_hunter.py --source targets
```

Generate target/search links and open the top 15:

```bash
python job_hunter.py --source targets --open 15
```

Use Adzuna if you already have credentials:

```bash
export ADZUNA_APP_ID="your_app_id"
export ADZUNA_APP_KEY="your_app_key"
python job_hunter.py --source adzuna --pages 1
```

Use target links plus Adzuna results:

```bash
python job_hunter.py --source both --pages 1 --open 10
```

If you run with the default `--source auto`, the script uses Adzuna when credentials are set. If credentials are missing, it automatically falls back to target/search links so you are not blocked.

## Daily workflow

1. Run the script each morning.
2. Open `job_leads/today_application_plan.md`.
3. Open `job_leads/applications.csv`.
4. Apply to the highest-priority postings first.
5. Use the matching draft in `job_leads/drafts/` as your starting cover note.
6. Update `status`, `date_applied`, `follow_up_date`, and `notes` in the CSV.
7. Follow up three to five business days later for restaurants where you really want to work.

## Suggested search terms for your situation

The example profile is tuned toward:

- Server
- Restaurant server
- Lead server
- Server supervisor
- Shift lead restaurant
- Restaurant supervisor
- Food runner
- Bartender

The example location list includes San Fernando Valley, Sherman Oaks, Studio City, Burbank, Glendale, Calabasas, Woodland Hills, Thousand Oaks, Westlake Village, and Agoura Hills.
