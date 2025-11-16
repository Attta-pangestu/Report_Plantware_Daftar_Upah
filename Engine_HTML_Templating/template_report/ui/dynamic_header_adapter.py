import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from daftar_upah_engine_real_database import DaftarUpahEngineRealFixed


class DynamicHeaderAdapter:
    def __init__(self, json_path: str):
        self.json_path = Path(json_path)
        self.spec = self._load_json(self.json_path)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_premi_level2_texts(self) -> List[str]:
        columns = self.spec.get('table_structure', {}).get('hierarchy', {}).get('level_2', {}).get('columns', [])
        texts = []
        for col in columns:
            if col.get('parent') == 'premi':
                txt = col.get('text')
                if isinstance(txt, str):
                    texts.append(txt.strip())
        return texts

    def compute_dynamic_headers(self, month: int, year: int, gang_code: Optional[str] = None, limit: int = 100) -> List[str]:
        engine = DaftarUpahEngineRealFixed(month=f"{month:02d}", year=str(year))
        employees = engine.query_manager.get_employees_by_gang(gang_code or 'H1H', limit)
        merged = engine.merge_employee_with_cuti_data(employees, engine.month_name, str(engine.year))
        base = engine.get_dynamic_premi_headers(engine.month, engine.year)
        filtered = engine.filter_dynamic_headers_by_nonzero(base, merged, engine.month, engine.year)
        if not filtered:
            return base[:5]
        return filtered[:5]

    def apply_dynamic_premi_to_html(self, html: str, dynamic_headers: List[str]) -> str:
        fixed_prefix = ['BRONDOL', 'PRUNING']
        premi_texts = self.get_premi_level2_texts()
        replaceable = []
        for t in premi_texts:
            if t not in fixed_prefix and 'KOREKSI' not in t.upper():
                replaceable.append(t)

        result = html
        for i, static_text in enumerate(replaceable):
            if i < len(dynamic_headers):
                dyn = dynamic_headers[i]
                result = result.replace(f">{static_text}<", f">{dyn}<")
            else:
                result = result.replace(f">{static_text}<", ">&nbsp;<")
        return result


def run(gang_code: str, month: int, year: int, template_file: str, json_path: str) -> Path:
    engine = DaftarUpahEngineRealFixed(month=f"{month:02d}", year=str(year))
    output_path = engine.generate_report_from_real_database(gang_code=gang_code, limit=100, template_file=template_file, output_file=None)
    if not output_path:
        raise RuntimeError('Failed to generate base report HTML')

    adapter = DynamicHeaderAdapter(json_path)
    dynamic_headers = adapter.compute_dynamic_headers(month, year, gang_code)

    with open(output_path, 'r', encoding='utf-8') as f:
        html = f.read()

    html_updated = adapter.apply_dynamic_premi_to_html(html, dynamic_headers)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    final_name = f"daftar_upah_gang_{gang_code}_real_dynamic_{timestamp}.html"
    final_path = Path(output_path).parent / final_name

    with open(final_path, 'w', encoding='utf-8') as f:
        f.write(html_updated)

    return final_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gang', default='H1H')
    parser.add_argument('--month', type=int, default=5)
    parser.add_argument('--year', type=int, default=2025)
    parser.add_argument('--template', default='daftar_upah_template_final.html')
    parser.add_argument('--json', default='D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Engine_HTML_Templating/template_report/struktur_header_report.json')
    args = parser.parse_args()

    out = run(args.gang, args.month, args.year, args.template, args.json)
    print(str(out))
