@echo off
echo Cleaning Next.js cache...
cd frontend
if exist .next (
    rmdir /s /q .next
    echo Deleted .next folder
)
if exist node_modules\.cache (
    rmdir /s /q node_modules\.cache
    echo Deleted node_modules\.cache folder
)
echo Cache cleaned! Now run: npm run dev
pause
