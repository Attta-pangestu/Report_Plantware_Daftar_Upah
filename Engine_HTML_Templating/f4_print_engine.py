import json
import os
from pathlib import Path

class F4PrintTemplateEngine:
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
        """Render a single employee row for F4 print layout"""
        row = f"""
        <tr class="data-row" style="height: 20px;">
            <td class="col-1">{index}</td>
            <td class="col-2">{employee.get('jenis_kelamin', '')}</td>
            <td class="col-3">{employee.get('nik', '')}</td>
            <td class="col-4 text-left" colspan="4">{employee.get('nama', '')}</td>

            <!-- Cuti/Libur Section -->
            <td class="col-5">{employee.get('cuti_tahun_hari', 0)}</td>
            <td class="col-6 text-right">{self.format_rupiah(employee.get('cuti_tahun_jumlah', 0))}</td>
            <td class="col-7">{employee.get('cuti_sakit_hari', 0)}</td>
            <td class="col-8 text-right">{self.format_rupiah(employee.get('cuti_sakit_jumlah', 0))}</td>
            <td class="col-9">{employee.get('cuti_haid_hari', 0)}</td>
            <td class="col-10 text-right">{self.format_rupiah(employee.get('cuti_haid_jumlah', 0))}</td>
            <td class="col-11">{employee.get('cuti_minggu_hari', 0)}</td>
            <td class="col-12 text-right">{self.format_rupiah(employee.get('cuti_minggu_jumlah', 0))}</td>
            <td class="col-13">{employee.get('cuti_nasional_hari', 0)}</td>
            <td class="col-14 text-right">{self.format_rupiah(employee.get('cuti_nasional_jumlah', 0))}</td>
            <td class="col-15">{employee.get('cuti_hamil_hari', 0)}</td>
            <td class="col-16 text-right">{self.format_rupiah(employee.get('cuti_hamil_jumlah', 0))}</td>
            <td class="col-17">{employee.get('cuti_izin_hari', 0)}</td>
            <td class="col-18 text-right">{self.format_rupiah(employee.get('cuti_izin_jumlah', 0))}</td>
            <td class="col-20 text-right">{self.format_rupiah(employee.get('tunjangan_beras', 0))}</td>
            <td class="col-21 text-right">{self.format_rupiah(employee.get('tunjangan_beras_jumlah', 0))}</td>
            <td class="col-22 text-right">{self.format_rupiah(employee.get('tunjangan_jabatan', 0))}</td>
            <td class="col-23">{employee.get('tunjangan_jabatan_hk', 0)}</td>
            <td class="col-24 text-right">{self.format_rupiah(employee.get('tunjangan_masa_kerja', 0))}</td>
            <td class="col-25 text-right">{self.format_rupiah(employee.get('tunjangan_masa_kerja_jumlah', 0))}</td>

            <!-- Work and Salary -->
            <td class="col-26">{employee.get('jumlah_hk', 0)}</td>
            <td class="col-27 text-right">{self.format_rupiah(employee.get('upah_harian', 0))}</td>
            <td class="col-28">{employee.get('masa_kerja_tahun', 0)}</td>
            <td class="col-29 text-right">{self.format_rupiah(employee.get('tunjangan_masa_kerja_total', 0))}</td>
            <td class="col-30 text-right">{self.format_rupiah(employee.get('tunjangan_lembur', 0))}</td>
            <td class="col-31 text-right">{self.format_rupiah(employee.get('tunjangan_premi', 0))}</td>
            <td class="col-32 text-right">{self.format_rupiah(employee.get('tunjangan_koreksi', 0))}</td>
            <td class="col-33 text-right">{self.format_rupiah(employee.get('upah_kotor', 0))}</td>

            <!-- Potongan Section -->
            <td class="col-34 text-right">{self.format_rupiah(employee.get('potongan_astek_pekerja', 0))}</td>
            <td class="col-35 text-right">{self.format_rupiah(employee.get('potongan_astek_majikan', 0))}</td>
            <td class="col-36 text-right">{self.format_rupiah(employee.get('potongan_astek_jumlah', 0))}</td>
            <td class="col-37 text-right">{self.format_rupiah(employee.get('potongan_bpjs_kesehatan', 0))}</td>
            <td class="col-38 text-right">{self.format_rupiah(employee.get('potongan_bpjs_pekerja', 0))}</td>
            <td class="col-39 text-right">{self.format_rupiah(employee.get('potongan_bpjs_pensiun', 0))}</td>
            <td class="col-40 text-right">{self.format_rupiah(employee.get('potongan_bpjs_majikan', 0))}</td>
            <td class="col-41 text-right">{self.format_rupiah(employee.get('potongan_bpjs_jumlah', 0))}</td>
            <td class="col-42 text-right">{self.format_rupiah(employee.get('potongan_pph21', 0))}</td>
            <td class="col-43 text-right">{self.format_rupiah(employee.get('potongan_premi_kontan', 0))}</td>
            <td class="col-44 text-right">{self.format_rupiah(employee.get('potongan_lebih_potong_pajak_thr', 0))}</td>
            <td class="col-45 text-right">{self.format_rupiah(employee.get('potongan_pinjaman_uang', 0))}</td>
            <td class="col-46 text-right">{self.format_rupiah(employee.get('upah_bersih', 0))}</td>

            <!-- Absence -->
            <td class="col-47">{employee.get('tidak_hadir_cth', 0)}</td>
            <td class="col-48">{employee.get('tidak_hadir_alpa', 0)}</td>
        </tr>
        """
        return row

    def calculate_totals(self, karyawan_list):
        """Calculate totals from karyawan list"""
        totals = {
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
            'jumlah_hk': 0,
            'tunjangan_beras': 0,
            'tunjangan_beras_jumlah': 0,
            'tunjangan_jabatan': 0,
            'tunjangan_jabatan_hk': 0,
            'tunjangan_masa_kerja': 0,
            'tunjangan_masa_kerja_jumlah': 0,
            'upah_harian': 0,
            'masa_kerja_tahun': 0,
            'tunjangan_masa_kerja_total': 0,
            'tunjangan_lembur': 0,
            'tunjangan_premi': 0,
            'tunjangan_koreksi': 0,
            'upah_kotor': 0,
            'potongan_astek_pekerja': 0,
            'potongan_astek_majikan': 0,
            'potongan_astek_jumlah': 0,
            'potongan_bpjs_kesehatan': 0,
            'potongan_bpjs_pekerja': 0,
            'potongan_bpjs_pensiun': 0,
            'potongan_bpjs_majikan': 0,
            'potongan_bpjs_jumlah': 0,
            'potongan_pph21': 0,
            'potongan_premi_kontan': 0,
            'potongan_lebih_potong_pajak_thr': 0,
            'potongan_pinjaman_uang': 0,
            'upah_bersih': 0,
            'tidak_hadir_cth': 0,
            'tidak_hadir_alpa': 0
        }

        for emp in karyawan_list:
            for key in totals:
                if key in emp:
                    totals[key] += emp.get(key, 0)

        return totals

    def chunk_employees(self, employees, chunk_size=25):
        """Split employees into chunks for print pagination"""
        chunks = []
        for i in range(0, len(employees), chunk_size):
            chunks.append(employees[i:i + chunk_size])
        return chunks

    def render_template(self, template_content, data):
        """Render template with F4 print optimization"""
        template = template_content

        # Replace simple variables
        template = template.replace('{bulan}', data.get('bulan', ''))
        template = template.replace('{tahun}', data.get('tahun', ''))
        template = template.replace('{catatan}', data.get('catatan', ''))
        template = template.replace('{upah_dasar}', data.get('upah_dasar', ''))

        # Process employee data in chunks for better print layout
        employees = data.get('karyawan', [])
        employee_chunks = self.chunk_employees(employees, 30)  # 30 employees per page

        all_employee_rows = ""
        all_total_rows = ""

        for chunk_index, chunk in enumerate(employee_chunks):
            # Process chunk employees
            employee_rows = ""
            for global_index, employee in enumerate(chunk):
                local_index = global_index + 1
                row = self.render_employee_row(local_index, employee)
                employee_rows += row

            # Calculate totals for this chunk
            chunk_totals = self.calculate_totals(chunk)

            # Add total row for this chunk
            total_row = f"""
            <tr class="total-row" style="height: 20px;">
                <td class="col-1" colspan="7" style="text-align: left; font-weight: bold;">
                    SUBTOTAL HALAMAN {chunk_index + 1}
                </td>

                <!-- Cuti/Libur Totals -->
                <td class="col-5">{chunk_totals['cuti_tahun_hari']}</td>
                <td class="col-6 text-right">{self.format_rupiah(chunk_totals['cuti_tahun_jumlah'])}</td>
                <td class="col-7">{chunk_totals['cuti_sakit_hari']}</td>
                <td class="col-8 text-right">{self.format_rupiah(chunk_totals['cuti_sakit_jumlah'])}</td>
                <td class="col-9">{chunk_totals['cuti_haid_hari']}</td>
                <td class="col-10 text-right">{self.format_rupiah(chunk_totals['cuti_haid_jumlah'])}</td>
                <td class="col-11">{chunk_totals['cuti_minggu_hari']}</td>
                <td class="col-12 text-right">{self.format_rupiah(chunk_totals['cuti_minggu_jumlah'])}</td>
                <td class="col-13">{chunk_totals['cuti_nasional_hari']}</td>
                <td class="col-14 text-right">{self.format_rupiah(chunk_totals['cuti_nasional_jumlah'])}</td>
                <td class="col-15">{chunk_totals['cuti_hamil_hari']}</td>
                <td class="col-16 text-right">{self.format_rupiah(chunk_totals['cuti_hamil_jumlah'])}</td>
                <td class="col-17">{chunk_totals['cuti_izin_hari']}</td>
                <td class="col-18 text-right">{self.format_rupiah(chunk_totals['cuti_izin_jumlah'])}</td>
                <td class="col-20 text-right">{self.format_rupiah(chunk_totals['tunjangan_beras'])}</td>
                <td class="col-21 text-right">{self.format_rupiah(chunk_totals['tunjangan_beras_jumlah'])}</td>
                <td class="col-22 text-right">{self.format_rupiah(chunk_totals['tunjangan_jabatan'])}</td>
                <td class="col-23">{chunk_totals['tunjangan_jabatan_hk']}</td>
                <td class="col-24 text-right">{self.format_rupiah(chunk_totals['tunjangan_masa_kerja'])}</td>
                <td class="col-25 text-right">{self.format_rupiah(chunk_totals['tunjangan_masa_kerja_jumlah'])}</td>

                <!-- Work and Salary Totals -->
                <td class="col-26">{chunk_totals['jumlah_hk']}</td>
                <td class="col-27 text-right">{self.format_rupiah(chunk_totals['upah_harian'])}</td>
                <td class="col-28">{chunk_totals['masa_kerja_tahun']}</td>
                <td class="col-29 text-right">{self.format_rupiah(chunk_totals['tunjangan_masa_kerja_total'])}</td>
                <td class="col-30 text-right">{self.format_rupiah(chunk_totals['tunjangan_lembur'])}</td>
                <td class="col-31 text-right">{self.format_rupiah(chunk_totals['tunjangan_premi'])}</td>
                <td class="col-32 text-right">{self.format_rupiah(chunk_totals['tunjangan_koreksi'])}</td>
                <td class="col-33 text-right">{self.format_rupiah(chunk_totals['upah_kotor'])}</td>

                <!-- Potongan Totals -->
                <td class="col-34 text-right">{self.format_rupiah(chunk_totals['potongan_astek_pekerja'])}</td>
                <td class="col-35 text-right">{self.format_rupiah(chunk_totals['potongan_astek_majikan'])}</td>
                <td class="col-36 text-right">{self.format_rupiah(chunk_totals['potongan_astek_jumlah'])}</td>
                <td class="col-37 text-right">{self.format_rupiah(chunk_totals['potongan_bpjs_kesehatan'])}</td>
                <td class="col-38 text-right">{self.format_rupiah(chunk_totals['potongan_bpjs_pekerja'])}</td>
                <td class="col-39 text-right">{self.format_rupiah(chunk_totals['potongan_bpjs_pensiun'])}</td>
                <td class="col-40 text-right">{self.format_rupiah(chunk_totals['potongan_bpjs_majikan'])}</td>
                <td class="col-41 text-right">{self.format_rupiah(chunk_totals['potongan_bpjs_jumlah'])}</td>
                <td class="col-42 text-right">{self.format_rupiah(chunk_totals['potongan_pph21'])}</td>
                <td class="col-43 text-right">{self.format_rupiah(chunk_totals['potongan_premi_kontan'])}</td>
                <td class="col-44 text-right">{self.format_rupiah(chunk_totals['potongan_lebih_potong_pajak_thr'])}</td>
                <td class="col-45 text-right">{self.format_rupiah(chunk_totals['potongan_pinjaman_uang'])}</td>
                <td class="col-46 text-right">{self.format_rupiah(chunk_totals['upah_bersih'])}</td>

                <!-- Absence Totals -->
                <td class="col-47">{chunk_totals['tidak_hadir_cth']}</td>
                <td class="col-48">{chunk_totals['tidak_hadir_alpa']}</td>
            </tr>
            """

            all_employee_rows += employee_rows + total_row

            # Add page break if not last chunk
            if chunk_index < len(employee_chunks) - 1:
                all_employee_rows += '<tr class="page-break"><td colspan="48"></td></tr>'

        # Calculate grand totals
        grand_totals = self.calculate_totals(employees)

        # Add grand total row
        grand_total_row = f"""
        <tr class="total-row" style="height: 25px; font-weight: bold; border-top: 2pt solid black;">
            <td class="col-1" colspan="7" style="text-align: left; font-weight: bold;">
                GRAND TOTAL
            </td>

            <!-- Cuti/Libur Grand Totals -->
            <td class="col-5">{grand_totals['cuti_tahun_hari']}</td>
            <td class="col-6 text-right">{self.format_rupiah(grand_totals['cuti_tahun_jumlah'])}</td>
            <td class="col-7">{grand_totals['cuti_sakit_hari']}</td>
            <td class="col-8 text-right">{self.format_rupiah(grand_totals['cuti_sakit_jumlah'])}</td>
            <td class="col-9">{grand_totals['cuti_haid_hari']}</td>
            <td class="col-10 text-right">{self.format_rupiah(grand_totals['cuti_haid_jumlah'])}</td>
            <td class="col-11">{grand_totals['cuti_minggu_hari']}</td>
            <td class="col-12 text-right">{self.format_rupiah(grand_totals['cuti_minggu_jumlah'])}</td>
            <td class="col-13">{grand_totals['cuti_nasional_hari']}</td>
            <td class="col-14 text-right">{self.format_rupiah(grand_totals['cuti_nasional_jumlah'])}</td>
            <td class="col-15">{grand_totals['cuti_hamil_hari']}</td>
            <td class="col-16 text-right">{self.format_rupiah(grand_totals['cuti_hamil_jumlah'])}</td>
            <td class="col-17">{grand_totals['cuti_izin_hari']}</td>
            <td class="col-18 text-right">{self.format_rupiah(grand_totals['cuti_izin_jumlah'])}</td>
            <td class="col-20 text-right">{self.format_rupiah(grand_totals['tunjangan_beras'])}</td>
            <td class="col-21 text-right">{self.format_rupiah(grand_totals['tunjangan_beras_jumlah'])}</td>
            <td class="col-22 text-right">{self.format_rupiah(grand_totals['tunjangan_jabatan'])}</td>
            <td class="col-23">{grand_totals['tunjangan_jabatan_hk']}</td>
            <td class="col-24 text-right">{self.format_rupiah(grand_totals['tunjangan_masa_kerja'])}</td>
            <td class="col-25 text-right">{self.format_rupiah(grand_totals['tunjangan_masa_kerja_jumlah'])}</td>

            <!-- Work and Salary Grand Totals -->
            <td class="col-26">{grand_totals['jumlah_hk']}</td>
            <td class="col-27 text-right">{self.format_rupiah(grand_totals['upah_harian'])}</td>
            <td class="col-28">{grand_totals['masa_kerja_tahun']}</td>
            <td class="col-29 text-right">{self.format_rupiah(grand_totals['tunjangan_masa_kerja_total'])}</td>
            <td class="col-30 text-right">{self.format_rupiah(grand_totals['tunjangan_lembur'])}</td>
            <td class="col-31 text-right">{self.format_rupiah(grand_totals['tunjangan_premi'])}</td>
            <td class="col-32 text-right">{self.format_rupiah(grand_totals['tunjangan_koreksi'])}</td>
            <td class="col-33 text-right">{self.format_rupiah(grand_totals['upah_kotor'])}</td>

            <!-- Potongan Grand Totals -->
            <td class="col-34 text-right">{self.format_rupiah(grand_totals['potongan_astek_pekerja'])}</td>
            <td class="col-35 text-right">{self.format_rupiah(grand_totals['potongan_astek_majikan'])}</td>
            <td class="col-36 text-right">{self.format_rupiah(grand_totals['potongan_astek_jumlah'])}</td>
            <td class="col-37 text-right">{self.format_rupiah(grand_totals['potongan_bpjs_kesehatan'])}</td>
            <td class="col-38 text-right">{self.format_rupiah(grand_totals['potongan_bpjs_pekerja'])}</td>
            <td class="col-39 text-right">{self.format_rupiah(grand_totals['potongan_bpjs_pensiun'])}</td>
            <td class="col-40 text-right">{self.format_rupiah(grand_totals['potongan_bpjs_majikan'])}</td>
            <td class="col-41 text-right">{self.format_rupiah(grand_totals['potongan_bpjs_jumlah'])}</td>
            <td class="col-42 text-right">{self.format_rupiah(grand_totals['potongan_pph21'])}</td>
            <td class="col-43 text-right">{self.format_rupiah(grand_totals['potongan_premi_kontan'])}</td>
            <td class="col-44 text-right">{self.format_rupiah(grand_totals['potongan_lebih_potong_pajak_thr'])}</td>
            <td class="col-45 text-right">{self.format_rupiah(grand_totals['potongan_pinjaman_uang'])}</td>
            <td class="col-46 text-right">{self.format_rupiah(grand_totals['upah_bersih'])}</td>

            <!-- Absence Grand Totals -->
            <td class="col-47">{grand_totals['tidak_hadir_cth']}</td>
            <td class="col-48">{grand_totals['tidak_hadir_alpa']}</td>
        </tr>
        """

        # Replace the {employee_rows} placeholder
        template = template.replace('{employee_rows}', all_employee_rows + grand_total_row)

        return template

    def generate_report(self, template_file="template_f4_print.html",
                       data_file="large_data.json",
                       output_file="daftar_upah_f4_print_large.html"):
        """Generate complete HTML report for F4 print"""
        print("Loading F4 print template...")
        template_content = self.load_template(template_file)

        print("Loading data...")
        data = self.load_data(data_file)

        print("Rendering F4 print template...")
        rendered_content = self.render_template(template_content, data)

        print("Saving F4 print output...")
        output_path = self.output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_content)

        print(f"F4 print report generated successfully: {output_path}")
        print("Open the file and use the Print button for F4 paper output")
        return output_path

def main():
    engine = F4PrintTemplateEngine()
    engine.generate_report()

if __name__ == "__main__":
    main()