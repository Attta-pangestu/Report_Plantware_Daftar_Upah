#!/usr/bin/env python3
"""
Daftar Upah Template Engine with Real Database Integration
Uses simple database connection to get real employee data from SQL query
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import argparse
from jinja2 import Environment, FileSystemLoader, Template

from simple_database_query import SimpleEmployeeQueryManager


@dataclass
class PayrollData:
    """Payroll calculation data"""
    basic_salary: float = 4000000
    overtime_hours: int = 0
    overtime_rate: float = 20000
    allowance_transport: float = 500000
    allowance_meal: float = 300000
    allowance_other: float = 200000
    deduction_bpjs: float = 200000
    deduction_pph: float = 150000
    deduction_other: float = 0
    loan_payment: float = 200000
    gross_salary: float = 0
    net_salary: float = 0


class DaftarUpahEngineReal:
    """Template engine with real database integration"""

    def __init__(self):
        self.template_dir = Path(__file__).parent
        self.output_dir = self.template_dir / "output"
        self.output_dir.mkdir(exist_ok=True)

        # Initialize database query manager
        query_file = "D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Engine_HTML_Templating/template_report/query/get_detail_emp_each_gang.sql"
        config_file = "D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json"
        self.query_manager = SimpleEmployeeQueryManager(query_file, config_file)

        self.stats = {
            'reports_generated': 0,
            'total_employees_processed': 0,
            'database_queries_executed': 0,
            'processing_times': []
        }

    def load_sample_payroll_data(self, sample_data_path: str) -> Dict[str, Any]:
        """Load sample payroll data for merging"""
        try:
            with open(sample_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"[OK] Sample payroll data loaded: {len(data.get('karyawan', []))} records")
            return data
        except Exception as e:
            print(f"[ERROR] Failed to load sample payroll data: {e}")
            return {}

    def merge_employee_with_payroll_data(self, employees: List, sample_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Merge real employee data with payroll data"""
        print(f"[MERGE] Merging {len(employees)} real employee records with payroll data...")

        if not sample_data:
            print("[WARN] No sample payroll data available, using default values")
            return self._create_default_payroll_data(employees)

        sample_employees = sample_data.get('karyawan', [])
        merged_employees = []

        for i, emp in enumerate(employees):
            # Use corresponding sample payroll data (cycle through if needed)
            sample_idx = i % len(sample_employees)
            sample_emp = sample_employees[sample_idx]

            merged_emp = {
                # Real employee data from database
                'nik': emp.nik,
                'nama': emp.nama,
                'jenis_kelamin': emp.jenis_kelamin,
                'loc_code': emp.LocCode,
                'gang_code': emp.GangCode,  # Added GangCode

                # Payroll data from sample
                'gaji_pokok': sample_emp.get('gaji_pokok', 4000000),
                'uang_lembur': sample_emp.get('uang_lembur', 0),
                'tunjangan_transport': sample_emp.get('tunjangan_transport', 500000),
                'tunjangan_makan': sample_emp.get('tunjangan_makan', 300000),
                'tunjangan_lain': sample_emp.get('tunjangan_lain', 200000),
                'potongan_bpjs': sample_emp.get('potongan_bpjs', 200000),
                'potongan_pph': sample_emp.get('potongan_pph', 150000),
                'potongan_lain': sample_emp.get('potongan_lain', 0),
                'potongan_pinjaman_uang': sample_emp.get('potongan_pinjaman_uang', 200000),
                'upah_bersih': sample_emp.get('upah_bersih', 3750000),
                'tidak_hadir_cth': sample_emp.get('tidak_hadir_cth', 0),
                'tidak_hadir_alpa': sample_emp.get('tidak_hadir_alpa', 0)
            }

            merged_employees.append(merged_emp)

        print(f"[OK] Successfully merged {len(merged_employees)} employee records")
        return merged_employees

    def _create_default_payroll_data(self, employees: List) -> List[Dict[str, Any]]:
        """Create default payroll data when sample data is not available"""
        merged_employees = []
        for emp in employees:
            payroll = PayrollData()
            merged_emp = {
                'nik': emp.nik,
                'nama': emp.nama,
                'jenis_kelamin': emp.jenis_kelamin,
                'loc_code': emp.LocCode,
                'gang_code': emp.GangCode,  # Add gang_code field
                'gaji_pokok': payroll.basic_salary,
                'uang_lembur': payroll.overtime_hours * payroll.overtime_rate,
                'tunjangan_transport': payroll.allowance_transport,
                'tunjangan_makan': payroll.allowance_meal,
                'tunjangan_lain': payroll.allowance_other,
                'potongan_bpjs': payroll.deduction_bpjs,
                'potongan_pph': payroll.deduction_pph,
                'potongan_lain': payroll.deduction_other,
                'potongan_pinjaman_uang': payroll.loan_payment,
                'upah_bersih': payroll.basic_salary + payroll.allowance_transport + payroll.allowance_meal - payroll.deduction_bpjs - payroll.deduction_pph,
                'tidak_hadir_cth': 0,
                'tidak_hadir_alpa': 0
            }
            merged_employees.append(merged_emp)

        return merged_employees

    def generate_report_from_real_database(self, gang_code: str = 'H1H', limit: int = 100,
                                         template_file: str = "daftar_upah_template_fixed.html",
                                         sample_data_file: str = "large_data.json",
                                         output_file: Optional[str] = None) -> Optional[Path]:
        """Generate report using real database query"""
        try:
            start_time = datetime.now()

            print("=" * 80)
            print("DAFTAR UPAH TEMPLATE ENGINE - REAL DATABASE INTEGRATION")
            print("=" * 80)

            print(f"[INFO] Gang Code: {gang_code}")
            print(f"[TEMPLATE] Template: {template_file}")
            print(f"[SAMPLE] Sample Data: {sample_data_file}")
            print(f"[QUERY] Query File: {self.query_manager.query_file_path}")
            print(f"[LIMIT] Max Employees: {limit}")

            print(f"\n[1] Getting real employee data for gang '{gang_code}'...")

            # Get real employee data from database
            start_processing = datetime.now()
            employees = self.query_manager.get_employees_by_gang(gang_code, limit)
            processing_time = (datetime.now() - start_processing).total_seconds()
            print(f"   Query time: {processing_time:.2f}s")

            if not employees:
                print(f"[ERROR] No employee data found for gang '{gang_code}'")
                return None

            print(f"\n[OK] Found {len(employees)} real employees from database")
            print(f"[DATA] Sample employees:")
            for i, emp in enumerate(employees[:3], 1):
                print(f"   {i}. {emp.nik} - {emp.nama} ({emp.jenis_kelamin}) - {emp.LocCode}")

            # Load sample payroll data
            print(f"\n[2] Loading sample payroll data...")
            sample_data = self.load_sample_payroll_data(sample_data_file)

            # Merge employee data with payroll
            print(f"\n[3] Merging data...")
            merged_employees = self.merge_employee_with_payroll_data(employees, sample_data)

            # Calculate totals
            total_gaji_pokok = sum(emp['gaji_pokok'] for emp in merged_employees)
            total_uang_lembur = sum(emp['uang_lembur'] for emp in merged_employees)
            total_tunjangan = sum(emp['tunjangan_transport'] + emp['tunjangan_makan'] + emp['tunjangan_lain'] for emp in merged_employees)
            total_potongan = sum(emp['potongan_bpjs'] + emp['potongan_pph'] + emp['potongan_lain'] + emp['potongan_pinjaman_uang'] for emp in merged_employees)
            total_upah_bersih = sum(emp['upah_bersih'] for emp in merged_employees)

            # Clean NIK function
            def clean_nik(nik):
                """Clean NIK by removing extra spaces and dots"""
                return nik.strip().replace('.', '').replace(' ', '')

            # Generate employee rows HTML with improved formatting
            employee_rows = ""
            for i, emp in enumerate(merged_employees, 1):
                # Clean the NIK
                clean_emp_nik = clean_nik(emp['nik'])

                # Generate employee row with proper styling
                employee_rows += f"""
                <tr class="employee-row">
                    <td class="number-cell col-no">{i}</td>
                    <td class="text-cell col-gender">{emp['jenis_kelamin']}</td>
                    <td class="nik-cell col-nik">{clean_emp_nik}</td>
                    <td class="text-cell col-name text-left">{emp['nama']}</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-hk">25</td>
                    <td class="number-cell col-cuti">0</td>
                    <td class="number-cell col-tunjangan">{emp['tunjangan_transport']:,.0f}</td>
                    <td class="number-cell col-tunjangan">0</td>
                    <td class="number-cell col-tunjangan">{emp['tunjangan_makan']:,.0f}</td>
                    <td class="number-cell col-tunjangan">0</td>
                    <td class="number-cell col-tunjangan">0</td>
                    <td class="number-cell col-tunjangan">0</td>
                    <td class="number-cell col-tunjangan">0</td>
                    <td class="number-cell col-tunjangan">0</td>
                    <td class="number-cell col-tunjangan">0</td>
                    <td class="number-cell col-tunjangan">0</td>
                    <td class="number-cell col-tunjangan">0</td>
                    <td class="number-cell col-tunjangan">0</td>
                    <td class="number-cell col-tunjangan">0</td>
                    <td class="number-cell col-tunjangan">{emp['gaji_pokok']:,.0f}</td>
                    <td class="number-cell col-potongan">0</td>
                    <td class="number-cell col-potongan">{emp['potongan_bpjs']:,.0f}</td>
                    <td class="number-cell col-potongan">0</td>
                    <td class="number-cell col-potongan">0</td>
                    <td class="number-cell col-potongan">0</td>
                    <td class="number-cell col-potongan">{emp['potongan_pph']:,.0f}</td>
                    <td class="number-cell col-potongan">0</td>
                    <td class="number-cell col-potongan">0</td>
                    <td class="number-cell col-potongan">{emp['potongan_pinjaman_uang']:,.0f}</td>
                    <td class="number-cell col-upah-bersih">{emp['upah_bersih']:,.0f}</td>
                    <td class="number-cell col-tidak-hadir">0</td>
                    <td class="number-cell col-tidak-hadir">0</td>
                </tr>"""

            # Get unique gang codes and locations for title
            unique_gangs = list(set(emp['gang_code'] for emp in merged_employees))
            unique_locs = list(set(emp['loc_code'] for emp in merged_employees))

            # Prepare comprehensive data for template
            report_data = {
                'bulan': 'Mei',
                'tahun': '2025',
                'gang_code': ', '.join(unique_gangs),
                'loc_code': ', '.join(unique_locs),
                'tanggal_cetak': datetime.now().strftime('%d-%m-%Y'),
                'employee_rows': employee_rows,
                'karyawan': merged_employees,
                'total_karyawan': len(merged_employees),
                'total': {
                    # Cut/Cuti totals
                    'cuti_tahun_hari': 0,
                    'cuti_tahun_jumlah': 0,
                    'cuti_sakit_hari': 0,
                    'cuti_sakit_jumlah': 0,
                    'cuti_haid_hari': 0,
                    'cuti_haid_jumlah': 0,
                    'cuti_minggu_hari': 0,
                    'cuti_minggu_jumlah': 0,
                    'cuti_nasional_hari': 0,
                    'cuti_nasional_jumlah': 0,
                    'cuti_hamil_hari': 0,
                    'cuti_hamil_jumlah': 0,
                    'cuti_izin_hari': 0,
                    'cuti_izin_jumlah': 0,

                    # Working days
                    'jumlah_hk': 25 * len(merged_employees),

                    # Allowances (Tunjangan)
                    'tunjangan_beras': 0,
                    'tunjangan_beras_jumlah': 0,
                    'tunjangan_jabatan': 0,
                    'tunjangan_jabatan_hk': 0,
                    'tunjangan_masa_kerja': 0,
                    'tunjangan_masa_kerja_jumlah': 0,
                    'tunjangan_lembur': total_uang_lembur,
                    'tunjangan_premi': 0,
                    'tunjangan_angkut_tbs': 0,
                    'tunjangan_angkut_pc_tbk': 0,
                    'tunjangan_premi_retase': 0,
                    'tunjangan_antar_jemput': 0,
                    'tunjangan_angkut_puru': 0,
                    'tunjangan_premi_kontan': 0,
                    'tunjangan_koreksi': 0,
                    'upah_kotor': total_gaji_pokok + total_tunjangan,

                    # Deductions (Potongan)
                    'potongan_astek_pekerja': 0,
                    'potongan_astek_majikan': 0,
                    'potongan_astek_jumlah': 0,
                    'potongan_bpjs_kesehatan': 0,
                    'potongan_bpjs_pekerja': sum(emp['potongan_bpjs'] for emp in merged_employees),
                    'potongan_bpjs_pensiun': 0,
                    'potongan_bpjs_majikan': 0,
                    'potongan_bpjs_jumlah': sum(emp['potongan_bpjs'] for emp in merged_employees),
                    'potongan_pph21': sum(emp['potongan_pph'] for emp in merged_employees),
                    'potongan_premi_kontan': 0,
                    'potongan_lebih_potong_pajak_thr': 0,
                    'potongan_pinjaman_uang': sum(emp['potongan_pinjaman_uang'] for emp in merged_employees),

                    # Final totals
                    'upah_bersih': total_upah_bersih,
                    'tidak_hadir_cth': 0,
                    'tidak_hadir_alpa': 0
                },
                'tanggal_cetak': datetime.now().strftime('%d-%m-%Y'),
                'data_source': 'Real Database Query + Sample Payroll'
            }

            # Load template
            print(f"\n[4] Loading HTML template...")
            template_path = self.template_dir / template_file
            if not template_path.exists():
                print(f"[ERROR] Template file not found: {template_path}")
                return None

            # Render template using custom placeholder replacement
            print(f"[5] Rendering template...")
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Replace placeholders safely (only replace specific placeholders)
            html_content = template_content

            # Header placeholders
            html_content = html_content.replace('{bulan}', report_data['bulan'])
            html_content = html_content.replace('{tahun}', report_data['tahun'])
            html_content = html_content.replace('{gang_code}', report_data['gang_code'])
            html_content = html_content.replace('{loc_code}', report_data['loc_code'])
            html_content = html_content.replace('{tanggal_cetak}', report_data['tanggal_cetak'])
            html_content = html_content.replace('{employee_rows}', report_data['employee_rows'])

            # Total placeholders
            total = report_data['total']
            for key, value in total.items():
                html_content = html_content.replace(f'{{total.{key}}}', str(value))

            # Generate output filename
            if output_file is None:
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                output_file = f"daftar_upah_gang_{gang_code}_real_{timestamp}.html"

            output_path = self.output_dir / output_file

            # Save output
            print(f"[6] Saving output...")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Calculate statistics
            total_time = (datetime.now() - start_time).total_seconds()
            file_size = output_path.stat().st_size

            # Update statistics
            self.stats['reports_generated'] += 1
            self.stats['total_employees_processed'] += len(merged_employees)
            self.stats['processing_times'].append(total_time)
            self.stats['database_queries_executed'] += 1

            print(f"\n" + "=" * 80)
            print("[OK] REPORT GENERATION COMPLETED!")
            print("=" * 80)
            print(f"[FILE] Output: {output_path}")
            print(f"[SIZE] File Size: {file_size:,} bytes")
            print(f"[EMPLOYEES] Real Employees: {len(merged_employees)}")
            print(f"[GANG] Gang: {gang_code}")
            print(f"[TIME] Total Time: {total_time:.2f}s")
            print(f"[DATA] Data Source: Real Database Query + Sample Payroll")
            print(f"[INFO] Gender Mapping: 1->L, 0->P")
            print(f"[TARGET] Query File: {self.query_manager.query_file_path}")

            print(f"\n[STATS] STATISTICS:")
            print(f"   Total Reports Generated: {self.stats['reports_generated']}")
            print(f"   Total Employees Processed: {self.stats['total_employees_processed']}")
            print(f"   Database Queries Executed: {self.stats['database_queries_executed']}")
            print(f"   Average Processing Time: {sum(self.stats['processing_times'])/len(self.stats['processing_times']):.2f}s")

            return output_path

        except Exception as e:
            print(f"\n[ERROR] Report generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            # Always cleanup database connection
            self.query_manager.cleanup()

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'stats': self.stats,
            'last_processed': datetime.now().isoformat()
        }


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Daftar Upah Template Engine with Real Database')
    parser.add_argument('--gang', default='H1H', help='Gang code (default: H1H)')
    parser.add_argument('--limit', type=int, default=100, help='Maximum employees (default: 100)')
    parser.add_argument('--template', default='daftar_upah_template_improved.html', help='Template file')
    parser.add_argument('--sample-data', default='large_data.json', help='Sample data file')
    parser.add_argument('--output', help='Output file name')

    args = parser.parse_args()

    try:
        # Initialize engine
        engine = DaftarUpahEngineReal()

        # Generate report
        result = engine.generate_report_from_real_database(
            gang_code=args.gang,
            limit=args.limit,
            template_file=args.template,
            sample_data_file=args.sample_data,
            output_file=args.output
        )

        if result:
            print(f"\n[SUCCESS] Report saved to: {result}")
        else:
            print("\n[ERROR] Failed to generate report")

        # Show statistics
        stats = engine.get_statistics()
        print(f"\n[STATS] Final Statistics:")
        print(f"   Reports Generated: {stats['stats']['reports_generated']}")
        print(f"   Employees Processed: {stats['stats']['total_employees_processed']}")
        print(f"   Database Queries: {stats['stats']['database_queries_executed']}")

    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Operation cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()