# -*- coding: utf-8 -*-
"""Đối chiếu báo cáo Newman (JSON reporter) với trạng thái trong TestCase.xlsx.
python -I qa_tests/verify_newman.py <newman_report.json>"""
import sys, json, os, openpyxl
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rep = json.load(open(sys.argv[1], encoding="utf-8"))
wb = openpyxl.load_workbook(os.path.join(ROOT, "TestCase.xlsx"), data_only=True)
X = {}
for s in wb.sheetnames[1:6]:
    for r in wb[s].iter_rows(min_row=3, values_only=True):
        if r[0]: X[r[0]] = r[9]
res = {}
for ex in rep["run"]["executions"]:
    name = ex["item"]["name"]
    tid = name.split(" - ")[0]
    a = ex.get("assertions") or []
    fails = [x["assertion"] for x in a if x.get("error")]
    code = (ex.get("response") or {}).get("code")
    if tid.startswith("TC_"):
        res[tid] = dict(n=len(a), fails=fails, code=code, err=bool(ex.get("requestError")))
    elif fails or ex.get("requestError"):
        print("SETUP LỖI:", name, fails)
ok = bad = 0
for tid, st in X.items():
    r = res.get(tid)
    if r is None: print("KHÔNG CHẠY:", tid); bad += 1; continue
    got = "PASS" if not r["fails"] and r["n"] > 0 else "FAIL (Bug)"
    exp = "PASS" if st == "CHƯA XÁC ĐỊNH" else st
    if got == exp and not r["err"]: ok += 1
    else:
        bad += 1; print(f"LỆCH {tid}: Excel={st}  Newman={got} (HTTP {r['code']}, {r['n']} assert, fail={r['fails']})")
print(f"KHỚP {ok}/{len(X)}  LỆCH {bad}")
s = rep["run"]["stats"]
print("Newman stats: requests", s["requests"], "assertions", s["assertions"])
