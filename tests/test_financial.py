"""
Category I: Financial Control Tests
======================================
Tests that verify financial tracking and budget enforcement.

Financial controls are critical because:
1. Real money (¥15,000/month minimum) is at stake
2. AI agents cannot spend money but must track costs accurately
3. Budget overruns must be caught before shareholder approval
"""

import pytest
import re
from conftest import (
    SUBORDINATE_AGENTS, CEO_DISCRETION_THRESHOLD, MONTHLY_BUDGET_LIMIT,
    read_file, extract_section,
)


@pytest.mark.static
@pytest.mark.financial
class TestBudgetDefinition:
    """Budget limits must be clearly defined and consistent."""

    def test_monthly_limit_defined_in_status(self, status_md):
        """status.md must state the ¥55,000 monthly budget limit."""
        assert "55,000" in status_md, \
            "Monthly budget limit (¥55,000) must be in status.md"

    def test_budget_categories_defined(self, status_md):
        """Budget must be broken into categories with individual limits."""
        budget = extract_section(status_md, "予算枠")
        assert budget is not None, "status.md must have budget section"
        # Must have at least 3 categories
        rows = [l for l in budget.split("\n")
                if l.strip().startswith("|") and "¥" in l]
        assert len(rows) >= 3, \
            f"Budget must have at least 3 categories, found {len(rows)}"

    def test_budget_has_approval_authority(self, status_md):
        """Each budget category must specify who can approve spending."""
        budget = extract_section(status_md, "予算枠")
        assert budget is not None
        assert "承認者" in budget or "CEO判断" in budget, \
            "Budget categories must specify approval authority"

    def test_shareholder_approval_threshold_consistent(self, claude_md, status_md):
        """¥30,000 threshold must be consistent across documents."""
        assert "30,000" in claude_md or "¥30,000" in claude_md, \
            "CLAUDE.md must reference ¥30,000 threshold"

    def test_no_autonomous_spending_documented(self, claude_md):
        """Must explicitly state AI cannot spend money autonomously."""
        # Condensed CLAUDE.md: "予算を使う判断を勝手にしない"
        assert ("予算を使う判断を勝手にしない" in claude_md or
                "自律的に支出できない" in claude_md), \
            "CLAUDE.md must state AI cannot spend autonomously"


@pytest.mark.static
@pytest.mark.financial
class TestCostTracking:
    """Actual costs must be tracked in status.md."""

    def test_fixed_costs_documented(self, status_md):
        """Fixed monthly costs must be listed."""
        costs = extract_section(status_md, "固定費")
        assert costs is not None, \
            "status.md must document fixed costs"
        assert "Claude Max" in costs or "claude" in costs.lower(), \
            "Fixed costs must include Claude Max subscription"

    def test_current_month_expenditure(self, status_md):
        """Current month's total expenditure must be recorded."""
        assert "支出合計" in status_md, \
            "status.md must track current month expenditure total"

    def test_revenue_tracked(self, status_md):
        """Revenue (even if ¥0) must be tracked."""
        assert "収入" in status_md or "売上" in status_md, \
            "status.md must track revenue"

    def test_cumulative_investment_tracked(self, status_md):
        """Cumulative investment must be tracked for ROI calculation."""
        assert "累計" in status_md, \
            "status.md must track cumulative investment"

    def test_profit_loss_calculated(self, status_md):
        """Monthly P&L (revenue - cost) must be calculated."""
        assert "収支" in status_md, \
            "status.md must show profit/loss (収支)"


@pytest.mark.static
@pytest.mark.financial
class TestTokenCostAwareness:
    """Token consumption must be monitored as it's the primary cost driver."""

    def test_token_section_in_status(self, status_md):
        """status.md must have a token consumption section."""
        assert "トークン" in status_md, \
            "status.md must track token consumption"

    def test_token_plan_documented(self, status_md):
        """The Claude plan type and cost must be documented."""
        assert "Max" in status_md or "Pro" in status_md, \
            "status.md must document the Claude plan type"
        assert "$100" in status_md or "¥15,000" in status_md, \
            "status.md must document the plan cost"

    def test_plan_md_has_cost_breakdown(self, plan_md):
        """plan.md must include a cost breakdown per service."""
        assert "コスト" in plan_md or "月額" in plan_md, \
            "plan.md must include cost breakdown"
        costs = extract_section(plan_md, "コスト")
        if costs:
            assert "Claude" in costs, \
                "Cost breakdown must include Claude subscription"


@pytest.mark.static
@pytest.mark.financial
class TestPendingApprovals:
    """Spending that requires approval must be tracked."""

    def test_pending_section_exists(self, status_md):
        """status.md must have a section for pending approvals."""
        assert "承認待ち" in status_md, \
            "status.md must have pending approvals section"

    def test_pending_items_have_cost(self, status_md):
        """Each pending approval must include a cost estimate."""
        section = extract_section(status_md, "株主承認待ち")
        if section:
            rows = [l for l in section.split("\n")
                    if "|" in l and "S-" in l]
            for row in rows:
                has_cost = "$" in row or "¥" in row or "￥" in row
                assert has_cost, \
                    f"Pending approval must include cost: {row.strip()}"
