"""Job search assistant for restaurant/service roles.

This tool finds matching job listings through the Adzuna Jobs API, scores them against
an applicant profile, creates application-tracking CSV files, and writes tailored
application notes the applicant can review before submitting.

It can also build an application campaign without API credentials: a ready-to-use
profile, a prioritized target list, outreach scripts, and browser links to direct
restaurant career searches. It intentionally does not auto-submit applications.
Many job boards prohibit bots, and restaurant roles often ask business-specific
screening questions. Human review keeps applications accurate and avoids violating
site terms.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import os
import re
import sys
import textwrap
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse

import requests
import yaml

ADZUNA_SEARCH_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
DEFAULT_PROFILE = "job_profile.yaml"
DEFAULT_OUTPUT_DIR = "job_leads"
DEFAULT_RESUME_PATH = "/Users/dylanzimmerman/Library/Mobile Documents/com~apple~CloudDocs/RESUME copy.docx"

TRACKER_FIELDS = [
    "lead_id",
    "date_found",
    "status",
    "priority",
    "score",
    "title",
    "company",
    "location",
    "salary_min",
    "salary_max",
    "source",
    "url",
    "score_notes",
    "next_step",
    "date_applied",
    "follow_up_date",
    "interview_date",
    "notes",
]

DEFAULT_TARGET_COMPANIES = [
    "Mastro's Steakhouse Thousand Oaks",
    "Crawford's Social Westlake Village",
    "Paul Martin's American Grill Westlake Village",
    "The Stonehaus Westlake Village",
    "Mediterraneo Westlake Village",
    "Finney's Crafthouse Westlake Village",
    "Tarantula Hill Brewing Co Thousand Oaks",
    "Larsen's Grill Oxnard or Encino",
    "The Six Chow House Calabasas",
    "King's Fish House Calabasas",
    "Fleming's Prime Steakhouse Woodland Hills",
    "Joey Woodland Hills",
    "The Local Peasant Woodland Hills",
    "Casalena Woodland Hills",
    "Firefly Studio City",
    "Black Market Liquor Bar Studio City",
    "The Front Yard Studio City",
    "Granville Studio City",
    "Mizlala Sherman Oaks",
    "The Local Peasant Sherman Oaks",
    "Castaway Burbank",
    "Granville Burbank",
    "Din Tai Fung Glendale",
    "The Americana at Brand restaurants Glendale",
]

CAREER_SEARCHES = [
    ("Culinary Agents", "https://culinaryagents.com/search/jobs?search%5Bname%5D={query}"),
    ("Poached Jobs", "https://poachedjobs.com/jobs/all/{query}"),
    ("Indeed", "https://www.indeed.com/jobs?q={query}&l={location}"),
    ("Google Jobs", "https://www.google.com/search?q={query}+{location}+restaurant+server+jobs"),
    ("Craigslist food/bev", "https://losangeles.craigslist.org/search/fbh?query={query}"),
]


@dataclass(slots=True)
class ApplicantProfile:
    name: str
    email: str
    phone: str
    city: str
    resume_path: str
    experience_summary: str
    strengths: list[str]
    target_titles: list[str]
    target_locations: list[str]
    positive_keywords: list[str]
    negative_keywords: list[str]
    target_companies: list[str] = field(default_factory=lambda: DEFAULT_TARGET_COMPANIES.copy())
    minimum_score: int = 35
    results_per_query: int = 20
    max_leads: int = 50

    @classmethod
    def from_file(cls, path: Path) -> "ApplicantProfile":
        if not path.exists():
            raise FileNotFoundError(
                f"Profile file not found: {path}. Run `python job_hunter.py --init-profile` first, "
                f"or copy job_profile.example.yaml to {path} and fill it in."
            )
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        required = [
            "name",
            "email",
            "phone",
            "city",
            "resume_path",
            "experience_summary",
            "strengths",
            "target_titles",
            "target_locations",
            "positive_keywords",
            "negative_keywords",
        ]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Missing required profile fields in {path}: {', '.join(missing)}")
        data.setdefault("target_companies", DEFAULT_TARGET_COMPANIES.copy())
        return cls(**data)


@dataclass(slots=True)
class JobLead:
    lead_id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    created: str
    salary_min: str = ""
    salary_max: str = ""
    score: int = 0
    score_notes: list[str] = field(default_factory=list)
    priority: str = "A"

    def as_row(self) -> dict[str, str | int]:
        return {
            "lead_id": self.lead_id,
            "date_found": dt.date.today().isoformat(),
            "status": "found",
            "priority": self.priority,
            "score": self.score,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "source": self.source,
            "url": self.url,
            "score_notes": "; ".join(self.score_notes),
            "next_step": "Open link, apply with resume, then mark date_applied and follow_up_date.",
            "date_applied": "",
            "follow_up_date": "",
            "interview_date": "",
            "notes": "",
        }


def clean_text(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:12]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "application"


def require_adzuna_credentials() -> tuple[str, str]:
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        raise RuntimeError(
            "Set ADZUNA_APP_ID and ADZUNA_APP_KEY first. Register for API credentials at "
            "https://developer.adzuna.com/. You can still run without credentials by using "
            "`python job_hunter.py --source targets --open 10`."
        )
    return app_id, app_key


def has_adzuna_credentials() -> bool:
    return bool(os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY"))


def fetch_adzuna_jobs(profile: ApplicantProfile, country: str, pages: int) -> list[JobLead]:
    app_id, app_key = require_adzuna_credentials()
    leads: dict[str, JobLead] = {}

    for title in profile.target_titles:
        for location in profile.target_locations:
            for page in range(1, pages + 1):
                params = {
                    "app_id": app_id,
                    "app_key": app_key,
                    "what": title,
                    "where": location,
                    "results_per_page": profile.results_per_query,
                    "sort_by": "date",
                    "content-type": "application/json",
                }
                response = requests.get(
                    ADZUNA_SEARCH_URL.format(country=country, page=page),
                    params=params,
                    timeout=30,
                )
                response.raise_for_status()
                for raw in response.json().get("results", []):
                    lead = parse_adzuna_job(raw)
                    lead.score, lead.score_notes = score_lead(lead, profile)
                    lead.priority = priority_for_score(lead.score)
                    if lead.score >= profile.minimum_score:
                        leads.setdefault(lead.lead_id, lead)

    return sorted(leads.values(), key=lambda lead: lead.score, reverse=True)[: profile.max_leads]


def parse_adzuna_job(raw: dict[str, Any]) -> JobLead:
    title = clean_text(raw.get("title"))
    company = clean_text((raw.get("company") or {}).get("display_name")) or "Unknown company"
    area = raw.get("location", {}).get("area") or []
    location = clean_text(", ".join(area[-3:]) or raw.get("location", {}).get("display_name"))
    url = clean_text(raw.get("redirect_url"))
    description = clean_text(raw.get("description"))
    created = clean_text(raw.get("created"))
    return JobLead(
        lead_id=stable_id(title, company, location, url),
        title=title,
        company=company,
        location=location,
        description=description,
        url=url,
        source=urlparse(url).netloc or "Adzuna",
        created=created,
        salary_min=str(raw.get("salary_min") or ""),
        salary_max=str(raw.get("salary_max") or ""),
    )


def build_target_leads(profile: ApplicantProfile) -> list[JobLead]:
    """Create high-intent application targets that do not require API credentials.

    These are not presented as confirmed open jobs. They are direct search/action links
    for places and job boards where the applicant should apply or check openings today.
    """
    leads: list[JobLead] = []
    location = "San Fernando Valley Thousand Oaks Westlake Village CA"
    title = "server restaurant supervisor lead server"

    for company in profile.target_companies:
        query = quote_plus(f'{company} careers server restaurant jobs')
        url = f"https://www.google.com/search?q={query}"
        lead = JobLead(
            lead_id=stable_id("target-company", company, url),
            title="Server / Lead Server / Restaurant Supervisor",
            company=company,
            location="Target area",
            description=(
                "High-priority restaurant target. Use this search link to find the company career page, "
                "current postings, manager contact info, and same-day application options."
            ),
            url=url,
            source="target-list",
            created=dt.date.today().isoformat(),
            score=82,
            score_notes=["known local restaurant target", "apply or contact directly today"],
            priority="A",
        )
        leads.append(lead)

    for source_name, template in CAREER_SEARCHES:
        query = quote_plus(title)
        encoded_location = quote_plus(location)
        url = template.format(query=query, location=encoded_location)
        lead = JobLead(
            lead_id=stable_id("career-search", source_name, url),
            title="Live restaurant job search",
            company=source_name,
            location="SFV / Thousand Oaks / Westlake Village",
            description=(
                "Open this board search, filter for recent server, bartender, lead server, trainer, "
                "shift lead, and supervisor roles, then add the best postings to the tracker."
            ),
            url=url,
            source="career-search",
            created=dt.date.today().isoformat(),
            score=78,
            score_notes=["live job board search", "fast way to submit applications today"],
            priority="A",
        )
        leads.append(lead)

    return leads[: profile.max_leads]


def score_lead(lead: JobLead, profile: ApplicantProfile) -> tuple[int, list[str]]:
    haystack = " ".join([lead.title, lead.company, lead.location, lead.description]).lower()
    score = 0
    notes: list[str] = []

    for title in profile.target_titles:
        if title.lower() in haystack:
            score += 18
            notes.append(f"title match: {title}")
            break

    for location in profile.target_locations:
        if location.lower() in haystack:
            score += 12
            notes.append(f"location match: {location}")
            break

    positive_hits = [word for word in profile.positive_keywords if word.lower() in haystack]
    if positive_hits:
        score += min(40, len(positive_hits) * 6)
        notes.append("keyword fit: " + ", ".join(positive_hits[:6]))

    negative_hits = [word for word in profile.negative_keywords if word.lower() in haystack]
    if negative_hits:
        score -= min(35, len(negative_hits) * 10)
        notes.append("possible mismatch: " + ", ".join(negative_hits[:4]))

    if lead.salary_min or lead.salary_max:
        score += 4
        notes.append("salary data included")

    if any(word in haystack for word in ["supervisor", "lead", "captain", "manager"]):
        score += 8
        notes.append("leadership path")

    return max(score, 0), notes


def priority_for_score(score: int) -> str:
    if score >= 70:
        return "A"
    if score >= 45:
        return "B"
    return "C"


def write_tracker(leads: list[JobLead], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    tracker_path = output_dir / "applications.csv"
    fieldnames = TRACKER_FIELDS

    existing: dict[str, dict[str, str]] = {}
    if tracker_path.exists():
        with tracker_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if not row.get("lead_id"):
                    continue
                upgraded = {field: row.get(field, "") for field in fieldnames}
                existing[row["lead_id"]] = upgraded

    for lead in leads:
        existing.setdefault(lead.lead_id, {key: str(value) for key, value in lead.as_row().items()})

    with tracker_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing.values())

    return tracker_path


def write_drafts(leads: list[JobLead], profile: ApplicantProfile, output_dir: Path) -> Path:
    drafts_dir = output_dir / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    for lead in leads:
        path = drafts_dir / f"{lead.priority}_{lead.score:03d}_{slugify(lead.company)}_{lead.lead_id}.md"
        path.write_text(build_application_draft(lead, profile), encoding="utf-8")
    return drafts_dir


def build_application_draft(lead: JobLead, profile: ApplicantProfile) -> str:
    strengths = "\n".join(f"- {item}" for item in profile.strengths)
    return textwrap.dedent(
        f"""
        # Application Draft: {lead.title} at {lead.company}

        **Apply/search link:** {lead.url}
        **Location:** {lead.location}
        **Priority:** {lead.priority}
        **Score:** {lead.score}/100-ish
        **Why it matched:** {'; '.join(lead.score_notes) or 'General fit'}
        **Resume path:** {profile.resume_path}

        ## Short message / cover note

        Hi {lead.company} team,

        I'm applying for the {lead.title} role. I have strong restaurant and theater-hospitality
        experience, including service in a high-expectation guest environment, and I can step into
        either a serving role or a lead/supervisory role where reliability, pace, teamwork, and guest
        recovery matter. {profile.experience_summary}

        A few things I would bring to your team:
        {strengths}

        I would appreciate the chance to interview and show how quickly I can contribute.

        Thank you,
        {profile.name}
        {profile.phone} | {profile.email}

        ## Fast-apply checklist

        - Upload the resume from: `{profile.resume_path}`.
        - If the site accepts a cover note, paste the short message above and make it specific to this company.
        - If it asks why you left iPic, keep it short: bankruptcy/restructuring reduced your opportunity, and you want a stable restaurant team.
        - After submitting, set `status=applied`, fill `date_applied`, and set `follow_up_date` for 3 to 5 business days later.
        - If this is a target restaurant but no posting is visible, call or visit during a slow time and ask for the hiring manager.

        ## Resume tailoring checklist

        - Put your strongest serving/guest-service experience in the top third of the resume.
        - Mention supervisory duties if this posting includes lead, trainer, captain, shift lead, or manager language.
        - Add restaurant POS, wine/cocktail, premium guest service, conflict resolution, upselling, and closing/opening duties if true.
        - Save the final resume as a PDF before uploading.

        ## Interview prep notes

        - Reliability story: explain that you show up, pick up shifts, and do not leave the team short.
        - Rush story: describe a busy service rush where you stayed calm, helped teammates, and protected guest experience.
        - Supervisor story: explain how you coached, covered stations, handled guest issues, or helped managers keep service moving.
        """
    ).strip() + "\n"


def write_campaign_plan(leads: list[JobLead], profile: ApplicantProfile, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today()
    plan_path = output_dir / "today_application_plan.md"
    top_leads = "\n".join(
        f"{index}. **{lead.company}** — {lead.title} — [{lead.source}]({lead.url})"
        for index, lead in enumerate(leads[:15], start=1)
    )
    plan_path.write_text(
        textwrap.dedent(
            f"""
            # Application plan for {today.isoformat()}

            Goal: submit 10 quality applications today and create follow-up tasks for each one.

            ## 60-minute sprint

            1. Open your resume: `{profile.resume_path}`.
            2. Export it as a PDF if you only have a `.docx` version.
            3. Open the first 10 links below.
            4. Apply to any real server, bartender, lead server, trainer, shift lead, or restaurant supervisor opening.
            5. Update `applications.csv` with `status=applied`, today's date, and a follow-up date 3 to 5 business days out.

            ## First links to open

            {top_leads}

            ## Phone / in-person script

            Hi, my name is {profile.name}. I'm an experienced server with premium hospitality experience at iPic.
            I'm looking for a server, lead server, trainer, or shift lead role in the area. Are you hiring right now,
            and is there a best manager or application link I should send my resume to?

            ## Follow-up message

            Hi, this is {profile.name}. I applied for a serving/lead server role earlier this week and wanted to follow up.
            I have strong guest-service experience, I'm reliable, and I can interview or stage whenever is convenient.
            My number is {profile.phone}.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return plan_path


def write_profile_template(path: Path, overwrite: bool = False) -> Path:
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists. Use --force to overwrite it.")
    path.write_text(build_profile_template(), encoding="utf-8")
    return path


def build_profile_template() -> str:
    companies = "\n".join(f'  - "{company}"' for company in DEFAULT_TARGET_COMPANIES)
    return f"""# Private file. Fill in email/phone before applying.
name: "Dylan Zimmerman"
email: "your_email@example.com"
phone: "your phone number"
city: "San Fernando Valley, CA"
resume_path: "{DEFAULT_RESUME_PATH}"

experience_summary: >
  My recent iPic Theaters experience gave me premium guest-service, serving, teamwork,
  and problem-solving experience in a fast-paced hospitality setting. I am looking for
  a stable restaurant team where I can serve, support coworkers, and grow into lead or
  supervisory responsibility.

strengths:
  - "Hard-working, reliable, and willing to pick up shifts when the team needs help."
  - "Experienced with high-touch guest service, handling rushes, and staying calm under pressure."
  - "Comfortable helping lead a shift, supporting coworkers, and taking responsibility for guest experience."
  - "Interested in serving, lead server, trainer, captain, shift lead, or restaurant supervisor opportunities."

target_titles:
  - "server"
  - "restaurant server"
  - "lead server"
  - "server supervisor"
  - "shift lead restaurant"
  - "restaurant supervisor"
  - "food runner"
  - "bartender"

target_locations:
  - "San Fernando Valley, CA"
  - "Sherman Oaks, CA"
  - "Studio City, CA"
  - "Burbank, CA"
  - "Glendale, CA"
  - "Calabasas, CA"
  - "Woodland Hills, CA"
  - "Thousand Oaks, CA"
  - "Westlake Village, CA"
  - "Agoura Hills, CA"

target_companies:
{companies}

positive_keywords:
  - "server"
  - "restaurant"
  - "hospitality"
  - "guest service"
  - "fine dining"
  - "upscale"
  - "premium"
  - "tips"
  - "supervisor"
  - "lead"
  - "trainer"
  - "shift lead"
  - "team"
  - "wine"
  - "cocktail"
  - "POS"

negative_keywords:
  - "cook"
  - "dishwasher"
  - "delivery driver"
  - "warehouse"
  - "commission only"
  - "temporary"
  - "volunteer"

minimum_score: 35
results_per_query: 20
max_leads: 50
"""


def open_top_links(leads: list[JobLead], limit: int) -> None:
    for lead in leads[:limit]:
        if lead.url:
            webbrowser.open(lead.url)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find, score, and organize restaurant job applications.")
    parser.add_argument("--profile", default=DEFAULT_PROFILE, help="Path to your YAML applicant profile.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Directory for leads, drafts, and tracker CSV.")
    parser.add_argument("--country", default="us", help="Adzuna country code. Default: us.")
    parser.add_argument("--pages", type=int, default=1, help="Adzuna result pages per title/location query.")
    parser.add_argument("--open", type=int, default=0, help="Open the top N application/search links in your browser.")
    parser.add_argument(
        "--source",
        choices=["auto", "adzuna", "targets", "both"],
        default="auto",
        help="Lead source. auto uses Adzuna when credentials exist, otherwise target links.",
    )
    parser.add_argument(
        "--init-profile",
        action="store_true",
        help="Create a ready-to-edit job_profile.yaml for Dylan's restaurant search.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite files created by --init-profile.")
    return parser.parse_args(argv)


def collect_leads(profile: ApplicantProfile, source: str, country: str, pages: int) -> tuple[list[JobLead], list[str]]:
    warnings: list[str] = []
    leads: list[JobLead] = []

    resolved_source = source
    if source == "auto":
        resolved_source = "adzuna" if has_adzuna_credentials() else "targets"
        if resolved_source == "targets":
            warnings.append("Adzuna credentials were not set, so I built target/search links you can use immediately.")

    if resolved_source in {"targets", "both"}:
        leads.extend(build_target_leads(profile))

    if resolved_source in {"adzuna", "both"}:
        try:
            leads.extend(fetch_adzuna_jobs(profile, country, pages))
        except RuntimeError as exc:
            if resolved_source == "both":
                warnings.append(str(exc))
            else:
                raise

    unique: dict[str, JobLead] = {}
    for lead in leads:
        unique.setdefault(lead.lead_id, lead)
    return sorted(unique.values(), key=lambda lead: lead.score, reverse=True)[: profile.max_leads], warnings


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    profile_path = Path(args.profile)

    if args.init_profile:
        created_path = write_profile_template(profile_path, overwrite=args.force)
        print(f"Created profile template: {created_path}")
        print("Next: edit email/phone if needed, then run `python job_hunter.py --source targets --open 10`.")
        return 0

    profile = ApplicantProfile.from_file(profile_path)
    output_dir = Path(args.output)

    leads, warnings = collect_leads(profile, args.source, args.country, args.pages)
    tracker_path = write_tracker(leads, output_dir)
    drafts_dir = write_drafts(leads, profile, output_dir)
    plan_path = write_campaign_plan(leads, profile, output_dir)

    if args.open:
        open_top_links(leads, args.open)

    for warning in warnings:
        print(f"Warning: {warning}")
    print(f"Found {len(leads)} application targets/leads.")
    print(f"Tracker: {tracker_path}")
    print(f"Drafts: {drafts_dir}")
    print(f"Today's plan: {plan_path}")
    if leads:
        print("\nTop matches:")
        for lead in leads[:10]:
            print(f"- {lead.priority} | {lead.score:3d} | {lead.title} | {lead.company} | {lead.location}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
