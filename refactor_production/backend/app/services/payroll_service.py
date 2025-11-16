from typing import Dict, Any, List, Tuple
from app.repositories.employee_repository import EmployeeRepository
from app.models.payroll import PayrollRow
from datetime import datetime
from pathlib import Path
from database.services.database import Database
import logging

class PayrollService:
    def _paramify(self, sql: str, emp_code: str, start_date: str = None, end_date: str = None) -> Tuple[str, Tuple]:
        import re
        s = sql
        s = re.sub(r"(?i)([\"\[]?EmpCode[\"\]]?\s*(?:=|LIKE)\s*)'[^']*'", r"\1?", s)
        if start_date and end_date:
            s = re.sub(r"(?i)([\w\.\"\[\]]*DocDate)\s*>=\s*'[^']*'", r"\1 >= ?", s)
            s = re.sub(r"(?i)([\w\.\"\[\]]*DocDate)\s*<\s*'[^']*'", r"\1 < ?", s)
            if s.count('?') < 3:
                s = re.sub(r"'\d{4}-\d{2}-\d{2}'", '?', s, count=2)
            return s, (emp_code, start_date, end_date)
        return s, (emp_code,)
    async def calculate(self, upah_dasar: float, hk_count: int, allowances: Dict[str, float], deductions: Dict[str, float]) -> Dict[str, Any]:
        working_days = hk_count
        basic_salary = working_days * upah_dasar
        total_allowances = sum(allowances.values()) if allowances else 0
        total_deductions = sum(deductions.values()) if deductions else 0
        net_salary = basic_salary + total_allowances - total_deductions
        return {"hk_count": hk_count, "working_days": working_days, "basic_salary": basic_salary, "allowances": allowances, "deductions": deductions, "net_salary": net_salary}

    def _dates(self, month: int, year: int) -> Tuple[str, str]:
        s = f"{year:04d}-{month:02d}-01"
        e = f"{year+1:04d}-01-01" if month == 12 else f"{year:04d}-{month+1:02d}-01"
        return s, e

    def _scalar(self, cur_row, idx=0):
        if not cur_row:
            return 0
        v = cur_row[idx]
        return float(v or 0)

    async def generate_rows(self, repo: EmployeeRepository, gang_code: str = None, month: int = None, year: int = None) -> List[PayrollRow]:
        rows: List[PayrollRow] = []
        db = Database.instance()
        employees = repo.list(0, 1000, gang_code=gang_code)
        s, e = self._dates(month or datetime.now().month, year or datetime.now().year)

        for i, emp in enumerate(employees, start=1):
            nik = (emp.get("nik") or "").strip()
            import calendar
            month_i = int((month or datetime.now().month))
            year_i = int((year or datetime.now().year))
            hk_count = calendar.monthrange(year_i, month_i)[1]

            pay_q = "SELECT TOP 1 \"PayRate\" FROM \"HR_PAYROLL\" WHERE \"EmpCode\" = ?"
            payrate = self._scalar(db.query_one(pay_q, (nik,)))

            beras_q_path = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query" / "Tunjangan" / "Payrate_Beras.sql"
            with beras_q_path.open('r', encoding='utf-8') as f:
                beras_q_raw = f.read()
            beras_q, beras_params = self._paramify(beras_q_raw, nik)
            beras_rate = self._scalar(db.query_one(beras_q, beras_params))

            jab_q_path = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query" / "Tunjangan" / "Gett_Amount_Tunjangan_Jabatan.sql"
            with jab_q_path.open('r', encoding='utf-8') as f:
                jab_q_raw = f.read()
            jab_q, jab_params = self._paramify(jab_q_raw, nik, s, e)
            jab_res = db.query_one(jab_q, jab_params)
            jabatan_jumlah = self._scalar(jab_res, -1)
            jabatan_rate = (jabatan_jumlah / hk_count) if hk_count > 0 and jabatan_jumlah > 0 else 0

            mk_years_q_path = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query" / "Tunjangan" / "count_masa_kerja.sql"
            with mk_years_q_path.open('r', encoding='utf-8') as f:
                mk_y_raw = f.read()
            mk_y_q, mk_y_params = self._paramify(mk_y_raw, nik)
            mk_years_res = db.query_one(mk_y_q, mk_y_params)
            masa_kerja_tahun = int((mk_years_res[-1] or 0) if mk_years_res else 0)

            mk_amt_q_path = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query" / "Tunjangan" / "get_amount_masa_kerja.sql"
            with mk_amt_q_path.open('r', encoding='utf-8') as f:
                mk_amt_raw = f.read()
            mk_amt_q, mk_amt_params = self._paramify(mk_amt_raw, nik, s, e)
            mk_amt_res = db.query_one(mk_amt_q, mk_amt_params)
            masa_kerja_jumlah = self._scalar(mk_amt_res, -1)

            lembur_q_path = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query" / "Tunjangan" / "get_amount_lembur.sql"
            with lembur_q_path.open('r', encoding='utf-8') as f:
                lembur_raw = f.read()
            lembur_q, lembur_params = self._paramify(lembur_raw, nik, s, e)
            lembur_res = db.query_one(lembur_q, lembur_params)
            lembur_jumlah = self._scalar(lembur_res, 0)
            lembur_jam = int(self._scalar(lembur_res, 1))

            brondol_q_path = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query" / "Tunjangan" / "get_brondol_amount.sql"
            with brondol_q_path.open('r', encoding='utf-8') as f:
                brondol_raw = f.read()
            brondol_q, brondol_params = self._paramify(brondol_raw, nik, s, e)
            brondol_res = db.query_one(brondol_q, brondol_params)
            premi_brondol = self._scalar(brondol_res, 0)

            def premi_amount(pattern: str) -> float:
                q = (
                    "SELECT SUM(ln.Amount) FROM PR_ADTRANS_ARC t JOIN PR_ADTRANSLN_ARC ln ON t.ID = ln.MasterID "
                    "WHERE t.EmpCode = ? AND t.DocDate >= ? AND t.DocDate < ? AND UPPER(t.DocDesc) LIKE UPPER(?)"
                )
                res = db.query_one(q, (nik, s, e, pattern))
                return self._scalar(res, 0)

            premi_pruning = premi_amount('%PRUNING%')
            premi_angkut_material = premi_amount('%ANGKUT%MATERIAL%')
            premi_angkut_tbs = premi_amount('%ANGKUT%TBS%')
            premi_harvesting = premi_amount('%HARVESTING%')
            premi_harvesting_incentive = premi_amount('%INCENTIVE%PANEN%')
            premi_pupuk = premi_amount('%PUPUK%')

            spsi_path = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query" / "potongan" / "potongan_spsi.sql"
            with spsi_path.open('r', encoding='utf-8') as f:
                spsi_raw = f.read()
            spsi_q, spsi_params = self._paramify(spsi_raw, nik, s, e)
            spsi_res = db.query_one(spsi_q, spsi_params)
            pot_spsi = self._scalar(spsi_res, -1)

            pph_path = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query" / "potongan" / "potong_pph21.sql"
            with pph_path.open('r', encoding='utf-8') as f:
                pph_raw = f.read()
            pph_q, pph_params = self._paramify(pph_raw, nik, s, e)
            pph_res = db.query_one(pph_q, pph_params)
            pot_pph21 = self._scalar(pph_res, -1)

            cuti_tahunan_q_path = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query" / "get_cuti_tahunan.sql"
            with cuti_tahunan_q_path.open('r', encoding='utf-8') as f:
                cuti_tah_raw = f.read()
            cuti_tah_q, cuti_tah_params = self._paramify(cuti_tah_raw, nik, s, e)
            cuti_tah_count = len(db.query_all(cuti_tah_q, cuti_tah_params))

            cuti_sakit_q_path = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query" / "get_cuti_sakit.sql"
            with cuti_sakit_q_path.open('r', encoding='utf-8') as f:
                cuti_sakit_raw = f.read()
            cuti_sakit_q, cuti_sakit_params = self._paramify(cuti_sakit_raw, nik, s, e)
            cuti_sakit_count = len(db.query_all(cuti_sakit_q, cuti_sakit_params))

            hk_minggu_q_path = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query" / "get_HK_minggu.sql"
            with hk_minggu_q_path.open('r', encoding='utf-8') as f:
                hk_minggu_raw = f.read()
            hk_minggu_q, hk_minggu_params = self._paramify(hk_minggu_raw, nik, s, e)
            cuti_minggu_hari = len(db.query_all(hk_minggu_q, hk_minggu_params))

            hk_nas_q_path = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query" / "get_HK_national_holiday.sql"
            with hk_nas_q_path.open('r', encoding='utf-8') as f:
                hk_nas_raw = f.read()
            hk_nas_q, hk_nas_params = self._paramify(hk_nas_raw, nik, s, e)
            cuti_nasional_hari = len(db.query_all(hk_nas_q, hk_nas_params))

            cuti_izin_hari = 0

            hari_kerja = max(0, int(hk_count) - (cuti_tah_count + cuti_sakit_count + cuti_minggu_hari + cuti_nasional_hari))
            upah_pokok = payrate * hari_kerja

            beras_jumlah = hk_count * beras_rate if beras_rate > 0 else 0
            total_tunjangan = beras_jumlah + jabatan_jumlah + masa_kerja_jumlah + lembur_jumlah

            total_premi = sum([
                premi_brondol, premi_pruning, premi_angkut_material, premi_angkut_tbs, premi_harvesting,
                premi_harvesting_incentive, premi_pupuk
            ])
            jumlah_upah_kotor = upah_pokok + total_tunjangan + total_premi

            bpjs_kes_rate = 0.01
            bpjs_pek_rate = 0.02
            bpjs_maj_rate = 0.0374
            pot_bpjs_kes = min(upah_pokok * bpjs_kes_rate, 150000)
            pot_bpjs_pek = min(jumlah_upah_kotor * bpjs_pek_rate, 300000)
            pot_bpjs_maj = min(jumlah_upah_kotor * bpjs_maj_rate, 600000)

            pot_kontan = 0.0
            pot_thr = 0.0
            pot_pinjam = 0.0
            pot_kl = 0.0

            pot_total_1 = pot_bpjs_kes
            pot_total_2 = pot_bpjs_pek
            pot_total_3 = pot_bpjs_maj
            pot_total_4 = pot_pph21 + pot_kontan + pot_thr + pot_pinjam + pot_kl + pot_spsi
            total_potongan = pot_total_1 + pot_total_2 + pot_total_3 + pot_total_4
            upah_bersih = jumlah_upah_kotor - total_potongan

            row = PayrollRow(
                no=i,
                jenis_kelamin=emp.get("jenis_kelamin", ""),
                nik=nik,
                nama=emp.get("nama", ""),
                upah_dasar=payrate,
                hari_kerja=hari_kerja,
                upah_pokok=upah_pokok,
                cuti_tahunan_hari=int(cuti_tah_count),
                cuti_sakit_haid_hari=int(cuti_sakit_count),
                cuti_minggu_hari=int(cuti_minggu_hari),
                cuti_nasional_hari=int(cuti_nasional_hari),
                cuti_izin_hari=int(cuti_izin_hari),
                jumlah_hk=int(hk_count),
                gaji_pokok=payrate * int(hk_count),
                beras_rate=beras_rate,
                beras_jumlah=beras_jumlah,
                jabatan_rate=jabatan_rate,
                jabatan_jumlah=jabatan_jumlah,
                masa_kerja_tahun=int(masa_kerja_tahun),
                masa_kerja_jumlah=masa_kerja_jumlah,
                lembur_jam=int(lembur_jam),
                lembur_jumlah=lembur_jumlah,
                total_tunjangan=total_tunjangan,
                premi_brondol=premi_brondol,
                premi_pruning=premi_pruning,
                premi_angkut_material=premi_angkut_material,
                premi_angkut_tbs=premi_angkut_tbs,
                premi_harvesting=premi_harvesting,
                premi_harvesting_incentive=premi_harvesting_incentive,
                premi_pupuk=premi_pupuk,
                total_premi=total_premi,
                jumlah_upah_kotor=jumlah_upah_kotor,
                pot_pph21=pot_pph21,
                pot_kontan=pot_kontan,
                pot_thr=pot_thr,
                pot_pinjam=pot_pinjam,
                pot_kl=pot_kl,
                pot_bpjs_kes=pot_bpjs_kes,
                pot_bpjs_pek=pot_bpjs_pek,
                pot_bpjs_maj=pot_bpjs_maj,
                pot_total_1=pot_total_1,
                pot_total_2=pot_total_2,
                pot_total_3=pot_total_3,
                pot_total_4=pot_total_4,
                total_potongan=total_potongan,
                upah_bersih=upah_bersih,
                tidak_hadir_cth=0,
                tidak_hadir_alpa=0,
            )
            rows.append(row)
        try:
            logger = logging.getLogger(__name__)
            fields = [
                'upah_dasar','hari_kerja','upah_pokok','beras_rate','beras_jumlah','jabatan_jumlah',
                'masa_kerja_tahun','masa_kerja_jumlah','lembur_jam','lembur_jumlah','total_tunjangan',
                'premi_brondol','premi_pruning','premi_angkut_material','premi_angkut_tbs','premi_harvesting',
                'premi_harvesting_incentive','premi_pupuk','total_premi','jumlah_upah_kotor','pot_pph21',
                'pot_bpjs_kes','pot_bpjs_pek','pot_bpjs_maj','total_potongan','upah_bersih'
            ]
            for f in fields:
                try:
                    values = { getattr(r, f) for r in rows }
                    if len(values) <= 1:
                        v = next(iter(values), None)
                        logger.info(f"Uniform {f} across rows: {v}")
                except Exception:
                    pass
        except Exception:
            pass
        return rows
