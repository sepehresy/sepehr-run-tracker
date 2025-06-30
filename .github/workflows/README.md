# GitHub Actions Workflows

## Daily Auto Commit

### Purpose
This workflow automatically makes a daily commit to keep your Streamlit app deployed on cloud platforms (like Streamlit Cloud) from going to sleep due to inactivity.

### How it works
- **Schedule**: Runs daily at 2:00 AM UTC
- **Action**: Updates the `.auto-commit-tracker` file with a timestamp
- **Commit**: Makes an automated commit with a clear message indicating it's for app maintenance
- **Manual Trigger**: Can also be manually triggered from the GitHub Actions tab

### Files
- `daily-commit-clean.yml`: The main workflow file

### What it creates
- `.auto-commit-tracker`: A small file that tracks when the last auto-commit happened

### Customization
To change the schedule, modify the cron expression in the workflow file:
```yaml
- cron: '0 2 * * *'  # Currently 2:00 AM UTC daily
```

Common cron schedules:
- `0 0 * * *` - Daily at midnight UTC
- `0 12 * * *` - Daily at noon UTC  
- `0 0 * * 1` - Weekly on Mondays at midnight UTC

### Manual Trigger
You can manually trigger the workflow:
1. Go to your repository on GitHub
2. Click on "Actions" tab
3. Select "Daily Auto Commit (Clean Version)"
4. Click "Run workflow"

### Benefits
- Keeps your Streamlit app active and prevents it from sleeping
- Minimal impact on your codebase (only affects a dedicated tracker file)
- Clear commit messages for easy identification
- No impact on your main application files 