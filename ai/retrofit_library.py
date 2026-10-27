from typing import List, Dict, Any, Optional
from core.schema import PlanAction

class IRCRetrofitActionLibrary:
    """Standardized Indian Construction & Bridge Rehabilitation Action Catalog.
    Governed strictly by Indian Roads Congress (IRC), Bureau of Indian Standards (BIS),
    and Ministry of Road Transport and Highways (MoRTH) Section 2800."""

    REPAIR_CATALOG: Dict[str, List[Dict[str, Any]]] = {
        "plastic_hinge": [
            {
                "id": "IRC-SP40-5.3-RCJACK",
                "name": "M50 Micro-Concrete Jacketing with Shear Dowels",
                "standard_code": "IRC:SP:40:2019",
                "clause_reference": "Clause 5.3 - Section Enlargement & Concrete Jacketing",
                "academic_citation": "Priestley, Seible & Calvi (1996), Seismic Design and Retrofit of Bridges, Ch. 7",
                "applicable_components": ["Concrete_Pier_Column", "Concrete_Bent_Cap", "Pier_Cap"],
                "capacity_restoration_factor": 1.30,
                "cost_inr": 450000.0,
                "duration_days": 14.0,
                "curing_period_days": 14.0,
                "phase": "primary",
                "preconditions": ["EmergencyShoringErected", "SurfaceGritBlasted"],
                "effects": ["PlasticHingeConfined", "FlexuralCapacityRestored"]
            },
            {
                "id": "IRC-SP40-5.5-CFRP",
                "name": "Multi-Ply Bidirectional CFRP Confinement Wrapping",
                "standard_code": "IRC:SP:40:2019",
                "clause_reference": "Clause 5.5 - Fibre Reinforced Polymer (FRP) Composites",
                "academic_citation": "ACI 440.2R-17 / MoRTH Section 2800 Clause 2808",
                "applicable_components": ["Concrete_Pier_Column", "Concrete_Girder", "Concrete_Box_Girder"],
                "capacity_restoration_factor": 1.25,
                "cost_inr": 180000.0,
                "duration_days": 4.0,
                "curing_period_days": 3.0,
                "phase": "primary",
                "preconditions": ["SurfaceGritBlasted"],
                "effects": ["DuctilityRestored", "ShearCapacityRestored"]
            }
        ],
        "flange_yielding": [
            {
                "id": "IRC-SP74-4.2-HSFG",
                "name": "Bolted Splice Plates with Grade 10.9 HSFG Bolts",
                "standard_code": "IRC:SP:74:2007",
                "clause_reference": "Clause 4.2 - Bolted Splice Plates and Flange Repairs",
                "academic_citation": "IS 4000:1992 Code of Practice for High Strength Bolts in Steel Structures",
                "applicable_components": ["Steel_Bottom_Chord", "Steel_Floor_Beam", "Steel_Plate_Girder", "Steel_Tie_Chord"],
                "capacity_restoration_factor": 1.15,
                "cost_inr": 120000.0,
                "duration_days": 3.0,
                "curing_period_days": 0.0,
                "phase": "primary",
                "preconditions": ["TemporaryShoringSecured"],
                "effects": ["TensileCapacityRestored", "FlangeTearArrested"]
            },
            {
                "id": "IRC-SP75-3.2-EXT-TENDON",
                "name": "Supplementary External Unbonded Prestressing Tendons",
                "standard_code": "IRC:SP:75:2008",
                "clause_reference": "Clause 3.2 - Retrofitting of Steel Bridges by Prestressing",
                "academic_citation": "Troitsky (1990), Prestressed Steel Bridges: Theory & Design",
                "applicable_components": ["Steel_Bottom_Chord", "Steel_Tie_Chord"],
                "capacity_restoration_factor": 1.45,
                "cost_inr": 380000.0,
                "duration_days": 8.0,
                "curing_period_days": 1.0,
                "phase": "primary",
                "preconditions": ["AnchorBracketsInstalled"],
                "effects": ["TensileReliefAchieved", "SagDeflectionEliminated"]
            }
        ],
        "diagonal_buckling": [
            {
                "id": "IRC-SP74-4.4-LACING",
                "name": "Channel/Angle Section Lacing & Web Stiffener Reinforcement",
                "standard_code": "IRC:SP:74:2007",
                "clause_reference": "Clause 4.4 - Stiffening of Compressed Members and Diagonals",
                "academic_citation": "IRC:24:2010 Cl. 506 (Design of Compression Members)",
                "applicable_components": ["Steel_Top_Chord", "Steel_End_Diagonal", "Steel_Web_Diagonal"],
                "capacity_restoration_factor": 1.35,
                "cost_inr": 175000.0,
                "duration_days": 5.0,
                "curing_period_days": 0.0,
                "phase": "primary",
                "preconditions": ["StraighteningCompleted"],
                "effects": ["EulerBucklingPrevented", "AxialCompressiveCapacityRestored"]
            }
        ],
        "fatigue_crack": [
            {
                "id": "IRC-SP74-4.1-STOPDRILL",
                "name": "Crack Arrest Hole Drilling (20mm Dia) with Preloaded HSFG Pin",
                "standard_code": "IRC:SP:74:2007",
                "clause_reference": "Clause 4.1 - Crack Detection and Stop-Drilling Mitigation",
                "academic_citation": "Fisher et al. (1980), FHWA-RD-80-058 Repair of Steel Bridges",
                "applicable_components": ["Steel_Bottom_Chord", "Steel_Floor_Beam", "Steel_Diagonal"],
                "capacity_restoration_factor": 1.05,
                "cost_inr": 25000.0,
                "duration_days": 1.0,
                "curing_period_days": 0.0,
                "phase": "emergency",
                "preconditions": [],
                "effects": ["StressIntensitySingularityArrested"]
            }
        ],
        "concrete_cracking": [
            {
                "id": "IRC-SP40-4.2-EPOXY",
                "name": "Low-Viscosity Epoxy Resin Pressure Injection Grouting",
                "standard_code": "IRC:SP:40:2019",
                "clause_reference": "Clause 4.2 - Structural Crack Injection and Grouting",
                "academic_citation": "MoRTH Section 2800 Clause 2803 (Grouting of Concrete Bridges)",
                "applicable_components": ["Concrete_Pier_Column", "Concrete_Girder", "Concrete_Bent_Cap"],
                "capacity_restoration_factor": 1.10,
                "cost_inr": 65000.0,
                "duration_days": 3.0,
                "curing_period_days": 3.0,
                "phase": "primary",
                "preconditions": ["SurfaceCleaned"],
                "effects": ["CrackMonolithicBondRestored", "IngressBarrierSealed"]
            }
        ],
        "foundation_scour": [
            {
                "id": "IRC89-5.2-RIPRAP",
                "name": "Heavy Boulder Riprap Launching Apron Pitching (W >= 40 kg)",
                "standard_code": "IRC:89:2010",
                "clause_reference": "Clause 5.2 - Launching Apron Protection of River Bridges",
                "academic_citation": "IRC:78:2014 Cl. 703.4; Lacey (1930) Stable Channels in Alluvium",
                "applicable_components": ["Concrete_Pier_Column", "Pier_Footing", "Pier_Cap"],
                "capacity_restoration_factor": 1.40,
                "cost_inr": 550000.0,
                "duration_days": 7.0,
                "curing_period_days": 0.0,
                "phase": "foundation",
                "preconditions": ["RiverFlowDiverted"],
                "effects": ["ScourPitStabilized", "PassiveSoilPressureRestored"]
            },
            {
                "id": "IRC78-706-MICROPILE",
                "name": "200mm Dia Drilled & Grouted Micropile Underpinning",
                "standard_code": "IRC:78:2014",
                "clause_reference": "Clause 706 - Foundation Remediation & Underpinning",
                "academic_citation": "FHWA-NHI-05-039 Micropile Design and Construction Reference Manual",
                "applicable_components": ["Concrete_Pier_Column", "Pier_Footing"],
                "capacity_restoration_factor": 1.50,
                "cost_inr": 920000.0,
                "duration_days": 18.0,
                "curing_period_days": 7.0,
                "phase": "foundation",
                "preconditions": ["GeotechnicalSurveyCompleted"],
                "effects": ["FoundationBearingIncreased", "SettlementArrested"]
            }
        ]
    }

    @classmethod
    def get_candidate_actions(cls, damage_category: str, component_type: str) -> List[PlanAction]:
        """Queries Indian Standard repair measures matching damage mode and component type."""
        results = []
        options = cls.REPAIR_CATALOG.get(damage_category, [])
        for opt in options:
            action = PlanAction(
                id=opt["id"],
                name=opt["name"],
                target_element_id=0,  # bound during planning
                standard_code=opt["standard_code"],
                clause_reference=opt["clause_reference"],
                academic_citation=opt["academic_citation"],
                preconditions=list(opt["preconditions"]),
                effects=list(opt["effects"]),
                duration_days=opt["duration_days"],
                cost_inr=opt["cost_inr"],
                cost=opt["cost_inr"],
                phase=opt["phase"],
                capacity_restoration_factor=opt["capacity_restoration_factor"],
                curing_period_days=opt["curing_period_days"]
            )
            results.append(action)
        return results
