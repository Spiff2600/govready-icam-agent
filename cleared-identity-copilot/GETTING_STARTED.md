# Getting Started Guide — Cleared Identity Co-Pilot

> **Plain-English guide for first-time users.**  
> No programming experience required to run the demo. If you can install an app and type a command, you can do this.

---

## What is this program?

**Cleared Identity Co-Pilot** is a web app that runs on your computer and opens in your browser — just like a website, but offline.  
It shows a pretend federal agency's security problems (fake data, nobody is real) and lets an AI called **Claude** help explain what's risky and what to fix.

Think of it like a security report viewer with an AI assistant built in.

---

## What you need before you start

| Thing | Why you need it | Free? |
|-------|----------------|-------|
| A computer running **Windows, Mac, or Linux** | To run the app | — |
| **Python 3.11 or newer** | The app is built in Python | ✅ Yes |
| **A terminal (command-line window)** | To type a few install commands | ✅ Built in |
| **An Anthropic API key** *(optional)* | To ask Claude real questions | Free trial available |

> **Don't have an API key?** No problem — the app works without one and shows you pre-loaded example AI output automatically.

---

## Step 1 — Check if Python is installed

Open a terminal:

- **Mac:** press `Command + Space`, type `Terminal`, press `Enter`
- **Windows:** press `Windows key`, type `cmd`, press `Enter`
- **Linux:** look for "Terminal" in your apps

Type this and press `Enter`:

```bash
python --version
```

You should see something like `Python 3.11.9`. If it says `3.11` or higher, you're good!

If you see an error or a version lower than 3.11, download Python from **https://python.org/downloads** and install it. Come back here when done.

---

## Step 2 — Navigate to the project folder

In the same terminal window, type these commands one at a time (press `Enter` after each):

```bash
cd /path/to/caib
```

> Replace `/path/to/caib` with wherever you saved or downloaded this repository.  
> For example: `cd C:\Users\YourName\Downloads\caib` on Windows, or `cd ~/Downloads/caib` on Mac.

---

## Step 3 — Create a virtual environment

A "virtual environment" is a clean space just for this app's software. It keeps things tidy. Type:

```bash
python -m venv .venv
```

Then **activate** it:

**Mac / Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```cmd
.venv\Scripts\activate
```

Your terminal prompt will now start with `(.venv)` — that means it worked!

---

## Step 4 — Install the app's requirements

This downloads all the pieces the app needs (like streamlit, plotly, etc.). Type:

```bash
pip install -r cleared-identity-copilot/requirements.txt
```

This may take 1–3 minutes. You'll see a list of things being downloaded. That's normal.

---

## Step 5 — (Optional) Add your Anthropic API key

If you have an Anthropic API key and want Claude to answer questions live:

```bash
cp cleared-identity-copilot/.env.example cleared-identity-copilot/.env
```

Then open the file `cleared-identity-copilot/.env` in any text editor and change this line:

```
ANTHROPIC_API_KEY=your_key_here
```

to your real key, for example:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Save the file and close it.

> **No API key?** Skip this step entirely — the app will show a yellow banner saying "No API key - showing cached example output" and everything still works.

---

## Step 6 — Launch the app

Type this and press `Enter`:

```bash
streamlit run cleared-identity-copilot/app.py
```

After a few seconds you'll see:

```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

Your browser should open automatically. If it doesn't, open your browser and go to:

**http://localhost:8501**

---

## You're in! Here's what you'll see

The app has **6 tabs** along the top. Here's what each one does:

---

### Tab 1 — Customer Overview

![Customer Overview tab shows the fictional agency, cloud footprint table, MFA distribution pie chart, and 4 risk metric cards]

**What it shows:**  
The fictional customer "Orion Federal Analytics Agency" — their cloud systems, the security problems they have, and a summary of how many people are at risk.

**Things to look at:**
- The red warning banner at the top — this reminds you all data is fake
- The pie chart showing how people log in (some use weak SMS text-message codes)
- The four numbers at the bottom: Critical users, High-risk accounts, Weak MFA, Unowned accounts

---

### Tab 2 — Identity Exposure Graph

**What it shows:**  
A visual map (a "graph") of every fake user, their role, and how they connect to cloud systems. Big red dots = most dangerous accounts.

**Things to do:**
- **Hover your mouse** over any colored dot to see who it is and their risk score
- Use the **sidebar on the left** to filter by risk level (try unchecking LOW and MED to see only the risky ones)
- Check the **"Highlight cross-cloud admins"** box to see who has admin power in both Microsoft Azure and Amazon AWS — the most dangerous combination

**Color code:**
- 🔴 Red = CRITICAL risk
- 🟠 Orange = HIGH risk  
- 🟡 Yellow = MEDIUM risk
- 🟢 Green = LOW risk

---

### Tab 3 — Claude Analysis *(the AI tab)*

**What it shows:**  
This is where Claude (the AI) looks at the fake data and tells you what's wrong.

**How to use it:**

1. There's a text box with a pre-written question: *"Identify the top identity risks and provide evidence-based recommendations"*  
   — Leave it as-is, or type your own question
2. Choose a Claude model from the dropdown (start with `claude-sonnet-4-5`)
3. Click the **"Run Analysis"** button
4. Wait a few seconds (or instantly if no API key — it uses the cached example)

**What you'll see after clicking:**

- **Yellow banner** (if no API key): "No API key - showing cached example output." — that's fine, continue reading
- **Tool Call Trace** — expandable items showing every "tool" Claude used to look up data. Click the arrows to see what information Claude fetched and what it found
- **Analysis** — Claude's written explanation of the risks, in plain English
- **Structured Output** — the same findings in computer-readable JSON format
- **Token/Cost meter** — shows how many words were processed and the estimated cost if you have an API key
- **Human Approval Gate** (if Claude recommends actions) — buttons to Approve, Reject, or Modify any suggestion. **Nothing happens automatically — you must click Approve first.**

> 💡 **Try asking:** `"Explain why Diana Reyes is high risk"` or `"What happened with Tamara Osei?"`

---

### Tab 4 — Executive Brief

**What it shows:**  
A summary written for a manager or executive — no technical jargon.

**How to use it:**
1. Click the **"Generate Executive Brief"** button
2. Wait a moment
3. You'll see:
   - A short paragraph summarizing the risk (the "CIO Summary")
   - A risk posture table
   - A **30/60/90 day plan** — what to fix in the next 30 days, 60 days, and 90 days

---

### Tab 5 — Technical Remediation

**What it shows:**  
Step-by-step fix instructions for each risky user, plus general guidance for both Microsoft Azure and Amazon AWS.

**Things to look at:**
- Scroll through the user cards — each shows a risk badge, risk factors, and exactly what to do
- Below the user cards, there are sections for **Azure-specific** and **AWS-specific** fixes
- At the bottom, there's a **"Download Remediation Report"** button to save the findings as a file

---

### Tab 6 — Evals *(the AI grading tab)*

**What it shows:**  
A set of 15 test questions that can be used to grade how well different AI models perform on this task.

> ⚠️ **Warning shown in the app:** Running evals with a real API key costs real money. Each eval run calls Claude many times. Only click "Run Evals" if you understand this.

**Without an API key:** You can see the 15 test questions in the table, but the "Run Evals" button won't produce results (it needs a live API connection).

**With an API key:**
1. Choose a model or "Run All Models" from the dropdown
2. Click **"Run Evals"**
3. A progress bar will appear while the 15 questions are tested
4. Results show Pass Rate, Average Latency, and Total Cost per model

---

## How to stop the app

Go back to your terminal window and press **`Ctrl + C`** (hold Control and press C). The app will stop.

---

## How to start it again next time

You only need to repeat Steps 3 (activate), and 6 (run):

```bash
# Navigate to project folder
cd /path/to/caib

# Activate virtual environment
source .venv/bin/activate     # Mac/Linux
# OR
.venv\Scripts\activate        # Windows

# Launch
streamlit run cleared-identity-copilot/app.py
```

---

## Frequently Asked Questions

**Q: I see "No API key - showing cached example output." Is something broken?**  
A: No! The app is working correctly. It's showing pre-saved AI output. To get live Claude responses, add your API key to `cleared-identity-copilot/.env` (see Step 5).

**Q: The browser didn't open automatically.**  
A: Open your browser and type `http://localhost:8501` in the address bar.

**Q: I get a "command not found" error for `python`.**  
A: Try `python3` instead of `python`. On some systems Python 3 is called `python3`.

**Q: Can I break anything by clicking around?**  
A: No. All data is fake. Nothing connects to real systems. Click freely.

**Q: What is the "Human Approval Gate" for?**  
A: It's a safety feature. Claude can suggest actions (like "remove this user's admin access"), but it cannot actually do anything — it can only suggest. You have to click "Approve" to log that you agreed. In a real system, that approval would trigger the actual change. Here it just logs your decision.

**Q: Is any of this data real?**  
A: No. Every name, agency, account, finding, and recommendation is 100% fictional and created for demonstration purposes only.

---

## 5-Minute Demo Walkthrough

If you want to show this to someone else, here's a quick script:

| Time | What to do | What to say |
|------|-----------|-------------|
| 0:00 | Open Tab 1: Customer Overview | "This is a fictional federal agency with a hybrid cloud — Azure and AWS. Look at the risk numbers — 5 critical accounts." |
| 1:00 | Click Tab 2: Identity Exposure Graph | "This graph shows every user and how they connect to cloud systems. The big red dots are the most dangerous accounts." |
| 1:30 | Filter sidebar to CRITICAL + HIGH only | "Let's focus on just the serious ones. See how 4 people have admin access in both Azure and AWS simultaneously?" |
| 2:00 | Click Tab 3: Claude Analysis | "Now I'll ask Claude to analyze the risks." Click Run Analysis. |
| 2:30 | Expand a tool call in the trace | "See this? Claude fetched data using tools — it didn't make anything up. Every finding cites a real tool call." |
| 3:30 | Scroll to Human Approval Gate | "Claude can recommend actions but can't do anything automatically. A human has to approve every step." |
| 4:00 | Click Tab 4: Executive Brief | "One click generates a CIO-ready summary and a 30/60/90 day roadmap." |
| 4:30 | Click Tab 5: Technical Remediation | "Each person gets specific fix instructions. Azure and AWS teams each get their own guidance section." |
| 5:00 | Click Tab 6: Evals | "Finally, we can grade how well the AI performs across 15 test questions and compare models by cost and accuracy." |

---

*All identities, agency names, cloud tenants, and findings in this demo are entirely fictional.*
