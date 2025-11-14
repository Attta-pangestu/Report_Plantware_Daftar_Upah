SELECT TOP 100 * 
FROM "PR_EMP_ATTN_ARC"
WHERE EmpCode = 'H0517'
  AND AttnDate >= '2025-05-01'
  AND AttnDate < '2025-06-01'
AND "TodayIsRestDay" = 'true'
