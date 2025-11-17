from typing import Dict, Any, List, Tuple, Optional
from app.repositories.employee_repository import EmployeeRepository
from app.models.payroll import PayrollRow
from datetime import datetime
from pathlib import Path
from database.services.database import Database
import time
import logging
from app.core.config import get_testing_token, is_test_mode

class PayrollService:
    """
    Payroll calculation service implementing correct formulas from reference code
    daftar_upah_engine_real_database.py
    """

    def __init__(self):
        # Constants from reference code (can be made configurable)
        self.gaji_pokok_min = 3876600  # Default BPJS calculation base

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

    def calculate_hari_kerja(self, hk_count: int, cuti_tahunan: int, cuti_sakit: int,
                           hk_minggu: int, hk_nasional: int) -> int:
        """
        Calculate Hari Kerja = HK - (Tahunan + Sakit + Minggu + Nasional)
        """
        total_cuti = cuti_tahunan + cuti_sakit + hk_minggu + hk_nasional
        hari_kerja = max(0, hk_count - total_cuti)
        return hari_kerja

    def calculate_gaji_pokok(self, hk_count: int, payrate: float,
                           cuti_tahunan: int = 0, cuti_sakit: int = 0,
                           hk_minggu: int = 0, hk_nasional: int = 0) -> float:
        """
        Calculate Gaji Pokok = (HK - Total Cuti) x Payrate (Rp)
        """
        total_cuti = cuti_tahunan + cuti_sakit + hk_minggu + hk_nasional
        hari_kerja = max(0, hk_count - total_cuti)
        return hari_kerja * float(payrate) if payrate else 0

    def calculate_gaji_pokok_jmlhk(self, hk_count: int, payrate: float) -> float:
        """
        Calculate Gaji Pokok (JML HK × Upah Dasar) - THIS IS USED FOR UPAH KOTOR CALCULATION
        """
        return hk_count * float(payrate) if payrate else 0

    def calculate_total_tunjangan(self, hk_count: int, beras_payrate: float,
                                 jabatan_amount: float, masa_kerja_amount: float,
                                 lembur_amount: float) -> float:
        """
        Calculate Total Tunjangan = Beras + Jabatan + Masa Kerja + Lembur
        """
        beras_jumlah = hk_count * beras_payrate if beras_payrate > 0 else 0
        return beras_jumlah + jabatan_amount + masa_kerja_amount + lembur_amount

    def calculate_total_premi(self, brondol_amount: float, pruning_amount: float,
                              dynamic_premi_amounts: List[float], koreksi_amount: float) -> float:
        """
        Calculate Total Premi = BRONDOL + PRUNING + Dynamic Premi + Koreksi
        """
        total_dynamic = sum(dynamic_premi_amounts)
        return brondol_amount + pruning_amount + total_dynamic + koreksi_amount

    def calculate_bpjs_components(self, masa_kerja_jumlah: float) -> Dict[str, float]:
        """
        Calculate BPJS components based on reference code formulas
        Formula: (gaji_pokok_min + masa_kerja_jumlah) × 1% for pekerja, majikan = 4 × pekerja
        """
        bpjs_base = self.gaji_pokok_min + masa_kerja_jumlah

        # Pekerja calculations (1% of base)
        bpjs_kesehatan_pekerja = bpjs_base * 0.01
        bpjs_pensiun_pekerja = self.gaji_pokok_min * 0.01  # Always use minimum for pension
        bpjs_pensiun_majikan = self.gaji_pokok_min * 0.02

        # Majikan calculations (4 × pekerja amount for health)
        bpjs_kesehatan_majikan = bpjs_kesehatan_pekerja * 4

        # Total BPJS (only pekerja components for deduction)
        bpjs_pekerja_total = bpjs_kesehatan_pekerja + bpjs_pensiun_pekerja

        return {
            'kesehatan_pekerja': bpjs_kesehatan_pekerja,
            'kesehatan_majikan': bpjs_kesehatan_majikan,
            'pensiun_pekerja': bpjs_pensiun_pekerja,
            'pensiun_majikan': bpjs_pensiun_majikan,
            'jumlah': bpjs_kesehatan_pekerja + bpjs_kesehatan_majikan + bpjs_pensiun_pekerja + bpjs_pensiun_majikan,
            'pekerja_total': bpjs_pekerja_total
        }

    def calculate_jumlah_upah_kotor(self, hk_count: int, payrate: float,
                                    total_tunjangan: float, total_premi: float) -> float:
        """
        Calculate Jumlah Upah Kotor = Gaji Pokok (JML HK × Upah Dasar) + Total Tunjangan + Total Premi
        """
        gaji_pokok = self.calculate_gaji_pokok_jmlhk(hk_count, payrate)
        return gaji_pokok + total_tunjangan + total_premi

    def calculate_total_potongan(self, bpjs_pekerja_total: float, spsi_amount: float,
                               pph21_amount: float) -> float:
        """
        Calculate Total Potongan = BPJS Kesehatan Pekerja + BPJS Pensiun Pekerja + Iuran SPSI + PPH21
        """
        return bpjs_pekerja_total + spsi_amount + pph21_amount

    def calculate_upah_bersih(self, jumlah_upah_kotor: float, total_potongan: float) -> float:
        """
        Calculate Upah Bersih = Jumlah Upah Kotor - Total Potongan
        """
        return jumlah_upah_kotor - total_potongan

    async def calculate(self, upah_dasar: float, hk_count: int,
                        allowances: Dict[str, float], deductions: Dict[str, float]) -> Dict[str, Any]:
        """
        Legacy method - simplified calculation for backward compatibility
        """
        working_days = hk_count
        basic_salary = working_days * upah_dasar
        total_allowances = sum(allowances.values()) if allowances else 0
        total_deductions = sum(deductions.values()) if deductions else 0
        net_salary = basic_salary + total_allowances - total_deductions

        return {
            "hk_count": hk_count,
            "working_days": working_days,
            "basic_salary": basic_salary,
            "allowances": allowances,
            "deductions": deductions,
            "net_salary": net_salary
        }

    def _dates(self, month: int, year: int) -> Tuple[str, str]:
        s = f"{year:04d}-{month:02d}-01"
        e = f"{year+1:04d}-01-01" if month == 12 else f"{year:04d}-{month+1:02d}-01"
        return s, e

    def _scalar(self, cur_row, idx=0):
        if not cur_row:
            return 0
        v = cur_row[idx]
        return float(v or 0)

    _cache: Dict[str, Any] = {}
    _cache_exp: Dict[str, float] = {}
    _cache_ttl: int = 300

    def _cache_get(self, key: str):
        exp = self._cache_exp.get(key)
        if not exp:
            return None
        if exp < time.time():
            try:
                del self._cache[key]
                del self._cache_exp[key]
            except Exception:
                pass
            return None
        return self._cache.get(key)

    def _cache_set(self, key: str, value: Any, ttl: int = None):
        t = ttl if isinstance(ttl, int) and ttl > 0 else self._cache_ttl
        self._cache[key] = value
        self._cache_exp[key] = time.time() + t

    def _chunks(self, arr: List[str], size: int) -> List[List[str]]:
        out = []
        for i in range(0, len(arr), size):
            out.append(arr[i:i+size])
        return out

    def _payrates_map(self, db: Database, emp_codes: List[str]) -> Dict[str, float]:
        if not emp_codes:
            return {}
        key = f"payrates:{hash(tuple(emp_codes))}"
        cached = self._cache_get(key)
        if isinstance(cached, dict):
            return cached
        m: Dict[str, float] = {}
        for chunk in self._chunks(emp_codes, 200):
            ph = ','.join(['?']*len(chunk))
            sql = f'SELECT "EmpCode","PayRate" FROM "HR_PAYROLL" WHERE "EmpCode" IN ({ph})'
            rows = db.query_all(sql, tuple(chunk))
            for r in rows:
                m[str(r[0]).strip()] = float(r[1] or 0)
        self._cache_set(key, m)
        return m

    def _premi_map(self, db: Database, emp_codes: List[str], start_date: str, end_date: str, pattern: str) -> Dict[str, float]:
        if not emp_codes:
            return {}
        key = f"premi:{pattern}:{start_date}:{end_date}:{hash(tuple(emp_codes))}"
        cached = self._cache_get(key)
        if isinstance(cached, dict):
            return cached
        m: Dict[str, float] = {}
        for chunk in self._chunks(emp_codes, 200):
            ph = ','.join(['?']*len(chunk))
            sql = (
                f'SELECT t."EmpCode", SUM(ln."Amount") '
                f'FROM "PR_ADTRANS_ARC" t JOIN "PR_ADTRANSLN_ARC" ln ON t."ID" = ln."MasterID" '
                f'WHERE t."EmpCode" IN ({ph}) AND t."DocDate" >= ? AND t."DocDate" < ? AND UPPER(t."DocDesc") LIKE UPPER(?) '
                f'GROUP BY t."EmpCode"'
            )
            params = tuple(chunk) + (start_date, end_date, pattern)
            rows = db.query_all(sql, params)
            for r in rows:
                m[str(r[0]).strip()] = float(r[1] or 0)
        self._cache_set(key, m)
        return m

    def _cuti_maps(self, db: Database, emp_codes: List[str], start_date: str, end_date: str, cuti_tah_raw: str, cuti_sakit_raw: str, hk_minggu_raw: str, hk_nas_raw: str) -> Dict[str, Dict[str, int]]:
        key = f"cuti:{start_date}:{end_date}:{hash(tuple(emp_codes))}"
        cached = self._cache_get(key)
        if isinstance(cached, dict):
            return cached
        out: Dict[str, Dict[str, int]] = { c: { 'tahunan':0, 'sakit':0, 'minggu':0, 'nasional':0 } for c in emp_codes }
        if not emp_codes:
            return out
        for chunk in self._chunks(emp_codes, 100):
            with db.transaction() as cur:
                for nik in chunk:
                    ct_q, ct_p = self._paramify(cuti_tah_raw, nik, start_date, end_date)
                    cs_q, cs_p = self._paramify(cuti_sakit_raw, nik, start_date, end_date)
                    hm_q, hm_p = self._paramify(hk_minggu_raw, nik, start_date, end_date)
                    hn_q, hn_p = self._paramify(hk_nas_raw, nik, start_date, end_date)
                    cur.execute(ct_q, *ct_p)
                    t_rows = cur.fetchall()
                    cur.execute(cs_q, *cs_p)
                    s_rows = cur.fetchall()
                    cur.execute(hm_q, *hm_p)
                    m_rows = cur.fetchall()
                    cur.execute(hn_q, *hn_p)
                    n_rows = cur.fetchall()
                    out[nik]['tahunan'] = len(t_rows)
                    out[nik]['sakit'] = len(s_rows)
                    out[nik]['minggu'] = len(m_rows)
                    out[nik]['nasional'] = len(n_rows)
        self._cache_set(key, out)
        return out

    async def generate_rows(self, repo: EmployeeRepository, gang_code: str = None, month: int = None, year: int = None, skip: int = 0, limit: int = 1000, fields: List[str] = None) -> List[PayrollRow]:
        rows: List[PayrollRow] = []
        db = Database.instance()
        employees = repo.list(skip, limit, gang_code=gang_code)
        s, e = self._dates(month or datetime.now().month, year or datetime.now().year)
        want_all = fields is None or len(fields) == 0
        want = (lambda name: True) if want_all else (lambda name: name in set(fields))
        from pathlib import Path
        base = Path(__file__).resolve().parents[4] / "Engine_HTML_Templating" / "template_report" / "query"
        with (base / "Tunjangan" / "Payrate_Beras.sql").open('r', encoding='utf-8') as f:
            beras_q_raw = f.read()
        with (base / "Tunjangan" / "Gett_Amount_Tunjangan_Jabatan.sql").open('r', encoding='utf-8') as f:
            jab_q_raw = f.read()
        with (base / "Tunjangan" / "count_masa_kerja.sql").open('r', encoding='utf-8') as f:
            mk_y_raw = f.read()
        with (base / "Tunjangan" / "get_amount_masa_kerja.sql").open('r', encoding='utf-8') as f:
            mk_amt_raw = f.read()
        with (base / "Tunjangan" / "get_amount_lembur.sql").open('r', encoding='utf-8') as f:
            lembur_raw = f.read()
        with (base / "Tunjangan" / "get_brondol_amount.sql").open('r', encoding='utf-8') as f:
            brondol_raw = f.read()
        with (base / "potongan" / "potongan_spsi.sql").open('r', encoding='utf-8') as f:
            spsi_raw = f.read()
        with (base / "potongan" / "potong_pph21.sql").open('r', encoding='utf-8') as f:
            pph_raw = f.read()
        with (base / "get_cuti_tahunan.sql").open('r', encoding='utf-8') as f:
            cuti_tah_raw = f.read()
        with (base / "get_cuti_sakit.sql").open('r', encoding='utf-8') as f:
            cuti_sakit_raw = f.read()
        with (base / "get_HK_minggu.sql").open('r', encoding='utf-8') as f:
            hk_minggu_raw = f.read()
        with (base / "get_HK_national_holiday.sql").open('r', encoding='utf-8') as f:
            hk_nas_raw = f.read()

        emp_codes = [ (e.get('nik') or '').strip() for e in employees ]
        payrate_map: Dict[str, float] = {}
        if want_all or want('upah_dasar') or want('upah_pokok') or want('gaji_pokok'):
            payrate_map = self._payrates_map(db, emp_codes)
        premi_maps: Dict[str, Dict[str, float]] = {}
        if want_all or any([want('premi_brondol'), want('premi_pruning'), want('premi_angkut_material'), want('premi_angkut_tbs'), want('premi_harvesting'), want('premi_harvesting_incentive'), want('premi_pupuk'), want('total_premi'), want('jumlah_upah_kotor'), want('upah_bersih')]):
            premi_maps = {
                'pruning': self._premi_map(db, emp_codes, s, e, '%PRUNING%'),
                'angkut_material': self._premi_map(db, emp_codes, s, e, '%ANGKUT%MATERIAL%'),
                'angkut_tbs': self._premi_map(db, emp_codes, s, e, '%ANGKUT%TBS%'),
                'harvesting': self._premi_map(db, emp_codes, s, e, '%HARVESTING%'),
                'harvesting_incentive': self._premi_map(db, emp_codes, s, e, '%INCENTIVE%PANEN%'),
                'pupuk': self._premi_map(db, emp_codes, s, e, '%PUPUK%'),
            }
        cuti_maps: Dict[str, Dict[str, int]] = {}
        if want_all or any([want('cuti_tahunan_hari'), want('cuti_sakit_haid_hari'), want('cuti_minggu_hari'), want('cuti_nasional_hari'), want('hari_kerja'), want('jumlah_hk')]):
            cuti_maps = self._cuti_maps(db, emp_codes, s, e, cuti_tah_raw, cuti_sakit_raw, hk_minggu_raw, hk_nas_raw)

        for i, emp in enumerate(employees, start=1):
            nik = (emp.get("nik") or "").strip()
            import calendar
            month_i = int((month or datetime.now().month))
            year_i = int((year or datetime.now().year))
            hk_count = calendar.monthrange(year_i, month_i)[1]
            payrate = float(payrate_map.get(nik, 0.0))
            beras_rate = 0.0
            jabatan_jumlah = 0.0
            jabatan_rate = 0.0
            masa_kerja_tahun = 0
            masa_kerja_jumlah = 0.0
            lembur_jumlah = 0.0
            lembur_jam = 0
            if want_all or any([want('beras_rate'), want('beras_jumlah'), want('jabatan_rate'), want('jabatan_jumlah'), want('masa_kerja_tahun'), want('masa_kerja_jumlah'), want('lembur_jam'), want('lembur_jumlah'), want('total_tunjangan')]):
                beras_q, beras_params = self._paramify(beras_q_raw, nik)
                beras_rate = self._scalar(db.query_one(beras_q, beras_params))
                jab_q, jab_params = self._paramify(jab_q_raw, nik, s, e)
                jab_res = db.query_one(jab_q, jab_params)
                jabatan_jumlah = self._scalar(jab_res, -1)
                jabatan_rate = (jabatan_jumlah / hk_count) if hk_count > 0 and jabatan_jumlah > 0 else 0
                mk_y_q, mk_y_params = self._paramify(mk_y_raw, nik)
                mk_years_res = db.query_one(mk_y_q, mk_y_params)
                masa_kerja_tahun = int((mk_years_res[-1] or 0) if mk_years_res else 0)
                mk_amt_q, mk_amt_params = self._paramify(mk_amt_raw, nik, s, e)
                mk_amt_res = db.query_one(mk_amt_q, mk_amt_params)
                masa_kerja_jumlah = self._scalar(mk_amt_res, -1)
                lembur_q, lembur_params = self._paramify(lembur_raw, nik, s, e)
                lembur_res = db.query_one(lembur_q, lembur_params)
                lembur_jumlah = self._scalar(lembur_res, 0)
                lembur_jam = int(self._scalar(lembur_res, 1))
            brondol_res = None
            premi_brondol = 0.0
            if want_all or any([want('premi_brondol'), want('total_premi'), want('jumlah_upah_kotor'), want('upah_bersih')]):
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

            premi_pruning = float(premi_maps.get('pruning', {}).get(nik, 0.0))
            premi_angkut_material = float(premi_maps.get('angkut_material', {}).get(nik, 0.0))
            premi_angkut_tbs = float(premi_maps.get('angkut_tbs', {}).get(nik, 0.0))
            premi_harvesting = float(premi_maps.get('harvesting', {}).get(nik, 0.0))
            # Combine harvesting + incentive into a single column value
            premi_harvesting_incentive = (
                float(premi_maps.get('harvesting_incentive', {}).get(nik, 0.0)) + premi_harvesting
            )
            premi_pupuk = float(premi_maps.get('pupuk', {}).get(nik, 0.0))

            pot_spsi = 0.0
            pot_pph21 = 0.0
            if want_all or any([want('pot_pph21'), want('total_potongan'), want('upah_bersih')]):
                spsi_q, spsi_params = self._paramify(spsi_raw, nik, s, e)
                spsi_res = db.query_one(spsi_q, spsi_params)
                pot_spsi = self._scalar(spsi_res, -1)
                pph_q, pph_params = self._paramify(pph_raw, nik, s, e)
                pph_res = db.query_one(pph_q, pph_params)
                pot_pph21 = self._scalar(pph_res, -1)

            cuti_tah_count = int(cuti_maps.get(nik, {}).get('tahunan', 0))
            cuti_sakit_count = int(cuti_maps.get(nik, {}).get('sakit', 0))
            cuti_minggu_hari = int(cuti_maps.get(nik, {}).get('minggu', 0))
            cuti_nasional_hari = int(cuti_maps.get(nik, {}).get('nasional', 0))
            cuti_izin_hari = 0

            hari_kerja = max(0, int(hk_count) - (cuti_tah_count + cuti_sakit_count + cuti_minggu_hari + cuti_nasional_hari))

            # Correct calculation from reference code:
            # gaji_pokok_jmlhk = hk_count * payrate (use total HK count, not working days after deductions)
            # upah_pokok column displays hari_kerja * payrate for display purposes
            gaji_pokok_jmlhk = hk_count * payrate if payrate else 0
            upah_pokok = payrate * hari_kerja if (want_all or want('upah_pokok')) else 0

            beras_jumlah = hk_count * beras_rate if beras_rate > 0 else 0
            total_tunjangan = beras_jumlah + jabatan_jumlah + masa_kerja_jumlah + lembur_jumlah

            # Avoid double-counting: harvesting is merged into harvesting_incentive
            total_premi = sum([
                premi_brondol, premi_pruning, premi_angkut_material, premi_angkut_tbs,
                premi_harvesting_incentive, premi_pupuk
            ])

            # Correct calculation from reference code:
            # jumlah_upah_kotor = gaji_pokok_jmlhk + total_tunjangan + total_premi
            jumlah_upah_kotor = gaji_pokok_jmlhk + total_tunjangan + total_premi

            bpjs_kes_rate = 0.01
            bpjs_pek_rate = 0.02
            bpjs_maj_rate = 0.0374
            pot_bpjs_kes = min(gaji_pokok_jmlhk * bpjs_kes_rate, 150000)  # Use gaji_pokok_jmlhk (total HK base) for consistency
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
                gaji_pokok=gaji_pokok_jmlhk,
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
                premi_harvesting=0.0,
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
                pot_spsi=pot_spsi,
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
