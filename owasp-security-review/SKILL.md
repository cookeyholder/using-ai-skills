---
name: owasp-security-review
description: Performs comprehensive OWASP security code review covering OWASP Top 10 Web (2025), OWASP API Security Top 10 (2023), and OWASP Top 10 for LLM Applications (2025). Use when the user asks for a security audit, vulnerability scan, OWASP review, security assessment, code security check, or wants to find security flaws in a codebase. Use when implementing or reviewing features that handle authentication, user input, file uploads, database queries, API endpoints, LLM integrations, or sensitive data. Covers all major languages and frameworks.
---

# OWASP Security Review

## Overview

Systematic security code review covering three OWASP standards:

| Standard | Version | Focus | When to Apply |
|----------|---------|-------|---------------|
| [OWASP Top 10](references/owasp-top10.md) | 2025 | Web application vulnerabilities | Always -- baseline for all projects |
| [OWASP API Security Top 10](references/owasp-api-top10.md) | 2023 | API-specific risks (BOLA, mass assignment, rate limiting) | Project has REST/GraphQL/gRPC APIs |
| [OWASP LLM Top 10](references/owasp-llm-top10.md) | 2025 | LLM integration risks (prompt injection, agent security, RAG) | Project uses LLMs, agents, or RAG |

### What is New in OWASP Top 10 2025

| Change | Detail |
|--------|--------|
| A02: Security Misconfiguration | Moved up from #5 to #2 |
| A03: Software Supply Chain Failures | New -- expanded from Vulnerable Components to full supply chain |
| A10: Mishandling of Exceptional Conditions | New -- error handling, failing open, resource leaks |
| SSRF | Moved from A10 (2021) into A01: Broken Access Control |

## Decision Tree: Which Lists to Apply

Project being reviewed:
- Does it expose web routes/pages? Apply OWASP Top 10 2025
- Does it have API endpoints (REST/GraphQL/gRPC)? Apply OWASP API Top 10 2023  
- Does it integrate LLMs, agents, or RAG? Apply OWASP LLM Top 10 2025

For a full-stack web app with APIs and LLM features, apply all three.

## Review Workflow

### Step 1: Scope and Classify

Before scanning, establish:

- What parts of the codebase to review? (entire repo, specific directories, recent changes)
- What language(s) and framework(s) are in use?
- Which OWASP lists apply based on the decision tree above?
- Are there auth, API, file upload, LLM, payment, or supply chain modules to prioritize?

### Step 2: Scan by Applicable OWASP Standard(s)

**For web app vulnerabilities**, load references/owasp-top10.md:
- A01 Broken Access Control to A10 Mishandling of Exceptional Conditions
- Detection patterns per category with vulnerable vs. safe code examples
- Quick Reference grep table at the bottom

**For API vulnerabilities**, load references/owasp-api-top10.md:
- API1 BOLA to API10 Unsafe Consumption of APIs
- Mass assignment, broken function-level auth, rate limiting

**For LLM vulnerabilities**, load references/owasp-llm-top10.md:
- LLM01 Prompt Injection to LLM10 Unbounded Consumption
- Agent permission scoping, output validation, RAG pipeline security

For language-specific patterns, load references/language-patterns.md covering Python, JavaScript/TypeScript, Java, Go, C#, PHP, and Ruby.

### Step 3: Cross-Reference with Dependency Check

npm audit / pip-audit / safety check / trivy fs . / snyk test

Map dependency findings to A03:2025 (Software Supply Chain Failures).

### Step 4: Generate Report

Use this format for the security report:

# OWASP Security Review Report

## Scope
- Standards Applied: OWASP Top 10 2025, [API 2023, LLM 2025]
- Reviewed: [directories, files, lines]
- Languages: [list]
- Frameworks: [list]

## Summary
Each finding rated: Critical / High / Medium / Low

## Findings
Group by severity (Critical first), with:
- Standard + Category (e.g. OWASP Top 10 2025 - A05 Injection)
- Location: file:line
- Description: what and why
- Exploitation scenario
- Fix: before/after code

## Category Coverage
Table of each OWASP category, files reviewed, findings per severity

## Actions Required
Prioritized list of fixes

### Step 5: Verify and Prioritize

- False positive check: Verify each finding is actually exploitable in context
- Severity:
  - Critical: RCE, auth bypass, data breach, SQL injection on public endpoint
  - High: Stored XSS, IDOR on sensitive data, hardcoded secrets, missing auth
  - Medium: Reflected XSS, weak crypto config, missing security headers
  - Low: Missing rate limiting, verbose errors (behind auth), dev-only issues

## Risk Rationalizations

| Excuse | Reality |
|--------|---------|
| Internal tool, security does not matter | Internal tools are #1 lateral movement target |
| Framework handles it | Frameworks provide tools, not guarantees |
| Fix security later | Retrofitting costs 10x more |
| LLM is sandboxed so it is fine | Prompt injection can bypass sandbox boundaries |
| API is internal only | Internal APIs get breached. Use same standards |

## Post-Review

- Fix in order: Critical to High to Medium to Low
- Re-scan after fixes to confirm resolution
- Recommend automated security scanning in CI/CD
- Flag systemic patterns (e.g., every endpoint missing auth = middleware refactor)
- For LLM projects: recommend red-teaming / adversarial testing
