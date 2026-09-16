"""Regression checks for lost topics, moved positions, citation scope and output links."""
import copy
import tempfile
import unittest
from pathlib import Path
from validate import validate_data, validate_markdown, markdown_anchors

ENTRY=dict(id='au-01-01',title='Check the alarm',jurisdiction='NSW',applies_to='Residents',action='Check the alarm',steps=[],cost='Time',benefit='Early warning',caveats='Leave the building in a fire',evidence_type='Official guidance',evidence_grade='规则',references='',sources=['O0101','H001'],reviewed_on='2026-09-16')
SOURCE=dict(id='H001',title='Alarms',publisher='Fire service',url='https://example.gov.au/alarms',accessed_on='2026-09-16',verification='full_page',supports='Explains alarm testing')
ORIGINAL=dict(id='O0101',title='Original item 1.1',publisher='Original author',url='https://github.com/example/book/blob/commit/book/01.md',accessed_on='2026-09-16',verification='upstream_citation',supports='Original topic and bibliography, not independent paper verification')
BASE=dict(chapters=[dict(number=1,title='Safety',summary='Act early',entries=[ENTRY])],sources=[SOURCE,ORIGINAL],mapping=[dict(original_chapter=1,original_item=1,original_title='Original',action='adapt',target_ids=['au-01-01'],reason='Replace with NSW guidance')])
UPSTREAM=[dict(chapter=1,item=1,title='Original',path='book/01-Safety.md')]

class ProvenanceGate(unittest.TestCase):
    def rejected(self,data,fragment):
        self.assertTrue(any(fragment in error for error in validate_data(data,UPSTREAM)),validate_data(data,UPSTREAM))

    def test_complete_release_and_visible_instructions_allow_empty_steps(self):
        self.assertEqual(validate_data(copy.deepcopy(BASE),UPSTREAM),[])

    def test_unresolvable_citation(self):
        d=copy.deepcopy(BASE);d['chapters'][0]['entries'][0]['sources'].append('MISSING');self.rejected(d,'MISSING')

    def test_missing_mapping(self):
        d=copy.deepcopy(BASE);d['mapping']=[];self.rejected(d,'1:1')

    def test_duplicate_mapping(self):
        d=copy.deepcopy(BASE);d['mapping']*=2;self.rejected(d,'duplicate mapping')

    def test_nonexistent_target(self):
        d=copy.deepcopy(BASE);d['mapping'][0]['target_ids']=['au-99-99'];self.rejected(d,'missing target')

    def test_unsafe_source_url(self):
        d=copy.deepcopy(BASE);d['sources'][0]['url']='javascript:alert(1)';self.rejected(d,'URL')

    def test_sourceless_entry(self):
        d=copy.deepcopy(BASE);d['chapters'][0]['entries'][0]['sources']=[];self.rejected(d,'sources')

    def test_no_merge_or_omit_even_with_reason(self):
        for action in ('merge','omit'):
            d=copy.deepcopy(BASE);d['mapping'][0]['action']=action;self.rejected(d,'not allowed')

    def test_missing_mapping_reason(self):
        d=copy.deepcopy(BASE);d['mapping'][0]['reason']='';self.rejected(d,'reason')

    def test_search_snippet_is_not_verified(self):
        d=copy.deepcopy(BASE);d['sources'][0]['verification']='search_snippet';self.rejected(d,'verification')

    def test_wrong_chapter(self):
        d=copy.deepcopy(BASE);d['chapters'][0]['number']=2;self.rejected(d,'chapter mismatch')

    def test_missing_release_chapter(self):
        self.assertTrue(any('chapter set' in e for e in validate_data(copy.deepcopy(BASE),UPSTREAM,range(1,3))))

    def test_nontext_content(self):
        for key,value in [('steps',[{}]),('action',{'draft':'unfinished'}),('references',None)]:
            d=copy.deepcopy(BASE);d['chapters'][0]['entries'][0][key]=value;self.rejected(d,key)

    def test_original_source_cannot_claim_independent_reading(self):
        d=copy.deepcopy(BASE);d['sources'][1]['verification']='full_page';self.rejected(d,'independent verification')

    def test_original_provenance_required(self):
        d=copy.deepcopy(BASE);d['chapters'][0]['entries'][0]['sources']=['H001'];self.rejected(d,'original provenance')

    def test_same_topic_cannot_move_position(self):
        d=copy.deepcopy(BASE);d['chapters'][0]['entries'][0]['id']='au-01-02';self.rejected(d,'count or order')

    def test_entry_omission_cannot_hide_behind_mapping(self):
        d=copy.deepcopy(BASE);d['chapters'][0]['entries']=[];self.rejected(d,'count or order')

    def test_extra_question_cannot_change_original_count(self):
        d=copy.deepcopy(BASE);e=copy.deepcopy(ENTRY);e['id']='au-01-02';d['chapters'][0]['entries'].append(e);self.rejected(d,'count or order')

    def test_mapping_must_have_exactly_one_same_position_target(self):
        d=copy.deepcopy(BASE);d['mapping'][0]['target_ids']*=2;self.rejected(d,'original position')

    def test_bad_evidence_grade(self):
        d=copy.deepcopy(BASE);d['chapters'][0]['entries'][0]['evidence_grade']='certain';self.rejected(d,'evidence grade')

    def test_explicit_and_github_heading_anchors(self):
        text='<a id="au-01-01"></a>\n# 怎么读\n# 怎么读\n```\n# not-an-anchor\n```'
        self.assertEqual(markdown_anchors(text),{'au-01-01','怎么读','怎么读-1'})

    def test_bad_local_fragment_and_wrong_filename_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'book').mkdir();(root/'sources').mkdir()
            (root/'sources/README.md').write_text('# Sources\n',encoding='utf-8')
            (root/'book/wrong.md').write_text('[bad](../sources/README.md#missing)',encoding='utf-8')
            errors,count=validate_markdown(root,BASE,UPSTREAM)
            self.assertEqual(count,1)
            self.assertTrue(any('filenames' in e for e in errors))
            self.assertTrue(any('broken anchor' in e for e in errors))

if __name__=='__main__': unittest.main()
