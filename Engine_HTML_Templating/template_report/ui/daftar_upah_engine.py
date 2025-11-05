#!/usr/bin/env python3
"""
Daftar Upah HTML Template Engine
Compatible with the reference HTML structure and large_data.json format
"""

import json
import os
import sys
from pathlib import Path

class DaftarUpahTemplateEngine:
    """
    HTML Template Engine for Daftar Upah (Payroll Reports)

    Features:
    - Compatible with reference HTML structure from Excel export
    - Handles large datasets efficiently
    - Supports complex payroll calculations and formatting
    - Generates print-ready HTML reports
    """

    def __init__(self, template_dir=None):
        if template_dir is None:
            self.template_dir = Path(__file__).parent
        else:
            self.template_dir = Path(template_dir)

        self.output_dir = self.template_dir / "output"
        self.output_dir.mkdir(exist_ok=True)

    def format_rupiah(self, amount):
        """Format number to Rupiah currency format with proper thousand separators"""
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

    def load_data(self, data_file):
        """Load JSON data file with flexible path handling"""
        # Handle different path formats
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
            raise FileNotFoundError(f"Data file not found: {data_path}")

        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def render_employee_row(self, index, employee):
        """Render a single employee row with all payroll details"""
        # Helper function to safely get values
        def get_value(key, default=0):
            return employee.get(key, default) if employee.get(key, default) is not None else default

        row = f"""
        <tr>
            <td class="text-center">{index}</td>
            <td class="text-center">{get_value('jenis_kelamin', '')}</td>
            <td class="text-center">{get_value('nik', '')}</td>
            <td class="text-left">{get_value('nama', '')}</td>

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

            <!-- Cuti Hamil/Melahirkan -->
            <td class="text-center">{get_value('cuti_hamil_hari')}</td>
            <td class="number-cell">{self.format_rupiah(get_value('cuti_hamil_jumlah'))}</td>

            <!-- Cuti Izin -->
            <td class="text-center">{get_value('cuti_izin_hari')}</td>
            <td class="number-cell">{self.format_rupiah(get_value('cuti_izin_jumlah'))}</td>

            <!-- Jumlah HK -->
            <td class="text-center">{get_value('jumlah_hk')}</td>

            <!-- Tunjangan Beras -->
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_beras'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_beras_jumlah'))}</td>

            <!-- Tunjangan Jabatan -->
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_jabatan'))}</td>
            <td class="text-center">{get_value('tunjangan_jabatan_hk')}</td>

            <!-- Tunjangan Masa Kerja -->
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_masa_kerja'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_masa_kerja_jumlah'))}</td>

            <!-- Lembur -->
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_lembur'))}</td>

            <!-- Premium Columns -->
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_premi'))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_angkut_tbs', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_angkut_pc_tbk', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_premi_retase', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_antar_jemput', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_angkut_puru', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_angkut_bibit', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_jaga_genset', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_premi_kontan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(get_value('tunjangan_koreksi', 0))}</td>

            <!-- Upah Kotor -->
            <td class="number-cell">{self.format_rupiah(get_value('upah_kotor'))}</td>

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

            <!-- Upah Bersih -->
            <td class="number-cell">{self.format_rupiah(get_value('upah_bersih'))}</td>

            <!-- Tidak Hadir -->
            <td class="text-center">{get_value('tidak_hadir_cth')}</td>
            <td class="text-center">{get_value('tidak_hadir_alpa')}</td>
        </tr>
        """
        return row

    def calculate_totals(self, data):
        """Calculate totals for all payroll columns"""
        employees = data.get('karyawan', [])

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
            'tunjangan_angkut_bibit': safe_sum('tunjangan_angkut_bibit'),
            'tunjangan_jaga_genset': safe_sum('tunjangan_jaga_genset'),
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

        print(f"Processing {len(employees)} employee records...")

        for index, employee in enumerate(employees, start=1):
            row = self.render_employee_row(index, employee)
            employee_rows += row

        # Replace the {employee_rows} placeholder
        template = template.replace('{employee_rows}', employee_rows)

        # Calculate and process totals
        print("Calculating totals...")
        totals = self.calculate_totals(data)

        # Replace total variables with formatted values
        for key, value in totals.items():
            template = template.replace(f'{{total.{key}}}', self.format_rupiah(value))

        return template

    def generate_report(self, template_file="daftar_upah_template.html",
                       data_file="../large_data.json",
                       output_file=None):
        """Generate complete HTML payroll report"""
        try:
            print("Loading template...")
            template_content = self.load_template(template_file)

            print("Loading data...")
            data = self.load_data(data_file)

            employee_count = len(data.get('karyawan', []))
            print(f"Loaded {employee_count} employee records")

            if employee_count == 0:
                print("Warning: No employee records found in data file")
                return None

            print("Rendering template...")
            rendered_content = self.render_template(template_content, data)

            # Generate output filename if not provided
            if output_file is None:
                period = f"{data.get('bulan', 'unknown')}-{data.get('tahun', 'unknown')}"
                output_file = f"daftar_upah_report_{period.lower()}.html"

            print("Saving output...")
            output_path = self.output_dir / output_file

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)

            file_size = output_path.stat().st_size
            print(f"Report generated successfully!")
            print(f"Output: {output_path}")
            print(f"Size: {file_size:,} bytes")
            print(f"Employees: {employee_count}")

            return output_path

        except Exception as e:
            print(f"Error generating report: {e}")
            return None

def main():
    """Main function for command line usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate Daftar Upah HTML Report')
    parser.add_argument('--template', '-t', default='daftar_upah_template.html',
                        help='Template file name (default: daftar_upah_template.html)')
    parser.add_argument('--data', '-d', default='../large_data.json',
                        help='Data file name (default: ../large_data.json)')
    parser.add_argument('--output', '-o', help='Output file name (auto-generated if not specified)')

    args = parser.parse_args()

    engine = DaftarUpahTemplateEngine()
    result = engine.generate_report(
        template_file=args.template,
        data_file=args.data,
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