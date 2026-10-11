"""Query-planning interface."""

from vidsearch.core.schemas import Query
from vidsearch.query.plan_schema import QueryPlan


class QueryPlanner:
    def plan(self, query: Query) -> QueryPlan:
        """Map free text to a validated plan using a configured model."""
        raise NotImplementedError("configure an LLM-backed query planner")
