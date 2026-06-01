# Restaurant Job Hunter

This repo now includes a focused job-search assistant for serving, lead server, shift lead, and restaurant supervisor jobs around the San Fernando Valley, Thousand Oaks, Westlake Village, and nearby areas.

## What it does

- Searches current job posts through the Adzuna Jobs API.
- Scores postings against your preferred titles, locations, and hospitality keywords.
- Creates `job_leads/applications.csv` so you can track every lead, application date, follow-up date, interview date, and notes.
- Writes tailored draft cover notes in `job_leads/drafts/` for the best matches.
- Optionally opens the top application links in your browser.

## What it will not do automatically

It does **not** submit applications without you reviewing them. Fully automated job applications can violate job-board terms, submit inaccurate answers, and hurt your chances. This tool gets you to the apply links quickly with a tailored note and a tracking system so you can apply fast but still stay accurate.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Register for Adzuna API credentials at <https://developer.adzuna.com/>.

3. Export your credentials:

   ```bash
   export ADZUNA_APP_ID="your_app_id"
   export ADZUNA_APP_KEY="your_app_key"
   ```

4. Copy the example profile and personalize it:

   ```bash
   cp job_profile.example.yaml job_profile.yaml
   ```

5. Edit `job_profile.yaml` with your real name, email, phone, resume path, strengths, target titles, and target cities.

## Run it

Search one page per title/location pair:

```bash
python job_hunter.py --profile job_profile.yaml --pages 1
```

Search more deeply and open the top 5 application links:

```bash
python job_hunter.py --profile job_profile.yaml --pages 2 --open 5
```

## Daily workflow

1. Run the script each morning.
2. Open `job_leads/applications.csv`.
3. Apply to the highest-score postings first.
4. Use the matching draft in `job_leads/drafts/` as your starting cover note.
5. Update `status`, `date_applied`, `follow_up_date`, and `notes` in the CSV.
6. Follow up three to five business days later for restaurants where you really want to work.

## Suggested search terms for your situation

The example profile is already tuned toward:

- Server
- Restaurant server
- Lead server
- Server supervisor
- Shift lead restaurant
- Restaurant supervisor
- Food runner
- Bartender

The example location list includes San Fernando Valley, Sherman Oaks, Studio City, Burbank, Glendale, Calabasas, Woodland Hills, Thousand Oaks, Westlake Village, and Agoura Hills.
