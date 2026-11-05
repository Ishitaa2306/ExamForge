"""Full end-to-end ExamForge workflow test v2."""
import requests
import time
import sys

BASE = "http://localhost:8000/api"

def log(msg):
    print(f"  {msg}", flush=True)

print("\n=== EXAMFORGE FULL WORKFLOW TEST v2 ===\n")

# 1. Auth
print("[1] Authentication")
r = requests.post(f"{BASE}/auth/login", data={"username": "test@examforge.ai", "password": "testpass123"})
assert r.status_code == 200, f"Login failed: {r.text}"
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
log("Login OK")
r = requests.get(f"{BASE}/auth/me", headers=headers)
log(f"User: {r.json()['name']}")

# 2. Upload PDF
print("\n[2] Document Upload & Analysis")
with open("test_material.pdf", "rb") as f:
    r = requests.post(
        f"{BASE}/documents/upload",
        files={"file": ("ml_study.pdf", f, "application/pdf")},
        headers=headers,
    )
assert r.status_code == 201, f"Upload failed: {r.text}"
doc_id = r.json()["id"]
log(f"Uploaded: doc_id={doc_id}")

start = time.time()
for i in range(60):
    time.sleep(2)
    r = requests.get(f"{BASE}/documents/{doc_id}/status", headers=headers)
    d = r.json()
    status = d["status"]
    if i % 5 == 0 or status in ("ANALYZED", "FAILED"):
        log(f"Poll {i+1}: {status} topics={d.get('topic_count',0)} q={d.get('question_count',0)} ({round(time.time()-start)}s)")
    if status == "ANALYZED":
        break
    if status == "FAILED":
        print("FAIL: analysis failed"); sys.exit(1)

assert d.get("topic_count", 0) >= 1, "No topics"
assert d.get("question_count", 0) >= 1, "No questions"
log(f"PASS: {d['topic_count']} topics, {d['question_count']} questions")

# 3. Knowledge map
print("\n[3] Knowledge Map")
r = requests.get(f"{BASE}/documents/{doc_id}/knowledge-map", headers=headers)
assert r.status_code == 200, f"KM failed: {r.text}"
km = r.json()
log(f"Topics: {km['total_topics']}, Subtopics: {km['total_subtopics']}, Concepts: {km['total_concepts']}")
for t in km["topics"][:3]:
    log(f"  Topic: '{t['name']}' — {t['question_count']} questions")

# 4. Create examination
print("\n[4] Examination Flow")
r = requests.post(f"{BASE}/examinations/", json={"document_id": doc_id, "max_questions": 5}, headers=headers)
assert r.status_code == 201, f"Create exam failed: {r.text}"
exam_id = r.json()["id"]
log(f"Examination created: exam_id={exam_id}")

# 5. Start
r = requests.post(f"{BASE}/examinations/{exam_id}/start", headers=headers)
assert r.status_code == 200, f"Start failed: {r.text}"
q = r.json()
log(f"Q1: [{q['category']}][{q['difficulty']}] {q['question_text'][:80]}")

# 6. Answer loop
sample_answers = [
    "Machine learning is a branch of artificial intelligence where algorithms learn patterns from data to make predictions without explicit programming.",
    "Supervised learning uses labeled training data with input-output pairs. The algorithm minimizes a loss function to learn the mapping between inputs and outputs.",
    "Classification predicts discrete class labels while regression predicts continuous numeric values. Both are supervised learning tasks.",
    "Neural networks consist of layers of interconnected nodes. Backpropagation computes gradients during training to update weights via gradient descent.",
    "K-means iteratively assigns points to the nearest centroid then recomputes centroids until convergence, partitioning data into k clusters.",
]

answered = 0
for i, answer_text in enumerate(sample_answers):
    if q.get("is_last") and q.get("question_asked_id") == -1:
        log(f"Completion signal after Q{i+1}"); break
    
    r = requests.post(
        f"{BASE}/examinations/{exam_id}/answer",
        json={
            "question_asked_id": q["question_asked_id"],
            "answer_text": answer_text,
            "time_taken_seconds": 60,
        },
        headers=headers,
    )
    assert r.status_code == 200, f"Answer {i+1} failed: {r.text}"
    answered += 1
    q = r.json()
    log(f"  A{i+1} submitted > progress={q.get('progress_pct',0)}% is_last={q.get('is_last')}")
    if q.get("is_last") and q.get("question_asked_id") == -1:
        log("Examination auto-completed"); break
    elif q.get("is_last"):
        # Answer this last question too
        log(f"  Last Q: {q['question_text'][:60]}")

log(f"Answered {answered} question(s)")

# 7. Force complete if still in progress
r = requests.get(f"{BASE}/examinations/{exam_id}", headers=headers)
exam_status = r.json()["status"]
if exam_status == "IN_PROGRESS":
    log("Forcing completion...")
    r = requests.post(f"{BASE}/examinations/{exam_id}/complete", headers=headers)
    assert r.status_code == 200, f"Complete failed: {r.text}"
    exam_status = r.json()["status"]
log(f"Examination status: {exam_status}")

# 8. Wait for async report generation
print("\n[5] Report Generation")
time.sleep(5)
r = requests.get(f"{BASE}/reports/examination/{exam_id}", headers=headers)
if r.status_code == 200:
    report = r.json()
    score_pct = round((report.get("overall_score") or 0) * 100, 1)
    log(f"Report: score={score_pct}% mode={report.get('provider_mode','?')}")
    log(f"Strong: {report.get('strong_concepts', [])}")
    log(f"Weak: {report.get('weak_concepts', [])}")
    log(f"Recommendations: {report.get('recommendations', [])[:1]}")
    print("\n  REPORT GENERATED SUCCESSFULLY")
else:
    log(f"Report status {r.status_code}: {r.text[:150]}")

# 9. Knowledge profile
r = requests.get(f"{BASE}/knowledge/profile/{doc_id}", headers=headers)
if r.status_code == 200:
    kp = r.json()
    log(f"Knowledge profile: score={kp.get('overall_score')}, total_exams={kp.get('total_examinations')}")
else:
    log(f"Knowledge profile: {r.status_code}")

# 10. Examination history
r = requests.get(f"{BASE}/examinations/", headers=headers)
log(f"Examination history: {r.json()['total']} exam(s)")

# 11. Document list
r = requests.get(f"{BASE}/documents/", headers=headers)
log(f"Documents: {r.json()['total']} doc(s)")

print("\n=== ALL WORKFLOW TESTS PASSED ===\n")
