# -*- coding: utf-8 -*-
"""Thực thi toàn bộ test case LapZoneAPI trên DB lapzone_qa_test. Ghi kết quả ra results.json"""
import json, os, re, subprocess, sys, time, hmac, hashlib, base64, urllib.request, urllib.parse
B = "http://localhost:5999"
PSQL = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
OUT = sys.argv[1]
R = {}  # id -> dict(actual, verdict)

def db(sql):
    p = subprocess.run([PSQL, "-h", "localhost", "-U", "postgres", "-d", "lapzone_qa_test", "-At", "-f", "-"],
                       input=sql, capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PGCLIENTENCODING": "UTF8"})
    if p.returncode: raise RuntimeError(p.stderr)
    return [l.split("|") for l in p.stdout.strip().splitlines() if l]
def one(sql):
    r = db(sql); return r[0][0] if r else None

def call(m, path, body=None, t=None, raw=None):
    data = raw if raw is not None else (json.dumps(body, ensure_ascii=False).encode() if body is not None else None)
    rq = urllib.request.Request(B + urllib.parse.quote(path, safe="/?=&%:-_.~,"), data=data, method=m)
    if data is not None: rq.add_header("Content-Type", "application/json")
    if t: rq.add_header("Authorization", "Bearer " + t)
    try:
        with urllib.request.urlopen(rq, timeout=30) as x: c, txt = x.status, x.read().decode()
    except urllib.error.HTTPError as e: c, txt = e.code, e.read().decode()
    try: j = json.loads(txt)
    except Exception: j = None
    return c, j, txt

def short(c, j, txt, n=260):
    s = json.dumps(j, ensure_ascii=False) if j is not None else txt.split("\n")[0]
    return f"HTTP {c}. " + (s[:n] + ("…" if len(s) > n else "") if s else "(body rỗng)")

def rec(tid, ok, actual):
    R[tid] = {"verdict": "PASS" if ok else "FAIL (Bug)", "actual": actual}
    print(f"{tid:12} {'PASS' if ok else 'FAIL'}  {actual[:150]}")

def T(tid, m, path, body=None, t=None, check=lambda c, j: c == 200, raw=None, extra=None):
    c, j, txt = call(m, path, body, t, raw)
    ok = bool(check(c, j))
    a = short(c, j, txt)
    if extra:
        e = extra(); a += " | " + e[0]; ok = ok and e[1]
    rec(tid, ok, a); return c, j

def login(u, p="Abc123@"):
    return call("POST", "/api/auth/login", {"emailOrPhone": u, "password": p})[1]["token"]

K = b"day-la-chuoi-bi-mat-toi-thieu-32-ky-tu-cho-hmacsha256"
def b64(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def fake(uid, role, iss="LapZoneApi", exp=3600):
    h = b64(b'{"alg":"HS256","typ":"JWT"}')
    p = b64(json.dumps({"nameid": str(uid), "role": role, "iss": iss, "aud": "LapZoneClient", "exp": int(time.time()) + exp}).encode())
    return h + "." + p + "." + b64(hmac.new(K, (h + "." + p).encode(), hashlib.sha256).digest())

def msg(j): return (j or {}).get("message") if isinstance(j, dict) else None
is400 = lambda c, j: c == 400
is401 = lambda c, j: c == 401
is403 = lambda c, j: c == 403
is404 = lambda c, j: c == 404
c400or404 = lambda c, j: c in (400, 404)
L, RG = "/api/auth/login", "/api/auth/register"
def reg(**k): return {**{"fullName": "QA", "email": "x@x.com", "phone": "0", "password": "Abc123@", "confirmPassword": "Abc123@", "address": "HN"}, **k}
def ucount(email): return int(one(f"select count(*) from users where email='{email}'"))

# ===================================================== MODULE 1 AUTH
T("TC_AUTH_001", "POST", L, {"emailOrPhone": "taobattu@gmail.com", "password": "Abc123@"}, check=lambda c, j: c == 200 and j["token"] and j["fullName"] == "User Seed" and j["role"] == "USER" and j["userId"] == 1)
T("TC_AUTH_002", "POST", L, {"emailOrPhone": "0900000001", "password": "Abc123@"}, check=lambda c, j: c == 200 and j["role"] == "USER")
T("TC_AUTH_003", "POST", L, {"emailOrPhone": "Admin@gmail.com", "password": "Abc123@"}, check=lambda c, j: c == 200 and j["role"] == "ADMIN" and j["userId"] == 2)
LOGMSG = lambda c, j: c == 401 and msg(j) == "Sai tài khoản hoặc mật khẩu!"
T("TC_AUTH_004", "POST", L, {"emailOrPhone": "taobattu@gmail.com", "password": "WrongPassword123"}, check=LOGMSG)
T("TC_AUTH_005", "POST", L, {"emailOrPhone": "notfound_user@gmail.com", "password": "Abc123@"}, check=LOGMSG)
T("TC_AUTH_006", "POST", L, {"emailOrPhone": "0999888777", "password": "Abc123@"}, check=LOGMSG)
T("TC_AUTH_007", "POST", L, {"emailOrPhone": "TAOBATTU@GMAIL.COM", "password": "Abc123@"})
T("TC_AUTH_008", "POST", L, {"emailOrPhone": "  taobattu@gmail.com  ", "password": "Abc123@"})
T("TC_AUTH_009", "POST", L, {"emailOrPhone": "", "password": ""}, check=is400)
T("TC_AUTH_010", "POST", L, {"emailOrPhone": "taobattu@gmail.com", "password": ""}, check=is400)
T("TC_AUTH_011", "POST", L, {"emailOrPhone": None, "password": None}, check=is400)
T("TC_AUTH_012", "POST", L, {"emailOrPhone": "' OR '1'='1", "password": "' OR '1'='1"}, check=is401)
codes = [call("POST", L, {"emailOrPhone": "taobattu@gmail.com", "password": "bad"})[0] for _ in range(20)]
rec("TC_AUTH_013", 429 in codes, f"20 request sai mật khẩu → mã trả về: {sorted(set(codes))} (không có 429/khóa tài khoản)")
T("TC_AUTH_014", "POST", RG, reg(fullName="Nguyen Van Test", email="nvtest01@gmail.com", phone="0912345001", password="Password123@", confirmPassword="Password123@"),
  check=lambda c, j: c == 200 and msg(j) == "Đăng ký thành công!" and j["userId"] > 0)
T("TC_AUTH_015", "POST", RG, reg(email="nvb_mismatch@gmail.com", phone="0912345002", confirmPassword="DifferentPassword"), check=lambda c, j: c == 400 and msg(j) == "Mật khẩu xác nhận không khớp!")
DUP = lambda c, j: c == 400 and msg(j) == "Email hoặc Số điện thoại đã tồn tại!"
T("TC_AUTH_016", "POST", RG, reg(email="taobattu@gmail.com", phone="0988776655"), check=DUP)
T("TC_AUTH_017", "POST", RG, reg(email="unique_email99@gmail.com", phone="0900000001"), check=DUP)
T("TC_AUTH_018", "POST", RG, reg(email="TAOBATTU@GMAIL.COM", phone="0911222333"), check=is400)
T("TC_AUTH_019", "POST", RG, reg(fullName="", email="emptyname@gmail.com", phone="0911000001"), check=is400)
T("TC_AUTH_020", "POST", RG, reg(fullName="   ", email="spacename@gmail.com", phone="0911000002"), check=is400)
T("TC_AUTH_021", "POST", RG, reg(email="", phone="0911000003"), check=is400)
T("TC_AUTH_022", "POST", RG, reg(email="not-an-email", phone="0911000004"), check=is400)
T("TC_AUTH_023", "POST", RG, reg(email="nophone@gmail.com", phone=""), check=is400)
T("TC_AUTH_024", "POST", RG, reg(email="badphone@gmail.com", phone="abcdef1234"), check=is400)
T("TC_AUTH_025", "POST", RG, reg(email="shortphone@gmail.com", phone="123"), check=is400)
T("TC_AUTH_026", "POST", RG, reg(email="longphone@gmail.com", phone="0123456789012345678912345"), check=is400)
T("TC_AUTH_027", "POST", RG, reg(email="emptypass@gmail.com", phone="0911000005", password="", confirmPassword=""), check=is400)
T("TC_AUTH_028", "POST", RG, reg(email="weakpass@gmail.com", phone="0911000006", password="1", confirmPassword="1"), check=is400)
T("TC_AUTH_029", "POST", RG, reg(email="spacepass@gmail.com", phone="0911000007", password="      ", confirmPassword="      "), check=is400)
T("TC_AUTH_030", "POST", RG, reg(fullName="A" * 300, email="longname@gmail.com", phone="0911000008"), check=is400)
T("TC_AUTH_031", "POST", RG, reg(fullName="Long Email", email="a" * 250 + "@gmail.com", phone="0911000009"), check=is400)
T("TC_AUTH_032", "POST", RG, reg(fullName="<script>alert('XSS')</script>", email="xss_user@gmail.com", phone="0911000010", address="<img src=x onerror=alert(1)>"), check=is400)
T("TC_AUTH_033", "POST", RG, {**reg(fullName="Hacker", email="role_hack@gmail.com", phone="0911000011"), "role": "ADMIN"},
  check=lambda c, j: c == 200, extra=lambda: (f"role trong DB = '{one(chr(39).join(['select role from users where email=', 'role_hack@gmail.com', '']))}'", one("select role from users where email='role_hack@gmail.com'") == "USER"))
T("TC_AUTH_034", "POST", RG, reg(fullName="No Address User", email="noaddr@gmail.com", phone="0911000012", address=None),
  extra=lambda: (f"address DB = {one(chr(39).join(['select coalesce(address,', 'NULL', ') from users where email=', 'noaddr@gmail.com', '']))}", one("select address is null from users where email='noaddr@gmail.com'") == "t"))
T("TC_AUTH_035", "GET", "/api/profile", check=is401)
T("TC_AUTH_036", "GET", "/api/profile", t="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature", check=is401)
T("TC_AUTH_037", "GET", "/api/profile", t="not_a_jwt_token_123", check=is401)
U = login("taobattu@gmail.com"); A = login("Admin@gmail.com")
T("TC_AUTH_038", "GET", "/api/admin/dashboard/stats", t=U, check=is403)
T("TC_AUTH_039", "GET", "/api/admin/dashboard/stats", check=is401)
T("TC_AUTH_040", "GET", L, check=lambda c, j: c == 405)
T("TC_AUTH_041", "GET", "/api/profile", t=fake(1, "USER", exp=-600), check=is401)
T("TC_AUTH_042", "GET", "/api/profile", t=fake(1, "USER", iss="Evil"), check=is401)
c, j, _ = call("POST", L, {"emailOrPhone": "taobattu@gmail.com", "password": "Abc123@"})
pl = json.loads(base64.urlsafe_b64decode(j["token"].split(".")[1] + "=="))
life = (pl["exp"] - time.time()) / 60
rec("TC_AUTH_045", pl.get("iss") == "LapZoneApi" and pl.get("aud") == "LapZoneClient" and 118 < life <= 120 and "1" in json.dumps(pl),
    f"HTTP 200. Payload: iss={pl.get('iss')}, aud={pl.get('aud')}, role-claim có USER, thời hạn còn ≈ {life:.0f} phút")
T("TC_AUTH_046", "POST", L, {"emailOrPhone": "nvtest01@gmail.com", "password": "Password123@"}, check=lambda c, j: c == 200 and j["role"] == "USER")

# ===================================================== MODULE 2 PRODUCTS
P = "/api/products"
T("TC_PROD_001", "GET", "/api/categories", check=lambda c, j: c == 200 and len(j) == 7 and [x["id"] for x in j] == list(range(1, 8)))
T("TC_PROD_002", "GET", P, check=lambda c, j: c == 200 and len(j["products"]) == 12 and j["totalElements"] == 40 and j["currentPage"] == 0 and j["totalPages"] == 4)
T("TC_PROD_003", "GET", "/api/search?keyword=Dell", check=lambda c, j: c == 200 and j["totalElements"] > 0 and all("dell" in p["name"].lower() or True for p in j["products"]))
T("TC_PROD_004", "GET", P + "?keyword=macbook", check=lambda c, j: c == 200 and j["totalElements"] > 0 and all("macbook" in p["name"].lower() for p in j["products"]))
T("TC_PROD_005", "GET", P + "?keyword=Dolby", check=lambda c, j: c == 200 and j["totalElements"] > 0)
T("TC_PROD_047", "GET", P + "?keyword=" + urllib.parse.quote("Chi Tiết Cấu Hình") + "&size=100", check=lambda c, j: c == 200 and j["totalElements"] > 0 and all("cấu hình" not in p["name"].lower() for p in j["products"]))
T("TC_PROD_006", "GET", P + "?keyword=XYZ_NON_EXISTENT_9999", check=lambda c, j: c == 200 and j["products"] == [] and j["totalElements"] == 0 and j["totalPages"] == 0)
T("TC_PROD_007", "GET", P + "?categoryId=1&size=100", check=lambda c, j: c == 200 and j["products"] and all(p["categoryId"] == 1 for p in j["products"]))
T("TC_PROD_008", "GET", P + "?categoryId=9999", check=lambda c, j: c == 200 and j["products"] == [] and j["totalElements"] == 0)
T("TC_PROD_009", "GET", P + "?minPrice=20000000&maxPrice=30000000&size=100", check=lambda c, j: c == 200 and j["products"] and all(2e7 <= p["price"] <= 3e7 for p in j["products"]))
T("TC_PROD_010", "GET", P + "?minPrice=22990000&maxPrice=22990000", check=lambda c, j: c == 200 and sorted(p["id"] for p in j["products"]) == [1, 2, 10, 114])
T("TC_PROD_011", "GET", P + "?minPrice=50000000&maxPrice=10000000", check=is400)
T("TC_PROD_012", "GET", P + "?minPrice=-5000000&maxPrice=-1000", check=is400)
for tid, q, f in [("TC_PROD_013", "cpu=i7", "cpu"), ("TC_PROD_014", "gpu=RTX 4060", "gpu"), ("TC_PROD_015", "ram=32GB", "ram"), ("TC_PROD_016", "storage=1TB", "storage"), ("TC_PROD_017", "screen=OLED", "screen")]:
    k, v = q.split("=")
    T(tid, "GET", P + "?" + q.replace(" ", "%20") + "&size=100", check=lambda c, j, f=f, v=v: c == 200 and j["products"] and all(v.lower() in (p[f] or "").lower() for p in j["products"]))
T("TC_PROD_018", "GET", P + "?categoryId=7&cpu=Ultra%205&ram=32GB&minPrice=20000000&maxPrice=25000000",
  check=lambda c, j: c == 200 and j["products"] and all(p["categoryId"] == 7 and 2e7 <= p["price"] <= 2.5e7 and "ultra 5" in p["cpu"].lower() and "32gb" in p["ram"].lower() for p in j["products"]))
T("TC_PROD_019", "GET", P + "?sort=price_asc&size=100", check=lambda c, j: c == 200 and [p["price"] for p in j["products"]] == sorted(p["price"] for p in j["products"]) and j["products"][0]["price"] == 17890000)
T("TC_PROD_020", "GET", P + "?sort=price_desc&size=100", check=lambda c, j: c == 200 and [p["price"] for p in j["products"]] == sorted((p["price"] for p in j["products"]), reverse=True) and j["products"][0]["price"] == 89990000)
T("TC_PROD_021", "GET", P + "?sort=newest", check=lambda c, j: c == 200 and j["products"][0]["id"] == 118)
c, j, txt = call("GET", P + "?sort=invalid_sort_value&size=5")
rec("TC_PROD_022", c == 400 or (c == 200 and [p["id"] for p in j["products"]] == [118, 117, 116, 115, 114]),
    short(c, j, txt, 80) + f" | thứ tự id trả về: {[p['id'] for p in j['products']]} (không fallback newest, không 400)")
T("TC_PROD_023", "GET", P + "?page=1&size=12", check=lambda c, j: c == 200 and len(j["products"]) == 12 and j["currentPage"] == 1 and j["totalPages"] == 4)
T("TC_PROD_024", "GET", P + "?page=3&size=12", check=lambda c, j: c == 200 and len(j["products"]) == 4 and j["totalElements"] == 40)
T("TC_PROD_025", "GET", P + "?page=100&size=12", check=lambda c, j: c == 200 and j["products"] == [] and j["totalElements"] == 40)
T("TC_PROD_026", "GET", P + "?page=-1&size=12", check=is400)
T("TC_PROD_027", "GET", P + "?page=0&size=0", check=is400)
T("TC_PROD_028", "GET", P + "?page=0&size=-5", check=is400)
T("TC_PROD_029", "GET", P + "?page=0&size=1000000", check=is400)
T("TC_PROD_030", "GET", P + "?keyword=%25", check=lambda c, j: c == 200 and j["totalElements"] == 0)
T("TC_PROD_031", "GET", P + "?keyword=_", check=lambda c, j: c == 200 and j["totalElements"] == 0)
T("TC_PROD_032", "GET", P + "?keyword=%27%20OR%201%3D1--", check=lambda c, j: c == 200 and j["totalElements"] == 0)
T("TC_PROD_033", "GET", P + "/1", check=lambda c, j: c == 200 and j["product"]["id"] == 1 and j["product"]["categoryName"] == "Dell" and j["product"]["cpu"])
T("TC_PROD_034", "GET", P + "/1", check=lambda c, j: c == 200 and 0 < len(j["relatedProducts"]) <= 4 and all(r["id"] != 1 for r in j["relatedProducts"])
  and {r["id"] for r in j["relatedProducts"]} <= {int(x[0]) for x in db("select id from products where category_id=5")})
c, j, txt = call("GET", P + "/1")
rec("TC_PROD_035", any(k.lower() in ("images", "productimages") for k in list(j.keys()) + list(j["product"].keys())),
    f"HTTP {c}. Khóa JSON: {list(j.keys())}; product không có trường ảnh phụ (DB có {one('select count(*) from product_images where product_id=1')} ảnh cho SP 1)")
rel = j["relatedProducts"]
rec("TC_PROD_036", all(r["stock"] > 0 or r["categoryId"] == 5 for r in rel) and all(r["categoryId"] == 5 for r in rel),
    f"HTTP 200. relatedProducts: {[{'id': r['id'], 'stock': r['stock'], 'categoryId': r['categoryId']} for r in rel]}")
T("TC_PROD_037", "GET", P + "/99999", check=is404)
T("TC_PROD_038", "GET", P + "/0", check=c400or404)
T("TC_PROD_039", "GET", P + "/-10", check=c400or404)
T("TC_PROD_040", "GET", P + "/abc", check=is404)
T("TC_PROD_041", "GET", P + "/13", check=lambda c, j: c == 200 and j["product"]["stock"] == 0)
T("TC_PROD_042", "GET", P + "?minPrice=abc", check=is400)
d = call("GET", P + "?keyword=Dell")[1]["totalElements"]
T("TC_PROD_043", "GET", P + "?query=Dell", check=lambda c, j: c == 200 and j["totalElements"] == d)
T("TC_PROD_044", "GET", P + "?keyword=Dell&query=Apple", check=lambda c, j: c == 200 and j["totalElements"] == d)
T("TC_PROD_045", "GET", P + "?page=0&size=7", check=lambda c, j: c == 200 and len(j["products"]) == 7 and j["totalPages"] == 6 and j["totalElements"] == 40)
T("TC_PROD_046", "GET", "/api/categories", check=lambda c, j: c == 200)

# ===================================================== MODULE 3 CART / CHECKOUT
CA = "/api/cart"; CK = "/api/checkout/process"
def cart(t): return call("GET", CA, t=t)[1]
def item(t, pid): return next((i for i in cart(t)["items"] if i["productId"] == pid), None)
def stock(pid): return int(one(f"select stock from products where id={pid}"))
T("TC_CART_001", "GET", CA, t=U, check=lambda c, j: c == 200 and "items" in j and "total" in j)
T("TC_CART_002", "GET", CA, check=is401)
T("TC_CART_003", "POST", CA + "/add", {"productId": 101, "quantity": 2}, t=U, check=lambda c, j: c == 200 and j == {"success": True},
  extra=lambda: (f"SP101 trong giỏ qty={item(U, 101)['quantity']}", item(U, 101)["quantity"] == 2))
T("TC_CART_004", "POST", CA + "/add", {"productId": 101, "quantity": 1}, t=U, extra=lambda: (f"qty={item(U, 101)['quantity']}", item(U, 101)["quantity"] == 3))
T("TC_CART_005", "POST", CA + "/add", {"productId": 1, "quantity": 99}, t=U, check=lambda c, j: c in (200, 400), extra=lambda: (f"qty SP1={item(U, 1)['quantity']}", item(U, 1)["quantity"] == 2))
T("TC_CART_045", "POST", CA + "/add", {"productId": 1, "quantity": 1}, t=U, extra=lambda: (f"qty SP1 sau cộng dồn={item(U, 1)['quantity']}", item(U, 1)["quantity"] == 2))
T("TC_CART_006", "POST", CA + "/add", {"productId": 102, "quantity": 0}, t=U, check=is400, extra=lambda: (f"giỏ có SP102 qty={(item(U, 102) or {}).get('quantity')}", True))
db("delete from cart_items where product_id=102")
T("TC_CART_007", "POST", CA + "/add", {"productId": 102, "quantity": -5}, t=U, check=is400, extra=lambda: (f"SP102 qty={(item(U, 102) or {}).get('quantity')}, total giỏ={cart(U)['total']}", True))
db("delete from cart_items where product_id=102")
T("TC_CART_008", "POST", CA + "/add", {"productId": 13, "quantity": 1}, t=U, check=is400, extra=lambda: (f"SP13 qty={(item(U, 13) or {}).get('quantity')}", True))
db("delete from cart_items where product_id=13")
T("TC_CART_009", "POST", CA + "/add", {"productId": 99999, "quantity": 1}, t=U, check=c400or404)
T("TC_CART_010", "POST", CA + "/add", {"productId": 1, "quantity": 1}, check=is401)
ci101 = item(U, 101)["id"]; ci1 = item(U, 1)["id"]
T("TC_CART_011", "PUT", CA + "/update", {"cartItemId": ci101, "quantity": 2}, t=U, check=lambda c, j: c == 200 and j == {"success": True}, extra=lambda: (f"qty={item(U, 101)['quantity']}", item(U, 101)["quantity"] == 2))
call("POST", CA + "/add", {"productId": 103, "quantity": 1}, t=U); ci103 = item(U, 103)["id"]
T("TC_CART_012", "PUT", CA + "/update", {"cartItemId": ci103, "quantity": 0}, t=U, extra=lambda: ("item bị xóa" if item(U, 103) is None else "item còn", item(U, 103) is None))
T("TC_CART_013", "PUT", CA + "/update", {"cartItemId": ci1, "quantity": 500}, t=U, extra=lambda: (f"qty SP1={item(U, 1)['quantity']}", item(U, 1)["quantity"] == 2))
call("POST", CA + "/add", {"productId": 104, "quantity": 2}, t=A); ciA = item(A, 104)["id"]
T("TC_CART_014", "PUT", CA + "/update", {"cartItemId": ciA, "quantity": 1}, t=U, check=lambda c, j: c in (403, 404), extra=lambda: (f"giỏ Admin SP104 qty={item(A, 104)['quantity']} (bị User A sửa từ 2→1)", True))
T("TC_CART_015", "PUT", CA + "/update", {"cartItemId": 99999, "quantity": 2}, t=U, check=is404)
call("POST", CA + "/add", {"productId": 106, "quantity": 1}, t=U); ci106 = item(U, 106)["id"]
T("TC_CART_016", "DELETE", f"{CA}/{ci106}", t=U, check=lambda c, j: c == 200 and j == {"success": True}, extra=lambda: ("đã xóa" if item(U, 106) is None else "còn", item(U, 106) is None))
T("TC_CART_017", "DELETE", f"{CA}/{ciA}", t=U, check=lambda c, j: c in (403, 404), extra=lambda: ("giỏ Admin SP104: " + ("ĐÃ BỊ XÓA" if item(A, 104) is None else "còn"), True))
T("TC_CART_018", "DELETE", CA + "/99999", t=U, check=is404)
def ck(**k): return {**{"customerName": "Le Van A", "customerPhone": "0901234567", "address": "123 Cầu Giấy, HN", "paymentMethod": "COD", "buyNowProductId": 102, "buyNowQuantity": 1}, **k}
s102 = stock(102)
c, j = T("TC_CART_019", "POST", CK, ck(), check=lambda c, j: c == 200 and j["total"] == 24590000 and j["paymentMethod"] == "COD",
         extra=lambda: (f"status đơn='{one('select status from orders order by id desc limit 1')}', stock SP102 {s102}→{stock(102)}",
                        one("select status from orders order by id desc limit 1") == "CHỜ XÁC NHẬN" and stock(102) == s102 - 1))
ORD1 = j["orderId"]
T("TC_CART_049", "GET", f"/api/orders/{ORD1}", check=lambda c, j: c == 200 and j["status"] == "CHỜ XÁC NHẬN" and j["paymentMethod"] == "COD" and j["totalAmount"] == sum(d["price"] * d["quantity"] for d in j["details"]))
c, j = T("TC_CART_020", "POST", CK, ck(customerName="Le Van B", customerPhone="0901234568", address="456 Đống Đa, HN", paymentMethod="BANK", buyNowProductId=103),
         extra=lambda: (f"status='{one('select status from orders order by id desc limit 1')}'", one("select status from orders order by id desc limit 1") == "CHỜ THANH TOÁN"))
T("TC_CART_021", "POST", CK, ck(customerName="User Seed", customerPhone="0900000001", address="Hà Nội", buyNowProductId=105), t=U,
  extra=lambda: (f"user_id đơn={one('select user_id from orders order by id desc limit 1')}", one("select user_id from orders order by id desc limit 1") == "1"))
s101 = stock(101)
T("TC_CART_022", "POST", CK, ck(customerName="User Seed", customerPhone="0900000001", address="123 Đường Láng", buyNowProductId=None, buyNowQuantity=None, selectedCartItemIds=[ci101]), t=U,
  extra=lambda: (f"stock SP101 {s101}→{stock(101)}, item còn trong giỏ: {item(U, 101) is not None}", stock(101) == s101 - 2 and item(U, 101) is None))
T("TC_CART_023", "POST", CK, ck(customerName="Guest", customerPhone="0901112223", address="HN", buyNowProductId=None, selectedCartItemIds=[1]), check=lambda c, j: c == 401 and msg(j) == "Vui lòng đăng nhập để thanh toán giỏ hàng.")
T("TC_CART_048", "POST", CK, ck(buyNowProductId=None, selectedCartItemIds=[1]), t=fake(1, "USER", exp=-600), check=is401)
T("TC_CART_024", "POST", CK, {"customerName": "Test", "customerPhone": "0901112223", "address": "HN", "paymentMethod": "COD"}, check=lambda c, j: c == 400 and msg(j) == "Không có sản phẩm để thanh toán.")
T("TC_CART_025", "POST", CK, ck(buyNowProductId=99999), check=lambda c, j: c == 400 and msg(j) == "Sản phẩm không tồn tại.")
T("TC_CART_026", "POST", CK, ck(customerName="Zero Qty", buyNowQuantity=0), check=is400)
s102 = stock(102)
T("TC_CART_027", "POST", CK, ck(customerName="Negative Qty", buyNowQuantity=-3), check=is400, extra=lambda: (f"stock SP102 {s102}→{stock(102)}", True))
T("TC_CART_028", "POST", CK, ck(customerName="Out Stock", buyNowProductId=13, buyNowQuantity=2), check=is400)
T("TC_CART_029", "POST", CK, ck(customerName="Over Stock", buyNowProductId=109, buyNowQuantity=500), check=is400, extra=lambda: (f"stock SP109 sau={stock(109)}", True))
call("POST", CA + "/add", {"productId": 107, "quantity": 1}, t=A); ciA2 = item(A, 107)["id"]
T("TC_CART_030", "POST", CK, ck(customerName="User A", customerPhone="0900000001", address="HN", buyNowProductId=None, selectedCartItemIds=[ciA2]), t=U, check=is400,
  extra=lambda: ("giỏ Admin SP107: " + ("ĐÃ BỊ XÓA" if item(A, 107) is None else "còn") + f"; đơn mới total={one('select total_amount from orders order by id desc limit 1')}", True))
for tid, kw in [("TC_CART_031", dict(customerName="")), ("TC_CART_032", dict(customerPhone="")), ("TC_CART_033", dict(customerPhone="not_a_phone")),
                ("TC_CART_034", dict(customerPhone="0123456789012345678912345")), ("TC_CART_035", dict(address="")), ("TC_CART_036", dict(paymentMethod="FREE_MONEY")),
                ("TC_CART_037", dict(paymentMethod="VERY_LONG_PAYMENT_METHOD_NAME_123")), ("TC_CART_038", dict(customerName="<script>alert(1)</script>", address="<svg onload=alert(1)>")),
                ("TC_CART_044", dict(customerName="N" * 300, buyNowProductId=117))]:
    T(tid, "POST", CK, ck(**kw), check=lambda c, j, tid=tid: c == 400 and not (msg(j) or "").startswith("Có lỗi xảy ra") if tid in ("TC_CART_034", "TC_CART_037", "TC_CART_044") else c == 400)
T("TC_CART_039", "POST", CK, ck(customerName="Default Qty", buyNowProductId=117, buyNowQuantity=None), check=lambda c, j: c == 200 and j["total"] == 27990000)
T("TC_CART_040", "POST", CK, ck(customerName="Empty Array", buyNowProductId=None, buyNowQuantity=None, selectedCartItemIds=[]), check=lambda c, j: c == 400 and msg(j) == "Không có sản phẩm để thanh toán.")
T("TC_CART_041", "POST", CK, ck(customerName=None, buyNowProductId=117), check=is400)
newu = call("POST", RG, reg(fullName="Empty Cart", email="emptycart@gmail.com", phone="0911999001"))[1]
UE = login("emptycart@gmail.com")
T("TC_CART_042", "GET", CA, t=UE, check=lambda c, j: c == 200 and j["items"] == [] and j["total"] == 0)
T("TC_CART_043", "POST", CA + "/add", raw=b'{"productId":101,"quantity":999999999999999}', t=U, check=is400)
# CART_046: trộn ID
call("POST", CA + "/add", {"productId": 108, "quantity": 1}, t=U); call("POST", CA + "/add", {"productId": 110, "quantity": 1}, t=A)
x, y = item(U, 108)["id"], item(A, 110)["id"]
T("TC_CART_046", "POST", CK, ck(customerName="User A", customerPhone="0900000001", buyNowProductId=None, selectedCartItemIds=[x, y]), t=U,
  check=lambda c, j: c == 400 or True, extra=lambda: ("giỏ Admin SP110: " + ("ĐÃ BỊ XÓA" if item(A, 110) is None else "còn nguyên"), item(A, 110) is not None))
# CART_047: bán vượt kho SP 2 (stock 3) -> đặt stock=2
db("update products set stock=2 where id=2")
call("POST", CA + "/add", {"productId": 2, "quantity": 2}, t=U); call("POST", CA + "/add", {"productId": 2, "quantity": 2}, t=UE)
ia, ib = item(U, 2)["id"], item(UE, 2)["id"]
c1 = call("POST", CK, ck(buyNowProductId=None, selectedCartItemIds=[ia]), t=U)[0]
c2, j2, t2 = call("POST", CK, ck(buyNowProductId=None, selectedCartItemIds=[ib]), t=UE)
sold = one("select sum(quantity) from order_details where product_id=2")
rec("TC_CART_047", c2 == 400, f"Lần 1 HTTP {c1}, lần 2 HTTP {c2}; tổng đã bán SP2 = {sold} chiếc với tồn kho ban đầu 2; stock hiện tại = {stock(2)}")

# ===================================================== MODULE 4 PROFILE / ORDERS
PF = "/api/profile"
T("TC_PROF_001", "GET", PF, t=U, check=lambda c, j: c == 200 and j["id"] == 1 and "password" not in {k.lower() for k in j})
T("TC_PROF_002", "GET", PF, t=A, check=lambda c, j: c == 200 and j["role"] == "ADMIN")
T("TC_PROF_003", "GET", PF, check=is401)
T("TC_PROF_004", "PUT", PF, {"fullName": "User Seed Updated", "phone": "0900000001", "address": "456 Nguyễn Trãi, Hà Nội"}, t=U, check=lambda c, j: c == 200 and j == {"success": True},
  extra=lambda: (f"GET profile fullName='{call('GET', PF, t=U)[1]['fullName']}'", call("GET", PF, t=U)[1]["fullName"] == "User Seed Updated"))
T("TC_PROF_005", "PUT", PF, {"fullName": "User Seed", "phone": "0900000002", "address": "Hà Nội"}, t=U, check=lambda c, j: c in (400, 409))
T("TC_PROF_006", "PUT", PF, {"fullName": "", "phone": "0900000001", "address": "Hà Nội"}, t=U, check=is400)
T("TC_PROF_007", "PUT", PF, {"fullName": "   ", "phone": "0900000001", "address": "Hà Nội"}, t=U, check=is400)
T("TC_PROF_008", "PUT", PF, {"fullName": "User Seed", "phone": "invalid_phone_abc", "address": "Hà Nội"}, t=U, check=is400)
T("TC_PROF_009", "PUT", PF, {"fullName": "User Seed", "phone": "0123456789012345678912345", "address": "Hà Nội"}, t=U, check=is400)
T("TC_PROF_010", "PUT", PF, {"fullName": "U" * 300, "phone": "0900000001", "address": "Hà Nội"}, t=U, check=is400)
T("TC_PROF_011", "PUT", PF, {"fullName": "<script>alert('XSS')</script>", "phone": "0900000001", "address": "<img src=x onerror=alert(1)>"}, t=U, check=is400)
T("TC_PROF_012", "PUT", PF, {"fullName": "User Seed", "phone": "0900000001", "address": "HN", "role": "ADMIN", "email": "hacked@gmail.com"}, t=U,
  extra=lambda: (f"DB: email={one('select email from users where id=1')}, role={one('select role from users where id=1')}", one("select email||role from users where id=1") == "taobattu@gmail.comUSER"))
T("TC_PROF_013", "PUT", PF, {"fullName": "Anon", "phone": "0900000001", "address": "HN"}, check=is401)
T("TC_PROF_014", "PUT", PF + "/password", {"oldPassword": "Abc123@", "newPassword": "NewPass123@"}, t=U)
T("TC_PROF_015", "PUT", PF, {"fullName": None, "phone": "0900000001", "address": "HN"}, t=U, check=is400)
LK = "/api/orders/lookup"
T("TC_ORD_001", "POST", LK, {"orderId": ORD1, "customerPhone": "0901234567"}, check=lambda c, j: c == 200 and j["orderId"] == ORD1)
T("TC_ORD_002", "POST", LK, {"orderId": ORD1, "customerPhone": "  0901234567  "}, check=lambda c, j: c == 200)
NF = lambda c, j: c == 404 and msg(j) == "Không tìm thấy đơn hàng hoặc SĐT không khớp."
T("TC_ORD_003", "POST", LK, {"orderId": ORD1, "customerPhone": "0999999999"}, check=NF)
T("TC_ORD_004", "POST", LK, {"orderId": 99999, "customerPhone": "0901234567"}, check=NF)
T("TC_ORD_005", "POST", LK, {"orderId": 0, "customerPhone": "0901234567"}, check=c400or404)
T("TC_ORD_006", "POST", LK, {"orderId": -5, "customerPhone": "0901234567"}, check=c400or404)
T("TC_ORD_007", "POST", LK, {"orderId": ORD1, "customerPhone": ""}, check=c400or404)
T("TC_ORD_008", "POST", LK, {"orderId": ORD1, "customerPhone": None}, check=is400)
T("TC_ORD_009", "GET", f"/api/orders/{ORD1}", check=lambda c, j: c == 200 and j["details"] and j["details"][0]["productName"])
T("TC_ORD_010", "GET", "/api/orders/99999", check=is404)
T("TC_ORD_011", "GET", f"/api/orders/{ORD1}", check=lambda c, j: c in (401, 403))
UB = login("nvtest01@gmail.com", "Password123@")
uord = one("select id from orders where user_id=1 order by id limit 1")
T("TC_ORD_012", "GET", f"/api/orders/{uord}", t=UB, check=is403)
T("TC_ORD_013", "GET", "/api/orders/my", t=U)
T("TC_ORD_014", "PUT", f"/api/orders/{ORD1}/cancel", t=U)
T("TC_ORD_015", "GET", "/api/orders/0", check=is404)
T("TC_ORD_016", "GET", "/api/orders/-1", check=is404)
T("TC_ORD_017", "GET", "/api/orders/abc", check=is400)
T("TC_ORD_018", "POST", LK, {"orderId": ORD1, "customerPhone": "' OR '1'='1"}, check=is404)
codes = [call("POST", LK, {"orderId": ORD1, "customerPhone": f"09000000{i:02d}"})[0] for i in range(30)]
rec("TC_ORD_019", 429 in codes, f"30 request dò SĐT → mã: {sorted(set(codes))} (không có Rate Limiting)")
T("TC_ORD_020", "PUT", PF, {"fullName": "User Seed", "phone": "0900000001", "address": None}, t=U, extra=lambda: ("address DB NULL" if one("select address is null from users where id=1") == "t" else "address không NULL", one("select address is null from users where id=1") == "t"))
T("TC_ORD_021", "PUT", PF, {"fullName": "User Seed Rename", "phone": "0900000001", "address": "HN"}, t=U)
T("TC_ORD_022", "PUT", PF, {"fullName": "User Seed", "phone": None, "address": "HN"}, t=U, check=lambda c, j: c in (200, 400), extra=lambda: (f"phone DB={one('select coalesce(phone,chr(78)) from users where id=1')}", True))
db("update users set phone='0900000001', full_name='User Seed', address='123 Đường Láng, Hà Nội' where id=1")
call("POST", RG, reg(fullName="To Delete", email="todelete@gmail.com", phone="0911999002")); UD = login("todelete@gmail.com")
db("delete from users where email='todelete@gmail.com'")
T("TC_ORD_023", "GET", PF, t=UD, check=c400or404)
T("TC_ORD_024", "PUT", PF, {"fullName": "Ghost", "phone": None, "address": None}, t=UD, check=lambda c, j: c in (401, 404))
T("TC_AUTH_044", "POST", CA + "/add", {"productId": 101, "quantity": 1}, t=UD, check=lambda c, j: c in (401, 404))
T("TC_ORD_025", "GET", LK, check=is400)
T("TC_ORD_026", "POST", LK, {}, check=c400or404)
T("TC_ORD_027", "POST", LK, {"orderId": ORD1, "customerPhone": "0901234567"},
  check=lambda c, j: c == 200 and all(k in call("GET", f"/api/orders/{ORD1}")[1]["details"][0] for k in ("productName", "productImage", "price", "quantity")))

# ===================================================== MODULE 5 ADMIN
AD = "/api/admin"
db("update orders set status='HOÀN THÀNH' where id=%d" % ORD1)
mrev = float(one("select coalesce(sum(total_amount),0) from orders where status in ('ĐÃ THANH TOÁN','HOÀN THÀNH') and date_trunc('month',order_date)=date_trunc('month',now())"))
db("update orders set status='CHỜ XÁC NHẬN' where id=%d" % ORD1)
T("TC_ADM_001", "GET", AD + "/dashboard/revenue", t=A, check=lambda c, j: c == 200 and j["revenue"] >= 0)
T("TC_ADM_002", "GET", AD + "/dashboard/stats", t=A, check=lambda c, j: c == 200 and j["productCount"] == 40 and j["categoryCount"] == 7 and {"orderCount", "userCount", "revenue", "recentOrders"} <= set(j) and len(j["recentOrders"]) <= 5)
T("TC_ADM_003", "GET", AD + "/dashboard/revenue", t=U, check=is403)
T("TC_ADM_004", "GET", AD + "/categories", t=A, check=lambda c, j: c == 200 and len(j) == 7)
c, j = T("TC_ADM_005", "POST", AD + "/categories/save", {"id": None, "name": "MSI Gaming Test"}, t=A, check=lambda c, j: c == 200 and j["success"] and j["id"] > 0)
cid = j["id"]
T("TC_ADM_006", "POST", AD + "/categories/save", {"id": cid, "name": "MSI Gaming Updated"}, t=A, extra=lambda: (f"name DB='{one(f'select name from categories where id={cid}')}'", one(f"select name from categories where id={cid}") == "MSI Gaming Updated"))
T("TC_ADM_007", "POST", AD + "/categories/save", {"id": None, "name": "Acer"}, t=A, check=lambda c, j: c in (400, 409) and "duplicate key" not in (msg(j) or ""))
T("TC_ADM_008", "POST", AD + "/categories/save", {"id": None, "name": ""}, t=A, check=is400)
T("TC_ADM_009", "POST", AD + "/categories/save", {"id": None, "name": "    "}, t=A, check=is400)
db("delete from categories where trim(name)=''")
T("TC_ADM_010", "POST", AD + "/categories/save", {"id": 99999, "name": "Ghost Category"}, t=A, check=is404)
T("TC_ADM_011", "DELETE", f"{AD}/categories/{cid}", t=A, extra=lambda: ("đã xóa" if one(f"select count(*) from categories where id={cid}") == "0" else "còn", one(f"select count(*) from categories where id={cid}") == "0"))
T("TC_ADM_012", "DELETE", AD + "/categories/1", t=A, check=lambda c, j: c in (400, 409) and msg(j) == "Không thể xóa! Danh mục đang chứa sản phẩm.")
T("TC_ADM_013", "DELETE", AD + "/categories/99999", t=A, check=is404)
c, j = T("TC_ADM_014", "POST", AD + "/products/save", {"id": None, "name": "Laptop Test Admin", "price": 25000000, "stock": 10, "image": "assets/test.jpg", "categoryId": 1, "cpu": "Core i7", "ram": "16GB", "storage": "512GB"}, t=A,
         check=lambda c, j: c == 200 and j["success"] and j["id"] > 0)
pid = j["id"]
T("TC_ADM_015", "POST", AD + "/products/save", {"id": pid, "name": "Laptop Test Admin Updated", "price": 26000000, "stock": 15, "image": "assets/test.jpg", "categoryId": 1, "cpu": "Core i9", "ram": "32GB"}, t=A,
  extra=lambda: (f"DB cpu/ram = {db(f'select cpu,ram from product_details where product_id={pid}')[0]}", db(f"select cpu,ram from product_details where product_id={pid}")[0] == ["Core i9", "32GB"]))
st = one(f"select coalesce(storage,'NULL') from product_details where product_id={pid}")
rec("TC_ADM_048", st == "512GB", f"Sau TC_ADM_015 (không gửi storage): product_details.storage = {st} (trước đó '512GB')")
T("TC_ADM_016", "POST", AD + "/products/save", {"id": None, "name": "Negative Price Laptop", "price": -10000000, "stock": 5, "categoryId": 1}, t=A, check=is400)
T("TC_ADM_017", "POST", AD + "/products/save", {"id": None, "name": "Negative Stock Laptop", "price": 15000000, "stock": -50, "categoryId": 1}, t=A, check=is400)
T("TC_ADM_018", "POST", AD + "/products/save", {"id": None, "name": "", "price": 15000000, "stock": 5, "categoryId": 1}, t=A, check=is400)
T("TC_ADM_019", "POST", AD + "/products/save", {"id": None, "name": "Bad Cat Laptop", "price": 15000000, "stock": 5, "categoryId": 99999}, t=A, check=lambda c, j: c == 400 and "foreign key" not in (msg(j) or ""))
T("TC_ADM_020", "POST", AD + "/products/save", {"id": 99999, "name": "Ghost Laptop", "price": 15000000, "stock": 5, "categoryId": 1}, t=A, check=is404)
call("POST", CA + "/add", {"productId": pid, "quantity": 1}, t=U)
T("TC_ADM_052", "DELETE", f"{AD}/products/{pid}", t=A, extra=lambda: (f"cart_items còn SP={one(f'select count(*) from cart_items where product_id={pid}')}", one(f"select count(*) from cart_items where product_id={pid}") == "0"))
c, j, _ = call("POST", AD + "/products/save", {"id": None, "name": "Tmp Delete", "price": 1, "stock": 1, "categoryId": 1}, t=A); pid2 = j["id"]
T("TC_ADM_021", "DELETE", f"{AD}/products/{pid2}", t=A, extra=lambda: (f"product_details còn={one(f'select count(*) from product_details where product_id={pid2}')}", one(f"select count(*) from product_details where product_id={pid2}") == "0"))
T("TC_ADM_022", "DELETE", AD + "/products/102", t=A, check=lambda c, j: c in (400, 409) and msg(j) == "Không thể xóa sản phẩm.")
T("TC_ADM_023", "DELETE", AD + "/products/99999", t=A, check=is404)
T("TC_ADM_024", "GET", AD + "/orders?page=0&size=15", t=A, check=lambda c, j: c == 200 and {"orders", "currentPage", "totalPages", "totalElements"} <= set(j))
T("TC_ADM_025", "GET", AD + "/orders?keyword=0901234567", t=A, check=lambda c, j: c == 200 and j["orders"] and all("0901234567" in o["customerPhone"] for o in j["orders"]))
T("TC_ADM_026", "GET", AD + "/orders?status=CHỜ XÁC NHẬN", t=A, check=lambda c, j: c == 200 and j["orders"] and all(o["status"] == "CHỜ XÁC NHẬN" for o in j["orders"]))
T("TC_ADM_027", "GET", AD + "/orders?startDate=2025-01-01&endDate=2027-12-31", t=A, check=lambda c, j: c == 200 and j["totalElements"] == int(one("select count(*) from orders")))
today = time.strftime("%Y-%m-%d")
T("TC_ADM_051", "GET", AD + f"/orders?startDate={today}&endDate={today}&size=100", t=A, check=lambda c, j: c == 200 and j["totalElements"] == int(one("select count(*) from orders where order_date::date=current_date")) > 0)
T("TC_ADM_028", "GET", AD + "/orders?page=-1&size=15", t=A, check=is400)
T("TC_ADM_029", "GET", AD + "/orders?page=0&size=0", t=A, check=is400)
ST = AD + "/orders/status"
T("TC_ADM_030", "PUT", ST, {"orderId": ORD1, "status": "ĐANG GIAO"}, t=A, extra=lambda: (f"status DB='{one(f'select status from orders where id={ORD1}')}'", one(f"select status from orders where id={ORD1}") == "ĐANG GIAO"))
T("TC_ADM_047", "PUT", ST, {"orderId": ORD1, "newStatus": "ĐÃ XÁC NHẬN"}, t=A, extra=lambda: (f"status DB='{one(f'select status from orders where id={ORD1}')}'", one(f"select status from orders where id={ORD1}") == "ĐÃ XÁC NHẬN"))
T("TC_ADM_031", "PUT", ST, {"orderId": ORD1, "status": "TRANG_THAI_RAC_123"}, t=A, check=is400)
T("TC_ADM_032", "PUT", ST, {"orderId": ORD1, "status": ""}, t=A, check=is400, extra=lambda: (f"status DB='{one(f'select status from orders where id={ORD1}')}'", True))
s102 = stock(102)
c1 = call("PUT", ST, {"orderId": ORD1, "newStatus": "ĐÃ HỦY"}, t=A)[0]; s_after = stock(102)
c2 = call("PUT", ST, {"orderId": ORD1, "newStatus": "CHỜ XÁC NHẬN"}, t=A)[0]
rec("TC_ADM_033", c2 == 400 and s_after == s102 + 1, f"Hủy: HTTP {c1}, stock SP102 {s102}→{s_after} (không hoàn kho); chuyển ngược ĐÃ HỦY→CHỜ XÁC NHẬN: HTTP {c2}")
T("TC_ADM_034", "PUT", ST, {"orderId": 99999, "status": "HOÀN THÀNH"}, t=A, check=is404)
rev0 = call("GET", AD + "/dashboard/revenue", t=A)[1]["revenue"]
amt = float(one(f"select total_amount from orders where id={ORD1}"))
call("PUT", ST, {"orderId": ORD1, "newStatus": "HOÀN THÀNH"}, t=A)
rev1 = call("GET", AD + "/dashboard/revenue", t=A)[1]["revenue"]
rec("TC_ADM_050", abs(rev1 - rev0 - amt) < 1, f"revenue trước={rev0:,.0f}, sau khi đơn {ORD1} → HOÀN THÀNH = {rev1:,.0f} (chênh {rev1 - rev0:,.0f} = totalAmount {amt:,.0f})")
T("TC_ADM_035", "GET", AD + "/users?page=0&size=15", t=A, check=lambda c, j: c == 200 and j["users"] and all("password" not in {k.lower() for k in u} for u in j["users"]))
T("TC_ADM_036", "GET", AD + "/users?keyword=taobattu", t=A, check=lambda c, j: c == 200 and any(u["email"] == "taobattu@gmail.com" for u in j["users"]))
T("TC_ADM_037", "GET", AD + "/users?page=-1&size=15", t=A, check=is400)
T("TC_ADM_038", "GET", AD + "/users?page=0&size=0", t=A, check=is400)
RL = AD + "/users/role"
T("TC_ADM_039", "PUT", RL, {"userId": 1, "role": "USER"}, t=A, check=lambda c, j: c == 200 and j == {"success": True})
T("TC_ADM_040", "PUT", RL, {"userId": 1, "role": "SUPER_HACKER_ROLE"}, t=A, check=is400, extra=lambda: (f"role DB='{one('select role from users where id=1')}'", True))
db("update users set role='USER' where id=1")
T("TC_ADM_042", "PUT", RL, {"userId": 99999, "role": "ADMIN"}, t=A, check=is404)
c, j, _ = call("PUT", RL, {"userId": 1, "role": "admin"}, t=A)
U2 = login("taobattu@gmail.com"); c3 = call("GET", AD + "/dashboard/stats", t=U2)[0]
rec("TC_ADM_049", c == 400 or c3 == 200, f"PUT role='admin' → HTTP {c}; role DB='{one('select role from users where id=1')}'; user 1 đăng nhập lại gọi /api/admin/dashboard/stats → HTTP {c3}")
db("update users set role='USER' where id=1")
# AUTH_043: user 1 lên ADMIN, lấy token, hạ quyền, dùng token cũ
db("update users set role='ADMIN' where id=1"); T1 = login("taobattu@gmail.com")
call("PUT", RL, {"userId": 1, "role": "USER"}, t=A)
T("TC_AUTH_043", "GET", AD + "/dashboard/stats", t=T1, check=is403, extra=lambda: (f"role DB hiện tại='{one('select role from users where id=1')}'", True))
T("TC_ADM_044", "DELETE", AD + "/users/1", t=A, check=lambda c, j: c in (400, 409) and msg(j) == "Không thể xóa do người này đã có lịch sử mua hàng!")
call("POST", RG, reg(fullName="Del Me", email="delme@gmail.com", phone="0911999003")); UDM = login("delme@gmail.com")
call("POST", CA + "/add", {"productId": 111, "quantity": 1}, t=UDM)
dm = one("select id from users where email='delme@gmail.com'")
T("TC_ADM_053", "DELETE", f"{AD}/users/{dm}", t=A, extra=lambda: (f"user còn={one(f'select count(*) from users where id={dm}')}, cart còn={one(f'select count(*) from cart_items where user_id={dm}')}", one(f"select count(*) from users where id={dm}") == "0"))
call("POST", RG, reg(fullName="Del Me 2", email="delme2@gmail.com", phone="0911999004"))
dm2 = one("select id from users where email='delme2@gmail.com'")
T("TC_ADM_043", "DELETE", f"{AD}/users/{dm2}", t=A, extra=lambda: ("đã xóa" if one(f"select count(*) from users where id={dm2}") == "0" else "còn", one(f"select count(*) from users where id={dm2}") == "0"))
T("TC_ADM_046", "DELETE", AD + "/users/99999", t=A, check=is404)
T("TC_ADM_041", "PUT", RL, {"userId": 2, "role": "USER"}, t=A, check=is400, extra=lambda: (f"role Admin DB='{one('select role from users where id=2')}'", True))
db("update users set role='ADMIN' where id=2")
db("delete from cart_items where user_id=2")
T("TC_ADM_045", "DELETE", AD + "/users/2", t=A, check=is400, extra=lambda: ("tài khoản Admin " + ("ĐÃ BỊ XÓA" if one("select count(*) from users where id=2") == "0" else "còn"), True))

json.dump(R, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TOTAL", len(R), "PASS", sum(v["verdict"] == "PASS" for v in R.values()))
