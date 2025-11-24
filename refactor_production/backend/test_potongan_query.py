import sys
sys.path.append('.')
from database.services.database import Database
from database.services.queries import Queries

# Initialize database
db = Database.instance()
q = Queries()

# First, let's check available gang codes
print("=== MENCARI GANG YANG MEMILIKI DATA POTONGAN ===")

# Query to find available gang codes with potongan data (tanpa filter bulan)
gang_sql = """
SELECT DISTINCT g.GangCode, COUNT(*) as count
FROM "HR_GANGLN" AS g
JOIN "PR_ADTRANS_ARC" AS t ON g.GangMember = t.EmpCode
JOIN "PR_ADTRANSLN_ARC" AS ln ON t.ID = ln.MasterID
WHERE COALESCE(ln.Amount,0) < 0
AND t.DocDesc IS NOT NULL
GROUP BY g.GangCode
ORDER BY count DESC
"""

# Query to test potongan dengan LIKE 'POT%'
pot_like_sql = """
SELECT DISTINCT g.GangCode, t.DocDesc, COUNT(*) as count
FROM "HR_GANGLN" AS g
JOIN "PR_ADTRANS_ARC" AS t ON g.GangMember = t.EmpCode
JOIN "PR_ADTRANSLN_ARC" AS ln ON t.ID = ln.MasterID
WHERE COALESCE(ln.Amount,0) < 0
AND UPPER(t.DocDesc) LIKE 'POT%'
AND UPPER(t.DocDesc) NOT LIKE '%ASTEK%'
AND UPPER(t.DocDesc) NOT LIKE '%PREMI%'
AND UPPER(t.DocDesc) NOT LIKE '%BPJS%'
AND t.DocDesc IS NOT NULL
GROUP BY g.GangCode, t.DocDesc
ORDER BY g.GangCode, count DESC
"""

try:
    rows = db.query_all(gang_sql, [])
    if rows:
        print(f'Found {len(rows)} gangs with potongan data:')
        for i, row in enumerate(rows[:10], 1):
            print(f'{i}. Gang {row[0]}: {row[1]} records')
        first_gang = rows[0][0] if rows else 'C1H'
    else:
        print('No gangs with potongan data found for May 2025')
        first_gang = 'C1H'
except Exception as e:
    print(f'Error: {e}')
    first_gang = 'C1H'

# Test query sederhana untuk melihat semua data
print("\n=== TEST QUERY SEMUA DATA TRANSAKSI ===")
simple_sql = """
SELECT TOP 10 g.GangCode, t.EmpCode, t.DocDate, t.DocDesc, ln.Amount
FROM "HR_GANGLN" AS g
JOIN "PR_ADTRANS_ARC" AS t ON g.GangMember = t.EmpCode
JOIN "PR_ADTRANSLN_ARC" AS ln ON t.ID = ln.MasterID
WHERE g.GangCode = 'C1H'
ORDER BY t.DocDate DESC
"""

# Query untuk mencari semua PPH21 transactions
pph21_sql = """
SELECT TOP 10 g.GangCode, t.EmpCode, t.DocDate, t.DocDesc, ln.Amount
FROM "HR_GANGLN" AS g
JOIN "PR_ADTRANS_ARC" AS t ON g.GangMember = t.EmpCode
JOIN "PR_ADTRANSLN_ARC" AS ln ON t.ID = ln.MasterID
WHERE g.GangCode = 'C1H'
AND UPPER(t.DocDesc) = 'PPH21'
ORDER BY t.DocDate DESC
"""

try:
    rows = db.query_all(simple_sql, [])
    if rows:
        print(f'Found {len(rows)} transaction records:')
        print('Gang\tEmpCode\tDocDate\t\tDocDesc\t\t\tAmount')
        print('-' * 80)
        for row in rows:
            gang = row[0] if row else "NULL"
            emp = row[1] if len(row) > 1 else "NULL"
            date = str(row[2]) if len(row) > 2 else "NULL"
            desc = (row[3] if len(row) > 3 else "NULL")[:30]
            amount = str(row[4]) if len(row) > 4 else "NULL"
            print(f'{gang}\t{emp}\t{date}\t{desc}\t{amount}')
    else:
        print('No transaction records found for C1H')
except Exception as e:
    print(f'Error: {e}')

# Query khusus untuk PPH21
print("\n=== DETAIL TRANSAKSI PPH21 ===")
try:
    rows = db.query_all(pph21_sql, [])
    if rows:
        print(f'Found {len(rows)} PPH21 transactions:')
        print('Gang\tEmpCode\tDocDate\t\tAmount')
        print('-' * 60)
        for row in rows:
            gang = row[0] if row else "NULL"
            emp = row[1] if len(row) > 1 else "NULL"
            date = str(row[2]) if len(row) > 2 else "NULL"
            amount = row[4] if len(row) > 4 else 0
            print(f'{gang}\t{emp}\t{date}\t{amount}')
    else:
        print('No PPH21 transactions found')
except Exception as e:
    print(f'Error: {e}')

# Test query tanpa filter amount negatif
no_amount_filter_sql = f"""
SELECT DISTINCT t.DocDesc, COUNT(*) as count, SUM(COALESCE(ln.Amount,0)) as total_amount
FROM "PR_ADTRANS_ARC" AS t
JOIN "PR_ADTRANSLN_ARC" AS ln ON t.ID = ln.MasterID
WHERE t.EmpCode IN (
    SELECT "HR_EMPLOYEE"."EmpCode"
    FROM "HR_EMPLOYEE"
    JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
    WHERE "HR_GANGLN"."GangCode" = 'C1H'
)
AND t.DocDate >= '2025-10-01'
AND t.DocDate < '2025-11-01'
AND UPPER(t.DocDesc) LIKE 'POT%'
AND t.DocDesc IS NOT NULL
GROUP BY t.DocDesc
HAVING COUNT(*) > 0
ORDER BY COUNT(*) DESC
"""

print("\n=== POTONGAN DENGAN LIKE 'POT%' (TANPA FILTER AMOUNT) ===")
try:
    rows = db.query_all(no_amount_filter_sql, [])
    if rows:
        print(f'Found {len(rows)} POT items in October 2025:')
        print('Description\t\t\tCount\tTotal Amount')
        print('-' * 70)
        for i, row in enumerate(rows[:30], 1):
            desc = (row[0] if row else "NULL")[:30]
            count = row[1] if len(row) > 1 else 0
            amount = row[2] if len(row) > 2 else 0
            print(f'{i}. {desc}\t{count}\t{amount}')
    else:
        print('No POT items found in October 2025')
except Exception as e:
    print(f'Error: {e}')

# Test query dengan LIKE 'POT%'
print("\n=== TEST QUERY POTONGAN DENGAN LIKE 'POT%' ===")
try:
    rows = db.query_all(pot_like_sql, [])
    if rows:
        print(f'Found {len(rows)} potongan items starting with POT:')
        # Group by gang
        gangs = {}
        for row in rows:
            gang_code = row[0]
            doc_desc = row[1]
            count = row[2]
            
            if gang_code not in gangs:
                gangs[gang_code] = []
            gangs[gang_code].append((doc_desc, count))
        
        # Display by gang
        for gang_code, items in list(gangs.items())[:5]:  # Show top 5 gangs
            print(f"\nGang {gang_code}:")
            for i, (doc_desc, count) in enumerate(items[:10], 1):  # Show top 10 per gang
                print(f'  {i}. {doc_desc} ({count} records)')
        
        first_gang = list(gangs.keys())[0] if gangs else 'C1H'
    else:
        print('No potongan items found with LIKE POT%')
except Exception as e:
    print(f'Error: {e}')

# Test query dengan gang yang berbeda
print("\n=== CEK GANG YANG TERSEDIA ===")
gang_check_sql = """
SELECT DISTINCT GangCode 
FROM "HR_GANGLN" 
ORDER BY GangCode
"""

try:
    rows = db.query_all(gang_check_sql, [])
    if rows:
        print(f'Available gang codes:')
        for i, row in enumerate(rows[:20], 1):
            print(f'{i}. {row[0]}')
    else:
        print('No gang codes found')
except Exception as e:
    print(f'Error: {e}')

# Now let's test potongan data with October 2025 (when we have actual data)
october_sql = f"""
SELECT DISTINCT t.DocDesc, COUNT(*) as count, SUM(COALESCE(ln.Amount,0)) as total_amount
FROM "PR_ADTRANS_ARC" AS t
JOIN "PR_ADTRANSLN_ARC" AS ln ON t.ID = ln.MasterID
WHERE t.EmpCode IN (
    SELECT "HR_EMPLOYEE"."EmpCode"
    FROM "HR_EMPLOYEE"
    JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
    WHERE "HR_GANGLN"."GangCode" = 'C1H'
)
AND t.DocDate >= '2025-10-01'
AND t.DocDate < '2025-11-01'
AND COALESCE(ln.Amount,0) < 0
AND t.DocDesc IS NOT NULL
GROUP BY t.DocDesc
HAVING COUNT(*) > 0
ORDER BY COUNT(*) DESC
"""

potongan_like_sql = f"""
SELECT DISTINCT t.DocDesc, COUNT(*) as count, SUM(ABS(COALESCE(ln.Amount,0))) as total_deduction
FROM "PR_ADTRANS_ARC" AS t
JOIN "PR_ADTRANSLN_ARC" AS ln ON t.ID = ln.MasterID
WHERE t.EmpCode IN (
    SELECT "HR_EMPLOYEE"."EmpCode"
    FROM "HR_EMPLOYEE"
    JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
    WHERE "HR_GANGLN"."GangCode" = 'C1H'
)
AND t.DocDate >= '2025-10-01'
AND t.DocDate < '2025-11-01'
AND COALESCE(ln.Amount,0) < 0
AND (
    UPPER(t.DocDesc) LIKE 'POT%'
    OR UPPER(t.DocDesc) LIKE '%POTONGAN%'
    OR UPPER(t.DocDesc) LIKE '%POT %'
    OR UPPER(t.DocDesc) LIKE '%DEDUCT%'
    OR UPPER(t.DocDesc) LIKE '%DENDA%'
    OR UPPER(t.DocDesc) LIKE '%CUTI%'
    OR UPPER(t.DocDesc) LIKE '%IZIN%'
)
AND UPPER(t.DocDesc) NOT LIKE '%ASTEK%'
AND UPPER(t.DocDesc) NOT LIKE '%PREMI%'
AND UPPER(t.DocDesc) NOT LIKE '%BPJS%'
AND t.DocDesc IS NOT NULL
GROUP BY t.DocDesc
HAVING COUNT(*) > 0
ORDER BY COUNT(*) DESC
"""

print(f"\n=== SEMUA TRANSAKSI NEGATIF (POTONGAN) UNTUK GANG C1H - OKTOBER 2025 ===")
try:
    rows = db.query_all(october_sql, [])
    if rows:
        print(f'Found {len(rows)} potongan items in October 2025:')
        print('Description\t\t\tCount\tTotal Amount')
        print('-' * 70)
        for i, row in enumerate(rows[:30], 1):  # Show first 30
            desc = (row[0] if row else "NULL")[:30]
            count = row[1] if len(row) > 1 else 0
            amount = row[2] if len(row) > 2 else 0
            print(f'{i}. {desc}\t{count}\t{amount}')
    else:
        print('No potongan transactions found in October 2025')
except Exception as e:
    print(f'Error: {e}')

print(f"\n=== POTONGAN DENGAN FILTER KEYWORD UNTUK GANG C1H - OKTOBER 2025 ===")
try:
    rows = db.query_all(potongan_like_sql, [])
    if rows:
        print(f'Found {len(rows)} potongan items with keywords in October 2025:')
        print('Description\t\t\tCount\tTotal Deduction')
        print('-' * 70)
        for i, row in enumerate(rows[:30], 1):  # Show first 30
            desc = (row[0] if row else "NULL")[:30]
            count = row[1] if len(row) > 1 else 0
            amount = row[2] if len(row) > 2 else 0
            print(f'{i}. {desc}\t{count}\t{amount}')
    else:
        print('No potongan items found with keywords in October 2025')
except Exception as e:
    print(f'Error: {e}')

# Test query for potongan lainnya with gang C1H
sql_entry = q.get('potongan', 'potongan_pattern_headers')
if sql_entry and 'sql' in sql_entry:
    sql = sql_entry['sql']
    params = ['C1H', '2025-05-01', '2025-06-01']
    print(f'Executing query: {sql}')
    print(f'Params: {params}')
    print('---')
    
    try:
        rows = db.query_all(sql, params)
        if rows:
            print(f'Found {len(rows)} potongan items:')
            for i, row in enumerate(rows[:20], 1):  # Show first 20
                item = row[0] if row else "NULL"
                print(f'{i}. {item}')
        else:
            print('No rows returned with POT filter')
    except Exception as e:
        print(f'Error: {e}')
else:
    print('SQL entry not found')

# Try another query with different filters
print("\n=== POTONGAN dengan berbagai keyword ===")
other_sql = """
SELECT DISTINCT t.DocDesc
FROM "PR_ADTRANS_ARC" AS t
JOIN "PR_ADTRANSLN_ARC" AS ln ON t.ID = ln.MasterID
WHERE t.EmpCode IN (
    SELECT "HR_EMPLOYEE"."EmpCode"
    FROM "HR_EMPLOYEE"
    JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
    WHERE "HR_GANGLN"."GangCode" = 'C1H'
)
AND t.DocDate >= '2025-05-01'
AND t.DocDate < '2025-06-01'
AND COALESCE(ln.Amount,0) < 0
AND (
    UPPER(t.DocDesc) LIKE '%POTONGAN%' 
    OR UPPER(t.DocDesc) LIKE '%POT%'
    OR UPPER(t.DocDesc) LIKE '%DEDUCT%'
    OR UPPER(t.DocDesc) LIKE '%DENDA%'
    OR UPPER(t.DocDesc) LIKE '%CUTI%'
    OR UPPER(t.DocDesc) LIKE '%IZIN%'
)
AND UPPER(t.DocDesc) NOT LIKE '%ASTEK%'
AND UPPER(t.DocDesc) NOT LIKE '%PREMI%'
AND UPPER(t.DocDesc) NOT LIKE '%BPJS%'
AND t.DocDesc IS NOT NULL
ORDER BY t.DocDesc
"""

try:
    rows = db.query_all(other_sql, [])
    if rows:
        print(f'Found {len(rows)} potongan items with various keywords:')
        for i, row in enumerate(rows[:30], 1):  # Show first 30
            item = row[0] if row else "NULL"
            print(f'{i}. {item}')
    else:
        print('No rows returned with various keywords')
except Exception as e:
    print(f'Error: {e}')
