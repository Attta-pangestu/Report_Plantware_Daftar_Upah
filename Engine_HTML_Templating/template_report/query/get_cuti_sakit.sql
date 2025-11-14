SELECT TOP 100 
    tr.*, 
    tc.taskDesc
FROM "PR_TASKREGLN_ARC" tr
LEFT JOIN "PR_TASKCODE" tc ON tr.TaskCode = tc.TaskCode
WHERE tr.EmpCode = 'H0080'
  AND tr.CreatedDate >= '2025-05-01'
  AND tr.CreatedDate < '2025-06-01'
  AND tr.TaskCode = 'GA9126AB2'
