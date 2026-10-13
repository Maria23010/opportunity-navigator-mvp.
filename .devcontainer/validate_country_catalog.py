"""Validate Opportunity Navigator country packs without Streamlit or external libraries.
Run from the repository: python validate_country_catalog.py
"""
from pathlib import Path
from urllib.parse import urlparse
import json

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'universities_catalog.json').read_text(encoding='utf-8'))
COUNTRY_DIR = ROOT / 'country_databases'
REQUESTED = {'BN','GB','HU','HK','CN','IT','CA','QA','RO','US','SG','TR','KR','JP'}


def assert_references(tree, all_sources):
    if isinstance(tree, dict):
        for key, val in tree.items():
            if key == 'source_ids':
                assert isinstance(val, list), 'source_ids must be a list'
                for source_id in val:
                    assert source_id in all_sources, 'Missing source: ' + source_id
            else:
                assert_references(val, all_sources)
    elif isinstance(tree, list):
        for val in tree:
            assert_references(val, all_sources)


def main():
    assert DATA['schema_version'] == '1.0'
    assert {f.stem for f in COUNTRY_DIR.glob('*.json')} == REQUESTED
    profiles = DATA['profiles'].copy()
    sources = DATA['sources'].copy()
    entries = {e['id']:e for e in DATA['entries']}
    countries = {c['code']: c for c in DATA['countries']}
    assert len(entries) == len(DATA['entries']), 'Duplicate IDs in consolidated JSON'
    for path in sorted(COUNTRY_DIR.glob('*.json')):
        country_pack = json.loads(path.read_text(encoding='utf-8'))
        code = country_pack['country']['code']
        assert path.stem == code
        assert code in countries
        profiles.update(country_pack['profiles'])
        sources.update(country_pack['sources'])
        assert len({e['id'] for e in country_pack['entries']}) == len(country_pack['entries'])
        assert set(country_pack['country']['entry_ids']) == {e['id'] for e in country_pack['entries']}
        for row in country_pack['entries']:
            assert row['country_code'] == code
            assert row['admission_stage'] == 'first_degree_after_school'
            entries[row['id']] = row
    for source in sources.values():
        uri = urlparse(source['url'])
        assert uri.scheme == 'https' and uri.netloc, source
    assert_references(list(entries.values()), sources)
    assert_references(list(profiles.values()), sources)
    for ent in entries.values():
        assert ent['profile_id'] in profiles, ent['id']
        assert ent['country_code'] in countries, ent['id']
        for course in ent['programs']:
            assert course.get('profile_id',ent['profile_id']) in profiles, ent['id']
            assert course['field_ids'], ent['id']
            if ent.get('record_status') == 'discovery_only':
                assert profiles[ent['profile_id']]['funding']['category'] == 'unverified', ent['id']
    print('PASS:',len(REQUESTED),'country packs,',len(entries),'records,',
          sum(e['kind']=='university' for e in entries.values()),'universities,',
          sum(len(e['programs']) for e in entries.values()),'programme/subject records')
    print('Reminder: file validation is NOT a verification of each university requirement or the Streamlit UI.')

if __name__=='__main__':
    main()
