import csv, os, random, pathlib, datetime as dt

base = pathlib.Path(__file__).resolve().parents[1] / "synthetic_data"
base.mkdir(parents=True, exist_ok=True)

roles = [
    {"principal":"alice@contoso.gov","role":"Owner","scope":"/subscriptions/0000","assignment_type":"permanent"},
    {"principal":"bob@contoso.gov","role":"User Access Administrator","scope":"/subscriptions/0000","assignment_type":"permanent"},
    {"principal":"carol@contoso.gov","role":"Contributor","scope":"/subscriptions/1111","assignment_type":"eligible"},
    {"principal":"dave@contoso.gov","role":"Reader","scope":"/subscriptions/2222","assignment_type":"eligible"},
    {"principal":"eve@contoso.gov","role":"Contributor","scope":"/subscriptions/3333/resourceGroups/rg1","assignment_type":"permanent"},
]

with open(base / "role_assignments.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["principal","role","scope","assignment_type"])
    w.writeheader()
    w.writerows(roles)

statuses = ["Success", "Failure"]
risks = ["low","medium","high"]
apps = ["Azure Portal","Graph Explorer","Teams Admin","M365 Admin","Custom Script"]
rows = []
for i in range(200):
    rows.append({
        "time": (dt.datetime.utcnow() - dt.timedelta(minutes=i*7)).isoformat() + "Z",
        "user": random.choice(["alice","bob","carol","dave","eve"]) + "@contoso.gov",
        "app": random.choice(apps),
        "ip": f"192.0.2.{random.randint(1,254)}",
        "status": random.choices(statuses, weights=[0.85,0.15])[0],
        "risk": random.choices(risks, weights=[0.7,0.2,0.1])[0]
    })

with open(base / "signins.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["time","user","app","ip","status","risk"])
    w.writeheader()
    w.writerows(rows)

print("Wrote:", base / "role_assignments.csv")
print("Wrote:", base / "signins.csv")
