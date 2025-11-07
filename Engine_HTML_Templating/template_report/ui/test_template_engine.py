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
        """Render a single employee row compatible with final template structure"""
        # Compute fields to match final template columns
        upah_dasar = employee.get('upah_dasar', 0)
        jumlah_hk = employee.get('jumlah_hk', 0)
        hari_kerja = employee.get('hari_kerja', jumlah_hk)
        upah_pokok = employee.get('upah_pokok', upah_dasar * max(hari_kerja, 0))
        gaji_pokok = upah_dasar * jumlah_hk if upah_dasar and jumlah_hk else 0

        cuti_tahunan = employee.get('cuti_tahun_hari', employee.get('cuti_tahunan_hari', 0))
        cuti_sakit = employee.get('cuti_sakit_hari', 0)
        cuti_haid = employee.get('cuti_haid_hari', 0)
        cuti_sakit_haid = cuti_sakit + cuti_haid
        cuti_minggu = employee.get('cuti_minggu_hari', 0)
        cuti_nasional = employee.get('cuti_nasional_hari', 0)
        cuti_izin = employee.get('cuti_izin_hari', 0)

        # Tunjangan base
        tunj_beras_rate = employee.get('tunjangan_beras', 0)
        tunj_beras_jumlah = employee.get('tunjangan_beras_jumlah', 0)
        tunj_jabatan_rate = employee.get('tunjangan_jabatan', 0)
        tunj_jabatan_jumlah = employee.get('tunjangan_jabatan_jumlah', employee.get('tunjangan_jabatan_hk', 0))
        masa_kerja_tahun = employee.get('masa_kerja_tahun', employee.get('tunjangan_masa_kerja', 0))
        masa_kerja_jumlah = employee.get('tunjangan_masa_kerja_jumlah', 0)
        lembur_jam = employee.get('tunjangan_lembur_jam', 0)
        lembur_jumlah = employee.get('tunjangan_lembur', 0)
        total_tunj_base = tunj_beras_jumlah + tunj_jabatan_rate + masa_kerja_jumlah + lembur_jumlah

        # Premi 8 columns (including Koreksi)
        premi_cols = [
            employee.get('tunjangan_premi', 0),
            employee.get('tunjangan_angkut_tbs', 0),
            employee.get('tunjangan_angkut_pc_tbk', 0),
            employee.get('tunjangan_premi_retase', 0),
            employee.get('tunjangan_antar_jemput', 0),
            employee.get('tunjangan_angkut_puru', 0),
            employee.get('tunjangan_angkut_bibit', 0),
            employee.get('tunjangan_koreksi', 0),
        ]

        # Summary calculations
        total_premi = sum(premi_cols)
        jumlah_upah_kotor = gaji_pokok + total_tunj_base + total_premi

        # Potongan 13 columns (map best-effort)
        potongan_pph21 = employee.get('potongan_pph21', employee.get('potongan_pph', 0))
        potongan_kontan = employee.get('potongan_kontan', employee.get('potongan_premi_kontan', 0))
        potongan_thr = employee.get('potongan_thr', employee.get('potongan_lebih_potong_pajak_thr', 0))
        potongan_pinjam = employee.get('potongan_pinjaman_uang', 0)
        potongan_kl = employee.get('potongan_kl', employee.get('potongan_lain', 0))
        pot_bpjs_kes = employee.get('potongan_bpjs_kesehatan', 0)
        pot_bpjs_pek = employee.get('potongan_bpjs_pekerja', employee.get('potongan_bpjs', 0))
        pot_bpjs_maj = employee.get('potongan_bpjs_majikan', 0)
        pot_bpjs_total = employee.get('potongan_bpjs_jumlah', pot_bpjs_kes + pot_bpjs_pek + pot_bpjs_maj)
        pot_total1 = 0
        pot_total2 = 0
        pot_total3 = 0
        pot_total4 = 0

        row = f"""
        <tr>
            <td class="text-center">{index}</td>
            <td class="text-center">{employee.get('jenis_kelamin', '')}</td>
            <td class="text-center">{employee.get('nik', '')}</td>
            <td class="text-left">{employee.get('nama', '')}</td>
            <td class="number-cell">{self.format_rupiah(upah_dasar)}</td>
            <td class="text-center">{hari_kerja}</td>
            <td class="number-cell">{self.format_rupiah(upah_pokok)}</td>

            <!-- Cuti/Libur (5 kolom) -->
            <td class="text-center">{cuti_tahunan}</td>
            <td class="text-center">{cuti_sakit_haid}</td>
            <td class="text-center">{cuti_minggu}</td>
            <td class="text-center">{cuti_nasional}</td>
            <td class="text-center">{cuti_izin}</td>

            <!-- JML HK & Gaji Pokok -->
            <td class="text-center">{jumlah_hk}</td>
            <td class="number-cell">{self.format_rupiah(gaji_pokok)}</td>

            <!-- Tunjangan Base (8 kolom) -->
            <td class="number-cell">{self.format_rupiah(tunj_beras_rate)}</td>
            <td class="number-cell">{self.format_rupiah(tunj_beras_jumlah)}</td>
            <td class="number-cell">{self.format_rupiah(tunj_jabatan_rate)}</td>
            <td class="number-cell">{tunj_jabatan_jumlah}</td>
            <td class="number-cell">{masa_kerja_tahun}</td>
            <td class="number-cell">{self.format_rupiah(masa_kerja_jumlah)}</td>
            <td class="number-cell">{lembur_jam}</td>
            <td class="number-cell">{self.format_rupiah(lembur_jumlah)}</td>

            <!-- Total Tunjangan -->
            <td class="number-cell">{self.format_rupiah(total_tunj_base)}</td>

            <!-- Premi (8 kolom termasuk Koreksi) -->
            <td class="number-cell">{self.format_rupiah(premi_cols[0])}</td>
            <td class="number-cell">{self.format_rupiah(premi_cols[1])}</td>
            <td class="number-cell">{self.format_rupiah(premi_cols[2])}</td>
            <td class="number-cell">{self.format_rupiah(premi_cols[3])}</td>
            <td class="number-cell">{self.format_rupiah(premi_cols[4])}</td>
            <td class="number-cell">{self.format_rupiah(premi_cols[5])}</td>
            <td class="number-cell">{self.format_rupiah(premi_cols[6])}</td>
            <td class="number-cell">{self.format_rupiah(premi_cols[7])}</td>

            <!-- Summary: Total Premi & Jumlah Upah Kotor -->
            <td class="number-cell">{self.format_rupiah(total_premi)}</td>
            <td class="number-cell">{self.format_rupiah(jumlah_upah_kotor)}</td>

            <!-- Potongan (13 kolom) -->
            <td class="number-cell">{self.format_rupiah(potongan_pph21)}</td>
            <td class="number-cell">{self.format_rupiah(potongan_kontan)}</td>
            <td class="number-cell">{self.format_rupiah(potongan_thr)}</td>
            <td class="number-cell">{self.format_rupiah(potongan_pinjam)}</td>
            <td class="number-cell">{self.format_rupiah(potongan_kl)}</td>
            <td class="number-cell">{self.format_rupiah(pot_bpjs_kes)}</td>
            <td class="number-cell">{self.format_rupiah(pot_bpjs_pek)}</td>
            <td class="number-cell">{self.format_rupiah(pot_bpjs_maj)}</td>
            <td class="number-cell">{self.format_rupiah(pot_bpjs_total)}</td>
            <td class="number-cell">{self.format_rupiah(pot_total1)}</td>
            <td class="number-cell">{self.format_rupiah(pot_total2)}</td>
            <td class="number-cell">{self.format_rupiah(pot_total3)}</td>
            <td class="number-cell">{self.format_rupiah(pot_total4)}</td>

            <!-- Upah Bersih & Tidak Hadir -->
            <td class="number-cell">{self.format_rupiah(employee.get('upah_bersih', 0))}</td>
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

        # Compute and replace grand total placeholders used in final template
        employees = data.get('karyawan', [])
        grand_total_koreksi = totals.get('tunjangan_koreksi', 0)
        grand_total_total_premi = (
            totals.get('tunjangan_premi', 0) +
            totals.get('tunjangan_angkut_tbs', 0) +
            totals.get('tunjangan_angkut_pc_tbk', 0) +
            totals.get('tunjangan_premi_retase', 0) +
            totals.get('tunjangan_antar_jemput', 0) +
            totals.get('tunjangan_angkut_puru', 0) +
            totals.get('tunjangan_angkut_bibit', 0) +
            grand_total_koreksi
        )

        grand_total_gaji_pokok = sum(
            (emp.get('upah_dasar', 0) or 0) * (emp.get('jumlah_hk', emp.get('hari_kerja', 0)) or 0)
            for emp in employees
        )

        total_tunj_base_total = (
            totals.get('tunjangan_beras_jumlah', 0) +
            totals.get('tunjangan_jabatan', 0) +
            totals.get('tunjangan_masa_kerja_jumlah', 0) +
            totals.get('tunjangan_lembur', 0)
        )

        grand_total_jumlah_upah_kotor = grand_total_gaji_pokok + total_tunj_base_total + grand_total_total_premi

        template = template.replace('{grand_total.koreksi_total}', self.format_rupiah(grand_total_koreksi))
        template = template.replace('{grand_total.total_premi_total}', self.format_rupiah(grand_total_total_premi))
        template = template.replace('{grand_total.jumlah_upah_kotor_total}', self.format_rupiah(grand_total_jumlah_upah_kotor))

        return template

    def generate_report(self, template_file="daftar_upah_template_final.html",
                       data_file="../large_data.json",
                       output_file="daftar_upah_preview.html"):
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
