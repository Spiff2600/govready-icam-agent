# 5-Minute Demo Script

## 1. Open the app

- Run `streamlit run cleared-identity-copilot/app.py`.
- Land on **Customer Overview**.
- Point out the red synthetic-data banner and explain that all content is fictional.

## 2. Show the customer problem

- In **Customer Overview**, call out weak MFA, standing privilege, stale access, and unowned service accounts.
- Highlight the MFA pie chart and risk metrics.

## 3. Visualize cross-cloud exposure

- Click **Identity Exposure Graph**.
- Use the sidebar to filter for `CRITICAL` and `HIGH`.
- Turn on **Highlight cross-cloud admins** and hover on Diana Reyes or Sandra Okafor to show why those nodes are larger and red.

## 4. Show Claude tool use and reasoning

- Open **Claude Analysis**.
- Keep the default question or ask: `Analyze Tamara Osei's access profile and explain the anomaly.`
- Click **Run Analysis**.
- Expand the tool trace to show deterministic tool inputs and outputs.
- Scroll to the structured output and human approval gate.

## 5. Close with actionability

- Open **Executive Brief** and click **Generate Executive Brief** to show CIO/CISO-ready framing.
- Open **Technical Remediation** to show user-by-user fixes plus Azure and AWS recommendations.
- End on **Evals** to demonstrate repeatable model evaluation and cost awareness.
