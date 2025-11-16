from typing import Dict, Any, List
from app.repositories.employee_repository import EmployeeRepository
from app.models.payroll import PayrollRow
from datetime import datetime

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

        # Get working days for the month (simplified calculation)
        if month and year:
            # Simplified working days calculation - can be enhanced with actual calendar
            working_days = 22  # Default working days
            if month in [1, 3, 5, 7, 8, 10, 12]:  # 31 days months
                working_days = 23
            elif month in [4, 6, 9, 11]:  # 30 days months
                working_days = 22
            elif month == 2:  # February
                if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                    working_days = 20  # Leap year
                else:
                    working_days = 19  # Non-leap year
        else:
            working_days = 22  # Default

        employees = repo.list(0, 1000, gang_code=gang_code)

        for i, emp in enumerate(employees, start=1):
            # Use real employee data from database
            gaji_pokok_real = float(emp.get("gaji_pokok", 0))
            if gaji_pokok_real <= 0:
                # Fallback to calculation if gaji_pokok is not available
                upah_dasar = 129220.0  # Default base rate
                gaji_pokok_real = upah_dasar * working_days

            # Calculate upah pokok (daily wage * working days)
            upah_dasar = gaji_pokok_real / working_days
            upah_pokok = upah_dasar * working_days

            # Calculate tunjangan based on real data or standard rates
            beras_rate = 3650.0
            beras_jumlah = 31 * beras_rate  # 31 days * rice allowance

            jabatan_rate = 3500.0
            jabatan_jumlah = 17 * jabatan_rate  # Standard calculation

            # Calculate masa kerja (years of service)
            # This would normally be calculated from hire date
            masa_kerja_tahun = 1  # Default, can be calculated from employee join date
            masa_kerja_jumlah = masa_kerja_tahun * 10000  # Standard rate

            # Calculate lembur (overtime) - simplified
            lembur_jam = 0  # Would come from attendance data
            lembur_jumlah = lembur_jam * (upah_dasar * 1.5)  # 1.5x rate for overtime

            total_tunjangan = beras_jumlah + jabatan_jumlah + masa_kerja_jumlah + lembur_jumlah

            # Calculate premi values - these would normally come from production data
            # Using some sample values for demonstration
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
            jumlah_upah_kotor = gaji_pokok_real + total_tunjangan + total_premi

            # Calculate potongan (deductions)
            # BPJS calculations
            bpjs_kes_rate = 0.01  # 1%
            bpjs_pek_rate = 0.02  # 2%
            bpjs_maj_rate = 0.0374  # 3.74%

            pot_bpjs_kes = min(gaji_pokok_real * bpjs_kes_rate, 150000)  # Max 150k
            pot_bpjs_pek = min(jumlah_upah_kotor * bpjs_pek_rate, 300000)  # Max 300k
            pot_bpjs_maj = min(jumlah_upah_kotor * bpjs_maj_rate, 600000)  # Max 600k

            # Other deductions
            pot_pph21 = 0.0  # Would be calculated based on annual income
            pot_kontan = 0.0
            pot_thr = 0.0  # Would be calculated based on THR data
            pot_pinjam = 0.0  # Would come from loan data
            pot_kl = 0.0  # Koperasi loans

            pot_total_1 = pot_bpjs_kes
            pot_total_2 = pot_bpjs_pek
            pot_total_3 = pot_bpjs_maj
            pot_total_4 = pot_pph21 + pot_kontan + pot_thr + pot_pinjam + pot_kl

            total_potongan = pot_total_1 + pot_total_2 + pot_total_3 + pot_total_4
            upah_bersih = jumlah_upah_kotor - total_potongan

            # Attendance data (would normally come from attendance system)
            cuti_tahunan_hari = 0
            cuti_sakit_haid_hari = 0
            cuti_minggu_hari = 0
            cuti_nasional_hari = 0
            cuti_izin_hari = 0

            # Calculate actual HK (Hari Kerja)
            jumlah_hk = working_days - (cuti_tahunan_hari + cuti_sakit_haid_hari + cuti_minggu_hari +
                                       cuti_nasional_hari + cuti_izin_hari)

            # Tidak hadir (absence)
            tidak_hadir_cth = 0  # Cuti tanpa hak
            tidak_hadir_alpa = 0  # Tanpa keterangan

            row = PayrollRow(
                no=i,
                jenis_kelamin=emp.get("jenis_kelamin", ""),
                nik=emp.get("nik", ""),
                nama=emp.get("nama", ""),
                upah_dasar=upah_dasar,
                hari_kerja=working_days,
                upah_pokok=upah_pokok,
                cuti_tahunan_hari=cuti_tahunan_hari,
                cuti_sakit_haid_hari=cuti_sakit_haid_hari,
                cuti_minggu_hari=cuti_minggu_hari,
                cuti_nasional_hari=cuti_nasional_hari,
                cuti_izin_hari=cuti_izin_hari,
                jumlah_hk=jumlah_hk,
                gaji_pokok=gaji_pokok_real,
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
                tidak_hadir_cth=tidak_hadir_cth,
                tidak_hadir_alpa=tidak_hadir_alpa,
            )
            rows.append(row)
        return rows
