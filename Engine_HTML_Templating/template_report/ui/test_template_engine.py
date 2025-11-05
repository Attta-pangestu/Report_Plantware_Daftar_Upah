import json
import os
from pathlib import Path

class DaftarUpahTemplateEngine:
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
        # Handle relative path
        if data_file.startswith("../"):
            data_path = self.template_dir.parent.parent / data_file[3:]
        else:
            data_path = self.template_dir / data_file

        print(f"Loading data from: {data_path}")
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def render_employee_row(self, index, employee):
        """Render a single employee row compatible with the new template structure"""
        row = f"""
        <tr>
            <td class="text-center">{index}</td>
            <td class="text-center">{employee.get('jenis_kelamin', '')}</td>
            <td class="text-center">{employee.get('nik', '')}</td>
            <td class="text-left">{employee.get('nama', '')}</td>

            <!-- Cuti Tahun -->
            <td class="text-center">{employee.get('cuti_tahun_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_tahun_jumlah', 0))}</td>

            <!-- Cuti Sakit -->
            <td class="text-center">{employee.get('cuti_sakit_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_sakit_jumlah', 0))}</td>

            <!-- Cuti Haid -->
            <td class="text-center">{employee.get('cuti_haid_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_haid_jumlah', 0))}</td>

            <!-- Cuti Minggu -->
            <td class="text-center">{employee.get('cuti_minggu_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_minggu_jumlah', 0))}</td>

            <!-- Cuti Nasional -->
            <td class="text-center">{employee.get('cuti_nasional_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_nasional_jumlah', 0))}</td>

            <!-- Cuti Hamil/Melahirkan -->
            <td class="text-center">{employee.get('cuti_hamil_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_hamil_jumlah', 0))}</td>

            <!-- Cuti Izin -->
            <td class="text-center">{employee.get('cuti_izin_hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti_izin_jumlah', 0))}</td>

            <!-- Jumlah HK -->
            <td class="text-center">{employee.get('jumlah_hk', 0)}</td>

            <!-- Tunjangan Beras -->
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_beras', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_beras_jumlah', 0))}</td>

            <!-- Tunjangan Jabatan -->
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_jabatan', 0))}</td>
            <td class="text-center">{employee.get('tunjangan_jabatan_hk', 0)}</td>

            <!-- Tunjangan Masa Kerja -->
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_masa_kerja', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_masa_kerja_jumlah', 0))}</td>

            <!-- Lembur -->
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_lembur', 0))}</td>

            <!-- Premium Columns -->
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_premi', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_angkut_tbs', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_angkut_pc_tbk', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_premi_retase', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_antar_jemput', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_angkut_puru', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_angkut_bibit', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_jaga_genset', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_premi_kontan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan_koreksi', 0))}</td>

            <!-- Upah Kotor -->
            <td class="number-cell">{self.format_rupiah(employee.get('upah_kotor', 0))}</td>

            <!-- Potongan ASTEK -->
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_astek_pekerja', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_astek_majikan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_astek_jumlah', 0))}</td>

            <!-- Potongan BPJS -->
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_bpjs_kesehatan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_bpjs_pekerja', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_bpjs_pensiun', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_bpjs_majikan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_bpjs_jumlah', 0))}</td>

            <!-- Potongan Lainnya -->
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_pph21', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_premi_kontan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_lebih_potong_pajak_thr', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan_pinjaman_uang', 0))}</td>

            <!-- Upah Bersih -->
            <td class="number-cell">{self.format_rupiah(employee.get('upah_bersih', 0))}</td>

            <!-- Tidak Hadir -->
            <td class="text-center">{employee.get('tidak_hadir_cth', 0)}</td>
            <td class="text-center">{employee.get('tidak_hadir_alpa', 0)}</td>
        </tr>
        """
        return row

    def calculate_totals(self, data):
        """Calculate totals for all columns"""
        employees = data.get('karyawan', [])

        totals = {
            'cuti_tahun_hari': sum(emp.get('cuti_tahun_hari', 0) for emp in employees),
            'cuti_tahun_jumlah': sum(emp.get('cuti_tahun_jumlah', 0) for emp in employees),
            'cuti_sakit_hari': sum(emp.get('cuti_sakit_hari', 0) for emp in employees),
            'cuti_sakit_jumlah': sum(emp.get('cuti_sakit_jumlah', 0) for emp in employees),
            'cuti_haid_hari': sum(emp.get('cuti_haid_hari', 0) for emp in employees),
            'cuti_haid_jumlah': sum(emp.get('cuti_haid_jumlah', 0) for emp in employees),
            'cuti_minggu_hari': sum(emp.get('cuti_minggu_hari', 0) for emp in employees),
            'cuti_minggu_jumlah': sum(emp.get('cuti_minggu_jumlah', 0) for emp in employees),
            'cuti_nasional_hari': sum(emp.get('cuti_nasional_hari', 0) for emp in employees),
            'cuti_nasional_jumlah': sum(emp.get('cuti_nasional_jumlah', 0) for emp in employees),
            'cuti_hamil_hari': sum(emp.get('cuti_hamil_hari', 0) for emp in employees),
            'cuti_hamil_jumlah': sum(emp.get('cuti_hamil_jumlah', 0) for emp in employees),
            'cuti_izin_hari': sum(emp.get('cuti_izin_hari', 0) for emp in employees),
            'cuti_izin_jumlah': sum(emp.get('cuti_izin_jumlah', 0) for emp in employees),
            'jumlah_hk': sum(emp.get('jumlah_hk', 0) for emp in employees),
            'tunjangan_beras': sum(emp.get('tunjangan_beras', 0) for emp in employees),
            'tunjangan_beras_jumlah': sum(emp.get('tunjangan_beras_jumlah', 0) for emp in employees),
            'tunjangan_jabatan': sum(emp.get('tunjangan_jabatan', 0) for emp in employees),
            'tunjangan_jabatan_hk': sum(emp.get('tunjangan_jabatan_hk', 0) for emp in employees),
            'tunjangan_masa_kerja': sum(emp.get('tunjangan_masa_kerja', 0) for emp in employees),
            'tunjangan_masa_kerja_jumlah': sum(emp.get('tunjangan_masa_kerja_jumlah', 0) for emp in employees),
            'tunjangan_lembur': sum(emp.get('tunjangan_lembur', 0) for emp in employees),
            'tunjangan_premi': sum(emp.get('tunjangan_premi', 0) for emp in employees),
            'tunjangan_angkut_tbs': sum(emp.get('tunjangan_angkut_tbs', 0) for emp in employees),
            'tunjangan_angkut_pc_tbk': sum(emp.get('tunjangan_angkut_pc_tbk', 0) for emp in employees),
            'tunjangan_premi_retase': sum(emp.get('tunjangan_premi_retase', 0) for emp in employees),
            'tunjangan_antar_jemput': sum(emp.get('tunjangan_antar_jemput', 0) for emp in employees),
            'tunjangan_angkut_puru': sum(emp.get('tunjangan_angkut_puru', 0) for emp in employees),
            'tunjangan_angkut_bibit': sum(emp.get('tunjangan_angkut_bibit', 0) for emp in employees),
            'tunjangan_jaga_genset': sum(emp.get('tunjangan_jaga_genset', 0) for emp in employees),
            'tunjangan_premi_kontan': sum(emp.get('tunjangan_premi_kontan', 0) for emp in employees),
            'tunjangan_koreksi': sum(emp.get('tunjangan_koreksi', 0) for emp in employees),
            'upah_kotor': sum(emp.get('upah_kotor', 0) for emp in employees),
            'potongan_astek_pekerja': sum(emp.get('potongan_astek_pekerja', 0) for emp in employees),
            'potongan_astek_majikan': sum(emp.get('potongan_astek_majikan', 0) for emp in employees),
            'potongan_astek_jumlah': sum(emp.get('potongan_astek_jumlah', 0) for emp in employees),
            'potongan_bpjs_kesehatan': sum(emp.get('potongan_bpjs_kesehatan', 0) for emp in employees),
            'potongan_bpjs_pekerja': sum(emp.get('potongan_bpjs_pekerja', 0) for emp in employees),
            'potongan_bpjs_pensiun': sum(emp.get('potongan_bpjs_pensiun', 0) for emp in employees),
            'potongan_bpjs_majikan': sum(emp.get('potongan_bpjs_majikan', 0) for emp in employees),
            'potongan_bpjs_jumlah': sum(emp.get('potongan_bpjs_jumlah', 0) for emp in employees),
            'potongan_pph21': sum(emp.get('potongan_pph21', 0) for emp in employees),
            'potongan_premi_kontan': sum(emp.get('potongan_premi_kontan', 0) for emp in employees),
            'potongan_lebih_potong_pajak_thr': sum(emp.get('potongan_lebih_potong_pajak_thr', 0) for emp in employees),
            'potongan_pinjaman_uang': sum(emp.get('potongan_pinjaman_uang', 0) for emp in employees),
            'upah_bersih': sum(emp.get('upah_bersih', 0) for emp in employees),
            'tidak_hadir_cth': sum(emp.get('tidak_hadir_cth', 0) for emp in employees),
            'tidak_hadir_alpa': sum(emp.get('tidak_hadir_alpa', 0) for emp in employees),
        }

        return totals

    def render_template(self, template_content, data):
        """Render template with data"""
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

        # Replace the {employee_rows} placeholder
        template = template.replace('{employee_rows}', employee_rows)

        # Calculate and process totals
        totals = self.calculate_totals(data)

        # Replace total variables
        for key, value in totals.items():
            template = template.replace(f'{{total.{key}}}', self.format_rupiah(value))

        return template

    def generate_report(self, template_file="daftar_upah_template.html",
                       data_file="../large_data.json",
                       output_file="daftar_upah_report_large.html"):
        """Generate complete HTML report"""
        print("Loading template...")
        template_content = self.load_template(template_file)

        print("Loading data...")
        data = self.load_data(data_file)
        print(f"Loaded {len(data.get('karyawan', []))} employee records")

        print("Rendering template...")
        rendered_content = self.render_template(template_content, data)

        print("Saving output...")
        output_path = self.output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_content)

        print(f"Report generated successfully: {output_path}")
        return output_path

def main():
    engine = DaftarUpahTemplateEngine()
    engine.generate_report()

if __name__ == "__main__":
    main()