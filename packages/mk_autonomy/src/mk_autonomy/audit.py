from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionPathNode:
    node_id: str
    label: str
    children: tuple[DecisionPathNode, ...] = ()

    @property
    def node_count(self) -> int:
        return 1 + sum(child.node_count for child in self.children)


def build_default_decision_path_tree() -> DecisionPathNode:
    return DecisionPathNode(
        node_id="root",
        label="state_observation",
        children=(
            DecisionPathNode(
                node_id="risk",
                label="rule_layer_veto_check",
                children=(
                    DecisionPathNode("risk.pass", "risk_budget_passed"),
                    DecisionPathNode("risk.clip", "allocation_clipped"),
                ),
            ),
            DecisionPathNode(
                node_id="rl",
                label="rl_action_selection",
                children=(
                    DecisionPathNode("rl.allocate", "allocate_strategy_weights"),
                    DecisionPathNode("rl.explain", "write_decision_log"),
                ),
            ),
            DecisionPathNode(
                node_id="execution",
                label="adaptive_split_routing",
                children=(DecisionPathNode("execution.bandit", "contextual_bandit_choice"),),
            ),
        ),
    )
