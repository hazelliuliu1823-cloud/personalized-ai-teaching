#!/usr/bin/env python3
"""Static integrity checks for one plugin package (no model or platform claims)."""
from __future__ import annotations
import hashlib, json, pathlib, re, sys, tempfile, zipfile

BASELINE_HASHES = {
    'ai-era-teaching-methods.md': '8cc1f90ea74238b46b208df38bf9df27c17511326f127924654dc4364b29251e',
    'fundamental-education.md': '2e179581a14909534dc4af7f493900728b6f37777b6d00cca61528ba369dfde3',
    'method-extraction.md': '8173c91cbe93fb63b468b1a6ed4c31993dafdb83d6fdef31cd47d09e9bf22bb2',
}

def sha(path:pathlib.Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def derive_shards(text: str) -> dict[int, str]:
    """Parse method chapters as *data*; never execute code supplied by archive."""
    heads=list(re.finditer(r'^## M([1-5])｜[^\n]*$',text,re.M))
    tail=re.search(r'^## 02｜',text,re.M)
    if [int(h.group(1)) for h in heads] != [1,2,3,4,5] or not tail or tail.start() <= heads[-1].start():
        raise ValueError('Unexpected method chapter structure: M1–M5 / 02')
    return {i+1: text[h.start():heads[i+1].start() if i < 4 else tail.start()] for i,h in enumerate(heads)}

def check(root:pathlib.Path)->list[str]:
    bad=[]
    def required(path):
        p=root/path
        if not p.is_file():bad.append(f'missing: {path}')
        return p
    manifest_root=required('plugin.json')
    manifest_codex=required('.codex-plugin/plugin.json')
    if bad:return bad
    try:
        a=json.loads(manifest_root.read_text(encoding='utf-8'))
        b=json.loads(manifest_codex.read_text(encoding='utf-8'))
    except (ValueError,UnicodeError) as ex:
        return [f'invalid plugin manifest: {ex}']
    for k in ('name','version','description','license'):
        if a.get(k)!=b.get(k):bad.append('manifests disagree on '+k)
    slug=a.get('name','')
    ver=a.get('version','')
    if not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*',slug):bad.append('invalid plugin slug')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?',ver):bad.append('invalid semver')
    if a.get('license')!='MIT':bad.append('MIT not declared in both manifests')
    interface_a=a.get('extensions',{}).get('com.openai',{}).get('interface',{})
    interface_b=b.get('interface',{})
    for field in ('displayName','defaultPrompt','shortDescription','longDescription'):
        if interface_a.get(field)!=interface_b.get(field):bad.append('interface manifest mismatch: '+field)
    skill_candidates=[p for p in (root/'skills').glob('*/SKILL.md') if p.is_file()]
    if len(skill_candidates)!=1:
        return bad+['expected exactly one Skill entry; found '+str(len(skill_candidates))]
    skill=skill_candidates[0].parent
    skill_slug=skill.name
    required('README.md');required('PACKAGE_MANIFEST.json')
    for path in ['SKILL.md','agents/openai.yaml','assets/icon.svg','LICENSE',
                 'references/ai-era-teaching-methods.md','references/fundamental-education.md',
                 'references/interaction-router.md','references/method-extraction.md',
                 'references/family-methods.md','references/evaluation.md',
                 'references/parent-prompt.md','references/parent-prompt-medium.txt',
                 'tests/cases.json','tests/validate_package.py']:
        required(f'skills/{skill_slug}/{path}')
    required('LICENSE'); required('assets/icon.svg');required('tools/generate_ai_era_shards.py')
    if bad:return bad
    if (root/'LICENSE').read_bytes()!=(skill/'LICENSE').read_bytes():bad.append('two license files differ')
    if 'MIT License' not in (root/'LICENSE').read_text(encoding='utf-8'):bad.append('not MIT license text')
    expected_author=a.get('author',{}).get('name','')
    if not expected_author or f'Copyright (c) 2026 {expected_author}' not in (root/'LICENSE').read_text(encoding='utf-8'):
        bad.append('copyright attribution differs from plugin author')

    spec=(skill/'SKILL.md').read_text(encoding='utf-8')
    frontmatter=re.match(r'\A---\n(.*?)\n---',spec,re.S)
    if not frontmatter:bad.append('missing skill frontmatter')
    elif not re.search(r'^name:\s*'+re.escape(skill_slug)+r'\s*$',frontmatter.group(1),re.M):
        bad.append('skill name differs from manifest name')
    if interface_a.get('displayName','') not in spec:bad.append('displayName missing from SKILL title')
    yaml=(skill/'agents/openai.yaml').read_text(encoding='utf-8')
    if 'allow_implicit_invocation: false' not in yaml or 'allow_implicit_invocation: true' in yaml:
        bad.append('implicit invocation should be disabled')
    if f'${skill_slug}' not in yaml:bad.append('agent prompt does not call declared Skill ID')
    if f'display_name: {interface_a.get("displayName", "-missing-")}' not in yaml:
        bad.append('agent display_name mismatch')

    # Check file references, not literal phrases or exact authoring expressions.
    refnames=set(re.findall(r'`references/([^`\n]+?\.(?:md|txt))`',spec))
    for name in refnames:
        if not (skill/'references'/name).is_file():bad.append('broken SKILL reference: '+name)
    refs=skill/'references'
    for name,expected in BASELINE_HASHES.items():
        if sha(refs/name)!=expected:bad.append('locked baseline changed: '+name)
    # Parse the method chapters as data; do not execute scripts from the package.
    f=(refs/'ai-era-teaching-methods.md').read_text(encoding='utf-8')
    try:
        shards=derive_shards(f)
        for i,expected_text in shards.items():
            target=required(f'skills/{skill_slug}/references/ai-era-m{i}.md')
            if target.is_file() and target.read_text(encoding='utf-8')!=expected_text:
                bad.append(f'method shard differs from full methods baseline: M{i}')
    except ValueError as ex:
        bad.append('method shard parse failed: '+str(ex))
    if f.count('**教学转译**')!=5:bad.append('method layer missing teaching translations')
    if f.count('**低年级示范')!=5 or f.count('**高中 AI 实践示范')!=5:bad.append('method dual cases incomplete')
    fundamental=(refs/'fundamental-education.md').read_text(encoding='utf-8')
    for name in ('F1｜清晰讲解与示范','F2｜自适应帮助与逐步撤架','儿童保护'):
        if name not in fundamental:bad.append('fundamental missing: '+name)
    prompt=(refs/'parent-prompt-medium.txt').read_text(encoding='utf-8')
    if not 1000 <= len(re.sub(r'\s','',prompt)) <= 1500:bad.append('parent medium prompt not 1000-1500 chars')
    try:
        tests=json.loads((skill/'tests/cases.json').read_text(encoding='utf-8'))
    except ValueError as ex:
        return bad+[f'invalid cases JSON: {ex}']
    if tests.get('schema_version')!=ver:bad.append('case schema version mismatch')
    cases=tests.get('cases',[])
    ids=[x.get('id') for x in cases]
    if len(cases)<25 or len(ids)!=len(set(ids)):bad.append('cases absent or duplicate ids')
    for caseid in ('router_new_problem','router_same_problem_no_reload','router_unexpected_feedback','router_method_switch','shard_recovery_concrete_action','topic_switch_offtopic','topic_switch_return'):
        if caseid not in ids:bad.append('missing behavior case: '+caseid)
    if not all('expectation' in x and 'input' in x for x in cases):bad.append('case input/expectation incomplete')
    router_text=(refs/'interaction-router.md').read_text(encoding='utf-8')
    if not all(s in router_text for s in ('ai-era-m1.md','ai-era-m5.md','面向孩子的具体转译','反馈分支','新题/新学习任务')):
        bad.append('Router missing event triggers / translation / shard lookup')
    if not all(s in (refs/'method-extraction.md').read_text(encoding='utf-8') for s in ('P0｜','P6｜')):
        bad.append('P0–P6 extraction phases incomplete')
    try:
        family=(refs/'family-methods.md').read_text(encoding='utf-8')
        templ=json.loads(re.search(r'```json\n(.*?)\n```',family,re.S).group(1))
        if len(templ['methods'][0]['examples'])!=2:bad.append('family dual examples missing')
    except Exception as ex:bad.append('family schema invalid: '+str(ex))
    for raw in root.rglob('*'):
        if raw.is_file() and raw.suffix.lower() in ('.mp3','.mp4','.aac','.m4a','.pdf','.docx'):
            bad.append('unexpected raw media/file: '+str(raw.relative_to(root)))
    pkg=json.loads((root/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    actual={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and p.name!='PACKAGE_MANIFEST.json'}
    expected={x['path']:x['sha256'] for x in pkg.get('files',[])}
    if pkg.get('name')!=slug or pkg.get('version')!=ver or pkg.get('file_count_excluding_manifest')!=len(actual) or actual!=expected:
        bad.append('package manifest hash/name/version/count mismatch')
    return bad

def main():
    path=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
    if path.is_file() and path.suffix.lower()=='.zip':
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(path) as z:
                for name in z.namelist():
                    if name.startswith('/') or '..' in pathlib.PurePosixPath(name).parts:raise ValueError('unsafe archive path: '+name)
                z.extractall(tmp)
            bad=check(pathlib.Path(tmp))
    else:bad=check(path)
    if bad:
        print('FAIL');print('\n'.join(' - '+x for x in bad));return 1
    print('PASS: manifest symmetry, dynamic version, inert method shard check, baseline hashes, paths, MIT, tests and package integrity')
    return 0

if __name__=='__main__':sys.exit(main())
