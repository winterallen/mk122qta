from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    request_id: str
    action: str
    requester: str
    approvers: tuple[str, ...] = ()
    required_approvals: int = 2

    @property
    def approved(self) -> bool:
        return len(set(self.approvers)) >= self.required_approvals


class TwoPersonApprovalWorkflow:
    def create_request(self, request_id: str, action: str, requester: str) -> ApprovalRequest:
        return ApprovalRequest(request_id=request_id, action=action, requester=requester)

    def approve(self, request: ApprovalRequest, approver: str) -> ApprovalRequest:
        if approver == request.requester:
            raise ValueError("requester cannot approve own request")
        if approver in request.approvers:
            return request
        return ApprovalRequest(
            request_id=request.request_id,
            action=request.action,
            requester=request.requester,
            approvers=request.approvers + (approver,),
            required_approvals=request.required_approvals,
        )


@dataclass(frozen=True, slots=True)
class EmergencyKillSwitch:
    armed: bool = True
    tripped: bool = False
    reason: str = ""

    def trip(self, reason: str) -> EmergencyKillSwitch:
        if not self.armed:
            raise ValueError("kill switch is not armed")
        return EmergencyKillSwitch(armed=True, tripped=True, reason=reason)

    def reset(self) -> EmergencyKillSwitch:
        return EmergencyKillSwitch(armed=True, tripped=False, reason="")
