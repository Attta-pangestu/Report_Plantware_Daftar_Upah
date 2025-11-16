from typing import Dict, Any, List
from app.repositories.employee_repository import EmployeeRepository
from app.models.payroll import PayrollRow

class PayrollService:
    async def calculate(self, upah_dasar: float, hk_count: int, allowances: Dict[str, float], deductions: Dict[str, float]) -> Dict[str, Any]:
        working_days = hk_count
        basic_salary = working_days * upah_dasar
        total_allowances = sum(allowances.values()) if allowances else 0
        total_deductions = sum(deductions.values()) if deductions else 0
        net_salary = basic_salary + total_allowances - total_deductions
        return {"hk_count": hk_count, "working_days": working_days, "basic_salary": basic_salary, "allowances": allowances, "deductions": deductions, "net_salary": net_salary}

    async def generate_rows(self, repo: EmployeeRepository, gang_code: str = None, month: int = None, year: int = None) -> List[PayrollRow]:
        rows: List[PayrollRow] = []
        base_rate = 129220.0
        base_days = 31
        employees = repo.list(0, 1000, gang_code=gang_code)
        for i, emp in enumerate(employees, start=1):
            upah_pokok = base_rate * base_days
            gaji_pokok = upah_pokok
            beras_rate = 3650.0
            beras_jumlah = 114150.0
            jabatan_rate = 3500.0
            jabatan_jumlah = 59500.0
            masa_kerja_tahun = 0
            masa_kerja_jumlah = 0.0
            lembur_jam = 0
            lembur_jumlah = 0.0
            total_tunjangan = beras_jumlah + jabatan_jumlah + masa_kerja_jumlah + lembur_jumlah
            premi_values = {
                "premi_brondol": 0.0,
                "premi_pruning": 0.0,
                "premi_angkut_material": 0.0,
                "premi_angkut_tbs": 0.0,
                "premi_harvesting": 0.0,
                "premi_harvesting_incentive": 0.0,
                "premi_pupuk": 0.0,
            }
            total_premi = sum(premi_values.values())
            jumlah_upah_kotor = gaji_pokok + total_tunjangan + total_premi
            pot_pph21 = 0.0
            pot_kontan = 0.0
            pot_thr = 0.0
            pot_pinjam = 0.0
            pot_kl = 0.0
            pot_bpjs_kes = 0.0
            pot_bpjs_pek = 0.0
            pot_bpjs_maj = 0.0
            pot_total_1 = 0.0
            pot_total_2 = 0.0
            pot_total_3 = 0.0
            pot_total_4 = 0.0
            total_potongan = 0.0
            upah_bersih = jumlah_upah_kotor - total_potongan
            row = PayrollRow(
                no=i,
                jenis_kelamin=emp.get("jenis_kelamin", ""),
                nik=emp.get("nik", ""),
                nama=emp.get("nama", ""),
                upah_dasar=base_rate,
                hari_kerja=base_days,
                upah_pokok=upah_pokok,
                cuti_tahunan_hari=0,
                cuti_sakit_haid_hari=0,
                cuti_minggu_hari=0,
                cuti_nasional_hari=0,
                cuti_izin_hari=0,
                jumlah_hk=base_days,
                gaji_pokok=gaji_pokok,
                beras_rate=beras_rate,
                beras_jumlah=beras_jumlah,
                jabatan_rate=jabatan_rate,
                jabatan_jumlah=jabatan_jumlah,
                masa_kerja_tahun=masa_kerja_tahun,
                masa_kerja_jumlah=masa_kerja_jumlah,
                lembur_jam=lembur_jam,
                lembur_jumlah=lembur_jumlah,
                total_tunjangan=total_tunjangan,
                premi_brondol=premi_values["premi_brondol"],
                premi_pruning=premi_values["premi_pruning"],
                premi_angkut_material=premi_values["premi_angkut_material"],
                premi_angkut_tbs=premi_values["premi_angkut_tbs"],
                premi_harvesting=premi_values["premi_harvesting"],
                premi_harvesting_incentive=premi_values["premi_harvesting_incentive"],
                premi_pupuk=premi_values["premi_pupuk"],
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
        return rows
