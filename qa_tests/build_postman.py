# -*- coding: utf-8 -*-
"""
Sinh lại toàn bộ Postman collection từ TestCase.xlsx (tên, mô tả, trạng thái, mức ưu tiên)
+ đặc tả request/assert bên dưới (đã kiểm chứng bằng qa_tests/run_all_testcases.py).

Quy ước assert: mỗi TC kiểm tra đúng "Kết quả mong đợi" trong Excel. Vì vậy:
  - TC trạng thái PASS            -> toàn bộ pm.test phải xanh.
  - TC trạng thái FAIL (Bug)      -> ít nhất 1 pm.test đỏ (đó là bug đã ghi nhận).
  - TC trạng thái CHƯA XÁC ĐỊNH   -> chỉ ghi nhận hành vi hiện tại (test "INFO" luôn xanh).
Chạy:  python -I qa_tests/build_postman.py   (từ thư mục gốc dự án)
Yêu cầu khi chạy collection: DB vừa reset bằng sql/full_setup_and_reset.sql; chạy theo thứ tự.
"""
import json, re, uuid, sys, os
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.join(ROOT, "TestCase.xlsx")
OUTD = os.path.join(ROOT, "postman")
SCHEMA = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
MODS = [("01_Auth_TaiKhoan", "AUTH"), ("02_SanPham_DanhMuc", "PROD"), ("03_GioHang_ThanhToan", "CART"),
        ("04_HoSo_DonHang", "PROF_ORD"), ("05_QuanTri_Admin", "ADM")]

# ------------------------------------------------------------------ JS helpers
LIB = r"""var B = pm.variables.get('base_url');
function v(k) { return pm.variables.get(k); }
function setv(k, x) { pm.collectionVariables.set(k, x); if (pm.environment && pm.environment.name) pm.environment.set(k, x); }
function api(m, p, t, b, cb) {
  var h = { 'Content-Type': 'application/json' }; if (t) h['Authorization'] = 'Bearer ' + v(t);
  var o = { url: B + p, method: m, header: h }; if (b !== undefined) o.body = { mode: 'raw', raw: JSON.stringify(b) };
  pm.sendRequest(o, function (e, r) { var j = null; try { j = r.json(); } catch (x) {} cb(r ? r.code : 0, j, r); });
}
function b64u(w) { return CryptoJS.enc.Base64.stringify(w).replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_'); }
function fakeJwt(uid, role, iss, expSec) {
  var h = b64u(CryptoJS.enc.Utf8.parse(JSON.stringify({ alg: 'HS256', typ: 'JWT' })));
  var p = b64u(CryptoJS.enc.Utf8.parse(JSON.stringify({ nameid: String(uid), role: role, iss: iss, aud: 'LapZoneClient', exp: Math.floor(Date.now() / 1000) + expSec })));
  return h + '.' + p + '.' + b64u(CryptoJS.HmacSHA256(h + '.' + p, v('jwt_key')));
}
function J() { try { return pm.response.json(); } catch (e) { return null; } }
"""

def st(*codes):
    return f"pm.test('HTTP status ∈ {list(codes)}', function () {{ pm.expect(pm.response.code).to.be.oneOf({json.dumps(list(codes))}); }});"
def chk(cond, label):
    return f"pm.test({json.dumps(label, ensure_ascii=False)}, function () {{ var j = J(); pm.expect(!!({cond}), {json.dumps(label, ensure_ascii=False)}).to.be.true; }});"
def msg(m):
    return chk(f"j && j.message === {json.dumps(m, ensure_ascii=False)}", f"message = '{m}'")
def save(var, expr):
    return f"try {{ var j = J(); setv('{var}', {expr}); }} catch (e) {{}}"
def after(js):  # follow-up check sau request chính (sendRequest bất đồng bộ, pm.test trong callback)
    return js
def info():
    return "pm.test('INFO (CHƯA XÁC ĐỊNH – gap yêu cầu): ghi nhận HTTP ' + pm.response.code, function () { pm.expect(true).to.be.true; });"

SPEC = {}   # id -> dict
def tc(tid, m, path, body=None, tok=None, tests=(), pre=(), raw=None):
    SPEC[tid] = dict(m=m, path=path, body=body, tok=tok, tests=list(tests), pre=list(pre), raw=raw)

def N(var):  # placeholder số (không ngoặc kép)
    return f"__NUM__{var}__"

L, RG, P, CA, CK, PF, LK, AD = "/api/auth/login", "/api/auth/register", "/api/products", "/api/cart", "/api/checkout/process", "/api/profile", "/api/orders/lookup", "/api/admin"
def reg(**k): return {**{"fullName": "QA", "email": "x@x.com", "phone": "0", "password": "Abc123@", "confirmPassword": "Abc123@", "address": "HN"}, **k}
def ck(**k): return {**{"customerName": "Le Van A", "customerPhone": "0901234567", "address": "123 Cầu Giấy, HN", "paymentMethod": "COD", "buyNowProductId": 102, "buyNowQuantity": 1}, **k}
S400, S401, S403, S404 = st(400), st(401), st(403), st(404)
S200 = st(200)
cartItemJs = "function itemOf(c, pid) { return (c && c.items || []).filter(function (i) { return i.productId === pid; })[0]; }"
def cart_check(tok, pid, cond, label):
    return f"""{cartItemJs}
api('GET', '/api/cart', '{tok}', undefined, function (c, j) {{ var it = itemOf(j, {pid}); pm.test({json.dumps(label, ensure_ascii=False)}, function () {{ pm.expect(!!({cond}), {json.dumps(label, ensure_ascii=False)}).to.be.true; }}); }});"""
def cart_cleanup(tok, pid):
    return f"""{cartItemJs}
api('GET', '/api/cart', '{tok}', undefined, function (c, j) {{ var it = itemOf(j, {pid}); if (it) api('DELETE', '/api/cart/' + it.id, '{tok}', undefined, function () {{}}); }});"""
def stock_pre(pid, var):
    return f"api('GET', '/api/products/{pid}', null, undefined, function (c, j) {{ setv('{var}', j.product.stock); }});"
def stock_check(pid, cond, label):  # cond dùng s (stock mới)
    return f"api('GET', '/api/products/{pid}', null, undefined, function (c, j) {{ var s = j.product.stock; pm.test({json.dumps(label, ensure_ascii=False)}, function () {{ pm.expect(!!({cond}), {json.dumps(label, ensure_ascii=False)}).to.be.true; }}); }});"
def user_role_check(email, cond, label):
    return f"api('GET', '/api/admin/users?keyword={email}', 'admin_token', undefined, function (c, j) {{ var u = (j.users || [])[0]; pm.test({json.dumps(label, ensure_ascii=False)}, function () {{ pm.expect(!!({cond}), {json.dumps(label, ensure_ascii=False)}).to.be.true; }}); }});"
def login_pre(email, pwd, var):
    return f"api('POST', '/api/auth/login', null, {{ emailOrPhone: '{email}', password: '{pwd}' }}, function (c, j) {{ if (j && j.token) setv('{var}', j.token); }});"
def reg_login_pre(email, phone, var, name="QA User"):
    return f"""api('POST', '/api/auth/register', null, {{ fullName: '{name}', email: '{email}', phone: '{phone}', password: 'Abc123@', confirmPassword: 'Abc123@', address: 'HN' }}, function () {{
  api('POST', '/api/auth/login', null, {{ emailOrPhone: '{email}', password: 'Abc123@' }}, function (c, j) {{ if (j && j.token) setv('{var}', j.token); }});
}});"""
def order_status_check(cond, label):
    return f"api('GET', '/api/orders/' + v('order_id'), null, undefined, function (c, j) {{ pm.test({json.dumps(label, ensure_ascii=False)}, function () {{ pm.expect(!!({cond}), {json.dumps(label, ensure_ascii=False)}).to.be.true; }}); }});"

# ================================================================== MODULE 1 AUTH
tc("TC_AUTH_001", "POST", L, {"emailOrPhone": "{{user_email}}", "password": "{{user_password}}"}, tests=[S200, chk("j.token && j.fullName === 'User Seed' && j.role === 'USER' && j.userId === 1", "token + fullName 'User Seed' + role USER + userId 1")])
tc("TC_AUTH_002", "POST", L, {"emailOrPhone": "{{user_phone}}", "password": "{{user_password}}"}, tests=[S200, chk("j.token && j.role === 'USER'", "token + role USER")])
tc("TC_AUTH_003", "POST", L, {"emailOrPhone": "{{admin_email}}", "password": "{{admin_password}}"}, tests=[S200, chk("j.role === 'ADMIN' && j.userId === 2", "role ADMIN, userId 2")])
for t, e in [("004", "taobattu@gmail.com"), ("005", "notfound_user@gmail.com"), ("006", "0999888777")]:
    tc(f"TC_AUTH_{t}", "POST", L, {"emailOrPhone": e, "password": "WrongPassword123" if t == "004" else "Abc123@"}, tests=[S401, msg("Sai tài khoản hoặc mật khẩu!")])
tc("TC_AUTH_007", "POST", L, {"emailOrPhone": "TAOBATTU@GMAIL.COM", "password": "Abc123@"}, tests=[S200])
tc("TC_AUTH_008", "POST", L, {"emailOrPhone": "  taobattu@gmail.com  ", "password": "Abc123@"}, tests=[S200])
tc("TC_AUTH_009", "POST", L, {"emailOrPhone": "", "password": ""}, tests=[S400])
tc("TC_AUTH_010", "POST", L, {"emailOrPhone": "taobattu@gmail.com", "password": ""}, tests=[S400])
tc("TC_AUTH_011", "POST", L, {"emailOrPhone": None, "password": None}, tests=[S400])
tc("TC_AUTH_012", "POST", L, {"emailOrPhone": "' OR '1'='1", "password": "' OR '1'='1"}, tests=[S401])
tc("TC_AUTH_013", "POST", L, {"emailOrPhone": "taobattu@gmail.com", "password": "bad"},
   pre=["for (var i = 0; i < 19; i++) api('POST', '/api/auth/login', null, { emailOrPhone: 'taobattu@gmail.com', password: 'bad' }, function () {});"],
   tests=["pm.test('Lần thử sai thứ 20 phải bị chặn (429 / khóa tài khoản)', function () { pm.expect(pm.response.code).to.equal(429); });"])
tc("TC_AUTH_014", "POST", RG, reg(fullName="Nguyen Van Test", email="nvtest01@gmail.com", phone="0912345001", password="Password123@", confirmPassword="Password123@"),
   tests=[S200, chk("j.message === 'Đăng ký thành công!' && j.userId > 0", "message 'Đăng ký thành công!' + userId > 0")])
tc("TC_AUTH_015", "POST", RG, reg(email="nvb_mismatch@gmail.com", phone="0912345002", confirmPassword="DifferentPassword"), tests=[S400, msg("Mật khẩu xác nhận không khớp!")])
tc("TC_AUTH_016", "POST", RG, reg(email="taobattu@gmail.com", phone="0988776655"), tests=[S400, msg("Email hoặc Số điện thoại đã tồn tại!")])
tc("TC_AUTH_017", "POST", RG, reg(email="unique_email99@gmail.com", phone="0900000001"), tests=[S400, msg("Email hoặc Số điện thoại đã tồn tại!")])
tc("TC_AUTH_018", "POST", RG, reg(email="TAOBATTU@GMAIL.COM", phone="0911222333"), tests=[S400])
for t, kw in [("019", dict(fullName="", email="emptyname@gmail.com", phone="0911000001")), ("020", dict(fullName="   ", email="spacename@gmail.com", phone="0911000002")),
              ("021", dict(email="", phone="0911000003")), ("022", dict(email="not-an-email", phone="0911000004")), ("023", dict(email="nophone@gmail.com", phone="")),
              ("024", dict(email="badphone@gmail.com", phone="abcdef1234")), ("025", dict(email="shortphone@gmail.com", phone="123")),
              ("026", dict(email="longphone@gmail.com", phone="0123456789012345678912345")),
              ("027", dict(email="emptypass@gmail.com", phone="0911000005", password="", confirmPassword="")),
              ("028", dict(email="weakpass@gmail.com", phone="0911000006", password="1", confirmPassword="1")),
              ("029", dict(email="spacepass@gmail.com", phone="0911000007", password="      ", confirmPassword="      ")),
              ("030", dict(fullName="{{long_name}}", email="longname@gmail.com", phone="0911000008")),
              ("031", dict(fullName="Long Email", email="{{long_email}}", phone="0911000009")),
              ("032", dict(fullName="<script>alert('XSS')</script>", email="xss_user@gmail.com", phone="0911000010", address="<img src=x onerror=alert(1)>"))]:
    pre = []
    if t == "030": pre = ["pm.variables.set('long_name', 'A'.repeat(300));"]
    if t == "031": pre = ["pm.variables.set('long_email', 'a'.repeat(250) + '@gmail.com');"]
    tc(f"TC_AUTH_{t}", "POST", RG, reg(**kw), pre=pre, tests=[S400])
tc("TC_AUTH_033", "POST", RG, {**reg(fullName="Hacker", email="role_hack@gmail.com", phone="0911000011"), "role": "ADMIN"},
   tests=[S200, user_role_check("role_hack@gmail.com", "u && u.role === 'USER'", "role trong DB vẫn là USER")])
tc("TC_AUTH_034", "POST", RG, reg(fullName="No Address User", email="noaddr@gmail.com", phone="0911000012", address=None),
   tests=[S200, user_role_check("noaddr@gmail.com", "u && u.address === null", "address lưu NULL")])
tc("TC_AUTH_035", "GET", PF, tests=[S401])
tc("TC_AUTH_036", "GET", PF, tok="fake_jwt_token", tests=[S401])
tc("TC_AUTH_037", "GET", PF, tok="malformed_token", tests=[S401])
tc("TC_AUTH_038", "GET", AD + "/dashboard/stats", tok="user_token", tests=[S403])
tc("TC_AUTH_039", "GET", AD + "/dashboard/stats", tests=[S401])
tc("TC_AUTH_040", "GET", L, tests=[st(405)])
tc("TC_AUTH_041", "GET", PF, tok="tmp_token", pre=["setv('tmp_token', fakeJwt(1, 'USER', 'LapZoneApi', -600));"], tests=[S401])
tc("TC_AUTH_042", "GET", PF, tok="tmp_token", pre=["setv('tmp_token', fakeJwt(1, 'USER', 'Evil', 3600));"], tests=[S401])
tc("TC_AUTH_043", "GET", AD + "/dashboard/stats", tok="t1_token",
   pre=["""api('GET', '/api/admin/users?keyword=nvtest01', 'admin_token', undefined, function (c, j) {
  var id = j.users[0].id; setv('ub_id', id);
  api('PUT', '/api/admin/users/role', 'admin_token', { userId: id, role: 'ADMIN' }, function () {
    api('POST', '/api/auth/login', null, { emailOrPhone: 'nvtest01@gmail.com', password: 'Password123@' }, function (c2, j2) {
      setv('t1_token', j2.token);
      api('PUT', '/api/admin/users/role', 'admin_token', { userId: id, role: 'USER' }, function () {});
    });
  });
});"""],
   tests=["pm.test('Token cấp khi còn ADMIN phải mất quyền sau khi bị hạ xuống USER (403)', function () { pm.expect(pm.response.code).to.equal(403); });"])
tc("TC_AUTH_044", "POST", CA + "/add", {"productId": 101, "quantity": 1}, tok="ud_token",
   pre=["""api('POST', '/api/auth/register', null, { fullName: 'To Delete', email: 'todelete@gmail.com', phone: '0911999002', password: 'Abc123@', confirmPassword: 'Abc123@', address: 'HN' }, function () {
  api('POST', '/api/auth/login', null, { emailOrPhone: 'todelete@gmail.com', password: 'Abc123@' }, function (c, j) {
    setv('ud_token', j.token);
    api('GET', '/api/admin/users?keyword=todelete', 'admin_token', undefined, function (c2, j2) {
      api('DELETE', '/api/admin/users/' + j2.users[0].id, 'admin_token', undefined, function () {});
    });
  });
});"""], tests=[st(401, 404)])
tc("TC_AUTH_045", "POST", L, {"emailOrPhone": "{{user_email}}", "password": "{{user_password}}"},
   tests=[S200, """pm.test('JWT: iss/aud đúng, có role USER, hạn ≈ 120 phút', function () {
  var p = JSON.parse(CryptoJS.enc.Base64.parse(J().token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')).toString(CryptoJS.enc.Utf8));
  var mins = (p.exp - Date.now() / 1000) / 60;
  pm.expect(p.iss).to.equal('LapZoneApi'); pm.expect(p.aud).to.equal('LapZoneClient');
  pm.expect(JSON.stringify(p)).to.include('USER'); pm.expect(mins).to.be.within(118, 120.5);
});"""])
tc("TC_AUTH_046", "POST", L, {"emailOrPhone": "nvtest01@gmail.com", "password": "Password123@"}, tests=[S200, chk("j.role === 'USER'", "role USER")])

# ================================================================== MODULE 2 PRODUCTS
def every(cond, label): return chk(f"j.products.length > 0 && j.products.every(function (p) {{ return {cond}; }})", label)
tc("TC_PROD_001", "GET", "/api/categories", tests=[S200, chk("j.length === 7 && j.map(function (c) { return c.id; }).join() === '1,2,3,4,5,6,7'", "7 danh mục, id 1..7 tăng dần")])
tc("TC_PROD_002", "GET", P, tests=[S200, chk("j.products.length === 12 && j.totalElements === 40 && j.currentPage === 0 && j.totalPages === 4", "12 SP, totalElements 40, currentPage 0, totalPages 4")])
tc("TC_PROD_003", "GET", "/api/search?keyword=Dell", tests=[S200, chk("j.totalElements > 0", "có kết quả")])
tc("TC_PROD_004", "GET", P + "?keyword=macbook", tests=[S200, every("p.name.toLowerCase().indexOf('macbook') >= 0", "mọi SP chứa 'macbook'")])
tc("TC_PROD_005", "GET", P + "?keyword=Chi%20Ti%E1%BA%BFt%20C%E1%BA%A5u%20H%C3%ACnh&size=100", tests=[S200, chk("j.totalElements > 0", "tìm thấy SP theo more_info")])
tc("TC_PROD_006", "GET", P + "?keyword=XYZ_NON_EXISTENT_9999", tests=[S200, chk("j.products.length === 0 && j.totalElements === 0 && j.totalPages === 0", "products [] / totalElements 0 / totalPages 0")])
tc("TC_PROD_007", "GET", P + "?categoryId=1&size=100", tests=[S200, every("p.categoryId === 1", "mọi SP categoryId = 1")])
tc("TC_PROD_008", "GET", P + "?categoryId=9999", tests=[S200, chk("j.products.length === 0 && j.totalElements === 0", "rỗng")])
tc("TC_PROD_009", "GET", P + "?minPrice=20000000&maxPrice=30000000&size=100", tests=[S200, every("p.price >= 20000000 && p.price <= 30000000", "20tr ≤ price ≤ 30tr")])
tc("TC_PROD_010", "GET", P + "?minPrice=22990000&maxPrice=22990000", tests=[S200, chk("j.products.map(function (p) { return p.id; }).sort(function (a, b) { return a - b; }).join() === '1,2,10,114'", "đúng ID 1, 2, 10, 114")])
tc("TC_PROD_011", "GET", P + "?minPrice=50000000&maxPrice=10000000", tests=[S400])
tc("TC_PROD_012", "GET", P + "?minPrice=-5000000&maxPrice=-1000", tests=[S400])
for t, q, f, val in [("013", "cpu=i7", "cpu", "i7"), ("014", "gpu=RTX%204060", "gpu", "rtx 4060"), ("015", "ram=32GB", "ram", "32gb"), ("016", "storage=1TB", "storage", "1tb"), ("017", "screen=OLED", "screen", "oled")]:
    tc(f"TC_PROD_{t}", "GET", f"{P}?{q}&size=100", tests=[S200, every(f"(p.{f} || '').toLowerCase().indexOf('{val}') >= 0", f"mọi SP có {f} chứa '{val}'")])
tc("TC_PROD_018", "GET", P + "?categoryId=7&cpu=Ultra%205&ram=32GB&minPrice=20000000&maxPrice=25000000",
   tests=[S200, every("p.categoryId === 7 && p.price >= 20000000 && p.price <= 25000000 && p.cpu.toLowerCase().indexOf('ultra 5') >= 0 && p.ram.toLowerCase().indexOf('32gb') >= 0", "thỏa đồng thời 5 bộ lọc")])
tc("TC_PROD_019", "GET", P + "?sort=price_asc&size=100", tests=[S200, chk("j.products.every(function (p, i, a) { return i === 0 || a[i - 1].price <= p.price; }) && j.products[0].price === 17890000", "giá tăng dần từ 17.890.000")])
tc("TC_PROD_020", "GET", P + "?sort=price_desc&size=100", tests=[S200, chk("j.products.every(function (p, i, a) { return i === 0 || a[i - 1].price >= p.price; }) && j.products[0].price === 89990000", "giá giảm dần từ 89.990.000")])
tc("TC_PROD_021", "GET", P + "?sort=newest", tests=[S200, chk("j.products[0].id === 118", "ID 118 đứng đầu")])
tc("TC_PROD_022", "GET", P + "?sort=invalid_sort_value&size=5", tests=["pm.test('400 hoặc fallback newest (118,117,116,115,114)', function () { var j = J(); pm.expect(pm.response.code === 400 || j.products.map(function (p) { return p.id; }).join() === '118,117,116,115,114').to.be.true; });"])
tc("TC_PROD_023", "GET", P + "?page=1&size=12", tests=[S200, chk("j.products.length === 12 && j.currentPage === 1 && j.totalPages === 4", "trang 2: 12 SP, totalPages 4")])
tc("TC_PROD_024", "GET", P + "?page=3&size=12", tests=[S200, chk("j.products.length === 4 && j.totalElements === 40", "4 SP còn lại, totalElements 40")])
tc("TC_PROD_025", "GET", P + "?page=100&size=12", tests=[S200, chk("j.products.length === 0 && j.totalElements === 40", "products [] nhưng totalElements vẫn 40")])
for t, q in [("026", "page=-1&size=12"), ("027", "page=0&size=0"), ("028", "page=0&size=-5"), ("029", "page=0&size=1000000")]:
    tc(f"TC_PROD_{t}", "GET", f"{P}?{q}", tests=[S400])
tc("TC_PROD_030", "GET", P + "?keyword=%25", tests=[S200, chk("j.totalElements === 0", "'%' được escape → 0 SP")])
tc("TC_PROD_031", "GET", P + "?keyword=_", tests=[S200, chk("j.totalElements === 0", "'_' được escape → 0 SP")])
tc("TC_PROD_032", "GET", P + "?keyword=%27%20OR%201%3D1--", tests=[S200, chk("j.totalElements === 0", "không SQLi → 0 SP")])
tc("TC_PROD_033", "GET", P + "/1", tests=[S200, chk("j.product.id === 1 && j.product.categoryName === 'Dell' && j.product.cpu", "SP 1, categoryName Dell, có cpu")])
tc("TC_PROD_034", "GET", P + "/1", tests=[S200, """var rel = J().relatedProducts;
pm.test('relatedProducts: 1..4 SP, không chứa ID 1', function () { pm.expect(rel.length).to.be.within(1, 4); pm.expect(rel.map(function (r) { return r.id; })).to.not.include(1); });
api('GET', '/api/products?categoryId=5&size=100', null, undefined, function (c, j) {
  var ids = j.products.map(function (p) { return p.id; });
  pm.test('relatedProducts đều thuộc Category 5', function () { rel.forEach(function (r) { pm.expect(ids).to.include(r.id); }); });
});"""])
tc("TC_PROD_035", "GET", P + "/1", tests=[S200, info()])
tc("TC_PROD_036", "GET", P + "/1", tests=[S200, chk("j.relatedProducts.every(function (r) { return r.categoryId === 5 && r.stock > 0; })", "relatedProducts có categoryId và stock thực")])
tc("TC_PROD_037", "GET", P + "/99999", tests=[S404])
tc("TC_PROD_038", "GET", P + "/0", tests=[st(400, 404)])
tc("TC_PROD_039", "GET", P + "/-10", tests=[st(400, 404)])
tc("TC_PROD_040", "GET", P + "/abc", tests=[S404])
tc("TC_PROD_041", "GET", P + "/13", tests=[S200, chk("j.product.stock === 0", "stock = 0")])
tc("TC_PROD_042", "GET", P + "?minPrice=abc", tests=[S400])
tc("TC_PROD_043", "GET", P + "?query=Dell", pre=["api('GET', '/api/products?keyword=Dell', null, undefined, function (c, j) { setv('dell_total', j.totalElements); });"],
   tests=[S200, chk("j.totalElements === Number(v('dell_total'))", "kết quả = keyword=Dell")])
tc("TC_PROD_044", "GET", P + "?keyword=Dell&query=Apple", pre=["api('GET', '/api/products?keyword=Dell', null, undefined, function (c, j) { setv('dell_total', j.totalElements); });"],
   tests=[S200, chk("j.totalElements === Number(v('dell_total'))", "keyword được ưu tiên")])
tc("TC_PROD_045", "GET", P + "?page=0&size=7", tests=[S200, chk("j.products.length === 7 && j.totalPages === 6 && j.totalElements === 40", "7 SP, totalPages 6")])
tc("TC_PROD_046", "GET", "/api/categories", tests=[S200])

# ================================================================== MODULE 3 CART
U = "user_token"; A = "admin_token"
tc("TC_CART_001", "GET", CA, tok=U, tests=[S200, chk("'items' in j && 'total' in j", "có items và total")])
tc("TC_CART_002", "GET", CA, tests=[S401])
tc("TC_CART_003", "POST", CA + "/add", {"productId": 101, "quantity": 2}, tok=U, tests=[S200, chk("j.success === true", "{success:true}"), cart_check(U, 101, "it && it.quantity === 2", "SP101 trong giỏ quantity = 2")])
tc("TC_CART_004", "POST", CA + "/add", {"productId": 101, "quantity": 1}, tok=U, tests=[S200, cart_check(U, 101, "it && it.quantity === 3", "quantity cộng dồn = 3")])
tc("TC_CART_005", "POST", CA + "/add", {"productId": 1, "quantity": 99}, tok=U, tests=[st(200, 400), cart_check(U, 1, "it && it.quantity === 2", "quantity bị giới hạn = stock 2")])
tc("TC_CART_045", "POST", CA + "/add", {"productId": 1, "quantity": 1}, tok=U, tests=[S200, cart_check(U, 1, "it && it.quantity === 2", "quantity vẫn = 2")])
tc("TC_CART_006", "POST", CA + "/add", {"productId": 102, "quantity": 0}, tok=U, tests=[S400, cart_cleanup(U, 102)])
tc("TC_CART_007", "POST", CA + "/add", {"productId": 102, "quantity": -5}, tok=U, tests=[S400, cart_cleanup(U, 102)])
tc("TC_CART_008", "POST", CA + "/add", {"productId": 13, "quantity": 1}, tok=U, tests=[S400, cart_cleanup(U, 13)])
tc("TC_CART_009", "POST", CA + "/add", {"productId": 99999, "quantity": 1}, tok=U, tests=[st(400, 404)])
tc("TC_CART_010", "POST", CA + "/add", {"productId": 1, "quantity": 1}, tests=[S401])
SAVE_ITEMS = """api('GET', '/api/cart', 'user_token', undefined, function (c, j) { (j.items || []).forEach(function (i) { setv('ci_' + i.productId, i.id); }); });"""
tc("TC_CART_011", "PUT", CA + "/update", {"cartItemId": N("ci_101"), "quantity": 2}, tok=U, pre=[SAVE_ITEMS], tests=[S200, chk("j.success === true", "{success:true}"), cart_check(U, 101, "it && it.quantity === 2", "quantity = 2")])
tc("TC_CART_012", "PUT", CA + "/update", {"cartItemId": N("ci_103"), "quantity": 0}, tok=U,
   pre=["api('POST', '/api/cart/add', 'user_token', { productId: 103, quantity: 1 }, function () { " + SAVE_ITEMS + " });"], tests=[S200, cart_check(U, 103, "!it", "item bị xóa khỏi giỏ")])
tc("TC_CART_013", "PUT", CA + "/update", {"cartItemId": N("ci_1"), "quantity": 500}, tok=U, pre=[SAVE_ITEMS], tests=[S200, cart_check(U, 1, "it && it.quantity === 2", "quantity = stock 2")])
ADMIN_ITEM = lambda pid, var: f"api('POST', '/api/cart/add', 'admin_token', {{ productId: {pid}, quantity: 2 }}, function () {{ api('GET', '/api/cart', 'admin_token', undefined, function (c, j) {{ j.items.forEach(function (i) {{ if (i.productId === {pid}) setv('{var}', i.id); }}); }}); }});"
tc("TC_CART_014", "PUT", CA + "/update", {"cartItemId": N("admin_cart_item_id"), "quantity": 1}, tok=U, pre=[ADMIN_ITEM(104, "admin_cart_item_id")], tests=[st(403, 404), cart_check(A, 104, "it && it.quantity === 2", "giỏ Admin không bị đổi (vẫn 2)")])
tc("TC_CART_015", "PUT", CA + "/update", {"cartItemId": 99999, "quantity": 2}, tok=U, tests=[S404])
tc("TC_CART_016", "DELETE", CA + "/{{ci_106}}", tok=U, pre=["api('POST', '/api/cart/add', 'user_token', { productId: 106, quantity: 1 }, function () { " + SAVE_ITEMS + " });"],
   tests=[S200, chk("j.success === true", "{success:true}"), cart_check(U, 106, "!it", "item đã bị xóa")])
tc("TC_CART_017", "DELETE", CA + "/{{admin_cart_item_id}}", tok=U, tests=[st(403, 404), cart_check(A, 104, "!!it", "giỏ Admin không bị xóa")])
tc("TC_CART_018", "DELETE", CA + "/99999", tok=U, tests=[S404])
tc("TC_CART_019", "POST", CK, ck(), pre=[stock_pre(102, "s102")],
   tests=[S200, chk("j.total === 24590000 && j.paymentMethod === 'COD' && j.orderId > 0", "total 24.590.000, COD"), save("order_id", "j.orderId"),
          "api('GET', '/api/orders/' + J().orderId, null, undefined, function (c, j) { pm.test(\"status = 'CHỜ XÁC NHẬN'\", function () { pm.expect(j.status).to.equal('CHỜ XÁC NHẬN'); }); });",
          stock_check(102, "s === Number(v('s102')) - 1", "stock SP102 giảm 1")])
tc("TC_CART_049", "GET", "/api/orders/{{order_id}}", tests=[S200, chk("j.status === 'CHỜ XÁC NHẬN' && j.paymentMethod === 'COD' && j.totalAmount === j.details.reduce(function (s, d) { return s + d.price * d.quantity; }, 0)", "status, paymentMethod, totalAmount = Σ details")])
tc("TC_CART_020", "POST", CK, ck(customerName="Le Van B", customerPhone="0901234568", address="456 Đống Đa, HN", paymentMethod="BANK", buyNowProductId=103),
   tests=[S200, "api('GET', '/api/orders/' + J().orderId, null, undefined, function (c, j) { pm.test(\"status = 'CHỜ THANH TOÁN'\", function () { pm.expect(j.status).to.equal('CHỜ THANH TOÁN'); }); });"])
tc("TC_CART_021", "POST", CK, ck(customerName="User Seed", customerPhone="0900000001", address="Hà Nội", buyNowProductId=105), tok=U,
   tests=[S200, save("user_order_id", "j.orderId"), "api('GET', '/api/orders/' + J().orderId, null, undefined, function (c, j) { pm.test('đơn gắn user_id = 1', function () { pm.expect(j.userId).to.equal(1); }); });"])
tc("TC_CART_022", "POST", CK, {**ck(customerName="User Seed", customerPhone="0900000001", address="123 Đường Láng", buyNowProductId=None, buyNowQuantity=None), "selectedCartItemIds": [N("ci_101")]}, tok=U,
   pre=[SAVE_ITEMS, stock_pre(101, "s101")], tests=[S200, stock_check(101, "s === Number(v('s101')) - 2", "stock SP101 giảm 2"), cart_check(U, 101, "!it", "item đã thanh toán bị xóa khỏi giỏ")])
tc("TC_CART_023", "POST", CK, {**ck(customerName="Guest", customerPhone="0901112223", address="HN", buyNowProductId=None), "selectedCartItemIds": [1]}, tests=[S401, msg("Vui lòng đăng nhập để thanh toán giỏ hàng.")])
tc("TC_CART_048", "POST", CK, {**ck(buyNowProductId=None), "selectedCartItemIds": [1]}, tok="tmp_token", pre=["setv('tmp_token', fakeJwt(1, 'USER', 'LapZoneApi', -600));"], tests=[S401])
tc("TC_CART_024", "POST", CK, {"customerName": "Test", "customerPhone": "0901112223", "address": "HN", "paymentMethod": "COD"}, tests=[S400, msg("Không có sản phẩm để thanh toán.")])
tc("TC_CART_025", "POST", CK, ck(buyNowProductId=99999), tests=[S400, msg("Sản phẩm không tồn tại.")])
tc("TC_CART_026", "POST", CK, ck(customerName="Zero Qty", buyNowQuantity=0), tests=[S400])
tc("TC_CART_027", "POST", CK, ck(customerName="Negative Qty", buyNowQuantity=-3), pre=[stock_pre(102, "s102")], tests=[S400, stock_check(102, "s <= Number(v('s102'))", "tồn kho không được tăng")])
tc("TC_CART_028", "POST", CK, ck(customerName="Out Stock", buyNowProductId=13, buyNowQuantity=2), tests=[S400])
tc("TC_CART_029", "POST", CK, ck(customerName="Over Stock", buyNowProductId=109, buyNowQuantity=500), tests=[S400])
tc("TC_CART_030", "POST", CK, {**ck(customerName="User A", customerPhone="0900000001", address="HN", buyNowProductId=None), "selectedCartItemIds": [N("admin_cart_item_id2")]}, tok=U,
   pre=[ADMIN_ITEM(107, "admin_cart_item_id2")], tests=[S400, cart_check(A, 107, "!!it", "giỏ Admin (SP107) không bị xóa")])
for t, kw in [("031", dict(customerName="")), ("032", dict(customerPhone="")), ("033", dict(customerPhone="not_a_phone")), ("035", dict(address="")),
              ("036", dict(paymentMethod="FREE_MONEY")), ("038", dict(customerName="<script>alert(1)</script>", address="<svg onload=alert(1)>"))]:
    tc(f"TC_CART_{t}", "POST", CK, ck(**kw), tests=[S400])
NOLEAK = chk("!(j && j.message && j.message.indexOf('Có lỗi xảy ra') === 0)", "không lộ thông điệp lỗi DB")
tc("TC_CART_034", "POST", CK, ck(customerPhone="0123456789012345678912345"), tests=[S400, NOLEAK])
tc("TC_CART_037", "POST", CK, ck(paymentMethod="VERY_LONG_PAYMENT_METHOD_NAME_123"), tests=[S400, NOLEAK])
tc("TC_CART_044", "POST", CK, ck(customerName="{{long_name}}", buyNowProductId=117), pre=["pm.variables.set('long_name', 'N'.repeat(300));"], tests=[S400, NOLEAK])
tc("TC_CART_039", "POST", CK, ck(customerName="Default Qty", buyNowProductId=117, buyNowQuantity=None), tests=[S200, chk("j.total === 27990000", "total = 1 × 27.990.000")])
tc("TC_CART_040", "POST", CK, {**ck(customerName="Empty Array", buyNowProductId=None, buyNowQuantity=None), "selectedCartItemIds": []}, tests=[S400, msg("Không có sản phẩm để thanh toán.")])
tc("TC_CART_041", "POST", CK, ck(customerName=None, buyNowProductId=117), tests=[S400])
tc("TC_CART_042", "GET", CA, tok="ue_token", pre=[reg_login_pre("emptycart@gmail.com", "0911999001", "ue_token", "Empty Cart")], tests=[S200, chk("j.items.length === 0 && j.total === 0", "items [] / total 0")])
tc("TC_CART_043", "POST", CA + "/add", tok=U, raw='{"productId":101,"quantity":999999999999999}', tests=[S400])
tc("TC_CART_046", "POST", CK, {**ck(customerName="User A", customerPhone="0900000001", buyNowProductId=None), "selectedCartItemIds": [N("ci_108"), N("admin_cart_item_id3")]}, tok=U,
   pre=["api('POST', '/api/cart/add', 'user_token', { productId: 108, quantity: 1 }, function () { " + SAVE_ITEMS + " });", ADMIN_ITEM(110, "admin_cart_item_id3")],
   tests=[cart_check(A, 110, "!!it", "giỏ Admin (SP110) không bị ảnh hưởng")])
tc("TC_CART_047", "POST", CK, {**ck(buyNowProductId=None), "selectedCartItemIds": [N("ue_item")]}, tok="ue_token",
   pre=["""// SP 4 có stock = 2 (seed). User A và User B (emptycart) mỗi người cho 2 chiếc vào giỏ; User A thanh toán trước.
api('POST', '/api/cart/add', 'user_token', { productId: 4, quantity: 2 }, function () {
  api('POST', '/api/cart/add', 'ue_token', { productId: 4, quantity: 2 }, function () {
    api('GET', '/api/cart', 'ue_token', undefined, function (c, j) { j.items.forEach(function (i) { if (i.productId === 4) setv('ue_item', i.id); }); });
    api('GET', '/api/cart', 'user_token', undefined, function (c, j) {
      var ids = j.items.filter(function (i) { return i.productId === 4; }).map(function (i) { return i.id; });
      api('POST', '/api/checkout/process', 'user_token', { customerName: 'User A', customerPhone: '0900000001', address: 'HN', paymentMethod: 'COD', selectedCartItemIds: ids }, function () {});
    });
  });
});"""], tests=["pm.test('Lần thanh toán thứ 2 (kho đã hết) phải bị từ chối 400', function () { pm.expect(pm.response.code).to.equal(400); });"])

# ================================================================== MODULE 4 PROFILE / ORDERS
tc("TC_PROF_001", "GET", PF, tok=U, tests=[S200, chk("j.id === 1 && !('password' in j)", "id 1, không có password")])
tc("TC_PROF_002", "GET", PF, tok=A, tests=[S200, chk("j.role === 'ADMIN'", "role ADMIN")])
tc("TC_PROF_003", "GET", PF, tests=[S401])
tc("TC_PROF_004", "PUT", PF, {"fullName": "User Seed Updated", "phone": "0900000001", "address": "456 Nguyễn Trãi, Hà Nội"}, tok=U,
   tests=[S200, chk("j.success === true", "{success:true}"), "api('GET', '/api/profile', 'user_token', undefined, function (c, j) { pm.test('fullName đã cập nhật', function () { pm.expect(j.fullName).to.equal('User Seed Updated'); }); });"])
tc("TC_PROF_005", "PUT", PF, {"fullName": "User Seed", "phone": "0900000002", "address": "Hà Nội"}, tok=U, tests=[st(400, 409)])
for t, b in [("006", {"fullName": "", "phone": "0900000001", "address": "Hà Nội"}), ("007", {"fullName": "   ", "phone": "0900000001", "address": "Hà Nội"}),
             ("008", {"fullName": "User Seed", "phone": "invalid_phone_abc", "address": "Hà Nội"}), ("009", {"fullName": "User Seed", "phone": "0123456789012345678912345", "address": "Hà Nội"}),
             ("010", {"fullName": "{{long_name}}", "phone": "0900000001", "address": "Hà Nội"}), ("011", {"fullName": "<script>alert('XSS')</script>", "phone": "0900000001", "address": "<img src=x onerror=alert(1)>"})]:
    tc(f"TC_PROF_{t}", "PUT", PF, b, tok=U, pre=["pm.variables.set('long_name', 'U'.repeat(300));"] if t == "010" else [], tests=[S400])
tc("TC_PROF_012", "PUT", PF, {"fullName": "User Seed", "phone": "0900000001", "address": "HN", "role": "ADMIN", "email": "hacked@gmail.com"}, tok=U,
   tests=[S200, "api('GET', '/api/profile', 'user_token', undefined, function (c, j) { pm.test('email và role không đổi', function () { pm.expect(j.email).to.equal('taobattu@gmail.com'); pm.expect(j.role).to.equal('USER'); }); });"])
tc("TC_PROF_013", "PUT", PF, {"fullName": "Anon", "phone": "0900000001", "address": "HN"}, tests=[S401])
tc("TC_PROF_014", "PUT", PF + "/password", {"oldPassword": "Abc123@", "newPassword": "NewPass123@"}, tok=U, tests=[info()])
tc("TC_PROF_015", "PUT", PF, {"fullName": None, "phone": "0900000001", "address": "HN"}, tok=U, tests=[S400])
NF = "Không tìm thấy đơn hàng hoặc SĐT không khớp."
tc("TC_ORD_001", "POST", LK, {"orderId": N("order_id"), "customerPhone": "0901234567"}, tests=[S200, chk("j.orderId === Number(v('order_id'))", "trả về đúng orderId")])
tc("TC_ORD_002", "POST", LK, {"orderId": N("order_id"), "customerPhone": "  0901234567  "}, tests=[S200])
tc("TC_ORD_003", "POST", LK, {"orderId": N("order_id"), "customerPhone": "0999999999"}, tests=[S404, msg(NF)])
tc("TC_ORD_004", "POST", LK, {"orderId": 99999, "customerPhone": "0901234567"}, tests=[S404, msg(NF)])
tc("TC_ORD_005", "POST", LK, {"orderId": 0, "customerPhone": "0901234567"}, tests=[st(400, 404)])
tc("TC_ORD_006", "POST", LK, {"orderId": -5, "customerPhone": "0901234567"}, tests=[st(400, 404)])
tc("TC_ORD_007", "POST", LK, {"orderId": N("order_id"), "customerPhone": ""}, tests=[st(400, 404)])
tc("TC_ORD_008", "POST", LK, {"orderId": N("order_id"), "customerPhone": None}, tests=[S400])
tc("TC_ORD_009", "GET", "/api/orders/{{order_id}}", tests=[S200, chk("j.details.length > 0 && j.details[0].productName", "có details kèm productName")])
tc("TC_ORD_010", "GET", "/api/orders/99999", tests=[S404])
tc("TC_ORD_011", "GET", "/api/orders/{{order_id}}", tests=[st(401, 403)])
tc("TC_ORD_012", "GET", "/api/orders/{{user_order_id}}", tok="ub_token", pre=[login_pre("nvtest01@gmail.com", "Password123@", "ub_token")], tests=[S403])
tc("TC_ORD_013", "GET", "/api/orders/my", tok=U, tests=[info()])
tc("TC_ORD_014", "PUT", "/api/orders/{{order_id}}/cancel", tok=U, tests=[info()])
tc("TC_ORD_015", "GET", "/api/orders/0", tests=[S404])
tc("TC_ORD_016", "GET", "/api/orders/-1", tests=[S404])
tc("TC_ORD_017", "GET", "/api/orders/abc", tests=[S400])
tc("TC_ORD_018", "POST", LK, {"orderId": N("order_id"), "customerPhone": "' OR '1'='1"}, tests=[S404])
tc("TC_ORD_019", "POST", LK, {"orderId": N("order_id"), "customerPhone": "0900000099"},
   pre=["for (var i = 0; i < 29; i++) api('POST', '/api/orders/lookup', null, { orderId: Number(v('order_id')), customerPhone: '09000000' + ('0' + i).slice(-2) }, function () {});"],
   tests=["pm.test('Yêu cầu dò SĐT thứ 30 phải bị Rate Limit (429)', function () { pm.expect(pm.response.code).to.equal(429); });"])
tc("TC_ORD_020", "PUT", PF, {"fullName": "User Seed", "phone": "0900000001", "address": None}, tok=U,
   tests=[S200, "api('GET', '/api/profile', 'user_token', undefined, function (c, j) { pm.test('address = null', function () { pm.expect(j.address).to.equal(null); }); });"])
tc("TC_ORD_021", "PUT", PF, {"fullName": "User Seed Rename", "phone": "0900000001", "address": "HN"}, tok=U, tests=[S200])
tc("TC_ORD_022", "PUT", PF, {"fullName": "User Seed", "phone": None, "address": "HN"}, tok=U,
   tests=[info(), "api('PUT', '/api/profile', 'user_token', { fullName: 'User Seed', phone: '0900000001', address: '123 Đường Láng, Hà Nội' }, function () {});"])
DEL_USER_PRE = """api('POST', '/api/auth/register', null, { fullName: 'To Delete 2', email: 'todelete2@gmail.com', phone: '0911999005', password: 'Abc123@', confirmPassword: 'Abc123@', address: 'HN' }, function () {
  api('POST', '/api/auth/login', null, { emailOrPhone: 'todelete2@gmail.com', password: 'Abc123@' }, function (c, j) {
    if (j && j.token) setv('ud2_token', j.token);
    api('GET', '/api/admin/users?keyword=todelete2', 'admin_token', undefined, function (c2, j2) { if (j2.users.length) api('DELETE', '/api/admin/users/' + j2.users[0].id, 'admin_token', undefined, function () {}); });
  });
});"""
tc("TC_ORD_023", "GET", PF, tok="ud2_token", pre=[DEL_USER_PRE], tests=[st(400, 404)])
tc("TC_ORD_024", "PUT", PF, {"fullName": "Ghost", "phone": None, "address": None}, tok="ud2_token", tests=[st(401, 404)])
tc("TC_ORD_025", "GET", LK, tests=[S400])
tc("TC_ORD_026", "POST", LK, {}, tests=[st(400, 404)])
tc("TC_ORD_027", "POST", LK, {"orderId": N("order_id"), "customerPhone": "0901234567"},
   tests=[S200, "api('GET', '/api/orders/' + v('order_id'), null, undefined, function (c, j) { pm.test('details có productName, productImage, price, quantity', function () { ['productName', 'productImage', 'price', 'quantity'].forEach(function (k) { pm.expect(j.details[0]).to.have.property(k); }); }); });"])

# ================================================================== MODULE 5 ADMIN
tc("TC_ADM_001", "GET", AD + "/dashboard/revenue", tok=A, tests=[S200, chk("typeof j.revenue === 'number' && j.revenue >= 0", "revenue >= 0")])
tc("TC_ADM_002", "GET", AD + "/dashboard/stats", tok=A, tests=[S200, chk("j.productCount >= 40 && j.categoryCount >= 7 && 'orderCount' in j && 'userCount' in j && 'revenue' in j && j.recentOrders.length <= 5", "đủ 6 trường thống kê")])
tc("TC_ADM_003", "GET", AD + "/dashboard/revenue", tok=U, tests=[S403])
tc("TC_ADM_004", "GET", AD + "/categories", tok=A, tests=[S200, chk("j.length >= 7", "danh sách danh mục")])
tc("TC_ADM_005", "POST", AD + "/categories/save", {"id": None, "name": "MSI Gaming Test"}, tok=A, tests=[S200, chk("j.success === true && j.id > 0", "{success:true, id>0}"), save("created_cat_id", "j.id")])
tc("TC_ADM_006", "POST", AD + "/categories/save", {"id": N("created_cat_id"), "name": "MSI Gaming Updated"}, tok=A,
   tests=[S200, "api('GET', '/api/categories', null, undefined, function (c, j) { pm.test('tên đã đổi', function () { pm.expect(j.filter(function (x) { return x.id === Number(v('created_cat_id')); })[0].name).to.equal('MSI Gaming Updated'); }); });"])
tc("TC_ADM_007", "POST", AD + "/categories/save", {"id": None, "name": "Acer"}, tok=A, tests=[st(400, 409), chk("!(j && j.message && j.message.indexOf('duplicate key') >= 0)", "không lộ lỗi DB thô")])
CLEAN_CAT = "try { var j = J(); if (j && j.id) api('DELETE', '/api/admin/categories/' + j.id, 'admin_token', undefined, function () {}); } catch (e) {}"
tc("TC_ADM_008", "POST", AD + "/categories/save", {"id": None, "name": ""}, tok=A, tests=[S400, CLEAN_CAT])
tc("TC_ADM_009", "POST", AD + "/categories/save", {"id": None, "name": "    "}, tok=A, tests=[S400, CLEAN_CAT])
tc("TC_ADM_010", "POST", AD + "/categories/save", {"id": 99999, "name": "Ghost Category"}, tok=A, tests=[S404])
tc("TC_ADM_011", "DELETE", AD + "/categories/{{created_cat_id}}", tok=A,
   tests=[S200, "api('GET', '/api/categories', null, undefined, function (c, j) { pm.test('danh mục đã bị xóa', function () { pm.expect(j.map(function (x) { return x.id; })).to.not.include(Number(v('created_cat_id'))); }); });"])
tc("TC_ADM_012", "DELETE", AD + "/categories/1", tok=A, tests=[st(400, 409), msg("Không thể xóa! Danh mục đang chứa sản phẩm.")])
tc("TC_ADM_013", "DELETE", AD + "/categories/99999", tok=A, tests=[S404])
tc("TC_ADM_014", "POST", AD + "/products/save", {"id": None, "name": "Laptop Test Admin", "price": 25000000, "stock": 10, "image": "assets/test.jpg", "categoryId": 1, "cpu": "Core i7", "ram": "16GB", "storage": "512GB"}, tok=A,
   tests=[S200, chk("j.success === true && j.id > 0", "{success:true, id>0}"), save("created_prod_id", "j.id")])
tc("TC_ADM_015", "POST", AD + "/products/save", {"id": N("created_prod_id"), "name": "Laptop Test Admin Updated", "price": 26000000, "stock": 15, "image": "assets/test.jpg", "categoryId": 1, "cpu": "Core i9", "ram": "32GB"}, tok=A,
   tests=[S200, "api('GET', '/api/products/' + v('created_prod_id'), null, undefined, function (c, j) { pm.test('cpu Core i9, ram 32GB', function () { pm.expect(j.product.cpu).to.equal('Core i9'); pm.expect(j.product.ram).to.equal('32GB'); }); });"])
tc("TC_ADM_048", "GET", "/api/products/{{created_prod_id}}", tests=[S200, chk("j.product.storage === '512GB'", "storage giữ nguyên '512GB' sau cập nhật thiếu trường")])
CLEAN_PROD = "try { var j = J(); if (j && j.id) api('DELETE', '/api/admin/products/' + j.id, 'admin_token', undefined, function () {}); } catch (e) {}"
tc("TC_ADM_016", "POST", AD + "/products/save", {"id": None, "name": "Negative Price Laptop", "price": -10000000, "stock": 5, "categoryId": 1}, tok=A, tests=[S400, CLEAN_PROD])
tc("TC_ADM_017", "POST", AD + "/products/save", {"id": None, "name": "Negative Stock Laptop", "price": 15000000, "stock": -50, "categoryId": 1}, tok=A, tests=[S400, CLEAN_PROD])
tc("TC_ADM_018", "POST", AD + "/products/save", {"id": None, "name": "", "price": 15000000, "stock": 5, "categoryId": 1}, tok=A, tests=[S400, CLEAN_PROD])
tc("TC_ADM_019", "POST", AD + "/products/save", {"id": None, "name": "Bad Cat Laptop", "price": 15000000, "stock": 5, "categoryId": 99999}, tok=A, tests=[S400, chk("!(j && j.message && j.message.indexOf('foreign key') >= 0)", "không lộ lỗi DB thô")])
tc("TC_ADM_020", "POST", AD + "/products/save", {"id": 99999, "name": "Ghost Laptop", "price": 15000000, "stock": 5, "categoryId": 1}, tok=A, tests=[S404])
tc("TC_ADM_052", "DELETE", AD + "/products/{{created_prod_id}}", tok=A,
   pre=["api('POST', '/api/cart/add', 'user_token', { productId: Number(v('created_prod_id')), quantity: 1 }, function () {});"],
   tests=[S200, cart_check(U, "Number(v('created_prod_id'))", "!it", "cart_items chứa SP bị xóa theo (CASCADE)")])
tc("TC_ADM_021", "DELETE", AD + "/products/{{tmp_prod_id}}", tok=A,
   pre=["api('POST', '/api/admin/products/save', 'admin_token', { id: null, name: 'Tmp Delete', price: 1, stock: 1, categoryId: 1 }, function (c, j) { setv('tmp_prod_id', j.id); });"],
   tests=[S200, "api('GET', '/api/products/' + v('tmp_prod_id'), null, undefined, function (c) { pm.test('SP (và product_details) đã bị xóa', function () { pm.expect(c).to.equal(404); }); });"])
tc("TC_ADM_022", "DELETE", AD + "/products/102", tok=A, tests=[st(400, 409), msg("Không thể xóa sản phẩm.")])
tc("TC_ADM_023", "DELETE", AD + "/products/99999", tok=A, tests=[S404])
tc("TC_ADM_024", "GET", AD + "/orders?page=0&size=15", tok=A, tests=[S200, chk("'orders' in j && 'currentPage' in j && 'totalPages' in j && 'totalElements' in j", "orders/currentPage/totalPages/totalElements")])
tc("TC_ADM_025", "GET", AD + "/orders?keyword=0901234567", tok=A, tests=[S200, chk("j.orders.length > 0 && j.orders.every(function (o) { return o.customerPhone.indexOf('0901234567') >= 0; })", "mọi đơn khớp SĐT")])
tc("TC_ADM_026", "GET", AD + "/orders?status=CH%E1%BB%9C%20X%C3%81C%20NH%E1%BA%ACN", tok=A, tests=[S200, chk("j.orders.length > 0 && j.orders.every(function (o) { return o.status === 'CHỜ XÁC NHẬN'; })", "chỉ đơn 'CHỜ XÁC NHẬN'")])
tc("TC_ADM_027", "GET", AD + "/orders?startDate=2025-01-01&endDate=2027-12-31", tok=A, tests=[S200, chk("j.totalElements > 0", "có đơn trong khoảng ngày")])
tc("TC_ADM_051", "GET", AD + "/orders?startDate={{today}}&endDate={{today}}&size=100", tok=A, pre=["var d = new Date(); pm.variables.set('today', d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2));"],
   tests=[S200, chk("j.totalElements > 0 && j.orders.every(function (o) { return o.orderDate.slice(0, 10) === v('today'); })", "trả về đơn tạo trong ngày endDate")])
tc("TC_ADM_028", "GET", AD + "/orders?page=-1&size=15", tok=A, tests=[S400])
tc("TC_ADM_029", "GET", AD + "/orders?page=0&size=0", tok=A, tests=[S400])
ST = AD + "/orders/status"
tc("TC_ADM_030", "PUT", ST, {"orderId": N("order_id"), "status": "ĐANG GIAO"}, tok=A, tests=[S200, order_status_check("j.status === 'ĐANG GIAO'", "status = 'ĐANG GIAO'")])
tc("TC_ADM_047", "PUT", ST, {"orderId": N("order_id"), "newStatus": "ĐÃ XÁC NHẬN"}, tok=A, tests=[S200, order_status_check("j.status === 'ĐÃ XÁC NHẬN'", "status = 'ĐÃ XÁC NHẬN'")])
tc("TC_ADM_031", "PUT", ST, {"orderId": N("order_id"), "status": "TRANG_THAI_RAC_123"}, tok=A, tests=[S400])
tc("TC_ADM_032", "PUT", ST, {"orderId": N("order_id"), "status": ""}, tok=A, tests=[S400])
tc("TC_ADM_033", "PUT", ST, {"orderId": N("order_id"), "newStatus": "CHỜ XÁC NHẬN"}, tok=A,
   pre=["api('GET', '/api/products/102', null, undefined, function (c, j) { setv('s102', j.product.stock); api('PUT', '/api/admin/orders/status', 'admin_token', { orderId: Number(v('order_id')), newStatus: 'ĐÃ HỦY' }, function () { api('GET', '/api/products/102', null, undefined, function (c2, j2) { setv('s102_after', j2.product.stock); }); }); });"],
   tests=["pm.test('Hủy đơn phải hoàn tồn kho (+1)', function () { pm.expect(Number(v('s102_after'))).to.equal(Number(v('s102')) + 1); });",
          "pm.test('Không cho chuyển ngược ĐÃ HỦY → CHỜ XÁC NHẬN (400)', function () { pm.expect(pm.response.code).to.equal(400); });"])
tc("TC_ADM_034", "PUT", ST, {"orderId": 99999, "status": "HOÀN THÀNH"}, tok=A, tests=[S404])
tc("TC_ADM_050", "PUT", ST, {"orderId": N("order_id"), "newStatus": "HOÀN THÀNH"}, tok=A,
   pre=["api('GET', '/api/admin/dashboard/revenue', 'admin_token', undefined, function (c, j) { setv('rev0', j.revenue); api('GET', '/api/orders/' + v('order_id'), null, undefined, function (c2, j2) { setv('ord_amt', j2.totalAmount); }); });"],
   tests=[S200, "api('GET', '/api/admin/dashboard/revenue', 'admin_token', undefined, function (c, j) { pm.test('revenue tăng đúng totalAmount của đơn', function () { pm.expect(j.revenue - Number(v('rev0'))).to.equal(Number(v('ord_amt'))); }); });"])
tc("TC_ADM_035", "GET", AD + "/users?page=0&size=15", tok=A, tests=[S200, chk("j.users.length > 0 && j.users.every(function (u) { return !('password' in u); })", "không có trường password")])
tc("TC_ADM_036", "GET", AD + "/users?keyword=taobattu", tok=A, tests=[S200, chk("j.users.some(function (u) { return u.email === 'taobattu@gmail.com'; })", "tìm thấy User Seed")])
tc("TC_ADM_037", "GET", AD + "/users?page=-1&size=15", tok=A, tests=[S400])
tc("TC_ADM_038", "GET", AD + "/users?page=0&size=0", tok=A, tests=[S400])
RL = AD + "/users/role"
RESET_U1 = "api('PUT', '/api/admin/users/role', 'admin_token', { userId: 1, role: 'USER' }, function () {});"
tc("TC_ADM_039", "PUT", RL, {"userId": 1, "role": "USER"}, tok=A, tests=[S200, chk("j.success === true", "{success:true}")])
tc("TC_ADM_040", "PUT", RL, {"userId": 1, "role": "SUPER_HACKER_ROLE"}, tok=A, tests=[S400, RESET_U1])
tc("TC_ADM_042", "PUT", RL, {"userId": 99999, "role": "ADMIN"}, tok=A, tests=[S404])
tc("TC_ADM_049", "PUT", RL, {"userId": 1, "role": "admin"}, tok=A,
   tests=["""api('POST', '/api/auth/login', null, { emailOrPhone: 'taobattu@gmail.com', password: 'Abc123@' }, function (c, j) {
  setv('u2_token', j.token);
  api('GET', '/api/admin/dashboard/stats', 'u2_token', undefined, function (c2) {
    pm.test('Role sai chuẩn phải bị từ chối 400 (hoặc chuẩn hóa → user vào được Admin)', function () { pm.expect(pm.response.code === 400 || c2 === 200).to.be.true; });
    """ + RESET_U1 + """
  });
});"""])
tc("TC_ADM_044", "DELETE", AD + "/users/1", tok=A, tests=[st(400, 409), msg("Không thể xóa do người này đã có lịch sử mua hàng!")])
tc("TC_ADM_053", "DELETE", AD + "/users/{{dm_id}}", tok=A,
   pre=["""api('POST', '/api/auth/register', null, { fullName: 'Del Me', email: 'delme@gmail.com', phone: '0911999003', password: 'Abc123@', confirmPassword: 'Abc123@', address: 'HN' }, function (c, j) {
  setv('dm_id', j.userId);
  api('POST', '/api/auth/login', null, { emailOrPhone: 'delme@gmail.com', password: 'Abc123@' }, function (c2, j2) { setv('dm_token', j2.token); api('POST', '/api/cart/add', 'dm_token', { productId: 111, quantity: 1 }, function () {}); });
});"""], tests=[S200, "api('GET', '/api/admin/users?keyword=delme@gmail.com', 'admin_token', undefined, function (c, j) { pm.test('user đã bị xóa', function () { pm.expect(j.users.length).to.equal(0); }); });"])
tc("TC_ADM_043", "DELETE", AD + "/users/{{dm2_id}}", tok=A,
   pre=["api('POST', '/api/auth/register', null, { fullName: 'Del Me 2', email: 'delme2@gmail.com', phone: '0911999004', password: 'Abc123@', confirmPassword: 'Abc123@', address: 'HN' }, function (c, j) { setv('dm2_id', j.userId); });"],
   tests=[S200, "api('GET', '/api/admin/users?keyword=delme2', 'admin_token', undefined, function (c, j) { pm.test('user đã bị xóa', function () { pm.expect(j.users.length).to.equal(0); }); });"])
tc("TC_ADM_046", "DELETE", AD + "/users/99999", tok=A, tests=[S404])
tc("TC_ADM_054", "GET", AD + "/dashboard/stats", tok=A, tests=[S200, chk("j.recentOrders.length > 0 && 'customerName' in j.recentOrders[0] && 'totalAmount' in j.recentOrders[0] && 'orderDate' in j.recentOrders[0]", "recentOrders dùng camelCase")])
tc("TC_ADM_041", "PUT", RL, {"userId": 2, "role": "USER"}, tok=A,
   tests=[S400, "api('PUT', '/api/admin/users/role', 'admin_token', { userId: 2, role: 'ADMIN' }, function () {});"])
tc("TC_ADM_045", "DELETE", AD + "/users/2", tok=A, pre=["api('GET', '/api/cart', 'admin_token', undefined, function (c, j) { (j.items || []).forEach(function (i) { api('DELETE', '/api/cart/' + i.id, 'admin_token', undefined, function () {}); }); });"],
   tests=[S400])

# Thứ tự chạy trong từng module (phụ thuộc dữ liệu) = thứ tự khai báo ở trên.
ORDER = list(SPEC)

# ------------------------------------------------------------------ setup folders
def setup_item(name, m, path, body, tok, test):
    return dict(name=name, m=m, path=path, body=body, tok=tok, tests=[test], pre=[], raw=None)
SET_LOGIN = [
    setup_item("[SETUP] Đăng nhập USER → {{user_token}}", "POST", L, {"emailOrPhone": "{{user_email}}", "password": "{{user_password}}"}, None, "pm.test('Login USER 200', function () { pm.response.to.have.status(200); }); setv('user_token', J().token);"),
    setup_item("[SETUP] Đăng nhập ADMIN → {{admin_token}}", "POST", L, {"emailOrPhone": "{{admin_email}}", "password": "{{admin_password}}"}, None, "pm.test('Login ADMIN 200', function () { pm.response.to.have.status(200); }); setv('admin_token', J().token);"),
]
SET_CLEAN_CART = setup_item("[SETUP] Dọn giỏ hàng USER", "GET", CA, None, U,
    "pm.test('GET cart 200', function () { pm.response.to.have.status(200); }); (J().items || []).forEach(function (i) { api('DELETE', '/api/cart/' + i.id, 'user_token', undefined, function () {}); });")
SET_ORDERS = [
    setup_item("[SETUP] Tạo đơn khách vãng lai (0901234567) → {{order_id}}", "POST", CK, ck(), None, "pm.test('Order 200', function () { pm.response.to.have.status(200); }); setv('order_id', J().orderId);"),
    setup_item("[SETUP] Tạo đơn của USER 1 → {{user_order_id}}", "POST", CK, ck(customerName="User Seed", customerPhone="0900000001", buyNowProductId=105), U, "pm.test('Order 200', function () { pm.response.to.have.status(200); }); setv('user_order_id', J().orderId);"),
]
SET_UB = setup_item("[SETUP] Đảm bảo tồn tại User B (nvtest01@gmail.com)", "POST", RG,
    reg(fullName="Nguyen Van Test", email="nvtest01@gmail.com", phone="0912345001", password="Password123@", confirmPassword="Password123@"), None,
    "pm.test('Đăng ký mới (200) hoặc đã tồn tại (400)', function () { pm.expect(pm.response.code).to.be.oneOf([200, 400]); });")
MODULE_SETUP = {"AUTH": SET_LOGIN, "PROD": SET_LOGIN, "CART": SET_LOGIN + [SET_CLEAN_CART],
                "PROF_ORD": SET_LOGIN + [SET_UB] + SET_ORDERS, "ADM": SET_LOGIN + SET_ORDERS}

# ------------------------------------------------------------------ đọc Excel
wb = openpyxl.load_workbook(XLSX, data_only=True)
ROWS = {}
SHEET_OF = {}
for sheet, _ in MODS:
    for r in wb[sheet].iter_rows(min_row=3, values_only=True):
        if r[0]:
            ROWS[r[0]] = r; SHEET_OF[r[0]] = sheet
missing = set(ROWS) - set(SPEC); extra = set(SPEC) - set(ROWS)
assert not missing and not extra, (missing, extra)

def pm_body(body, raw):
    if raw is not None: return raw
    if body is None: return None
    s = json.dumps(body, ensure_ascii=False, indent=2)
    return re.sub(r'"__NUM__(\w+)__"', r"{{\1}}", s)

def url_obj(path):
    raw = "{{base_url}}" + path
    p, _, q = path.partition("?")
    o = {"raw": raw, "host": ["{{base_url}}"], "path": [x for x in p.split("/") if x]}
    if q:
        o["query"] = [dict(zip(("key", "value"), kv.split("=", 1))) if "=" in kv else {"key": kv, "value": None} for kv in q.split("&")]
    return o

def build_item(spec, name, desc):
    hdr = [{"key": "Accept", "value": "application/json"}]
    b = pm_body(spec["body"], spec["raw"])
    if b is not None: hdr.append({"key": "Content-Type", "value": "application/json"})
    if spec["tok"]: hdr.append({"key": "Authorization", "value": "Bearer {{%s}}" % spec["tok"]})
    req = {"method": spec["m"], "header": hdr, "url": url_obj(spec["path"]), "description": desc}
    if b is not None: req["body"] = {"mode": "raw", "raw": b, "options": {"raw": {"language": "json"}}}
    ev = []
    if spec["pre"]: ev.append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": (LIB + "\n".join(spec["pre"])).split("\n")}})
    ev.append({"listen": "test", "script": {"type": "text/javascript", "exec": (LIB + "\n".join(spec["tests"])).split("\n")}})
    return {"name": name, "event": ev, "request": req}

def tc_item(tid):
    r = ROWS[tid]
    _, func, typ, prio, prec, ep, data, exp, act, status, note = r
    first_note = (note or "").split("\n")[0]
    name = f"{tid} - [{status}] {first_note}"[:240]
    desc = "\n".join([
        f"**Mã Test Case:** `{tid}`  |  **Chức năng:** {func}  |  **Loại:** {typ}  |  **Ưu tiên:** {prio}",
        f"**Điều kiện tiên quyết:** {prec}", f"**Method & Endpoint (Excel):** {ep}", f"**Dữ liệu đầu vào:** {data}",
        f"**Kết quả mong đợi:** {exp}", f"**Kết quả thực tế:** {act}", f"**Trạng thái (đồng bộ TestCase.xlsx):** **{status}**",
        f"**Ghi chú:** {note}", "",
        "_Quy ước: các pm.test kiểm tra Kết quả mong đợi. TC FAIL (Bug) sẽ có test đỏ – đó là bug đã ghi nhận, không phải lỗi collection._"])
    return build_item(SPEC[tid], name, desc)

COLL_VARS = [("base_url", "http://localhost:5084"), ("user_email", "taobattu@gmail.com"), ("user_phone", "0900000001"), ("user_password", "Abc123@"),
             ("admin_email", "Admin@gmail.com"), ("admin_password", "Abc123@"), ("jwt_key", "day-la-chuoi-bi-mat-toi-thieu-32-ky-tu-cho-hmacsha256"),
             ("fake_jwt_token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"), ("malformed_token", "not_a_jwt_token_123"),
             ("user_token", ""), ("admin_token", ""), ("order_id", ""), ("user_order_id", "")]
README = ("Đồng bộ với TestCase.xlsx (sinh bởi qa_tests/build_postman.py ngày 18/11/2026).\n"
          "BẮT BUỘC: reset DB bằng sql/full_setup_and_reset.sql (hoặc qa_tests/reset_test_db.sh) trước MỖI lần chạy và chạy tuần tự bằng Collection Runner / Newman.\n"
          "Quy ước: pm.test kiểm tra Kết quả mong đợi → TC PASS xanh hết; TC FAIL (Bug) có test đỏ (bug đã ghi nhận); TC CHƯA XÁC ĐỊNH chỉ ghi nhận (INFO).\n"
          "Lưu ý: TC_ADM_045 xóa chính tài khoản Admin (bug) – luôn chạy cuối.")

def collection(title, folders):
    return {"info": {"_postman_id": str(uuid.uuid5(uuid.NAMESPACE_URL, "lapzone/" + title)), "name": title, "description": README, "schema": SCHEMA},
            "variable": [{"key": k, "value": v, "type": "string"} for k, v in COLL_VARS], "item": folders}

def folder(name, items, desc=""):
    return {"name": name, "description": desc, "item": items}

def module_folders(sheet, key):
    ids = [t for t in ORDER if SHEET_OF[t] == sheet]
    st_ = [ROWS[t][9] for t in ids]
    title = f"{sheet} ({len(ids)} TCs: {st_.count('PASS')} PASS / {st_.count('FAIL (Bug)')} FAIL / {st_.count('CHƯA XÁC ĐỊNH')} CHƯA XĐ)"
    setup = folder(f"00_SETUP_{sheet}", [build_item(s, s["name"], "Chuẩn bị dữ liệu – không phải test case.") for s in MODULE_SETUP[key]])
    return setup, folder(title, [tc_item(t) for t in ids]), len(ids)

full = []
summary = []
for sheet, key in MODS:
    s, f, n = module_folders(sheet, key)
    c = collection(f"LapZoneAPI - {sheet} ({n} TCs)", [s, f])
    json.dump(c, open(os.path.join(OUTD, f"LapZoneAPI_{sheet}.postman_collection.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    full += [s, f]; summary.append((sheet, n))
tot = sum(n for _, n in summary)
json.dump(collection(f"LapZoneAPI - Full Test Cases ({tot} TCs)", full), open(os.path.join(OUTD, "LapZoneAPI_Full_TestCases.postman_collection.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
env = {"id": "09e48e84-e3cc-4961-b342-c112cd5b6b2f", "name": "LapZoneAPI Local Environment (http://localhost:5084)",
       "values": [{"key": k, "value": v, "type": "default", "enabled": True} for k, v in COLL_VARS if k in ("base_url", "user_email", "user_phone", "user_password", "admin_email", "admin_password")],
       "_postman_variable_scope": "environment"}
json.dump(env, open(os.path.join(OUTD, "LapZoneAPI.postman_environment.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(summary, tot)
