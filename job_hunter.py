"""Job search assistant for restaurant/service roles.

This tool finds matching job listings through the Adzuna Jobs API, scores them against
an applicant profile, creates application-tracking CSV files, and writes tailored
application notes the applicant can review before submitting.

It intentionally does not auto-submit applications. Many job boards prohibit bots,
and restaurant roles often ask business-specific screening questions. Human review
keeps applications accurate and avoids violating site terms.
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
from urllib.parse import urlparse

import requests
import yaml

ADZUNA_SEARCH_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
DEFAULT_PROFILE = "job_profile.yaml"
DEFAULT_OUTPUT_DIR = "job_leads"


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
    minimum_score: int = 35
    results_per_query: int = 20
    max_leads: int = 50

    @classmethod
    def from_file(cls, path: Path) -> "ApplicantProfile":
        if not path.exists():
            raise FileNotFoundError(
                f"Profile file not found: {path}. Copy job_profile.example.yaml to {path} and fill it in."
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

    def as_row(self) -> dict[str, str | int]:
        return {
            "lead_id": self.lead_id,
            "date_found": dt.date.today().isoformat(),
            "status": "found",
            "score": self.score,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "source": self.source,
            "url": self.url,
            "score_notes": "; ".join(self.score_notes),
            "next_step": "Review posting, tailor resume if needed, then apply through the official link.",
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


def require_adzuna_credentials() -> tuple[str, str]:
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        raise RuntimeError(
            "Set ADZUNA_APP_ID and ADZUNA_APP_KEY first. Register for API credentials at "
            "https://developer.adzuna.com/."
        )
    return app_id, app_key


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


def write_tracker(leads: list[JobLead], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    tracker_path = output_dir / "applications.csv"
    fieldnames = list(JobLead("", "", "", "", "", "", "", "").as_row().keys())

    existing: dict[str, dict[str, str]] = {}
    if tracker_path.exists():
        with tracker_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                existing[row["lead_id"]] = row

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
        path = drafts_dir / f"{lead.score:03d}_{lead.lead_id}.md"
        path.write_text(build_application_draft(lead, profile), encoding="utf-8")
    return drafts_dir


def build_application_draft(lead: JobLead, profile: ApplicantProfile) -> str:
    strengths = "\n".join(f"- {item}" for item in profile.strengths)
    return textwrap.dedent(
        f"""
        # Application Draft: {lead.title} at {lead.company}

        **Apply link:** {lead.url}
        **Location:** {lead.location}
        **Score:** {lead.score}/100-ish
        **Why it matched:** {'; '.join(lead.score_notes) or 'General fit'}

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

        ## Resume tailoring checklist

        - Put your strongest serving/guest-service experience in the top third of the resume.
        - Mention supervisory duties if this posting includes lead, trainer, captain, shift lead, or manager language.
        - Add restaurant POS, wine/cocktail, premium guest service, conflict resolution, upselling, and closing/opening duties if true.
        - Save the final resume as a PDF before uploading.

        ## Interview prep notes

        - Why are you leaving iPic? Keep it short: bankruptcy/restructuring reduced your opportunity, and you want a stable restaurant team.
        - Best strength story: describe a busy service rush where you stayed calm, helped teammates, and protected guest experience.
        - Supervisor story: explain how you coached, covered stations, handled guest issues, or helped managers keep service moving.
        """
    ).strip() + "\n"


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
    parser.add_argument("--open", type=int, default=0, help="Open the top N application links in your browser.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    profile = ApplicantProfile.from_file(Path(args.profile))
    output_dir = Path(args.output)

    leads = fetch_adzuna_jobs(profile, args.country, args.pages)
    tracker_path = write_tracker(leads, output_dir)
    drafts_dir = write_drafts(leads, profile, output_dir)

    if args.open:
        open_top_links(leads, args.open)

    print(f"Found {len(leads)} matching leads.")
    print(f"Tracker: {tracker_path}")
    print(f"Drafts: {drafts_dir}")
    if leads:
        print("\nTop matches:")
        for lead in leads[:10]:
            print(f"- {lead.score:3d} | {lead.title} | {lead.company} | {lead.location}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
