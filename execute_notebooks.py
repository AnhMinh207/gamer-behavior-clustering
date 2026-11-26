"""Chạy notebook bằng kernel mới, lưu output thật và đối chiếu kết quả với báo cáo.

Chạy cả bộ: python execute_notebooks.py
Chỉ bản tổng hợp: python execute_notebooks.py --only-main
Không cần đăng ký kernel vào thư mục người dùng hoặc chạy jupyter server.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'outputs' / 'notebook' / ('validation_' + uuid.uuid4().hex[:10])
os.environ.setdefault('IPYTHONDIR', str(WORK / '.ipython'))
os.environ.setdefault('JUPYTER_RUNTIME_DIR', str(WORK / '.runtime'))
os.environ.setdefault('MPLCONFIGDIR', str(WORK / '.matplotlib'))

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager


def output_fingerprints():
    # Không đưa scratch notebook vào kiểm tra bất biến của bộ kết quả báo cáo.
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / 'outputs').rglob('*')
            if p.is_file() and not any(part in {'notebook', '.mplconfig'} for part in p.relative_to(ROOT).parts)
            and p.name != 'notebook_verification.json'}


def execute(path, workspace):
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            cell.outputs = []
            cell.execution_count = None
    manager = KernelManager(kernel_name='python3')
    # Dùng chính interpreter chạy script, kể cả máy có nhiều Python/kernel khác nhau.
    manager.kernel_spec.argv[0] = sys.executable
    kernel_env = os.environ.copy()
    kernel_env['GAMER_NOTEBOOK_OUTPUT'] = str(workspace)
    start = time.perf_counter()
    print(f'RUN {path.name}', flush=True)
    client = NotebookClient(notebook, km=manager, timeout=600, startup_timeout=120,
                            allow_errors=False, resources={'metadata': {'path': str(ROOT)}})
    try:
        executed = client.execute(env=kernel_env)
    finally:
        # NotebookClient không sở hữu kernel manager được truyền vào nên dọn rõ ràng.
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
        manager.cleanup_resources()
    nbformat.validate(executed)
    code_cells = [c for c in executed.cells if c.cell_type == 'code']
    assert all(c.execution_count is not None for c in code_cells), 'Có ô code chưa chạy.'
    assert not any(o.output_type == 'error' for c in code_cells for o in c.outputs), 'Có output lỗi.'
    image_count = sum('image/png' in o.get('data', {}) for c in code_cells for o in c.outputs)
    table_count = sum('text/html' in o.get('data', {}) for c in code_cells for o in c.outputs)
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        nbformat.write(executed, stream)
    result = {'file': path.name, 'code_cells': len(code_cells), 'images': image_count,
              'html_outputs': table_count, 'seconds': round(time.perf_counter() - start, 2),
              'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    print(f'PASS {path.name}: {len(code_cells)} code cells, {image_count} plots', flush=True)
    return result


def main(only_main=False):
    WORK.mkdir(parents=True, exist_ok=True)
    baseline = output_fingerprints()
    main_path = ROOT / 'notebooks' / '00_Gamer_Behavior_Clustering.ipynb'
    results = [execute(main_path, WORK / 'full')]
    full = json.loads((WORK / 'full' / 'verification.json').read_text(encoding='utf-8'))
    assert full['passed']
    if not only_main:
        # Kernel mới cho mỗi file; scratch khác bản tổng hợp để không vô tình tái dùng tệp của 00.
        for path in sorted((ROOT / 'notebooks').glob('*.ipynb')):
            if path.name != main_path.name:
                results.append(execute(path, WORK / 'modular'))
        modular = json.loads((WORK / 'modular' / 'verification.json').read_text(encoding='utf-8'))
        assert modular['passed']
    assert baseline == output_fingerprints(), 'Bộ kết quả báo cáo bị thay đổi.'
    report = {'passed': True, 'interpreter_version': sys.version.split()[0],
              'all_requested_notebooks_executed': True, 'mode': 'main_only' if only_main else 'all_nine',
              'fresh_kernel_per_notebook': True, 'separate_full_and_modular_workspace': True,
              'original_report_outputs_unchanged': True,
              'numerical_agreement': full['checks'], 'notebooks': results}
    (ROOT / 'outputs' / 'notebook_verification.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print('PASS: notebook chạy được từ kernel mới; số liệu khớp báo cáo; outputs gốc không thay đổi.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only-main', action='store_true')
    main(parser.parse_args().only_main)
