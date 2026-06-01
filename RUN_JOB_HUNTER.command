#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

echo ""
echo "=============================================="
echo " Restaurant Job Hunter - one-click launcher"
echo "=============================================="
echo ""
echo "This will create your private profile if needed, install Python packages,"
echo "then open restaurant job/application links in your browser."
echo ""

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Python was not found. Install Python 3 from https://www.python.org/downloads/ and run this again."
  read -r -p "Press Return to close this window... "
  exit 1
fi

echo "Using Python: $($PYTHON_BIN --version)"
echo ""
echo "Installing required packages..."
$PYTHON_BIN -m pip install -r requirements.txt

if [ ! -f job_profile.yaml ]; then
  echo ""
  echo "Creating your private job_profile.yaml..."
  $PYTHON_BIN job_hunter.py --init-profile
fi

echo ""
echo "IMPORTANT: job_profile.yaml needs your real email and phone number."
echo "I am opening it now. Fill those in, save the file, then come back here."
echo ""

if command -v open >/dev/null 2>&1; then
  open job_profile.yaml || true
else
  echo "Open job_profile.yaml manually and fill in email/phone before applying."
fi

read -r -p "After you save job_profile.yaml, press Return here to open job links... "

echo ""
echo "Building today's application packet and opening the first 10 links..."
$PYTHON_BIN job_hunter.py --source targets --open 10

echo ""
echo "Opening your application tracker and today's plan..."
if command -v open >/dev/null 2>&1; then
  open job_leads/today_application_plan.md || true
  open job_leads/applications.csv || true
fi

echo ""
echo "Done. Apply in the browser tabs that opened, then mark each application in job_leads/applications.csv."
read -r -p "Press Return to close this window... "
