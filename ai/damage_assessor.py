import polars as pl
from typing import List, Dict, Any
from core.schema import DamageReport

class DamageAssessor:
    """Forensic structural health assessor that inspects post-disaster FEA states,
    categorizes damage according to Indian Standard limit states (IRC:SP:40, IRC:SP:74, IRC:78),
    and computes criticality metrics."""

    @staticmethod
    def assess_structure(
        elements_df: pl.DataFrame,
        stresses: Dict[int, float],
        scour_depth_m: float = 0.0
    ) -> List[DamageReport]:
        """Analyzes elements against material yield thresholds and Indian Standard failure criteria."""
        reports: List[DamageReport] = []

        for row in elements_df.iter_rows(named=True):
            eid = row["id"]
            sec_type = str(row["section_type"])
            fy = float(row["yield_stress_fy"])
            sigma = stresses.get(eid, 0.0)
            dcr = sigma / (fy + 1e-6)

            # 1. Plastic Hinge in Concrete Substructures (IRC:SP:40 Cl. 5.3)
            if "Concrete" in sec_type and ("Pier" in sec_type or "Column" in sec_type or "Bent" in sec_type):
                if dcr >= 0.85 or scour_depth_m > 1.5:
                    cat = "foundation_scour" if scour_depth_m > 1.5 else "plastic_hinge"
                    governing = "IRC:89:2010 Cl. 5.2 / IRC:78 Cl. 703" if cat == "foundation_scour" else "IRC:SP:40:2019 Cl. 5.3"
                    sev = min(1.0, 0.5 + 0.5 * (dcr - 0.85) / 0.5) if cat == "plastic_hinge" else min(1.0, scour_depth_m / 4.0)
                    reports.append(DamageReport(
                        element_id=eid,
                        component_type=sec_type,
                        damage_category=cat,
                        dcr=round(dcr, 3),
                        plastic_rotation=round(max(0.0, (dcr - 1.0) * 0.015), 4),
                        severity_score=round(sev, 3),
                        governing_code=governing,
                        criticality_rank=1 if dcr > 1.0 else 2,
                        description=f"Severe plastic hinge demand on pier column. DCR={dcr:.2f} exceeds IRC:SP:40 allowable limit."
                    ))
                elif dcr >= 0.65:
                    reports.append(DamageReport(
                        element_id=eid,
                        component_type=sec_type,
                        damage_category="concrete_cracking",
                        dcr=round(dcr, 3),
                        plastic_rotation=0.0,
                        severity_score=round(0.4 * (dcr / 0.85), 3),
                        governing_code="IRC:SP:40:2019 Cl. 4.2",
                        criticality_rank=3,
                        description=f"Micro-crack formation along concrete tension zone. DCR={dcr:.2f}."
                    ))

            # 2. Steel Tension Chords (IRC:SP:74 Cl. 4.2 & IRC:SP:75 Cl. 3.2)
            elif "Bottom_Chord" in sec_type or "Tie_Chord" in sec_type or "Floor_Beam" in sec_type:
                if dcr >= 0.80:
                    reports.append(DamageReport(
                        element_id=eid,
                        component_type=sec_type,
                        damage_category="flange_yielding",
                        dcr=round(dcr, 3),
                        plastic_rotation=round(max(0.0, (dcr - 1.0) * 0.008), 4),
                        severity_score=round(min(1.0, 0.4 + 0.6 * (dcr - 0.8) / 0.4), 3),
                        governing_code="IRC:SP:74:2007 Cl. 4.2 / IRC:SP:75 Cl. 3.2",
                        criticality_rank=1 if dcr > 1.0 else 2,
                        description=f"Extreme tensile stress concentration on bottom chord. DCR={dcr:.2f}."
                    ))
                elif dcr >= 0.60:
                    reports.append(DamageReport(
                        element_id=eid,
                        component_type=sec_type,
                        damage_category="fatigue_crack",
                        dcr=round(dcr, 3),
                        plastic_rotation=0.0,
                        severity_score=0.35,
                        governing_code="IRC:SP:74:2007 Cl. 4.1",
                        criticality_rank=3,
                        description=f"Localized cyclic stress range susceptible to fatigue crack initiation. DCR={dcr:.2f}."
                    ))

            # 3. Steel Compression Diagonals & Top Struts (IRC:SP:74 Cl. 4.4)
            elif "Top_Chord" in sec_type or "Diagonal" in sec_type or "Vertical" in sec_type:
                if dcr >= 0.75:
                    reports.append(DamageReport(
                        element_id=eid,
                        component_type=sec_type,
                        damage_category="diagonal_buckling",
                        dcr=round(dcr, 3),
                        plastic_rotation=0.0,
                        severity_score=round(min(1.0, 0.5 + 0.5 * (dcr - 0.75) / 0.35), 3),
                        governing_code="IRC:SP:74:2007 Cl. 4.4 / IRC:24:2010 Cl. 506",
                        criticality_rank=1 if dcr > 0.95 else 2,
                        description=f"Axial compressive force approaching Johnson/Euler buckling limit. DCR={dcr:.2f}."
                    ))

        # Sort descending by severity score
        reports.sort(key=lambda r: (r.criticality_rank, -r.severity_score))
        return reports
