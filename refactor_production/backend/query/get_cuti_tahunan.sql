SELECT COUNT(*) as total_cuti
FROM "PR_TASKREGLN_ARC"
WHERE EmpCode = ?
  AND CreatedDate >= ?
  AND CreatedDate < ?
  AND TaskCode = 'GA9129AB2'
