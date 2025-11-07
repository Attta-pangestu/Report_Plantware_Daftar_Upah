SELECT DISTINCT
       t.DocDesc
FROM   PR_ADTRANS AS t
WHERE  t.DocDesc LIKE '%kor%'
ORDER  BY t.DocDesc;
