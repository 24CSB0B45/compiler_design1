"""
agent.py — Self-Healing Agentic Compiler Core
Gemini-powered agent that drives the detect → fix → verify loop.
Handles BOTH syntax errors and security vulnerabilities.
"""

from google import genai
import ast
import json
import re
from typing import List, Dict, Any

from vulnerability_detector import VulnerabilityModule
from transformation import SafeTransformationLibrary, transform_code
from verification_engine import VerificationEngine


class Agent:

    def __init__(self, api_key: str, model_name: str = 'gemini-2.5-flash'):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

        #
        self.iteration_logs: List[Dict] = []
        self.agent_decisions: List[Dict] = []
        self.fixes_applied: List[Dict] = []

    # ─────────────────────────────────────────────────────────────────────────
    # Logging
    # ─────────────────────────────────────────────────────────────────────────

    def _log(self, message: str, level: str = "info"):
        entry = {"level": level, "message": message}
        self.iteration_logs.append(entry)
        prefix = {"info": "ℹ", "success": "✅", "warn": "⚠", "error": "❌"}.get(level, "•")
        print(f"  {prefix} {message}")

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 1 — Syntax Error Fixing (runs before AST scan)
    # ─────────────────────────────────────────────────────────────────────────

    def _has_syntax_error(self, code: str):
        """Returns SyntaxError if code has one, else None."""
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return e

    def _fix_syntax_with_gemini(self, code: str, error: SyntaxError) -> str:
        """Ask Gemini to fix syntax errors. Returns corrected code string."""
        self._log(f"Syntax error at line {error.lineno}: {error.msg} — asking Gemini to fix...", "warn")

        prompt = f"""You are a Python syntax repair agent inside a self-healing compiler.

The following Python code has a syntax error:

SYNTAX ERROR:
  Line {error.lineno}: {error.msg}
  Text: {error.text}

FULL CODE:
```python
{code}
```

Your task:
1. Fix ALL syntax errors in the code.
2. Do NOT change the logic or intent of the code.
3. Do NOT add new features.
4. Return ONLY the corrected Python code with no explanation, no markdown, no backticks.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            fixed = response.text.strip()

            # Strip markdown fences if Gemini wraps in them
            if fixed.startswith('```'):
                fixed = re.sub(r'^```[a-zA-Z]*\n?', '', fixed)
                fixed = re.sub(r'\n?```$', '', fixed.strip())

            return fixed.strip()

        except Exception as e:
            self._log(f"Gemini syntax fix failed: {e}", "error")
            return code  # return original if Gemini fails

    def fix_syntax_loop(self, code: str, max_attempts: int = 5) -> str:
        """
        Loop: check syntax → ask Gemini to fix → repeat until clean or max_attempts.
        Returns syntactically valid code (or best attempt).
        """
        attempt = 0
        current_code = code

        while attempt < max_attempts:
            error = self._has_syntax_error(current_code)
            if error is None:
                if attempt > 0:
                    self._log("Syntax errors fully resolved!", "success")
                    self.fixes_applied.append({
                        'line': 'multiple',
                        'strategy': 'SYNTAX_FIX',
                        'original': 'syntax errors',
                        'replacement': 'corrected by Gemini'
                    })
                return current_code

            attempt += 1
            self._log(f"Syntax fix attempt {attempt}/{max_attempts}...", "info")
            fixed = self._fix_syntax_with_gemini(current_code, error)

            if fixed == current_code:
                self._log("Gemini returned same code — cannot fix syntax further", "error")
                break

            current_code = fixed

        # Final check
        error = self._has_syntax_error(current_code)
        if error:
            self._log(f"Could not fully fix syntax after {max_attempts} attempts — proceeding anyway", "warn")

        return current_code

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 2 — Vulnerability Scanning & Fixing
    # ─────────────────────────────────────────────────────────────────────────

    def _scan(self, code: str) -> List[Dict]:
        """Run vulnerability detector and return reports."""
        try:
            tree = ast.parse(code)
            detector = VulnerabilityModule()
            detector.visit(tree)
            lines = code.split('\n')
            for v in detector.reports:
                if v['line'] <= len(lines):
                    v['code_snippet'] = lines[v['line'] - 1].strip()
            return detector.reports
        except SyntaxError as e:
            self._log(f"Syntax error while scanning: {e}", "error")
            return []

    def _ask_gemini(self, vulnerability: Dict, current_code: str) -> Dict:
        """Ask Gemini what fix strategy to use for a given vulnerability."""
        lines = current_code.split('\n')
        ctx_start = max(0, vulnerability['line'] - 3)
        ctx_end   = min(len(lines), vulnerability['line'] + 2)
        context_block = '\n'.join(
            f"{'>>>' if i == vulnerability['line']-1 else '   '} {i+1}: {lines[i]}"
            for i in range(ctx_start, ctx_end)
        )

        prompt = f"""You are the security agent of a Self-Healing Agentic Compiler.

VULNERABILITY DETECTED:
  Type     : {vulnerability.get('type', 'UNKNOWN')}
  API      : {vulnerability.get('api', 'unknown')}
  Severity : {vulnerability.get('severity', 'MEDIUM')}
  Line {vulnerability['line']} : {vulnerability.get('code_snippet', '')}
  Description: {vulnerability.get('description', '')}

CODE CONTEXT:
{context_block}

YOUR JOB:
Choose one of these strategies and explain your reasoning:

  TRANSFORM_AST  — The SafeTransformationLibrary can handle this automatically (use for eval/exec/os.system)
  REPLACE_LINE   — Provide exact replacement Python code for that single line
  WRAP_SAFE      — Wrap the line in a try/except with a safe fallback
  ADD_COMMENT    — Add a security comment for manual review (last resort only)

Respond ONLY with valid JSON, no markdown, no backticks:
{{
  "strategy": "TRANSFORM_AST | REPLACE_LINE | WRAP_SAFE | ADD_COMMENT",
  "replacement_line": "exact Python code (only for REPLACE_LINE)",
  "wrap_fallback": "fallback value expression (only for WRAP_SAFE)",
  "explanation": "one sentence explaining why this fix is safe",
  "confidence": 0.0
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith('```'):
                text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
                text = re.sub(r'\n?```$', '', text.strip())
            decision = json.loads(text.strip())
            decision['source'] = 'gemini'
            return decision
        except Exception as e:
            self._log(f"Gemini API error: {e} — using fallback", "warn")
            return {
                "strategy": "ADD_COMMENT",
                "replacement_line": None,
                "explanation": f"Gemini unavailable: {str(e)[:80]}",
                "confidence": 0.1,
                "source": "fallback"
            }

    def _apply_fix(self, code: str, vuln: Dict, decision: Dict) -> str:
        strategy = decision.get('strategy', 'ADD_COMMENT')
        line_idx  = vuln['line'] - 1
        lines     = code.split('\n')

        # ── AST transformer (eval, exec, os.system) ──────────────────────────
        if strategy == 'TRANSFORM_AST' or vuln.get('api') in ('eval', 'exec', 'os.system', 'system'):
            try:
                new_code, changes = transform_code(code)
                if changes:
                    for c in changes:
                        self._log(f"AST transform line {c['line']}: {c['original']} → {c['replacement']}", "success")
                        self.fixes_applied.append({
                            'line': c['line'], 'strategy': 'TRANSFORM_AST',
                            'original': c['original'], 'replacement': c['replacement']
                        })
                    return new_code
                else:
                    self._log("AST transformer found nothing to change — falling through", "warn")
            except Exception as e:
                self._log(f"AST transform failed: {e}", "error")

        # ── Replace the single line with agent suggestion ─────────────────
        if strategy == 'REPLACE_LINE' and decision.get('replacement_line'):
            if 0 <= line_idx < len(lines):
                original_indent = len(lines[line_idx]) - len(lines[line_idx].lstrip())
                indent = ' ' * original_indent
                lines[line_idx] = indent + decision['replacement_line'].strip()
                self._log(f"Replaced line {vuln['line']} with Gemini suggestion", "success")
                self.fixes_applied.append({
                    'line': vuln['line'], 'strategy': 'REPLACE_LINE',
                    'original': vuln.get('code_snippet'), 'replacement': decision['replacement_line']
                })
                return '\n'.join(lines)

        
        if strategy == 'WRAP_SAFE':
            if 0 <= line_idx < len(lines):
                original_line   = lines[line_idx]
                original_indent = len(original_line) - len(original_line.lstrip())
                indent   = ' ' * original_indent
                fallback = decision.get('wrap_fallback', 'None')
                wrapped  = [
                    f"{indent}try:",
                    f"{indent}    {original_line.strip()}",
                    f"{indent}except Exception as _sec_err:",
                    f"{indent}    print(f'[SECURITY BLOCK] Unsafe operation prevented: {{_sec_err}}')",
                    f"{indent}    {fallback}",
                ]
                lines[line_idx:line_idx+1] = wrapped
                self._log(f"Wrapped line {vuln['line']} in safety try/except", "success")
                self.fixes_applied.append({
                    'line': vuln['line'], 'strategy': 'WRAP_SAFE',
                    'original': vuln.get('code_snippet'), 'replacement': 'try/except block'
                })
                return '\n'.join(lines)

        # ── Last resort: add review comment ───────────────────────────────────
        if 0 <= line_idx < len(lines):
            if '# [SECURITY]' not in lines[line_idx]:
                lines[line_idx] += '  # [SECURITY] Manual review required — flagged by self-healing compiler'
                self._log(f"Added security comment at line {vuln['line']}", "warn")
                self.fixes_applied.append({
                    'line': vuln['line'], 'strategy': 'ADD_COMMENT',
                    'original': vuln.get('code_snippet'), 'replacement': 'comment added'
                })

        return '\n'.join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # Main healing loop
    # ─────────────────────────────────────────────────────────────────────────

    def agentic_healing_loop(self, code: str, max_iterations: int = 5) -> Dict[str, Any]:
        """
        Full pipeline:
          PHASE 1 — Fix all syntax errors first (Gemini loop)
          PHASE 2 — Fix security vulnerabilities (detect → Gemini → transform → verify loop)
        """
        # Reset logs
        self.iteration_logs = []
        self.agent_decisions = []
        self.fixes_applied   = []

        original_code = code
        fully_healed  = False

        # ══════════════════════════════════════════════════════════════════════
        # PHASE 1: Fix syntax errors
        # ══════════════════════════════════════════════════════════════════════
        syntax_error = self._has_syntax_error(code)
        if syntax_error:
            self._log("═══ PHASE 1: Syntax Error Repair ═══", "info")
            self._log(f"Detected syntax error → line {syntax_error.lineno}: {syntax_error.msg}", "warn")
            code = self.fix_syntax_loop(code, max_attempts=max_iterations)
        else:
            self._log("═══ PHASE 1: Syntax Check — No errors found ✅ ═══", "success")

        current_code = code
        iteration    = 0

        # ══════════════════════════════════════════════════════════════════════
        # PHASE 2: Fix security vulnerabilities
        # ══════════════════════════════════════════════════════════════════════
        self._log("═══ PHASE 2: Security Vulnerability Repair ═══", "info")

        while iteration < max_iterations:
            iteration += 1
            self._log(f"── Iteration {iteration} ──", "info")

            vulnerabilities = self._scan(current_code)

            if not vulnerabilities:
                self._log("No vulnerabilities detected — code is clean!", "success")
                fully_healed = True
                break

            self._log(f"Found {len(vulnerabilities)} vulnerability/vulnerabilities", "warn")

            fixes_this_round = 0
            for vuln in vulnerabilities:
                self._log(f"Analyzing line {vuln['line']}: [{vuln['severity']}] {vuln['api']}")

                decision = self._ask_gemini(vuln, current_code)

                self.agent_decisions.append({
                    'iteration':     iteration,
                    'line':          vuln['line'],
                    'vulnerability': vuln['api'],
                    'severity':      vuln.get('severity', 'MEDIUM'),
                    'strategy':      decision['strategy'],
                    'explanation':   decision['explanation'],
                    'confidence':    decision.get('confidence', 0),
                    'source':        decision.get('source', 'gemini')
                })

                new_code = self._apply_fix(current_code, vuln, decision)

                if new_code != current_code:
                    current_code = new_code
                    fixes_this_round += 1
                else:
                    self._log(f"No change made for line {vuln['line']}", "warn")

            if fixes_this_round == 0:
                self._log("No fixes could be applied — stopping loop", "warn")
                break

         
            self._log("Running verification engine...", "info")
            verifier = VerificationEngine(original_code, current_code)
            results  = verifier.run_all()

            syntax_ok  = results.get('syntax',          {}).get('passed', False)
            vuln_ok    = results.get('vulnerabilities', {}).get('passed', False)
            compile_ok = results.get('compilable',      {}).get('passed', False)

            self._log(
                f"Syntax: {'✅' if syntax_ok else '❌'}  "
                f"Vulns: {'✅' if vuln_ok else '❌'}  "
                f"Compile: {'✅' if compile_ok else '❌'}"
            )

            if verifier.is_fully_healed():
                self._log("All checks passed — fully healed!", "success")
                fully_healed = True
                break

            if not syntax_ok or not compile_ok:
                self._log("Healed code broke syntax/compile — stopping", "error")
                break

        # ── Final verification ────────────────────────────────────────────────
        final_verifier = VerificationEngine(original_code, current_code)
        final_results  = final_verifier.run_all()

        return {
            'healed_code':               current_code,
            'original_code':             original_code,
            'fully_healed':              fully_healed,
            'iterations':                iteration,
            'agent_decisions':           self.agent_decisions,
            'fixes_applied':             self.fixes_applied,
            'iteration_logs':            self.iteration_logs,
            'verification':              final_results,
            'vulnerabilities_remaining': final_verifier.get_remaining_vulnerabilities()
        }