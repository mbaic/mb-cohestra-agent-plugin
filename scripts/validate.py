#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
errors=[]
def fail(x): errors.append(x)
def fm(path):
    t=path.read_text(encoding='utf-8')
    if not t.startswith('---\n') or len(t.split('---\n',2)) != 3:
        fail(f'Invalid frontmatter: {path.relative_to(ROOT)}'); return ''
    return t.split('---\n',2)[1]
manifest=json.loads((ROOT/'plugin.json').read_text())
if manifest.get('$schema')!='https://agent-plugins.org/schemas/1.0.0/plugin.schema.json': fail('Wrong schema')
if manifest.get('name')!='multi-agent-review-coordinator': fail('Wrong plugin name')
if manifest.get('version')!='4.0.0': fail('Wrong version')
agents=sorted((ROOT/'com.github.copilot/agents').glob('*.agent.md'))
if len(agents)!=7: fail(f'Expected 7 agents, found {len(agents)}')
for p in agents:
    h=fm(p)
    if re.search(r'^target:',h,re.M): fail(f'Target must be omitted: {p.name}')
    if re.search(r'^model:',h,re.M): fail(f'Model must be omitted: {p.name}')
coord=ROOT/'com.github.copilot/agents/coordinator.agent.md'
h=fm(coord)
if 'user-invocable: true' not in h: fail('Coordinator must be user-invocable')
if 'disable-model-invocation: true' not in h: fail('Coordinator must not be a subagent')
if 'agents:' not in h: fail('Coordinator needs specialist allowlist')
for p in agents:
    if p==coord: continue
    h=fm(p)
    if 'user-invocable: false' not in h: fail(f'Specialist visible: {p.name}')
    if 'disable-model-invocation: false' not in h: fail(f'Specialist unavailable: {p.name}')
    if 'agents: []' not in h: fail(f'Specialist can delegate: {p.name}')
for forbidden in (ROOT/'hooks',ROOT/'com.github.copilot/hooks',ROOT/'mcp.json'):
    if forbidden.exists(): fail(f'Forbidden component: {forbidden.relative_to(ROOT)}')
for p in ROOT.rglob('*.json'): json.loads(p.read_text())
if errors:
    print('Validation failed:'); [print('- '+e) for e in errors]; sys.exit(1)
print('Validation passed: Coordinator visible; 6 specialists hidden and callable; no hooks or MCP server.')
