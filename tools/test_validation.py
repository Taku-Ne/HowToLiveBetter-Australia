"""Publication gates: broken provenance and silent omissions must block a release."""
import copy
import unittest
from validate import validate_data

ENTRY = dict(id='au-01-01', title='Smoke alarm', jurisdiction='NSW', applies_to='Residents',
             action='Check the alarm', steps=['Follow the device instructions'], cost='Time',
             benefit='Early warning', caveats='Leave the building in a fire',
             evidence_type='Official guidance', sources=['H001'], reviewed_on='2026-09-16')
SOURCE = dict(id='H001', title='Alarms', publisher='Fire service', url='https://example.gov.au/alarms',
              accessed_on='2026-09-16', verification='full_page', supports='Explains alarm testing')
BASE = dict(chapters=[dict(number=1, title='Safety', summary='Act early', entries=[ENTRY])],
            sources=[SOURCE], mapping=[dict(original_chapter=1,original_item=1,original_title='Original',
            action='adapt',target_ids=['au-01-01'],reason='Replace with NSW guidance')])
UPSTREAM = [dict(chapter=1,item=1,title='Original')]

class ProvenanceGate(unittest.TestCase):
    def test_complete_small_release_is_allowed(self):
        self.assertEqual(validate_data(copy.deepcopy(BASE), UPSTREAM), [])

    def test_unresolvable_citation_is_rejected(self):
        d=copy.deepcopy(BASE); d['chapters'][0]['entries'][0]['sources']=['MISSING']
        self.assertTrue(any('MISSING' in e for e in validate_data(d,UPSTREAM)))

    def test_missing_upstream_item_is_rejected(self):
        d=copy.deepcopy(BASE); d['mapping']=[]
        self.assertTrue(any('1:1' in e for e in validate_data(d,UPSTREAM)))

    def test_duplicate_mapping_cannot_hide_omission(self):
        d=copy.deepcopy(BASE); d['mapping']*=2
        self.assertTrue(any('duplicate mapping' in e for e in validate_data(d,UPSTREAM)))

    def test_mapping_to_nonexistent_advice_is_rejected(self):
        d=copy.deepcopy(BASE); d['mapping'][0]['target_ids']=['au-99-99']
        self.assertTrue(any('au-99-99' in e for e in validate_data(d,UPSTREAM)))

    def test_unsafe_citation_url_is_rejected(self):
        d=copy.deepcopy(BASE); d['sources'][0]['url']='javascript:alert(1)'
        self.assertTrue(any('URL' in e for e in validate_data(d,UPSTREAM)))

    def test_sourceless_recommendation_is_rejected(self):
        d=copy.deepcopy(BASE); d['chapters'][0]['entries'][0]['sources']=[]
        self.assertTrue(any('sources' in e for e in validate_data(d,UPSTREAM)))

    def test_omission_needs_an_explanation(self):
        d=copy.deepcopy(BASE); d['mapping'][0].update(action='omit',target_ids=[],reason='')
        self.assertTrue(any('reason' in e for e in validate_data(d,UPSTREAM)))

    def test_search_snippet_cannot_pass_as_verified_source(self):
        d=copy.deepcopy(BASE); d['sources'][0]['verification']='search_snippet'
        self.assertTrue(any('verification' in e for e in validate_data(d,UPSTREAM)))

    def test_entry_cannot_silently_move_to_wrong_chapter(self):
        d=copy.deepcopy(BASE); d['chapters'][0]['number']=2
        self.assertTrue(any('chapter mismatch' in e for e in validate_data(d,UPSTREAM)))

    def test_full_release_cannot_omit_a_required_chapter(self):
        self.assertTrue(any('chapter set' in e for e in validate_data(copy.deepcopy(BASE),UPSTREAM,expected_chapters={1,2})))

    def test_structured_objects_cannot_be_published_as_body_text(self):
        for field,value in [('steps',[{}]),('action',{'draft':'unfinished'})]:
            d=copy.deepcopy(BASE); d['chapters'][0]['entries'][0][field]=value
            self.assertTrue(any(field in e for e in validate_data(d,UPSTREAM)))

if __name__=='__main__': unittest.main()
