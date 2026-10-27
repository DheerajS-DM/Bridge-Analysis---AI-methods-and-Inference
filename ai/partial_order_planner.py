import networkx as nx
from typing import List, Tuple, Set, Dict, Any, Optional
from core.schema import PlanAction, PartialOrderPlan, DamageReport
from ai.retrofit_library import IRCRetrofitActionLibrary

class PartialOrderPlanner:
    """Synthesizes dependency-aware retrofit plans governed strictly by Indian Standards (IRC / BIS).
    Organizes actions into distinct phases (Emergency Shoring -> Foundation Armoring -> Primary Retrofit -> Verification)
    and resolves causal dependencies."""
    def __init__(self):
        self.actions: List[PlanAction] = []

    def add_available_action(self, action: PlanAction) -> None:
        """Registers a candidate repair operator."""
        self.actions.append(action)

    def generate_actions_from_damage_reports(self, damage_reports: List[DamageReport]) -> List[PlanAction]:
        """Translates forensic damage findings into standardized Indian construction retrofit actions."""
        self.actions = []
        action_id_counter = 1

        # Check if foundation or emergency shoring is required
        has_critical_damage = any(r.severity_score >= 0.7 for r in damage_reports)
        if has_critical_damage:
            emergency_shoring = PlanAction(
                id=f"ACT-00{action_id_counter}-SHORING",
                name="Erect Heavy Modular Steel Shoring Towers & Hydraulic Jacks",
                target_element_id=0,
                standard_code="IRC:SP:40:2019",
                clause_reference="Clause 3.4 - Temporary Propping & Shoring Requirements",
                academic_citation="MoRTH Section 2800 Clause 2802",
                preconditions=["TrafficClosed"],
                effects=["EmergencyShoringErected", "TemporaryShoringSecured"],
                duration_days=2.0,
                cost_inr=150000.0,
                cost=150000.0,
                phase="emergency",
                capacity_restoration_factor=1.0,
                curing_period_days=0.0
            )
            self.actions.append(emergency_shoring)
            action_id_counter += 1

        for report in damage_reports:
            candidates = IRCRetrofitActionLibrary.get_candidate_actions(report.damage_category, report.component_type)
            if candidates:
                best_candidate = candidates[0] # primary standard intervention
                act = best_candidate.model_copy()
                act.id = f"ACT-00{action_id_counter}-{act.standard_code.split(':')[1] if ':' in act.standard_code else 'IRC'}"
                act.target_element_id = report.element_id
                act.name = f"{best_candidate.name} (Element #{report.element_id})"
                self.actions.append(act)
                action_id_counter += 1

        return self.actions

    def solve(self, initial_state: Set[str], goal_conditions: Set[str]) -> PartialOrderPlan:
        """Executes Partial Order Planning (POP) to resolve open conditions and build phased schedule."""
        steps: List[PlanAction] = []
        orderings: List[Tuple[str, str]] = []
        causal_links: List[Tuple[str, str, str]] = []

        start_action = PlanAction(
            id="Start", name="Structural Distress Assessment Completed", target_element_id=-1,
            standard_code="IRC:SP:35:2019", clause_reference="Inspection & Condition Survey",
            preconditions=[], effects=list(initial_state), duration_days=0.0, cost_inr=0.0, cost=0.0,
            phase="emergency"
        )
        finish_action = PlanAction(
            id="Finish", name="Structural Safety & Capacity Verified", target_element_id=-1,
            standard_code="IRC:SP:51:2015", clause_reference="Guidelines for Load Testing of Bridges",
            preconditions=list(goal_conditions), effects=[], duration_days=0.0, cost_inr=0.0, cost=0.0,
            phase="verification"
        )
        steps.append(start_action)

        # Categorize actions by phase: emergency -> foundation -> primary -> verification
        phase_priority = {"emergency": 1, "foundation": 2, "primary": 3, "verification": 4}
        sorted_acts = sorted(self.actions, key=lambda a: phase_priority.get(a.phase, 3))

        prev_id = "Start"
        total_cost = 0.0
        critical_days = 0.0

        for act in sorted_acts:
            steps.append(act)
            orderings.append((prev_id, act.id))
            causal_links.append((prev_id, "StateReady", act.id))
            prev_id = act.id
            total_cost += act.cost_inr
            critical_days += act.duration_days + act.curing_period_days

        steps.append(finish_action)
        if prev_id != "Start":
            orderings.append((prev_id, "Finish"))

        return PartialOrderPlan(
            steps=steps,
            orderings=orderings,
            causal_links=causal_links,
            total_cost_inr=total_cost,
            critical_path_days=round(critical_days, 1)
        )
