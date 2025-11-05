import json
import os
from pathlib import Path

class TemplateEngine:
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

        # Replace the {employee_rows} placeholder
        template = template.replace('{employee_rows}', employee_rows)

        # Process total row
        total_row = self.render_total_row(data.get('total', {}))

        # Replace total variables
        for key, value in data.get('total', {}).items():
            if key == 'cuti':
                for cut_type, cut_data in value.items():
                    template = template.replace(
                        f'{{{{total.cuti.{cut_type}.hari}}}}',
                        str(cut_data.get('hari', 0))
                    )
                    template = template.replace(
                        f'{{{{total.cuti.{cut_type}.jumlah}}}}',
                        self.format_rupiah(cut_data.get('jumlah', 0))
                    )
            elif key == 'tunjangan':
                for tunj_type, tunj_data in value.items():
                    if isinstance(tunj_data, dict):
                        for sub_key, sub_value in tunj_data.items():
                            template = template.replace(
                                f'{{{{total.tunjangan.{tunj_type}.{sub_key}}}}}',
                                self.format_rupiah(sub_value)
                            )
                    else:
                        template = template.replace(
                            f'{{{{total.tunjangan.{tunj_type}}}}}',
                            self.format_rupiah(tunj_data)
                        )
            elif key == 'potongan':
                for pot_type, pot_data in value.items():
                    if isinstance(pot_data, dict):
                        for sub_key, sub_value in pot_data.items():
                            template = template.replace(
                                f'{{{{total.potongan.{pot_type}.{sub_key}}}}}',
                                self.format_rupiah(sub_value)
                            )
                    else:
                        template = template.replace(
                            f'{{{{total.potongan.{pot_type}}}}}',
                            self.format_rupiah(pot_data)
                        )
            elif key == 'tidak_hadir':
                for hadir_type, hadir_value in value.items():
                    template = template.replace(
                        f'{{{{total.tidak_hadir.{hadir_type}}}}}',
                        str(hadir_value)
                    )
            else:
                if key == 'jumlah_hk':
                    template = template.replace('{{total.jumlah_hk}}', str(value))
                else:
                    template = template.replace(f'{{{{total.{key}}}}}', self.format_rupiah(value))

        # Clean up any remaining template variables
        template = self.cleanup_template(template)

        return template

    def render_employee_row(self, index, employee):
        """Render a single employee row"""
        row = f"""
        <tr>
            <td class="text-cell">{index}</td>
            <td>{employee.get('jenis_kelamin', '')}</td>
            <td>{employee.get('nik', '')}</td>
            <td class="text-cell">{employee.get('nama', '')}</td>

            <!-- Cuti/Libur Section -->
            <td>{employee.get('cuti', {}).get('sakit', {}).get('hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti', {}).get('sakit', {}).get('jumlah', 0))}</td>
            <td>{employee.get('cuti', {}).get('haid', {}).get('hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti', {}).get('haid', {}).get('jumlah', 0))}</td>
            <td>{employee.get('cuti', {}).get('minggu', {}).get('hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti', {}).get('minggu', {}).get('jumlah', 0))}</td>
            <td>{employee.get('cuti', {}).get('nasional', {}).get('hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti', {}).get('nasional', {}).get('jumlah', 0))}</td>
            <td>{employee.get('cuti', {}).get('hamil_melahirkan', {}).get('hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti', {}).get('hamil_melahirkan', {}).get('jumlah', 0))}</td>
            <td>{employee.get('cuti', {}).get('izin', {}).get('hari', 0)}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('cuti', {}).get('izin', {}).get('jumlah', 0))}</td>

            <!-- Work Days -->
            <td>{employee.get('jumlah_hk', 0)}</td>

            <!-- Tunjangan/Premi Section -->
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('beras', {}).get('tarif', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('beras', {}).get('jumlah', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('jabatan', {}).get('tarif', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('jabatan', {}).get('jumlah', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('masa_kerja', {}).get('tarif', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('masa_kerja', {}).get('jumlah', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('lembur', {}).get('jumlah', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('premi', {}).get('jumlah', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('angkut_tbs', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('angkut_pc_tbk', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('premi_retase', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('antar_jemput', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('angkut_puru', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('angkut_bibit', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('jaga_genset', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('premi_kontan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('tunjangan', {}).get('koreksi', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('upah_kotor', 0))}</td>

            <!-- Potongan Section -->
            <td class="number-cell">{self.format_rupiah(employee.get('potongan', {}).get('astek', {}).get('pekerja', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan', {}).get('astek', {}).get('majikan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan', {}).get('astek', {}).get('jumlah', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan', {}).get('bpjs', {}).get('kesehatan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan', {}).get('bpjs', {}).get('pekerja', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan', {}).get('bpjs', {}).get('pensiun_majikan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan', {}).get('bpjs', {}).get('jumlah', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan', {}).get('spsi', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan', {}).get('pph21', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan', {}).get('premi_kontan', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan', {}).get('lebih_potong_pajak_thr', 0))}</td>
            <td class="number-cell">{self.format_rupiah(employee.get('potongan', {}).get('pinjaman_uang', 0))}</td>

            <!-- Net Salary -->
            <td class="number-cell">{self.format_rupiah(employee.get('upah_bersih', 0))}</td>

            <!-- Absence -->
            <td>{employee.get('tidak_hadir', {}).get('cth', 0)}</td>
            <td>{employee.get('tidak_hadir', {}).get('alpa', 0)}</td>
        </tr>
        """
        return row

    def render_total_row(self, total_data):
        """Render total row - this is handled in render_template"""
        pass

    def cleanup_template(self, template):
        """Clean up any remaining template variables"""
        import re

        # Remove any remaining {{...}} patterns
        template = re.sub(r'\{\{[^}]+\}\}', '0', template)

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
    engine = TemplateEngine()
    engine.generate_report()

if __name__ == "__main__":
    main()