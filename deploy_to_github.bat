@echo off
echo 🚀 FinTrace GitHub Deployment Script
echo ======================================

echo.
echo 📁 Current directory: %CD%
echo.

echo 🔍 Checking if git is initialized...
if not exist ".git" (
    echo ❌ Git repository not found. Initializing...
    git init
    echo ✅ Git repository initialized
) else (
    echo ✅ Git repository already exists
)

echo.
echo 📝 Adding all files to git...
git add .

echo.
echo 💾 Committing changes...
git commit -m "Update FinTrace AML Dashboard - %date% %time%"

echo.
echo 🔗 Checking remote origin...
git remote -v

if %errorlevel% neq 0 (
    echo.
    echo ⚠️  No remote origin found.
    echo 📋 Please run the following command manually:
    echo    git remote add origin https://github.com/YOUR_USERNAME/FINTRACE_REPO_NAME.git
    echo.
    echo 📋 Then run:
    echo    git push -u origin main
    echo.
    pause
    exit /b 1
)

echo.
echo 🚀 Pushing to GitHub...
git push

echo.
echo ✅ Deployment completed!
echo.
echo 📋 Next steps:
echo    1. Check your GitHub repository
echo    2. Verify all files are uploaded
echo    3. Check GitHub Actions for test results
echo.
pause
