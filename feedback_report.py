"""Summarize visitor feedback: does "Great match" really work more often than "Okay"?

Usage: python feedback_report.py [path/to/feedback.db]
On PythonAnywhere, run it in a Bash console inside the haircare folder.
"""
import sys

import db
import feedback

conn = feedback.connect(sys.argv[1] if len(sys.argv) > 1 else None)
total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
print(f"{total} votes\n")
if not total:
    sys.exit()

print("By the label the site showed (a good model has more 👍 for better labels):")
for r in conn.execute("""SELECT COALESCE(NULLIF(label, ''), '(no label)') AS label, COUNT(*) AS n,
                                SUM(vote = 1) AS up FROM feedback GROUP BY 1 ORDER BY n DESC"""):
    print(f"  {r['label']:14} {r['n']:5} votes  {r['up'] * 100 // r['n']:3}% worked")

names = {r["url"]: f"{r['brand'] or ''} {r['name']}".strip()
         for r in db.connect().execute("SELECT url, name, brand FROM products")}
print("\nProducts rated as a match that didn't work for people (check the rules for these):")
rows = conn.execute("""SELECT product_url, COUNT(*) AS n, SUM(vote = -1) AS down FROM feedback
                       WHERE label IN ('Great match', 'Good match')
                       GROUP BY product_url HAVING down > 0 ORDER BY down DESC, n DESC LIMIT 15""")
for r in rows:
    print(f"  {r['down']}/{r['n']} 👎  {names.get(r['product_url'], r['product_url'])}")
