# Complete System Flow Breakdown

- Application opens with display (intermediate results are updated in real-time)

- User submits idea prompt

Phase 1 Guideline Establishment
- Garden Planner agent elaborates user task to produce project overview
	- Earth agent validates project overview against user request
	- if Earth agent detect major issues, it provides feedback to the Garden Planner for in-place refinement
- Garden Environmental Analysis agent analyzes requirements
- Garden Root System agent creates core data flow
- Tree Placement Planner agent delineates structural components
	- Fire agent analyzes structural components for overcomplexity
- if Fire agent detects overcomplex components, it decomposes them in-place
- all agents undergo output validation and self-reflection / revision
- agent self-reflection has a maximum number of iterations (e.g., three attempts)

- Phase 1 final outputs are saved and returned (not yet refinement)

- System starts phase 0 analysis feedback
	- Sun agent - analyzes initial description issues / gaps
	- Shade agent - analyzes initial description guideline conflicts
	- Soil agent - analyzes core requirement issues / gaps
	- Microbial agent - analyzes core requirement guideline conflicts
	- Worm agent - analyzes core data flow issues / gaps
	- Mycelial agent - analyzes core data flow guideline conflicts
	- Tree agent - analyzes structural component issues / gaps
	- Bird agent - analyzes structural component guideline conflicts
	- Evolution agent - adaptation meta-planning based on the rest of phase 0
	- Pollinator agent - analyzes opportunities for guideline optimization
	- all phase 0 agents work in parallel except for the Evolution agent
	- all agents undergo output validation and self-reflection / revision

- Phase 0 final outputs are saved and returned

- System starts phase 1 refinement 
	- Garden Foundation Refinement agent refines phase 1 operations (system recursion)
- refinement agent receives analysis feedback and determines whether critical system issues persist
- if major issues exist, they are traced back to the original agent responsible who receives refinement feedback and is prompted to revise their original output
- downstream processing resumes as usual, wiping the previous outputs from memory
- refinement has a maximum number of iterations to prevent system stalling, on the final attempt, refinement metadata is appended to the guidelines output for future reference

SPECIAL SYSTEM AGENT - Water agent facilitates agent cooperation by mediating between all sequential agents (e.g., Garden Planner & Earth agent, all phase one agents, refinement agent & the agent targeted for refinement), this holds true for the entire system not just phase one

SPECIAL SYSTEM AGENT - Air agent facilitates critical phase operations by providing succinct summaries for major guideline changes (e.g. refinement decisions, in-place revisions, Earth agent guideline update, Fire agent component decomposition), this condensed historical context is leveraged by high-level decision makers, i.e., Earth / Fire agents and refinement agents. This holds true for all phases, not just phase one.

Phase 2 System Development
	- System starts subphase 2a component guideline establishment
		- Tree Bed Planner agent elaborates structural component description
		- Tree Bed Environmental Analysis agent analyzes component requirements
		- Tree Bed Root System agent creates core component data flow
		- Flower Placement Planner agent delineates component features
		- Tree Bed Foundation Refinement agent refines subphase 2a operations
	- System conducts subphase 2a phase zero analysis feedback
	- Phase zero final outputs are saved and returned
	- System conducts subphase 2a refinement (maximum number of iterations)
	- After maximum number of refinement iterations or if no major issues are flagged, final subphase 2a outputs are saved and returned
	
- System proceeds through subphase 2a for all structural components

- After all component guidelines are established, system starts subphase 2b component test creation
	- System starts nested phase 3 call for feature cultivation of component tests
- (See below for phase 3)

- After components tests have been created, the system starts subphase 2c component code creation using test-driven development via nested phase 3 calls with tests provided

- System proceeds through 2b and 2c for all structural components

- As dependent components are created, integration tests can be created as well
	- Integration tests are included with the component tests provided to phase 3

- Once all components are created and all component / integration tests pass, the system starts subphase 2e system test creation which creates system tests via a nested phase 3 call

- Once system tests are created, subphase 2f system testing leverages the phase 3d feature debugging loop to address the remaining errors similar to how integration tests and components tests leverage phase 3 testing / debugging

	- Once all system tests are passing, the system starts subphase 2g deployment test creation just like subphase 2e but to test the actual deployment of the system once it is running

	- Once deployment tests are created, subphase 2h deployment testing first deploys the fully built software project at hand and then controls it using command line arguments to run the deployment tests
		- Failed deployment or deployment tests are fed into the phase 3d feature debugging loop similar to subphase 2f

	- Once all deployment tests are passing, phase two saves the final code and returns to the user
		
Phase 3 Feature Cultivation
	- System starts subphase 3a feature guideline establishment
- Flower Bed Planner agent elaborates component feature description
		- Flower Bed Environmental Analysis agent analyzes feature requirements
		- Flower Bed Root System Architect agent creates core feature data flow
		- Bud Placement Planner agent delineates feature functionality
		- Flower Bed Foundation Refinement agent refines subphase 3a operations
- System conducts subphase 3a phase zero analysis feedback and refinement
- Final subphase 3a outputs are saved and returned

- System proceeds through subphase 3a for all non-dependent features in parallel, dependent features in series

- After all feature guidelines are established, system starts subphase 3b feature test creation
	- System starts nested phase 4 call for code implementation of feature tests
	- (See below for phase 4)

- Once phase 4 returns initial feature test code, system starts subphase 3c feature code creation with test-driven development via a nested phase 4 call with feature tests provided

- After phase four returns feature code, the feature tests are run again to validate the feature code in case of phase 4 failure, and invalid results are fed into the subphase 3d feature debugging loop
	- Feature Analysis agent targets root cause of issues (test vs code)
	- Feature Refinement agent recommends course of actions
	- Feature Debugging agent implements the suggested fix
	- all subphase 3d agents are reflective and there is a maximum number of feature debugging iterations
	- any still failing features after the maximum number of iterations undergo Fire decomposition into subfeatures
		- this entails a change in guidelines, triggering Earth agent validation
		- if confirmed, the change in guidelines is propagated through the system via the established data flow, facilitated by the Water agent which provides succinct contextual information on the update at hand to the original agents responsible for revising their own guidelines
	- all operations on features (feature tests, initial code, Water updates, Fire decomposition, etc.) are saved by the Air agent which summarizes each piece of information for the system to compile into a succinct record of history for each feature
	- this summarized feature history is leveraged by the subphase 3d feature debugging loop, the Fire feature decomposition process, subphase 3e growth monitoring and subphase 3f natural selection for continuity
- Periodically, in subphase 3e growth monitoring, the development progress of all parallel features is measured by objective and subjective metrics, e.g., the test failure rate and a qualitative review of performance
	- Feature Audit agent reviews the performance of an individual feature based on its objective metrics and summarized history

- After feature review, in subphase 3f natural selection, the Natural Selection agent identifies the lowest performing features and the highest performing features
- the low performance features are removed to be replaced in the next iteration of feature cultivation
- the high performance features are enhanced by a round of additional development based on the summarized feature history

- As dependent features are implemented and pass feature tests, feature integration tests can be created. These are included with the feature tests provided to phase 4 for test-driven development

	- Once all features are implemented and all feature tests are passing, if component/integration tests were provided by phase 2, then these are now run as part of the phase 3d feature debugging loop as well

- Once all features are created and all tests are passing, the final phase 3 feature code is saved and returned to phase 2

Phase 4 Code Construction
- System starts subphase 4a feature code creation. There are five subphases in phase 4:
	- 4a Formatting Verification
	- 4b Style Verification
	- 4c Logic Verification
	- 4d Type-Correctness Verification
	- 4e Security Verification
	- Each subphase has a different static compiler used to validate software development standards of increasing complexity, e.g., in 4a Black formats the code, in 4b Flake8 checks basic style and simple errors, in 4c Pylint performs deep logical analysis, in 4d MyPy verifies type correctness and in 4e Bandit checks for security issues
		- In each phase four subphase, implementation is followed by automatic testing of the code (prior to static compilation) if tests are provided, otherwise static compilation verification begins immediately
		- In both cases, test errors / compilation flags are used to refine the code via the phase 4 agents:
			- Error Analysis agent
			- Code Refinement agent
			- Code Debugging agent
			- These agents are all specialized for their role, e.g., logical verification or feature testing
			- Phase 4 agent specializations:
				- Specialized agent suites for the five subphases
				- Specialized agent suite for feature testing
				- Specialized agent suite for feature integration testing

- After all feature / feature integration tests are passing, static compilation verification begins. Each subphase has a maximum number of iterations for testing loops as well as a limit for static compilation verification iterations to avoid system stalling
- After all compiler flags / tests are passing or if the maximum number of iterations is reached, the final feature code is saved and returned to phase 3. If the maximum number of iterations is reached without the code being valid, a summary of the remaining errors is included in the Air agent feature history for future reference

Miscellaneous

- Periodically, the System Monitoring agent provides system health reports to the user

- If the application encounters a system error, the System Monitoring agent selects the appropriate recovery strategy for the situation