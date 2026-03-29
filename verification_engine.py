import ast
from datetime import datetime
from vulnerability_detector import VulnerabilityModule


class VerificationEngine:
    """
    Verifies that healed code is:
      1. Syntactically valid Python
      2. Free of all originally detected vulnerabilities
      3. Compilable (no runtime-level errors)
    Returns structured results used by the agentic loop.
    """

    def __init__(self, original_code: str, healed_code: str):
        self.original = original_code
        self.healed = healed_code
        self.results = {}
        self.passed = False

    # ── Check 1: Syntax ──────────────────────────────────────────────────────
    def verify_syntax(self) -> bool:
        try:
            ast.parse(self.healed)
            self.results['syntax'] = {
                'passed': True,
                'message': 'Valid Python syntax'
            }
            return True
        except SyntaxError as e:
            self.results['syntax'] = {
                'passed': False,
                'message': f'SyntaxError at line {e.lineno}: {e.msg}'
            }
            return False

    # ── Check 2: Vulnerability scan ──────────────────────────────────────────
    def verify_vulnerabilities(self) -> bool:
        try:
            tree = ast.parse(self.healed)
            detector = VulnerabilityModule()
            detector.visit(tree)

            remaining = detector.reports
            if not remaining:
                self.results['vulnerabilities'] = {
                    'passed': True,
                    'message': 'All vulnerabilities resolved',
                    'remaining': []
                }
                return True
            else:
                self.results['vulnerabilities'] = {
                    'passed': False,
                    'message': f'{len(remaining)} vulnerability/vulnerabilities still present',
                    'remaining': remaining
                }
                return False
        except Exception as e:
            self.results['vulnerabilities'] = {
                'passed': False,
                'message': f'Scan error: {str(e)}',
                'remaining': []
            }
            return False

    # ── Check 3: Compile test ────────────────────────────────────────────────
    def verify_compilable(self) -> bool:
        try:
            compile(self.healed, '<healed_code>', 'exec')
            self.results['compilable'] = {
                'passed': True,
                'message': 'Code compiles successfully'
            }
            return True
        except Exception as e:
            self.results['compilable'] = {
                'passed': False,
                'message': str(e)
            }
            return False

    # ── Run all checks ───────────────────────────────────────────────────────
    def run_all(self) -> dict:
        syntax_ok   = self.verify_syntax()
        vuln_ok     = self.verify_vulnerabilities()
        compile_ok  = self.verify_compilable()

        self.passed = syntax_ok and vuln_ok and compile_ok

        self.results['overall'] = {
            'passed': self.passed,
            'timestamp': datetime.now().isoformat(),
            'summary': (
                'All checks passed — code is clean and safe'
                if self.passed else
                'One or more checks failed — further healing needed'
            )
        }

        return self.results

    # ── Convenience helpers ──────────────────────────────────────────────────
    def get_remaining_vulnerabilities(self) -> list:
        """Return list of vulnerabilities still in healed code."""
        return self.results.get('vulnerabilities', {}).get('remaining', [])

    def is_fully_healed(self) -> bool:
        return self.passed


if __name__ == "__main__":
    with open('healed_code.py', 'r') as f:
        healed = f.read()
    try:
        with open('test_code.py', 'r') as f:
            original = f.read()
    except FileNotFoundError:
        original = healed

    engine = VerificationEngine(original, healed)
    results = engine.run_all()
    print("\nVERIFICATION RESULTS")
    print("=" * 40)
    for check, result in results.items():
        if isinstance(result, dict) and 'passed' in result:
            icon = "✅" if result['passed'] else "❌"
            print(f"{icon} {check.upper()}: {result['message']}")