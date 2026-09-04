from fastapi import APIRouter, Depends

from recur.api.dependencies import get_recovery_service
from recur.api.schemas import (
    AnalyticsDashboardResponse,
    DistributionEntry,
    OverallMetrics,
)
from recur.services import RecoveryService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def to_dashboard_response(dashboard) -> AnalyticsDashboardResponse:
    summary = dashboard.summary
    return AnalyticsDashboardResponse(
        overall=OverallMetrics(
            total_records=summary.total_records,
            completed_records=summary.completed_records,
            blocked_records=summary.blocked_actions,
            requires_review_records=summary.records_requiring_review,
            total_amount_at_risk=summary.total_amount_at_risk,
            expected_recovery_value=summary.total_expected_recovery_value,
            total_recovered_amount=summary.total_recovered_amount,
            recovery_rate_pct=summary.recovery_rate,
        ),
        root_cause_distribution=[
            DistributionEntry(label=item.category, count=item.count)
            for item in dashboard.root_cause_distribution
        ],
        recovery_action_distribution=[
            DistributionEntry(label=item.category, count=item.count)
            for item in dashboard.recovery_action_distribution
        ],
    )


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
def analytics_dashboard(
    service: RecoveryService = Depends(get_recovery_service),
) -> AnalyticsDashboardResponse:
    return to_dashboard_response(service.get_analytics_dashboard())
