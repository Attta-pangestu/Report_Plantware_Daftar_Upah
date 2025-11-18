-- Query untuk mendapatkan detail karyawan per gang
-- Menggunakan struktur database yang ada di PT Rebinmas
-- TIDAK ADA FILTER STATUS - karena status field di database salah
SELECT
    "HR_EMPLOYEE"."EmpCode" AS nik,
    "HR_EMPLOYEE"."EmpName" AS nama,
    CASE
        WHEN "HR_EMPLOYEE"."Gender" = 1 THEN 'L'
        WHEN "HR_EMPLOYEE"."Gender" = 2 THEN 'P'
        ELSE 'L'
    END AS jenis_kelamin,
    "HR_EMPLOYEE"."LocCode" AS loc_code,
    "HR_GANGLN"."GangCode" AS gang_code
FROM "HR_EMPLOYEE"
JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
WHERE "HR_GANGLN"."GangCode" = ?
    AND "HR_EMPLOYEE"."EmpCode" IS NOT NULL
    AND "HR_EMPLOYEE"."EmpName" IS NOT NULL
ORDER BY "HR_EMPLOYEE"."EmpName"