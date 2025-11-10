SELECT TOP 100
       t.*,
       ln.Amount
FROM   PR_ADTRANS      AS t
JOIN   PR_ADTRANSLN    AS ln
       ON t.ID = ln.MasterID
WHERE  t.EmpCode = 'H0033'
  AND  t.DocDate >= '2025-05-01'
  AND  t.DocDate <  '2025-06-01'
  AND DocDesc = 'POTONGAN SPSI'
