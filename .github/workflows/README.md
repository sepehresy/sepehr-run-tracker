# GitHub Actions Workflows

## Auto Wake on Push

### Purpose
This workflow automatically keeps your Streamlit app deployed on cloud platforms (like Streamlit Cloud) from going to sleep due to inactivity.

### How it works
- **Daily Schedule**: Runs automatically every day at 2:00 AM UTC
- **Push Trigger**: Also runs when the `.wake-trigger` file is modified
- **Action**: Updates the `.wake-trigger` file with a timestamp and commit info
- **Commit**: Makes an automated commit to trigger Streamlit app redeployment
- **Result**: Keeps your Streamlit app active and prevents it from sleeping

### Files
- `auto-wake-on-push.yml`: The main and only workflow file
- `.wake-trigger`: File that tracks wake-up events and triggers the workflow

### Automatic Operation
The workflow runs completely automatically:
- **Daily at 2:00 AM UTC**: Scheduled automatic execution
- **No manual intervention needed**: Fully automated system
- **Reliable**: Proven working solution

### Manual Wake-Up (Optional)
If you need to wake your app immediately:

```bash
# Method 1: Update the wake trigger file
echo "Manual wake - $(date)" > .wake-trigger
git add .wake-trigger
git commit -m "Wake up Streamlit app"
git push

# Method 2: Simple touch and push
echo "Wake up now" > .wake-trigger && git add . && git commit -m "Manual wake" && git push
```

### Customization
To change the schedule, modify the cron expression in `auto-wake-on-push.yml`:
```yaml
- cron: '0 2 * * *'  # Currently 2:00 AM UTC daily
```

Common alternatives:
- `0 0 * * *` - Daily at midnight UTC
- `0 12 * * *` - Daily at noon UTC  
- `0 0 * * 1` - Weekly on Mondays at midnight UTC

### Benefits
- ✅ **Fully automated** - No manual intervention required
- ✅ **Dual triggers** - Both scheduled and on-demand
- ✅ **Minimal footprint** - Only affects the `.wake-trigger` file
- ✅ **Proven working** - Successfully tested and operational
- ✅ **Clean setup** - Single workflow handles everything
- ✅ **Streamlit app stays active** - Never goes to sleep 