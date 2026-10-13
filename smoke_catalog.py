"""Integration smoke-test without installing Streamlit; extracts pure functions from app.py.
Validates real loader/merging and 46 field search.
"""
from pathlib import Path
import sys,json,os,ast
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from program_search import FIELDS,match_programmes
functions={'load_universities_catalog','catalog_filter','catalog_candidates','catalog_exam_rows'}
tree=ast.parse((ROOT/'app.py').read_text(encoding='utf-8'))
subset=ast.Module(body=[fn for fn in tree.body if isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef)) and fn.name in functions], type_ignores=[])
namespace={'json':json,'os':os,'urlparse':urlparse,'match_programmes':match_programmes}
exec(compile(subset,'app.py (catalog-only)','exec'),namespace)
D=namespace['load_universities_catalog'](str(ROOT/'universities_catalog.json'))
assert len(D['countries'])==19
assert D['scope']['university_count']==183
assert len(list((ROOT/'country_databases').glob('*.json')))==19
for key,(_,aliases) in FIELDS.items():
    term=aliases.split('|')[0]
    matches,_=namespace['catalog_candidates'](D,'all','all',term,'university')
    exact=[e for e in matches if e['match_type']=='exact']
    assert exact, f'Missing global search category {key}'
for code in ('AE','KZ','RU'):
    for field in ('computer','data'):
        matches,_=namespace['catalog_candidates'](D,code,'all',FIELDS[field][1].split('|')[0],'university')
        assert any(e['match_type']=='exact' for e in matches),(code,field)
spbu=next(e for e in D['entries'] if e['id']=='ru_spbu')
assert any(pr['name'].startswith('AI360:') and any(ex.get('score') for ex in D['profiles'][pr['profile_id']]['exams']) for pr in spbu['programs'])
aitu=next(e for e in D['entries'] if e['id']=='kz_aitu')
pr=next(pr for pr in aitu['programs'] if pr['name']=='Software Engineering')
assert any(ex.get('score')==100 for ex in D['profiles'][pr['profile_id']]['exams'])
assert any(e['name']=='New York University Abu Dhabi (NYUAD)' for e in D['entries'] if e['country_code']=='AE')
print('SMOKE PASS:',len(FIELDS),'categories all find a university, 19 merged packs, specific exams for SPBU/KZ, UAE added; not Streamlit browser test')
