#!/usr/bin/env python3
"""
Daftar Upah HTML Template Engine with Database Integration
Fetches employee data from SQL Server and generates payroll reports
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from database_integration import DatabaseIntegration

class DaftarUpahTemplateEngineDB:
    """
    HTML Template Engine for Daftar Upah with Database Integration

    Features:
    - Fetches employee data from SQL Server database
    - Maps database fields to template format
    - Generates professional HTML payroll reports
    - Supports gang-based employee filtering
    """

    def __init__(self, template_dir=None):
        if template_dir is None:
            self.template_dir = Path(__file__).parent
        else:
            self.template_dir = Path(template_dir)

        self.output_dir = self.template_dir / "output"
        self.output_dir.mkdir(exist_ok=True)
        self.db_integration = DatabaseIntegration()

    def format_rupiah(self, amount):
        """Format number to Rupiah currency format with proper formatting"""
        try:
            if amount == 0 or amount is None:
                return "0"
            # Shorten large numbers for better display
            amt = float(amount)
            if amt >= 1000000:
                return f"{amt/1000000:.1f}jt"
            elif amt >= 1000:
                return f"{amt/1000:.0f}rb"
            return f"{amt:,.0f}".replace(",", ".")
        except (ValueError, TypeError):
            return "0"

    def format_rupiah_full(self, amount):
        """Format number to full Rupiah currency format"""
        try:
            if amount == 0 or amount is None:
                return "0"
            return f"{float(amount):,.0f}".replace(",", ".")
        except (ValueError, TypeError):
            return "0"

    def load_template(self, template_file):
        """Load HTML template file"""
        template_path = self.template_dir / template_file
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_sample_data(self, data_file):
        """Load sample JSON data file for non-database fields"""
        if isinstance(data_file, str):
            if data_file.startswith("../"):
                data_path = self.template_dir.parent.parent / data_file[3:]
            elif os.path.isabs(data_file):
                data_path = Path(data_file)
            else:
                data_path = self.template_dir / data_file
        else:
            data_path = Path(data_file)

        if not data_path.exists():
            raise FileNotFoundError(f"Sample data file not found: {data_path}")

        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def merge_employee_data(self, db_employees: List[Dict], sample_data: Dict) -> List[Dict]:
        """
        Merge database employee info with sample payroll data

        Args:
            db_employees: Employee data from database (nik, nama, jenis_kelamin)
            sample_data: Sample payroll data with financial information

        Returns:
            Merged employee list with complete information
        """
        sample_employees = sample_data.get('karyawan', [])
        merged_employees = []

        print(f"Merging {len(db_employees)} database employees with {len(sample_employees)} sample records")

        # Map sample employees by name for matching
        sample_map = {}
        for emp in sample_employees:
            name_key = emp.get('nama', '').strip().upper()
            if name_key:
                sample_map[name_key] = emp

        # Merge data
        for db_emp in db_employees:
            emp_name = db_emp.get('nama', '').strip().upper()

            # Try to find matching sample data
            sample_emp = sample_map.get(emp_name, {})

            # Create merged employee record
            merged_emp = {
                # Database fields
                'nik': db_emp.get('nik', ''),
                'nama': db_emp.get('nama', ''),
                'jenis_kelamin': db_emp.get('jenis_kelamin', 'L'),
                'loc_code': db_emp.get('loc_code', ''),

                # Sample payroll fields (use sample data if available, otherwise defaults)
                'cuti_tahun_hari': sample_emp.get('cuti_tahun_hari', 0),
                'cuti_tahun_jumlah': sample_emp.get('cuti_tahun_jumlah', 0),
                'cuti_sakit_hari': sample_emp.get('cuti_sakit_hari', 0),
                'cuti_sakit_jumlah': sample_emp.get('cuti_sakit_jumlah', 0),
                'cuti_haid_hari': sample_emp.get('cuti_haid_hari', 0),
                'cuti_haid_jumlah': sample_emp.get('cuti_haid_jumlah', 0),
                'cuti_minggu_hari': sample_emp.get('cuti_minggu_hari', 0),
                'cuti_minggu_jumlah': sample_emp.get('cuti_minggu_jumlah', 0),
                'cuti_nasional_hari': sample_emp.get('cuti_nasional_hari', 0),
                'cuti_nasional_jumlah': sample_emp.get('cuti_nasional_jumlah', 0),
                'cuti_hamil_hari': sample_emp.get('cuti_hamil_hari', 0),
                'cuti_hamil_jumlah': sample_emp.get('cuti_hamil_jumlah', 0),
                'cuti_izin_hari': sample_emp.get('cuti_izin_hari', 0),
                'cuti_izin_jumlah': sample_emp.get('cuti_izin_jumlah', 0),
                'jumlah_hk': sample_emp.get('jumlah_hk', 22),
                'tunjangan_beras': sample_emp.get('tunjangan_beras', 15000),
                'tunjangan_beras_jumlah': sample_emp.get('tunjangan_beras_jumlah', 330000),
                'tunjangan_jabatan': sample_emp.get('tunjangan_jabatan', 5000),
                'tunjangan_jabatan_hk': sample_emp.get('tunjangan_jabatan_hk', 22),
                'tunjangan_masa_kerja': sample_emp.get('tunjangan_masa_kerja', 2000),
                'tunjangan_masa_kerja_jumlah': sample_emp.get('tunjangan_masa_kerja_jumlah', 44000),
                'tunjangan_lembur': sample_emp.get('tunjangan_lembur', 250000),
                'tunjangan_premi': sample_emp.get('tunjangan_premi', 150000),
                'tunjangan_koreksi': sample_emp.get('tunjangan_koreksi', 0),
                'upah_kotor': sample_emp.get('upah_kotor', 4840000),
                'potongan_astek_pekerja': sample_emp.get('potongan_astek_pekerja', 200000),
                'potongan_astek_majikan': sample_emp.get('potongan_astek_majikan', 300000),
                'potongan_astek_jumlah': sample_emp.get('potongan_astek_jumlah', 500000),
                'potongan_bpjs_kesehatan': sample_emp.get('potongan_bpjs_kesehatan', 100000),
                'potongan_bpjs_pekerja': sample_emp.get('potongan_bpjs_pekerja', 50000),
                'potongan_bpjs_pensiun': sample_emp.get('potongan_bpjs_pensiun', 75000),
                'potongan_bpjs_majikan': sample_emp.get('potongan_bpjs_majikan', 75000),
                'potongan_bpjs_jumlah': sample_emp.get('potongan_bpjs_jumlah', 225000),
                'potongan_pph21': sample_emp.get('potongan_pph21', 150000),
                'potongan_premi_kontan': sample_emp.get('potongan_premi_kontan', 0),
                'potongan_lebih_potong_pajak_thr': sample_emp.get('potongan_lebih_potong_pajak_thr', 0),
                'potongan_pinjaman_uang': sample_emp.get('potongan_pinjaman_uang', 200000),
                'upah_bersih': sample_emp.get('upah_bersih', 3750000),
                'tidak_hadir_cth': sample_emp.get('tidak_hadir_cth', 0),
                'tidak_hadir_alpa': sample_emp.get('tidak_hadir_alpa', 0)
            }

            merged_employees.append(merged_emp)

        print(f"✓ Successfully merged {len(merged_employees)} employee records")
        return merged_employees

    def render_employee_row(self, index, employee):
        """Render a single employee row with database information"""
        def get_value(key, default=0):
            return employee.get(key, default) if employee.get(key, default) is not None else default

        row = f"""
        <tr>
            <td class="text-center">{index}</td>
            <td class="text-center">{get_value('jenis_kelamin', '')}</td>
            <td class="text-center">{get_value('nik', '')}</td>
            <td class="text-left" style="font-size:6pt;">{get_value('nama', '')}</td>

            <!-- Cuti Tahun -->
            <td class="text-center">{get_value('cuti_tahun_hari')}</td>
            <td class="number-cell">{self.format_rupiah(get_value('cuti_tahun_jumlah'))}</td>

            <!-- Cuti Sakit -->
            <td class="text-center">{get_value('cuti_sakit_hari')}</td>
            <td class="number-cell">{self.format_rupiah(get_value('cuti_sakit_jumlah'))}</td>

            <!-- Cuti Haid -->
            <td class="text-center">{get_value('cuti_haid_hari')}</td>
            <td class="number-cell">{self.format_rupiah(get_value('cuti_haid_jumlah'))}</td>

            <!-- Cuti Minggu -->
            <td class="text-center">{get_value('cuti_minggu_hari')}</td>
            <td class="number-cell">{self.format_rupiah(get_value('cuti_minggu_jumlah'))}</td>

            <!-- Cuti Nasional -->
            <td class="text-center">{get_value('cuti_nasional_hari')}</td>
            <td class="number-cell">{self.format_rupiah(get_value('cuti_nasional_jumlah'))}</td>

            <!-- Cuti Hamil -->
            <td class="text-center">{get_value('cuti_hamil_hari')}</td>
            <td class="number-cell">{self.format_rupiah(get_value('cuti_hamil_jumlah'))}</td>

            <!-- Cuti Izin -->
            <td class="text-center">{get_value('cuti_izin_hari')}</td>
            <td class="number-cell">{self.format_rupiah(get_value('cuti_izin_jumlah'))}</td>

            <!-- Jumlah HK -->
            <td class="text-center">{get_value('jumlah_hk')}</td>

            <!-- Tunjangan Beras -->
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_beras'))}</td>
            <td class="text-center">{get_value('tunjangan_jabatan_hk', 0)}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_beras_jumlah'))}</td>

            <!-- Tunjangan Jabatan -->
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_jabatan'))}</td>
            <td class="text-center">{get_value('tunjangan_masa_kerja', 0)}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_masa_kerja_jumlah'))}</td>

            <!-- Tunjangan Masa Kerja -->
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_masa_kerja'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_lembur'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_premi'))}</td>

            <!-- Premium Lainnya -->
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_angkut_tbs', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_angkut_pc_tbk', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_premi_retase', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_antar_jemput', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_angkut_puru', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_premi_kontan', 0))}</td>

            <!-- Koreksi dan Upah Kotor -->
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_koreksi', 0))}</td>
            <td class="number-cell">{self.format_rupiah_full(get_value('upah_kotor'))}</td>

            <!-- Potongan ASTEK -->
            <td class="number-cell">{self.format_rupiah(get_value('potongan_astek_pekerja'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('potongan_astek_majikan'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('potongan_astek_jumlah'))}</td>

            <!-- Potongan BPJS -->
            <td class="number-cell">{self.format_rupiah(get_value('potongan_bpjs_kesehatan'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('potongan_bpjs_pekerja'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('potongan_bpjs_pensiun'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('potongan_bpjs_majikan'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('potongan_bpjs_jumlah'))}</td>

            <!-- Potongan Lainnya -->
            <td class="number-cell">{self.format_rupiah(get_value('potongan_pph21'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('potongan_premi_kontan'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('potongan_lebih_potong_pajak_thr'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('potongan_pinjaman_uang'))}</td>
            <td class="number-cell">{self.format_rupiah_full(get_value('upah_kotor'))}</td>

            <!-- Upah Bersih -->
            <td class="number-cell">{self.format_rupiah_full(get_value('upah_bersih'))}</td>

            <!-- Tidak Hadir -->
            <td class="text-center">{get_value('tidak_hadir_cth')}</td>
            <td class="text-center">{get_value('tidak_hadir_alpa')}</td>
        </tr>
        """
        return row

    def calculate_totals(self, employees):
        """Calculate totals for all payroll columns"""
        if not employees:
            return {}

        def safe_sum(field):
            """Safely sum a field across all employees"""
            return sum(float(emp.get(field, 0) or 0) for emp in employees)

        totals = {
            'cuti_tahun_hari': safe_sum('cuti_tahun_hari'),
            'cuti_tahun_jumlah': safe_sum('cuti_tahun_jumlah'),
            'cuti_sakit_hari': safe_sum('cuti_sakit_hari'),
            'cuti_sakit_jumlah': safe_sum('cuti_sakit_jumlah'),
            'cuti_haid_hari': safe_sum('cuti_haid_hari'),
            'cuti_haid_jumlah': safe_sum('cuti_haid_jumlah'),
            'cuti_minggu_hari': safe_sum('cuti_minggu_hari'),
            'cuti_minggu_jumlah': safe_sum('cuti_minggu_jumlah'),
            'cuti_nasional_hari': safe_sum('cuti_nasional_hari'),
            'cuti_nasional_jumlah': safe_sum('cuti_nasional_jumlah'),
            'cuti_hamil_hari': safe_sum('cuti_hamil_hari'),
            'cuti_hamil_jumlah': safe_sum('cuti_hamil_jumlah'),
            'cuti_izin_hari': safe_sum('cuti_izin_hari'),
            'cuti_izin_jumlah': safe_sum('cuti_izin_jumlah'),
            'jumlah_hk': safe_sum('jumlah_hk'),
            'tunjangan_beras': safe_sum('tunjangan_beras'),
            'tunjangan_beras_jumlah': safe_sum('tunjangan_beras_jumlah'),
            'tunjangan_jabatan': safe_sum('tunjangan_jabatan'),
            'tunjangan_jabatan_hk': safe_sum('tunjangan_jabatan_hk'),
            'tunjangan_masa_kerja': safe_sum('tunjangan_masa_kerja'),
            'tunjangan_masa_kerja_jumlah': safe_sum('tunjangan_masa_kerja_jumlah'),
            'tunjangan_lembur': safe_sum('tunjangan_lembur'),
            'tunjangan_premi': safe_sum('tunjangan_premi'),
            'tunjangan_angkut_tbs': safe_sum('tunjangan_angkut_tbs'),
            'tunjangan_angkut_pc_tbk': safe_sum('tunjangan_angkut_pc_tbk'),
            'tunjangan_premi_retase': safe_sum('tunjangan_premi_retase'),
            'tunjangan_antar_jemput': safe_sum('tunjangan_antar_jemput'),
            'tunjangan_angkut_puru': safe_sum('tunjangan_angkut_puru'),
            'tunjangan_premi_kontan': safe_sum('tunjangan_premi_kontan'),
            'tunjangan_koreksi': safe_sum('tunjangan_koreksi'),
            'upah_kotor': safe_sum('upah_kotor'),
            'potongan_astek_pekerja': safe_sum('potongan_astek_pekerja'),
            'potongan_astek_majikan': safe_sum('potongan_astek_majikan'),
            'potongan_astek_jumlah': safe_sum('potongan_astek_jumlah'),
            'potongan_bpjs_kesehatan': safe_sum('potongan_bpjs_kesehatan'),
            'potongan_bpjs_pekerja': safe_sum('potongan_bpjs_pekerja'),
            'potongan_bpjs_pensiun': safe_sum('potongan_bpjs_pensiun'),
            'potongan_bpjs_majikan': safe_sum('potongan_bpjs_majikan'),
            'potongan_bpjs_jumlah': safe_sum('potongan_bpjs_jumlah'),
            'potongan_pph21': safe_sum('potongan_pph21'),
            'potongan_premi_kontan': safe_sum('potongan_premi_kontan'),
            'potongan_lebih_potong_pajak_thr': safe_sum('potongan_lebih_potong_pajak_thr'),
            'potongan_pinjaman_uang': safe_sum('potongan_pinjaman_uang'),
            'upah_bersih': safe_sum('upah_bersih'),
            'tidak_hadir_cth': safe_sum('tidak_hadir_cth'),
            'tidak_hadir_alpa': safe_sum('tidak_hadir_alpa'),
        }

        return totals

    def render_template(self, template_content, data):
        """Render HTML template with payroll data"""
        template = template_content

        # Replace simple header variables
        template = template.replace('{bulan}', data.get('bulan', ''))
        template = template.replace('{tahun}', data.get('tahun', ''))
        template = template.replace('{catatan}', data.get('catatan', ''))
        template = template.replace('{upah_dasar}', data.get('upah_dasar', ''))

        # Process employee data rows
        employee_rows = ""
        employees = data.get('karyawan', [])

        print(f"Rendering {len(employees)} employee records...")

        for index, employee in enumerate(employees, start=1):
            row = self.render_employee_row(index, employee)
            employee_rows += row

        # Replace the {employee_rows} placeholder
        template = template.replace('{employee_rows}', employee_rows)

        # Calculate and process totals
        print("Calculating totals...")
        totals = self.calculate_totals(employees)

        # Replace total variables with formatted values
        for key, value in totals.items():
            template = template.replace(f'{{total.{key}}}', self.format_rupiah_full(value))

        return template

    def generate_report_from_database(self, gang_code: str = 'H1H', limit: int = 100,
                                     template_file: str = "daftar_upah_template_fixed.html",
                                     sample_data_file: str = "../large_data.json",
                                     output_file: Optional[str] = None) -> Optional[Path]:
        """
        Generate report using database employee data

        Args:
            gang_code: Gang code to filter employees
            limit: Maximum number of employees to fetch
            template_file: HTML template file name
            sample_data_file: Sample data file for payroll fields
            output_file: Output file name (auto-generated if not specified)

        Returns:
            Path to generated report file or None if failed
        """
        try:
            print("Connecting to database...")
            if not self.db_integration.connect():
                print("Failed to connect to database")
                return None

            print(f"Fetching employee data for gang '{gang_code}'...")
            db_employees = self.db_integration.get_employee_data_by_gang(gang_code, limit)

            if not db_employees:
                print("No employees found for specified gang")
                self.db_integration.disconnect()
                return None

            print("Loading sample payroll data...")
            sample_data = self.load_sample_data(sample_data_file)

            print("Merging database employee info with payroll data...")
            merged_employees = self.merge_employee_data(db_employees, sample_data)

            # Prepare data for template
            report_data = {
                'bulan': sample_data.get('bulan', 'MEI'),
                'tahun': sample_data.get('tahun', '2025'),
                'catatan': f"Daftar upah karyawan periode {sample_data.get('bulan', 'MEI')} {sample_data.get('tahun', '2025')} - Gang {gang_code}",
                'upah_dasar': sample_data.get('upah_dasar', 'Upah Minimum Kabupaten (UMK) 2025'),
                'karyawan': merged_employees
            }

            print("Loading template...")
            template_content = self.load_template(template_file)

            print("Rendering template...")
            rendered_content = self.render_template(template_content, report_data)

            # Generate output filename
            if output_file is None:
                period = f"{report_data.get('bulan', 'unknown')}-{report_data.get('tahun', 'unknown')}"
                output_file = f"daftar_upah_gang_{gang_code}_{period.lower()}.html"

            print("Saving output...")
            output_path = self.output_dir / output_file

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)

            file_size = output_path.stat().st_size
            print(f"\n[SUCCESS] Report generated!")
            print(f"Output: {output_path}")
            print(f"Size: {file_size:,} bytes")
            print(f"Employees: {len(merged_employees)}")
            print(f"Gang: {gang_code}")
            print(f"Source: Database + Sample Data")

            self.db_integration.disconnect()
            return output_path

        except Exception as e:
            print(f"Error generating report: {e}")
            import traceback
            traceback.print_exc()
            if self.db_integration.connection:
                self.db_integration.disconnect()
            return None

def main():
    """Main function for command line usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate Daftar Upah HTML Report from Database')
    parser.add_argument('--gang', '-g', default='H1H', help='Gang code (default: H1H)')
    parser.add_argument('--limit', '-l', type=int, default=100, help='Maximum employees (default: 100)')
    parser.add_argument('--template', '-t', default='daftar_upah_template_fixed.html',
                        help='Template file name')
    parser.add_argument('--sample-data', '-s', default='../large_data.json',
                        help='Sample data file for payroll fields')
    parser.add_argument('--output', '-o', help='Output file name')

    args = parser.parse_args()

    engine = DaftarUpahTemplateEngineDB()
    result = engine.generate_report_from_database(
        gang_code=args.gang,
        limit=args.limit,
        template_file=args.template,
        sample_data_file=args.sample_data,
        output_file=args.output
    )

    if result:
        print(f"\n[SUCCESS] Report saved to: {result}")
        sys.exit(0)
    else:
        print("\n[ERROR] Failed to generate report")
        sys.exit(1)

if __name__ == "__main__":
    main()