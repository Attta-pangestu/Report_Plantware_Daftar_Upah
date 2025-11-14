SELECT SUM(trl."Amount") AS TotalAmount,
       SUM(trl."Hours") AS TotalHours
FROM "PR_TASKREG_ARC" tr
JOIN "PR_TASKREGLN_ARC" trl ON tr."id" = trl."masterId"
WHERE trl."EmpCode" = 'H0330'
  AND tr."DocDate" >= '2025-05-01'
  AND tr."DocDate" < '2025-06-01'
  AND trl.OT = 1
