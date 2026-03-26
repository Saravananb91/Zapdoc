@echo off
TITLE OCR Agent - Public Sharing
CLS

echo ========================================================
echo        OCR AGENT - PUBLIC SHARING (via Localtunnel)
echo ========================================================
echo.
echo This script will open two windows to share your local ports.
echo You will need to copy the URLs provided in those windows.
echo.
echo 1. Backend Tunnel (Port 8000)
echo 2. Frontend Tunnel (Port 3000)
echo.
echo NOTE: Localtunnel may ask for a password or IP check.
echo If asked, use the IP provided on their website.
echo.
pause

echo.
echo Lunching Backend Tunnel...
start "Backend Tunnel (8000)" cmd /k "npx localtunnel --port 8000"

echo.
echo Lunching Frontend Tunnel...
start "Frontend Tunnel (3000)" cmd /k "npx localtunnel --port 3000"

echo.
echo ========================================================
echo                 INSTRUCTIONS
echo ========================================================
echo 1. Copy the URL from the "Backend Tunnel" window (e.g., https://blue-cat-42.loca.lt)
echo 2. Open "frontend/.env" file.
echo 3. Update VITE_API_URL=[Backend URL]
echo 4. Restart your frontend server (Ctrl+C, then npm run dev)
echo 5. Share the URL from the "Frontend Tunnel" window with your user.
echo.
echo Press any key to exit this launcher (tunnels will stay open).
pause
