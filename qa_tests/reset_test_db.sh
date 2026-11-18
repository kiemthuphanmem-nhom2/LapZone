cd /c/Users/adm/Downloads/KiemThuPhanMem/LapZone
export PGPASSWORD=$(python -I -c "import json,re;c=json.load(open('appsettings.json',encoding='utf-8-sig'))['ConnectionStrings']['DefaultConnection'];print(re.search(r'(?i)password=([^;]*)',c).group(1))") PGCLIENTENCODING=UTF8
P="/c/Program Files/PostgreSQL/18/bin/psql.exe"
"$P" -h localhost -U postgres -d lapzone_qa_test -q -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" && "$P" -h localhost -U postgres -d lapzone_qa_test -q -v ON_ERROR_STOP=1 -f sql/full_setup_and_reset.sql >/dev/null && echo RESET_OK
