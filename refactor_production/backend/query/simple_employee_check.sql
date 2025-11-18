-- Query sederhana untuk debugging employee data
-- Jalankan query ini satu per satu untuk mengidentifikasi masalah

-- 1. Cek apakah tabel HR_EMPLOYEE ada
SELECT COUNT(*) as total_employees FROM "HR_EMPLOYEE"

-- 2. Cek employee dengan status 'A' (Active)
SELECT COUNT(*) as active_employees FROM "HR_EMPLOYEE" WHERE "Status" = 'A'

-- 3. Lihat sample data employee
SELECT TOP 5
    "EmpCode",
    "EmpName",
    "Status",
    "Gender",
    "LocCode"
FROM "HR_EMPLOYEE"
WHERE "Status" = 'A'

-- 4. Cek apakah tabel HR_GANGLN ada
SELECT COUNT(*) as total_gang_records FROM "HR_GANGLN"

-- 5. Lihat sample data gang
SELECT TOP 5
    "GangCode",
    "GangMember"
FROM "HR_GANGLN"
WHERE "GangCode" IS NOT NULL

-- 6. Test join antara employee dan gang (query asli)
SELECT COUNT(*) as joined_records
FROM "HR_EMPLOYEE" e
LEFT JOIN "HR_GANGLN" g ON g."GangMember" = e."EmpCode"
WHERE e."Status" = 'A'

-- 7. Test dengan H1H secara spesifik
SELECT COUNT(*) as h1h_records
FROM "HR_EMPLOYEE" e
LEFT JOIN "HR_GANGLN" g ON g."GangMember" = e."EmpCode"
WHERE e."Status" = 'A'
    AND (g."GangCode" = 'H1H' OR e."LocCode" = 'H1H')