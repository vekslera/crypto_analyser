# Data Recovery Options for crypto_analyser.db

## Current Situation
- Database accidentally cleared, now has only ~2 recent records
- Previous database had **6,281+ records** with comprehensive historical coverage
- Database file removed from Git tracking, so no Git history available

## Recovery Options (in order of preference)

### Option 1: OneDrive Version History (RECOMMENDED)
Since this project is in OneDrive, check for file version history:

1. **Right-click** on `data/crypto_analyser.db` in Windows Explorer
2. Click **"Version history"** or **"Restore previous versions"**
3. Look for versions from before the data was cleared (before today)
4. Restore the most recent version with larger file size

### Option 2: Windows File History / Shadow Copies
If OneDrive versioning doesn't work:

1. **Right-click** on `data/crypto_analyser.db` 
2. Click **"Properties"** → **"Previous Versions"** tab
3. Look for shadow copies from earlier today or yesterday
4. Restore a previous version

### Option 3: Use Gap Filling to Rebuild Historical Data
Use our new gap filling system to rebuild from CoinGecko API:

```bash
# Start the server (if not running)
python -m server.api_server

# Use the GUI "Fill Data Gaps" button, or use API directly:
curl -X POST "http://localhost:8000/data/fill-gaps"
```

**Note:** This will rebuild data but may not match exactly the previous database.

### Option 4: Check Temporary/Backup Files
Look for any temporary copies:

```bash
# Search for any .db files
dir /s *.db

# Check Windows temp folders
dir /s crypto_analyser.db C:\Windows\Temp\
dir /s crypto_analyser.db %TEMP%\
```

## Recommendation
**Try Option 1 (OneDrive Version History) first** - this is most likely to recover your exact data since OneDrive automatically versions files in real-time.

If that fails, Option 2 (Windows File History) is the next best choice.

Only use Option 3 (Gap Filling) as a last resort, as it will rebuild data but won't be identical to what you had.