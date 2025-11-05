import json
import os
from pathlib import Path

class SimpleTemplateEngine:
    def __init__(self):
        self.template_dir = Path(__file__).parent
        self.output_dir = self.template_dir / "output"
        self.output_dir.mkdir(exist_ok=True)

    def format_rupiah(self, amount):
        """Format number to Rupiah currency format"""
        if amount == 0:
            return "0"
        return f"{amount:,.0f}".replace(",", ".")

    def load_template(self, template_file):
        """Load HTML template file"""
        template_path = self.template_dir / template_file
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_data(self, data_file):
        """Load JSON data file"""
        data_path = self.template_dir / data_file
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def render_employee_row(self, index, employee):
        """Render a single employee row"""
        row = f"""
        <tr>
            <td>{index}</td>
            <td>{employee.get('jenis_kelamin', '')}</td>
            <td>{employee.get('nik', '')}</td>
            <td class="text-cell">{employee.get('nama', '')}</td>

            <!-- Cuti/Libur Section -->
            <td>{employee.get('cuti_sakit_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_sakit_jumlah', 0))}</td>
            <td>{employee.get('cuti_haid_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_haid_jumlah', 0))}</td>
            <td>{employee.get('cuti_minggu_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_minggu_jumlah', 0))}</td>
            <td>{employee.get('cuti_nasional_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_nasional_jumlah', 0))}</td>
            <td>{employee.get('cuti_hamil_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_hamil_jumlah', 0))}</td>
            <td>{employee.get('cuti_izin_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_izin_jumlah', 0))}</td>

            <!-- Work Days -->
            <td>{employee.get('jumlah_hk', 0)}</td>

            <!-- Tunjangan/Premi Section -->
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_beras', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_beras_jumlah', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_jabatan', 0))}</td>
            <td>{employee.get('tunjangan_jabatan_hk', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_masa_kerja', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_masa_kerja_jumlah', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_lembur', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_premi', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('upah_kotor', 0))}</td>

            <!-- Potongan Section -->
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_astek_pekerja', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_astek_majikan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_astek_jumlah', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_bpjs_kesehatan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_bpjs_pekerja', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_bpjs_pensiun', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_bpjs_majikan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_bpjs_jumlah', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_spsi', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_pph21', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_premi_kontan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_lebih_potong', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_pinjaman', 0))}</td>

            <!-- Net Salary -->
            <td class="number-cell">{self.format_rupiah(employee.get('upah_bersih', 0))}</td>

            <!-- Absence -->
            <td>{employee.get('tidak_hadir_cth', 0)}</td>
            <td>{employee.get('tidak_hadir_alpa', 0)}</td>
        </tr>
        """
        return row

    def calculate_totals(self, karyawan_list):
        """Calculate totals from karyawan list"""
        totals = {
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
            'jumlah_hk': 0,
            'tunjangan_beras': 0,
            'tunjangan_beras_jumlah': 0,
            'tunjangan_jabatan': 0,
            'tunjangan_jabatan_hk': 0,
            'tunjangan_masa_kerja': 0,
            'tunjangan_masa_kerja_jumlah': 0,
            'tunjangan_lembur': 0,
            'tunjangan_premi': 0,
            'upah_kotor': 0,
            'potongan_astek_pekerja': 0,
            'potongan_astek_majikan': 0,
            'potongan_astek_jumlah': 0,
            'potongan_bpjs_kesehatan': 0,
            'potongan_bpjs_pekerja': 0,
            'potongan_bpjs_pensiun': 0,
            'potongan_bpjs_majikan': 0,
            'potongan_bpjs_jumlah': 0,
            'potongan_spsi': 0,
            'potongan_pph21': 0,
            'potongan_premi_kontan': 0,
            'potongan_lebih_potong': 0,
            'potongan_pinjaman': 0,
            'upah_bersih': 0,
            'tidak_hadir_cth': 0,
            'tidak_hadir_alpa': 0
        }

        for emp in karyawan_list:
            for key in totals:
                if key in emp:
                    totals[key] += emp.get(key, 0)

        return totals

    def render_template(self, template_content, data):
        """Simple template rendering using string replacement"""
        template = template_content

        # Replace simple variables
        template = template.replace('{bulan}', data.get('bulan', ''))
        template = template.replace('{tahun}', data.get('tahun', ''))
        template = template.replace('{catatan}', data.get('catatan', ''))
        template = template.replace('{upah_dasar}', data.get('upah_dasar', ''))

        # Process employee data rows
        employee_rows = ""
        for index, employee in enumerate(data.get('karyawan', []), start=1):
            row = self.render_employee_row(index, employee)
            employee_rows += row

        # Calculate totals
        totals = self.calculate_totals(data.get('karyawan', []))

        # Add total row
        total_row = f"""
        <tr class="total-row">
            <td colspan="4" class="text-left">TOTAL</td>
            <td>{totals['cuti_sakit_hari']}</td>
            <td class="number-cell">{self.format_rupiah(totals['cuti_sakit_jumlah'])}</td>
            <td>{totals['cuti_haid_hari']}</td>
            <td class="number-cell">{self.format_rupiah(totals['cuti_haid_jumlah'])}</td>
            <td>{totals['cuti_minggu_hari']}</td>
            <td class="number-cell">{self.format_rupiah(totals['cuti_minggu_jumlah'])}</td>
            <td>{totals['cuti_nasional_hari']}</td>
            <td class="number-cell">{self.format_rupiah(totals['cuti_nasional_jumlah'])}</td>
            <td>{totals['cuti_hamil_hari']}</td>
            <td class="number-cell">{self.format_rupiah(totals['cuti_hamil_jumlah'])}</td>
            <td>{totals['cuti_izin_hari']}</td>
            <td class="number-cell">{self.format_rupiah(totals['cuti_izin_jumlah'])}</td>
            <td>{totals['jumlah_hk']}</td>
            <td class="number-cell">{self.format_rupiah(totals['tunjangan_beras'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['tunjangan_beras_jumlah'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['tunjangan_jabatan'])}</td>
            <td>{totals['tunjangan_jabatan_hk']}</td>
            <td class="number-cell">{self.format_rupiah(totals['tunjangan_masa_kerja'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['tunjangan_masa_kerja_jumlah'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['tunjangan_lembur'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['tunjangan_premi'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['upah_kotor'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_astek_pekerja'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_astek_majikan'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_astek_jumlah'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_bpjs_kesehatan'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_bpjs_pekerja'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_bpjs_pensiun'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_bpjs_majikan'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_bpjs_jumlah'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_spsi'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_pph21'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_premi_kontan'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_lebih_potong'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['potongan_pinjaman'])}</td>
            <td class="number-cell">{self.format_rupiah(totals['upah_bersih'])}</td>
            <td>{totals['tidak_hadir_cth']}</td>
            <td>{totals['tidak_hadir_alpa']}</td>
        </tr>
        """

        # Replace the {employee_rows} placeholder
        template = template.replace('{employee_rows}', employee_rows + total_row)

        return template

    def generate_report(self, template_file="template_simple.html",
                       data_file="simple_data.json",
                       output_file="daftar_upah_report.html"):
        """Generate complete HTML report"""
        print("Loading template...")
        template_content = self.load_template(template_file)

        print("Loading data...")
        data = self.load_data(data_file)

        print("Rendering template...")
        rendered_content = self.render_template(template_content, data)

        print("Saving output...")
        output_path = self.output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_content)

        print(f"Report generated successfully: {output_path}")
        return output_path

def main():
    engine = SimpleTemplateEngine()
    engine.generate_report()

if __name__ == "__main__":
    main()