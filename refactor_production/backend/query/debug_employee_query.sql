-- Debug query untuk menganalisis mengapa employee query mengembalikan 0 hasil

-- 1. Periksa apakah tabel HR_EMPLOYEE ada dan berisi data
SELECT
    'HR_EMPLOYEE' as table_name,
    COUNT(*) as total_records
FROM "HR_EMPLOYEE"
WHERE "Status" = 'A'

UNION ALL

-- 2. Periksa apakah tabel HR_GANGLN ada dan berisi data
SELECT
    'HR_GANGLN' as table_name,
    COUNT(*) as total_records
FROM "HR_GANGLN"
WHERE "GangCode" IS NOT NULL

UNION ALL

-- 3. Periksa apakah ada employee dengan status 'A'
SELECT
    'HR_EMPLOYEE_ACTIVE' as table_name,
    COUNT(*) as total_records
FROM "HR_EMPLOYEE"
WHERE "Status" = 'A'

UNION ALL

-- 4. Periksa struktur data di HR_EMPLOYEE (sample 5 records)
SELECT
    'HR_EMPLOYEE_SAMPLE' as info_type,
    CAST("EmpCode" AS VARCHAR(20)) + '|' + CAST("EmpName" AS VARCHAR(50)) + '|' + CAST("Status" AS VARCHAR(10)) + '|' + CAST("Gender" AS VARCHAR(5)) as sample_data
FROM "HR_EMPLOYEE"
WHERE "Status" = 'A'
LIMIT 5

UNION ALL

-- 5. Periksa apakah ada gang codes yang tersedia
SELECT
    'AVAILABLE_GANGS' as info_type,
    COUNT(DISTINCT "GangCode") as total_gangs
FROM "HR_GANGLN"
WHERE "GangCode" IS NOT NULL AND "GangCode" != ''

UNION ALL

-- 6. Sample gang codes
SELECT
    'SAMPLE_GANGS' as info_type,
    "GangCode" as sample_data
FROM "HR_GANGLN"
WHERE "GangCode" IS NOT NULL AND "GangCode" != ''
ORDER BY "GangCode"
LIMIT 10

UNION ALL

-- 7. Test query dengan H1H (default gang code)
SELECT
    'TEST_H1H_QUERY' as info_type,
    COUNT(*) as matching_records
FROM "HR_EMPLOYEE" e
LEFT JOIN "HR_GANGLN" g ON g."GangMember" = e."EmpCode"
WHERE e."Status" = 'A'
    AND (g."GangCode" = 'H1H' OR e."LocCode" = 'H1H' OR 'H1H' IS NULL)

UNION ALL

-- 8. Test query dengan semua gang codes
SELECT
    'TEST_ALL_ACTIVE' as info_type,
    COUNT(*) as matching_records
FROM "HR_EMPLOYEE" e
LEFT JOIN "HR_GANGLN" g ON g."GangMember" = e."EmpCode"
WHERE e."Status" = 'A'
    AND (g."GangCode" IS NOT NULL OR e."LocCode" IS NOT NULL OR NULL IS NULL)