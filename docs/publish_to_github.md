# Publish to GitHub (Windows PowerShell)

1. Install Git and Python 3.10+ if needed; sign in to GitHub.
2. Extract the project ZIP and open a terminal inside `customer-journey-analytics`.
3. Run the README quick start commands and confirm tests pass.
4. Create a **new empty public repository** named `customer-journey-analytics` on GitHub. Do not initialize it with a README, license or `.gitignore` (they are included here).
5. From the project root run:

```powershell
git init
git add .
git commit -m "Initial portfolio project: customer analytics and churn prediction"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/customer-journey-analytics.git
git push -u origin main
```

If Git requests credentials, authenticate with Git Credential Manager or GitHub CLI (`gh auth login`); GitHub account passwords are not used for HTTPS Git operations. Replace `YOUR_USERNAME` with your actual GitHub username.

## Make the repository recruiter-friendly
- Add `outputs/segments.png` as `docs/segments.png` if you want a chart preview tracked in Git; add it to the README.
- Build a Power BI report using `docs/powerbi_guide.md`, take screenshots and add them to `docs/`.
- In GitHub repo settings, add a short description and topics: `python`, `customer-analytics`, `churn-prediction`, `rfm`, `cohort-analysis`, `sql`, `power-bi`.
- Pin the repository on your GitHub profile and link it on your CV.
