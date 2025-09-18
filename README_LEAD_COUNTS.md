# LinkedIn Crawler - Lead Counts Feature

This document explains the lead counting functionality added to the LinkedIn Crawler application.

## Overview

The lead counting feature allows you to view the total number of leads collected for each search template. This helps track the effectiveness of different search templates and monitor the overall lead collection progress.

## Features

1. **Lead Count Display**: A dedicated page showing the number of leads collected for each template, sorted by count in descending order.

2. **Automatic Updates**: A Python script that can be run to update the lead counts based on the current data files.

3. **Navigation**: Easy access from the main application via the navigation bar.

## How to Use

### Viewing Lead Counts

1. Open the LinkedIn Crawler application in your browser.
2. Click on the "Lead Counts" link in the navigation bar at the top of the page.
3. The lead counts page will display a table with all templates and their respective lead counts.

### Updating Lead Counts

To update the lead counts with the latest data:

```bash
python3 update_lead_counts.py
```

This script will:
- Count leads from all JSON files in both the `data/` and `db/` directories
- Update the `lead_counts.html` file with the latest counts
- Display a summary of the counts in the terminal

### One-time Count

If you just want to see the counts without updating the HTML file:

```bash
python3 count_leads.py
```

## How It Works

The lead counting functionality works by:

1. Scanning all JSON files in the `data/` and `db/` directories
2. Extracting template names from filenames
3. Counting the number of leads in each file
4. Aggregating counts by template name
5. Displaying the results in a sorted table

## Files

- `count_leads.py`: Script to count leads and display results in the terminal
- `update_lead_counts.py`: Script to count leads and update the HTML display
- `lead_counts.html`: Web page displaying the lead counts in a formatted table

## Automation

You can set up a cron job or scheduled task to run `update_lead_counts.py` periodically to keep the lead counts up to date.

Example cron job (runs daily at midnight):

```
0 0 * * * cd /path/to/linkedin-crawler && python3 update_lead_counts.py
```