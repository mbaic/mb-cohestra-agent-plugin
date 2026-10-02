import json, re, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
    def test_identity(self):
        d=json.loads((ROOT/'plugin.json').read_text())
        self.assertEqual(d['name'],'multi-agent-review-coordinator')
        self.assertEqual(d['version'],'4.0.0')
    def test_visibility_and_delegation(self):
        files=list((ROOT/'com.github.copilot/agents').glob('*.agent.md'))
        self.assertEqual(len(files),7)
        for p in files:
            h=p.read_text().split('---\n',2)[1]
            if p.name=='coordinator.agent.md':
                self.assertIn('user-invocable: true',h)
                self.assertIn('disable-model-invocation: true',h)
                self.assertIn('agents:',h)
            else:
                self.assertIn('user-invocable: false',h)
                self.assertIn('disable-model-invocation: false',h)
                self.assertIn('agents: []',h)
    def test_no_old_runtime_ids(self):
        manifest = (ROOT / 'plugin.json').read_text()
        marketplace = (ROOT / '.github/plugin/marketplace.json').read_text()
        self.assertNotIn('agent-review-suite', manifest)
        self.assertNotIn('agent-review-suite', marketplace)
        self.assertFalse((ROOT / 'com.github.copilot/agents/orchestrator.agent.md').exists())
        self.assertTrue((ROOT / 'com.github.copilot/agents/coordinator.agent.md').exists())
    def test_no_hooks_or_mcp(self):
        self.assertFalse((ROOT/'hooks').exists())
        self.assertFalse((ROOT/'com.github.copilot/hooks').exists())
        self.assertFalse((ROOT/'mcp.json').exists())
if __name__=='__main__': unittest.main()
