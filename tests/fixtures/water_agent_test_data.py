"""
Realistic test data sets for Water Agent coordination testing.

This module provides comprehensive test scenarios with realistic agent outputs
that trigger various types of misunderstandings and coordination challenges.
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class MisunderstandingType(Enum):
    """Types of misunderstandings that can occur between agents."""
    TERMINOLOGY_CONFLICT = "terminology_conflict"
    MISSING_REQUIREMENTS = "missing_requirements"
    CONTRADICTORY_LOGIC = "contradictory_logic"
    SCOPE_MISALIGNMENT = "scope_misalignment"
    PRIORITY_CONFUSION = "priority_confusion"
    TECHNICAL_AMBIGUITY = "technical_ambiguity"


@dataclass
class CoordinationTestScenario:
    """A test scenario for coordination between two agents."""
    name: str
    description: str
    first_agent_output: str
    second_agent_output: str
    expected_misunderstanding_types: List[MisunderstandingType]
    expected_severity: str
    scenario_complexity: str  # "simple", "medium", "complex"


class WaterAgentTestDataProvider:
    """Provider for realistic Water Agent test data."""
    
    @staticmethod
    def get_basic_scenarios() -> List[CoordinationTestScenario]:
        """Get basic coordination test scenarios."""
        return [
            CoordinationTestScenario(
                name="garden_planner_earth_agent_terminology",
                description="Garden Planner and Earth Agent use different terminology for same concepts",
                first_agent_output="""
# Garden Planning Analysis

## Task Analysis
The user wants to create a sustainable urban food forest with the following requirements:
- Size: 1000 square meters
- Focus on native species
- Include fruit trees and vegetables
- Implement permaculture principles
- Budget: $10,000

## Structural Components Identified:
1. **Canopy Layer**: Large fruit trees (apple, pear)
2. **Understory**: Smaller fruit trees (plum, cherry)
3. **Shrub Layer**: Berry bushes (blueberry, raspberry)
4. **Herbaceous Layer**: Perennial vegetables and herbs
5. **Ground Cover**: Low-growing edibles
6. **Root Layer**: Root vegetables and tubers
7. **Vine Layer**: Climbing plants (grapes, beans)

## Dependencies:
- Soil analysis must be completed before tree selection
- Irrigation system design depends on tree placement
- Companion planting requires understanding of plant interactions
""",
                second_agent_output="""
# Earth Agent Validation Report

## Task Interpretation Assessment
Based on the Garden Planner output, I'm analyzing a request for sustainable food production system.

## Key Requirements Validation:
- Area: 1000 m² ✓
- Sustainable approach ✓
- Native species focus ✓
- Mixed cultivation system ✓
- Financial constraint: $10,000 ✓

## Structural Analysis:
1. **Tree Canopy**: Primary food producers
2. **Secondary Trees**: Support species
3. **Bush Systems**: Berry production
4. **Perennial Herbs**: Continuous harvest
5. **Ground Plants**: Space optimization
6. **Underground Systems**: Root crops
7. **Climbing Systems**: Vertical space usage

## Critical Dependencies:
- Ground assessment before plant selection
- Water distribution system contingent on plant layout
- Plant synergy analysis required for ecosystem design

## Validation Status: APPROVED with minor terminology standardization needed
""",
                expected_misunderstanding_types=[MisunderstandingType.TERMINOLOGY_CONFLICT],
                expected_severity="LOW",
                scenario_complexity="simple"
            ),
            
            CoordinationTestScenario(
                name="missing_critical_requirements",
                description="Second agent misses critical requirements from first agent",
                first_agent_output="""
# Environmental Analysis Agent Report

## Site Conditions Assessment
Location: Urban rooftop garden, 500m² space

### Critical Environmental Factors:
1. **Wind Exposure**: Severe - roof level winds 40-60 mph average
2. **Weight Limitations**: Maximum 150 lbs per square foot
3. **Sun Exposure**: Full sun 8+ hours daily
4. **Water Access**: Roof drain system only, no irrigation hookup
5. **Temperature Extremes**: -10°F to 105°F range
6. **Structural Requirements**: All installations must be removable (rental property)

### Plant Selection Constraints:
- Wind-resistant species only
- Lightweight growing medium required
- Drought-tolerant varieties essential
- Container-based planting mandatory

### Infrastructure Requirements:
- Wind barriers essential
- Weight distribution systems
- Water collection and storage
- Modular/removable design
""",
                second_agent_output="""
# Root System Architect Recommendations

## Foundation Design
Based on the environmental analysis, I'm designing root systems for optimal plant health.

## Root System Strategy:
1. **Deep Taproot Plants**: Fruit trees with extensive root systems
2. **Fibrous Root Networks**: Vegetables with spreading roots
3. **Companion Root Interactions**: Nitrogen-fixing legumes with heavy feeders

## Soil Preparation:
- 24-inch deep soil beds for tree roots
- Rich, heavy soil amendments for nutrient density
- Permanent raised bed construction
- In-ground irrigation system installation

## Plant Recommendations:
- Large apple and pear trees (20-foot spacing)
- Extensive vegetable plots with deep-rooted varieties
- Permanent greenhouse structure for season extension

## Implementation Timeline:
- Soil excavation and amendment: Month 1-2
- Permanent infrastructure installation: Month 3-4
- Tree planting in permanent locations: Month 5
""",
                expected_misunderstanding_types=[
                    MisunderstandingType.MISSING_REQUIREMENTS,
                    MisunderstandingType.CONTRADICTORY_LOGIC
                ],
                expected_severity="CRITICAL",
                scenario_complexity="complex"
            ),
            
            CoordinationTestScenario(
                name="scope_and_priority_misalignment",
                description="Agents have different understanding of project scope and priorities",
                first_agent_output="""
# Tree Placement Planner - Phase 1 Foundation

## Primary Objective
Establish the foundational framework for a 3-phase urban farming project:
- Phase 1 (Current): Demonstration plot - 100m²
- Phase 2 (Year 2): Expansion to 500m²
- Phase 3 (Year 3): Community scale - 2000m²

## Phase 1 Placement Strategy:
Focus on EDUCATIONAL DEMONSTRATION with:
1. One example of each forest layer
2. Quick-growing varieties for immediate results
3. Low-maintenance, beginner-friendly species
4. Maximum visual impact for community engagement

## Tree Placement:
- 1 dwarf apple tree (demonstration only)
- 2 berry bushes (visual appeal)
- Herb spiral (educational feature)
- Container gardens (mobility for events)

## Success Metrics for Phase 1:
- Community engagement events hosted
- Educational workshops conducted
- Volunteer participation numbers
- Social media visibility

## Phase 1 Budget Allocation:
- 60% education and community materials
- 30% plants and basic infrastructure
- 10% maintenance and events
""",
                second_agent_output="""
# Final Structural Breakdown - Production Optimization

## System Design Objective
Maximize food production efficiency for urban food security initiative.

## Production-Focused Layout:
Optimizing for maximum yield per square meter across full site:

### High-Yield Tree Placement:
- 15 full-size fruit trees for maximum production
- Dense planting schedule for optimal space utilization
- Focus on storage crops (apples, nuts) for year-round supply

### Production Infrastructure:
- Commercial-grade irrigation system
- Soil amendments for maximum fertility
- Season extension structures (hoop houses, cold frames)
- Processing and storage facilities

### Efficiency Metrics:
- Pounds of food produced per square meter
- Caloric output per dollar invested
- Storage life and preservation capacity
- Market value of harvest

### Resource Allocation:
- 80% production infrastructure and permanent plantings
- 15% soil preparation and amendments
- 5% basic tools and maintenance

## Implementation Priority:
Immediate full-scale production setup for food security goals.
""",
                expected_misunderstanding_types=[
                    MisunderstandingType.SCOPE_MISALIGNMENT,
                    MisunderstandingType.PRIORITY_CONFUSION
                ],
                expected_severity="HIGH",
                scenario_complexity="medium"
            )
        ]
    
    @staticmethod
    def get_complex_scenarios() -> List[CoordinationTestScenario]:
        """Get complex coordination test scenarios with multiple issues."""
        return [
            CoordinationTestScenario(
                name="multi_layered_misunderstanding",
                description="Multiple types of misunderstandings in technical planning",
                first_agent_output="""
# Advanced Permaculture Design - Technical Specifications

## System Architecture Overview
Implementing a closed-loop aquaponics-permaculture hybrid system with AI monitoring.

### Technical Components:
1. **Aquaponics Module**: 2000L fish tanks with automated nutrient cycling
2. **Sensor Network**: pH, nutrient levels, moisture sensors with IoT connectivity
3. **Climate Control**: Automated greenhouse with HVAC integration
4. **Water Management**: Rainwater harvesting with UV sterilization
5. **Energy Systems**: Solar panels with battery backup for 72-hour autonomy

### Plant Selection Algorithm:
- Machine learning models for optimal plant placement
- Companion planting matrices based on biochemical interactions
- Growth optimization through controlled environment variables
- Yield prediction modeling with weather integration

### Technical Dependencies:
- Electrical infrastructure (220V, 50A service)
- Internet connectivity for cloud-based monitoring
- Specialized growing medium (coconut coir, expanded clay pebbles)
- Professional installation of aquaponics equipment
- Building permits for structural modifications

### Performance Metrics:
- Nutrient cycling efficiency (target: 95% nitrogen retention)
- Energy consumption optimization (target: net-zero energy)
- Yield per square foot (target: 3x traditional farming)
- System uptime (target: 99.5% operational availability)

### Budget Requirements:
- Technology infrastructure: $25,000
- Professional installation: $15,000
- Specialized materials: $10,000
- Permitting and engineering: $5,000
Total: $55,000
""",
                second_agent_output="""
# Simple Container Garden Implementation

## Basic Setup Plan
Creating an easy-to-maintain container garden suitable for beginners.

### Container Selection:
- Standard plastic pots (5-gallon size)
- Basic potting soil from garden center
- Simple hand tools for planting and maintenance

### Plant Choices:
- Easy vegetables: tomatoes, lettuce, herbs
- Proven varieties that grow well in containers
- Purchased as seedlings from local nursery

### Watering System:
- Hand watering with garden hose
- Simple drip irrigation if needed
- Rain gauge for monitoring

### Maintenance Plan:
- Weekly watering and feeding
- Basic organic fertilizer application
- Seasonal replanting of annuals

### Cost Estimate:
- Containers and soil: $200
- Plants and seeds: $100
- Basic tools: $50
- Fertilizer and supplies: $50
Total: $400

### Success Goals:
- Grow enough herbs for family cooking
- Learn basic gardening skills
- Enjoy outdoor hobby activity
- Save money on grocery vegetables

This approach focuses on simplicity and learning rather than complex systems.
""",
                expected_misunderstanding_types=[
                    MisunderstandingType.SCOPE_MISALIGNMENT,
                    MisunderstandingType.TECHNICAL_AMBIGUITY,
                    MisunderstandingType.PRIORITY_CONFUSION,
                    MisunderstandingType.CONTRADICTORY_LOGIC
                ],
                expected_severity="CRITICAL",
                scenario_complexity="complex"
            ),
            
            CoordinationTestScenario(
                name="conflicting_technical_approaches",
                description="Agents propose contradictory technical solutions",
                first_agent_output="""
# Soil Management Strategy - Organic Regenerative Approach

## Philosophy: Work with Natural Systems
Building soil health through biological processes and minimal intervention.

### Soil Building Strategy:
1. **No-Till Methodology**: Preserve soil structure and microbial networks
2. **Cover Crop Integration**: Year-round living soil coverage
3. **Composting Systems**: On-site organic matter processing
4. **Mycorrhizal Inoculation**: Beneficial fungal network establishment
5. **Beneficial Insect Habitat**: Integrated pest management through biodiversity

### Organic Inputs Only:
- Aged animal manures
- Green manure crops
- Rock dust minerals
- Kelp meal and fish emulsion
- Worm castings and compost tea

### Timeline for Soil Development:
- Year 1: Cover crops and organic matter addition
- Year 2: Biological activity establishment
- Year 3: Full regenerative system maturity
- Years 4+: Self-sustaining soil ecosystem

### Expected Outcomes:
- 50% increase in soil organic matter by year 3
- Elimination of external fertilizer dependence
- Enhanced water retention and drought resistance
- Carbon sequestration and climate benefits

### Prohibited Inputs:
- Synthetic fertilizers
- Chemical pesticides/herbicides
- Genetically modified materials
- Non-organic soil amendments
""",
                second_agent_output="""
# Precision Agriculture Implementation - Technology-Enhanced Production

## Philosophy: Scientific Optimization for Maximum Efficiency

### Precision Soil Management:
1. **Soil Testing Protocol**: Monthly analysis of 15 key nutrient parameters
2. **Synthetic Fertilizer Program**: Custom blended NPK ratios based on soil data
3. **Chemical Pest Control**: Targeted applications using IPM thresholds
4. **Growth Regulators**: Hormone treatments for optimal plant development
5. **Hydroponic Integration**: Soilless systems for ultimate control

### Technology Integration:
- GPS-guided nutrient application
- Drone monitoring for pest and disease detection
- Automated irrigation with nutrient injection
- Climate-controlled growing environments
- Real-time soil sensor networks

### Chemical Inputs Program:
- Precision fertilizer applications (21-7-14 NPK base)
- Selective herbicide treatments for weed control
- Targeted fungicide applications
- Growth hormone supplements
- Soil sterilization protocols

### Implementation Schedule:
- Month 1: Comprehensive soil analysis and baseline establishment
- Month 2: Technology installation and calibration
- Month 3: Begin precision fertilization program
- Months 4-12: Continuous monitoring and optimization

### Performance Targets:
- 200% yield increase over organic methods
- 90% reduction in crop loss from pests/disease
- Precise nutrient management eliminates waste
- Year-round production capability

This approach maximizes productivity through scientific methods and proven technologies.
""",
                expected_misunderstanding_types=[
                    MisunderstandingType.CONTRADICTORY_LOGIC,
                    MisunderstandingType.PRIORITY_CONFUSION,
                    MisunderstandingType.TECHNICAL_AMBIGUITY
                ],
                expected_severity="CRITICAL",
                scenario_complexity="complex"
            )
        ]
    
    @staticmethod
    def get_edge_case_scenarios() -> List[CoordinationTestScenario]:
        """Get edge case scenarios for stress testing."""
        return [
            CoordinationTestScenario(
                name="empty_output_scenario",
                description="One agent produces minimal output",
                first_agent_output="Task completed. No issues found.",
                second_agent_output="""
# Comprehensive Analysis Report

## Detailed Assessment
Based on the previous analysis, I have conducted an extensive review of all aspects of the project requirements and constraints.

### Technical Considerations:
1. Multiple factors need consideration
2. Various approaches are possible
3. Several constraints must be evaluated
4. Different methodologies could apply

### Recommendations:
- Further analysis needed
- Additional consultation required
- More information necessary
- Continue investigation
""",
                expected_misunderstanding_types=[MisunderstandingType.MISSING_REQUIREMENTS],
                expected_severity="MEDIUM",
                scenario_complexity="simple"
            ),
            
            CoordinationTestScenario(
                name="very_long_technical_output",
                description="Agents produce extremely detailed technical outputs",
                first_agent_output="x" * 5000 + """
### Technical Specifications (continued):
The detailed analysis above outlines the comprehensive requirements for implementing a multi-phase agricultural system with integrated technology components, environmental monitoring, and sustainable practices that must be coordinated across multiple stakeholder groups while maintaining compliance with local regulations and optimization for both short-term productivity and long-term soil health.
""",
                second_agent_output="y" * 5000 + """
### Implementation Strategy (continued):
Following the extensive technical analysis provided, the implementation approach requires careful coordination of multiple simultaneous processes including infrastructure development, biological system establishment, technology integration, and stakeholder training programs that must be sequenced to avoid conflicts while maximizing efficiency and ensuring successful project outcomes.
""",
                expected_misunderstanding_types=[MisunderstandingType.TECHNICAL_AMBIGUITY],
                expected_severity="LOW",
                scenario_complexity="complex"
            ),
            
            CoordinationTestScenario(
                name="multilingual_terminology",
                description="Agents use different language conventions and technical terms",
                first_agent_output="""
# Análisis de Permacultura - Diseño Integrado

## Zones de Cultivo:
1. **Zone 1**: Huerta intensiva (vegetables intensivos)
2. **Zone 2**: Arboles frutales (fruit trees)
3. **Zone 3**: Crops extensivos (extensive farming)
4. **Zone 4**: Foresterie (silviculture)
5. **Zone 5**: Wild ecosystem preservation

## Techniques Applied:
- Companionage planting (companion planting)
- Swales y berms pour water retention
- Polyculture systems avec biodiversité
- No-till methods (sin labranza)
- Compostage et vermiculture

## Ressources Needed:
- Semillas (seeds) from heritage varieties
- Tools pour cultivation organique
- Materials for infrastructure (bamboo, stone)
- Water collection systems (cisterns)
""",
                second_agent_output="""
# Systematic Agricultural Implementation

## Cultivation Zones:
1. **Zone 1**: Intensive horticultural plots
2. **Zone 2**: Orchard development area
3. **Zone 3**: Field crop production
4. **Zone 4**: Agroforestry section
5. **Zone 5**: Conservation area

## Methods Implementation:
- Intercropping strategies
- Contour farming with water management
- Diversified cropping systems
- Conservation tillage practices
- Organic waste recycling

## Resource Requirements:
- Certified seed stock
- Agricultural implements
- Construction materials
- Irrigation infrastructure
""",
                expected_misunderstanding_types=[
                    MisunderstandingType.TERMINOLOGY_CONFLICT,
                    MisunderstandingType.TECHNICAL_AMBIGUITY
                ],
                expected_severity="MEDIUM",
                scenario_complexity="medium"
            )
        ]
    
    @staticmethod
    def get_all_scenarios() -> List[CoordinationTestScenario]:
        """Get all test scenarios."""
        return (
            WaterAgentTestDataProvider.get_basic_scenarios() + 
            WaterAgentTestDataProvider.get_complex_scenarios() + 
            WaterAgentTestDataProvider.get_edge_case_scenarios()
        )
    
    @staticmethod
    def get_expected_misunderstanding_for_scenario(scenario: CoordinationTestScenario) -> Dict[str, Any]:
        """Generate expected misunderstanding detection results for a scenario."""
        misunderstandings = []
        first_agent_questions = []
        second_agent_questions = []
        
        for i, misunderstanding_type in enumerate(scenario.expected_misunderstanding_types):
            misunderstanding_id = f"M{i+1}"
            
            if misunderstanding_type == MisunderstandingType.TERMINOLOGY_CONFLICT:
                misunderstandings.append({
                    "id": misunderstanding_id,
                    "description": "Agents use different terminology for the same concepts",
                    "severity": scenario.expected_severity,
                    "context": "Different terms used for similar concepts"
                })
                first_agent_questions.append({
                    "misunderstanding_id": misunderstanding_id,
                    "question": "Can you clarify the specific terminology you're using?"
                })
                second_agent_questions.append({
                    "misunderstanding_id": misunderstanding_id,
                    "question": "How do you interpret the terminology from the first agent?"
                })
                
            elif misunderstanding_type == MisunderstandingType.MISSING_REQUIREMENTS:
                misunderstandings.append({
                    "id": misunderstanding_id,
                    "description": "Critical requirements from first agent not addressed by second agent",
                    "severity": scenario.expected_severity,
                    "context": "Missing critical constraints or requirements"
                })
                first_agent_questions.append({
                    "misunderstanding_id": misunderstanding_id,
                    "question": "Which requirements are most critical for the second agent to address?"
                })
                second_agent_questions.append({
                    "misunderstanding_id": misunderstanding_id,
                    "question": "Have you considered all the constraints mentioned by the first agent?"
                })
                
            elif misunderstanding_type == MisunderstandingType.CONTRADICTORY_LOGIC:
                misunderstandings.append({
                    "id": misunderstanding_id,
                    "description": "Agents propose conflicting or contradictory approaches",
                    "severity": scenario.expected_severity,
                    "context": "Contradictory technical approaches or logic"
                })
                first_agent_questions.append({
                    "misunderstanding_id": misunderstanding_id,
                    "question": "How do you resolve the apparent conflict with the second agent's approach?"
                })
                second_agent_questions.append({
                    "misunderstanding_id": misunderstanding_id,
                    "question": "How does your approach align with the first agent's recommendations?"
                })
                
            elif misunderstanding_type == MisunderstandingType.SCOPE_MISALIGNMENT:
                misunderstandings.append({
                    "id": misunderstanding_id,
                    "description": "Agents have different understanding of project scope or scale",
                    "severity": scenario.expected_severity,
                    "context": "Misaligned understanding of project scope"
                })
                first_agent_questions.append({
                    "misunderstanding_id": misunderstanding_id,
                    "question": "Can you clarify the intended scope and scale of the project?"
                })
                second_agent_questions.append({
                    "misunderstanding_id": misunderstanding_id,
                    "question": "How do you understand the scope described by the first agent?"
                })
                
            elif misunderstanding_type == MisunderstandingType.PRIORITY_CONFUSION:
                misunderstandings.append({
                    "id": misunderstanding_id,
                    "description": "Agents prioritize different aspects of the project",
                    "severity": scenario.expected_severity,
                    "context": "Different prioritization of project goals"
                })
                first_agent_questions.append({
                    "misunderstanding_id": misunderstanding_id,
                    "question": "What are the top priorities you want the second agent to focus on?"
                })
                second_agent_questions.append({
                    "misunderstanding_id": misunderstanding_id,
                    "question": "How do you prioritize the various goals mentioned by the first agent?"
                })
                
            elif misunderstanding_type == MisunderstandingType.TECHNICAL_AMBIGUITY:
                misunderstandings.append({
                    "id": misunderstanding_id,
                    "description": "Technical specifications or methods are ambiguous or unclear",
                    "severity": scenario.expected_severity,
                    "context": "Ambiguous technical specifications"
                })
                first_agent_questions.append({
                    "misunderstanding_id": misunderstanding_id,
                    "question": "Can you provide more specific technical details?"
                })
                second_agent_questions.append({
                    "misunderstanding_id": misunderstanding_id,
                    "question": "How do you interpret the technical specifications provided?"
                })
        
        return {
            "misunderstandings": misunderstandings,
            "first_agent_questions": first_agent_questions,
            "second_agent_questions": second_agent_questions
        }