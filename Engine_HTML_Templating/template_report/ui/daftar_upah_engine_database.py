#!/usr/bin/env python3
"""
Daftar Upah HTML Template Engine - Database Query Integration
Integrates with SQL Server database to render reports with real employee data
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from employee_query_integration import EmployeeQueryManager, EmployeeDataProcessor
from daftar_upah_engine_fixed import DaftarUpahTemplateEngineFixed


class DaftarUpahTemplateEngineDatabase:
    """
    HTML Template Engine with Real Database Query Integration

    Features:
    - Real-time employee data from SQL Server
    - Uses the exact query from get_detail_emp_each_gang.sql
    - Gender mapping (1=L, 0=P) as specified
    - Merges with sample payroll data
    - Professional HTML report generation
    """

    def __init__(self, template_dir=None):
        """
        Initialize template engine with database integration

        Args:
            template_dir: Template directory path
        """
        if template_dir is None:
            self.template_dir = Path(__file__).parent
        else:
            self.template_dir = Path(template_dir)

        self.output_dir = self.template_dir / "output"
        self.output_dir.mkdir(exist_ok=True)

        # Initialize components
        self.query_manager = EmployeeQueryManager()
        self.data_processor = EmployeeDataProcessor()
        self.template_engine = DaftarUpahTemplateEngineFixed()

        # Track statistics
        self.stats = {
            'reports_generated': 0,
            'total_employees_processed': 0,
            'database_queries_executed': 0,
            'processing_times': []
        }

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
        """Render HTML template with employee data"""
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
        Generate payroll report using real database query

        Args:
            gang_code: Gang code to query (default: 'H1H')
            limit: Maximum number of employees to fetch (default: 100)
            template_file: HTML template file name
            sample_data_file: Sample data file for payroll fields
            output_file: Output file name (auto-generated if not specified)

        Returns:
            Path to generated report file or None if failed
        """
        try:
            start_time = datetime.now()

            print("=" * 80)
            print("DAFTAR UPAH TEMPLATE ENGINE - DATABASE QUERY INTEGRATION")
            print("=" * 80)

            print(f"[STATS] Gang Code: {gang_code}")
            print(f"[REPORT] Template: {template_file}")
            print(f"[FILE] Sample Data: {sample_data_file}")
            print(f"[QUERY] Query File: {self.query_manager.query_file_path}")
            print(f"[TARGET] Max Employees: {limit}")

            print(f"\n[1] Processing employee data for gang '{gang_code}'...")

            # Process complete gang data (database query + sample data merging)
            start_processing = datetime.now()
            merged_employees = self.data_processor.process_gang_data(
                gang_code=gang_code,
                limit=limit,
                sample_data_path=sample_data_file
            )
            processing_time = (datetime.now() - start_processing).total_seconds()
            print(f"   Processing time: {processing_time:.2f}s")

            if not merged_employees:
                print(f"[ERROR] No employee data found for gang '{gang_code}'")
                return None

            # Show processing summary
            summary = self.data_processor.get_processing_summary(merged_employees, gang_code)
            print(f"\n[STATS] PROCESSING SUMMARY:")
            print(f"   Gang: {summary['gang_code']}")
            print(f"   Total Employees: {summary['total_employees']}")
            print(f"   Data Source: {summary['data_source']}")
            print(f"   Gender Distribution: L={summary['gender_distribution']['Laki-laki']}, P={summary['gender_distribution']['Perempuan']}")
            print(f"   Locations: {', '.join(summary['locations'])}")

            # Prepare data for template
            report_data = {
                'bulan': 'MEI',  # Get from sample data or use default
                'tahun': '2025',  # Get from sample data or use default
                'catatan': f"Daftar upah karyawan periode MEI 2025 - Gang {gang_code} (Real Database Query)",
                'upah_dasar': 'Upah Minimum Kabupaten (UMK) 2025',
                'karyawan': merged_employees
            }

            print("\n[2] Loading HTML template...")
            template_content = self.load_template(template_file)

            print("[3] Rendering template...")
            rendering_start = datetime.now()
            rendered_content = self.render_template(template_content, report_data)
            rendering_time = (datetime.now() - rendering_start).total_seconds()
            print(f"   Rendering time: {rendering_time:.2f}s")

            # Generate output filename
            if output_file is None:
                period = f"{report_data.get('bulan', 'unknown')}-{report_data.get('tahun', 'unknown')}"
                output_file = f"daftar_upah_gang_{gang_code}_{period.lower()}_database.html"

            print("[4] Saving output...")
            output_path = self.output_dir / output_file

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)

            file_size = output_path.stat().st_size
            total_time = (datetime.now() - start_time).total_seconds()

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
            print(f"[EMPLOYEES] Employees: {len(merged_employees)}")
            print(f"[GANG] Gang: {gang_code}")
            print(f"[TIME] Total Time: {total_time:.2f}s")
            print(f"[DATA] Data Source: Real Database Query + Sample Payroll")
            print(f"[INFO] Gender Mapping: 1->L, 0->P")
            print(f"[TARGET] Query File: {self.query_manager.query_file_path}")

            print(f"\n[STATS] STATISTICS:")
            print(f"   Total Reports Generated: {self.stats['reports_generated']}")
            print(f"   Total Employees Processed: {self.stats['total_employees_processed']}")
            print(f"   Average Processing Time: {sum(self.stats['processing_times'])/len(self.stats['processing_times']):.2f}s")

            return output_path

        except Exception as e:
            print(f"\n[ERROR] Report generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_available_gangs(self) -> List[str]:
        """Get list of available gang codes from database"""
        print("[QUERY] Getting available gang codes from database...")
        return self.query_manager.get_available_gangs()

    def generate_multi_gang_report(self, gang_codes: List[str], template_file: str = "daftar_upah_template_fixed.html",
                                     sample_data_file: str = "../large_data.json",
                                     output_prefix: str = "multi_gang") -> Dict[str, Optional[Path]]:
        """
        Generate reports for multiple gangs

        Args:
            gang_codes: List of gang codes
            template_file: Template file name
            sample_data_file: Sample data file
            output_prefix: Output file prefix

        Returns:
            Dictionary with gang codes as keys and file paths as values
        """
        print(f"[PROCESS] Generating multi-gang report for {len(gang_codes)} gangs...")

        results = {}
        total_start_time = datetime.now()

        for gang_code in gang_codes:
            print(f"\n{'='*20} Processing Gang: {gang_code} {'='*20}")

            try:
                output_file = f"{output_prefix}_{gang_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                output_path = self.generate_report_from_database(
                    gang_code=gang_code,
                    limit=100,
                    template_file=template_file,
                    sample_data_file=sample_data_file,
                    output_file=output_file
                )

                if output_path:
                    results[gang_code] = output_path
                    print(f"[OK] Report generated: {output_path.name}")
                else:
                    results[gang_code] = None
                    print(f"[ERROR] Failed to generate report for {gang_code}")

            except Exception as e:
                print(f"[ERROR] Error processing gang {gang_code}: {e}")
                results[gang_code] = None

        total_time = (datetime.now() - total_start_time).total_seconds()
        successful_reports = len([r for r in results.values() if r is not None])

        print(f"\n{'='*80}")
        print("MULTI-GANG REPORT GENERATION SUMMARY")
        print(f"{'='*80}")
        print(f"Total Gangs: {len(gang_codes)}")
        print(f"Successful Reports: {successful_reports}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Average Time per Gang: {total_time/len(gang_codes):.2f}s")

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics"""
        return {
            'stats': self.stats,
            'query_manager': {
                'query_file': self.query_manager.query_file_path,
                'database_available': True if hasattr(self.query_manager, 'connector') and self.query_manager.connector else False
            },
            'template_engine': {
                'template_dir': str(self.template_dir),
                'output_dir': str(self.output_dir)
            }
        }

    def cleanup(self):
        """Cleanup resources"""
        if self.query_manager:
            self.query_manager.cleanup()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


def main():
    """Main function for command line usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate Daftar Upah HTML Report from Database Query')
    parser.add_argument('--gang', '-g', default='H1H',
                        help='Gang code to query (default: H1H)')
    parser.add_argument('--limit', '-l', type=int, default=100,
                        help='Maximum employees to fetch (default: 100)')
    parser.add_argument('--template', '-t', default='daftar_upah_template_fixed.html',
                        help='Template file name')
    parser.add_argument('--sample-data', '-s', default='../large_data.json',
                        help='Sample data file for payroll fields')
    parser.add_argument('--output', '-o', help='Output file name')
    parser.add_argument('--multi-gang', action='store_true',
                        help='Generate reports for all available gangs')
    parser.add_argument('--list-gangs', action='store_true',
                        help='List available gang codes')

    args = parser.parse_args()

    engine = DaftarUpahTemplateEngineDatabase()

    if args.list_gangs:
        # List available gangs
        print("=" * 60)
        print("AVAILABLE GANG CODES")
        print("=" * 60)

        gangs = engine.get_available_gangs()
        if gangs:
            print(f"Found {len(gangs)} gang codes:")
            for i, gang in enumerate(gangs, 1):
                count = engine.query_manager.get_employee_count_by_gang(gang)
                print(f"  {i}. {gang} ({count} employees)")
        else:
            print("No gang codes found")
            print("This could mean:")
            print("- Database is not connected")
            print("- No employees are assigned to gangs")
            print("- HR_GANGLN table is empty")

    elif args.multi_gang:
        # Generate reports for all gangs
        gangs = engine.get_available_gangs()
        if gangs:
            print(f"Generating reports for {len(gangs)} gangs: {', '.join(gangs)}")
            results = engine.generate_multi_gang_report(gangs, args.template, args.sample_data, args.output)

            print(f"\nReport generation completed for {len(gangs)} gangs")
            for gang, file_path in results.items():
                if file_path:
                    print(f"  {gang}: {file_path.name}")
                else:
                    print(f"  {gang}: Failed")

    else:
        # Generate single gang report
        result = engine.generate_report_from_database(
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


if __name__ == "__main__":
    main()