# CLAUDE.md

# Forest For The Trees (FFTT) High-Level Description of System Operation
Forest For The Trees (FFTT) is a nature-inspired Python application designed to allow for automated software development via a sophisticated system of LLM agent workflows. The system operation takes place in four phases, however, phases 3 and 4 are nested within phase 2 so that when phase two is complete, the desired software project will be fully implemented and deployed in a test-driven manner. 

## Phase 1
Phase 1 establishes foundational guidelines, phase 2 systematically develops the software project, phase 3 nested calls flexibly create feature sets, and phase 4 nested calls build feature tests / implementations with static compilers in the loop. To make software development into an atomic and compositional process, the overall project is defined as a set of structural components (phase 1), components are defined as a set of features (phase 2), and features are defined as a set of functionalities (phase 3). In addition, components and features also have a dependencies field that lists other components or features that they depend upon. These dependencies are automatically validated by the system dependency tracking mechanism, which receives the output of the structural breakdown agent responsible and returns feedback to it for in-place correction. 

## Phase 0
The system also has a phase 0, which serves as quality assurance for the various phase refinement agents, e.g., the final phase one agent. Phase 1 begins by creating foundation guidelines prior to testing and implementation. This consists of a series of agents which append their output to pass to the next agent. Specifically, this includes agents for initial task elaboration, requirements analysis, data flow analysis, structural breakdown and refinement. These five agents, along with specialized phase zero feedback agents, form a core pre-processing loop motif for the elaboration of guidelines, in this case, foundational elaboration. Phase 0 includes specialized agents which analyze various aspects of the elaboration process, specifically, guideline conflicts or gaps, e.g., structural breakdown gaps or structural breakdown conflicts with regards to the other foundational guidelines. Notice that different sets of specialized phase 0 agents are used for each distinct elaboration motif contained within the system architecture. Phase zero also includes two other specialized feedback agents, a component optimization analysis agent and an evolutionary agent which synthesizes the output of all other phase 0 agents to propose coordinated strategies for improvement. All phase 0 agent outputs are passed to the refinement agent responsible for that elaboration loop / motif. Refinement agents serve as decision bottlenecks in the system operation that allow for minimal agent intervention within the system. These refinement agents, if they detect critical flaws within the given guidelines, trace the root cause of the issue to return the system operation to the proper subphase for operations to resume from. This recursive process has a maximum number of refinement loops that are allowed before the output is passed as is along with refinement metadata. 

## Phase 2
Phase 2 picks up where phase 1 left off, having received a list of foundational structural components, the system begins the process of component creation in series, one structural component at a time starting from the most fundamental to the least. Component creation consists of a component elaboration loop, then component test creation, then component test-driven implementation. As components are generated, the system tracks the build progress of the application and the dependency between components / features, which is facilitated by dependencies being part of the initial structural breakdown provided by phase one and phase elaboration. Once multiple components have been implemented, integration tests can begin to be created and used for system verification. Once all components have been created and integrated, system tests can be created and used for additional verification. Once all system tests have passed, deployment tests can be created, then the system deploys the newly created application and the results are used to validate deployment expectations before finally returning to the user. This concludes phase two, which is the main systematic development process, however, phase 3 and phase 4 are nested processes used during phase 2 to actually build out the various tests and component implementations.

## Phase 3
Specifically, similar to how the overall project is defined as a set of components, each component is defined as a set of features. In phase 3, non-dependent features are developed in parallel, each with their own elaboration, feature test creation, implementation and testing processes. At periodic growth intervals, the objectively low-performance features are replaced, either conceptually, e.g., via feature reuse, or pragmatically, e.g., via feature recreation. This evolutionary parallel growth development process is supported by another specialized suite of phase zero agents which report to the phase 3 ‘natural selection’ refinement agent responsible for feature optimization decisions. Phase 3 also includes feature integration tests, once multiple dependent features are created. 

## Phase 4
The actual process of feature code implementation in phase 3 is delegated to nested phase four calls. Since phase three allows for parallel feature development, this means phase four code implementation occurs in parallel as well. Phase 4 is a tiered process of static code generation and compilation, whereby feature code is generated and has to undergo five levels of static compilation verification, each of increasing complexity. Specifically, in order, the compilers focus on formatting, style, logic, type correctness, and security. While phase four does not have a phase zero subphase, it does have specialized agents for compilation analysis and debugging, as well as a general refinement agent for system recursion. After all static compilers are passing, or after a maximum number of refinement loops, the final feature code is returned to phase 3 to serve as code implementation. Besides the various feedback refinement mechanisms described above, many of the complex or essential agents undergo automatic self-reflection on their initial outputs. This includes all foundational agents, e.g., all elaboration agents, all refinement agents, all code generation agents, and some important phase zero feedback agents, i.e., the ‘evolution’ agent and the data flow verification agent. In addition, a specialized ‘system monitoring’ agent periodically processes system metrics to give reports and acts in the case of system failure to recommend the appropriate recovery strategy based on recent history.

# File Breakdown
## Resource Modules:
common.py - dependencies: None
errors.py - dependencies: None
events.py - dependencies: common, errors
monitoring.py - dependencies: common, errors, events
base.py - dependencies: common, errors, events, monitoring
managers.py - dependencies: common, events, base
state.py - dependencies: common, events, base, monitoring
version.py - dependencies: common, errors, events, state, monitoring

## Core Modules:
api.py - dependencies: None
agent.py - dependencies: resources, agent validation, api
agent_validation.py - dependencies: resources, api
dependency.py - dependencies: resources
component.py - dependencies: resources, dependency
feature.py - dependencies: resources, dependency, component
system_error_recovery.py - dependencies: resources, agent, agent validation
interface.py - dependencies: resources, system error recovery, agent, agent validation, component, feature
phase_zero.py - dependencies: resources, interface
phase_four.py - dependencies: resources, interface
phase_three.py - dependencies: resources, interface, phase zero, phase four
phase_two.py - dependencies: resources, interface, phase zero, phase three
phase_one.py - dependencies: resources, interface, phase zero, phase two
display.py - dependencies: resources, interface
main.py - dependencies: resources, display, phase one

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Lint/Test Commands

- Run all tests: `python -m pytest -xvs --log-cli-level=INFO --log-file=test.log --color=yes`
- Run single test file: `python -m pytest -xvs tests/path/to/test_file.py`
- Run specific test: `python -m pytest -xvs tests/path/to/test_file.py::test_function_name`
- Run tests with async support: `python -m pytest -xvs --asyncio-mode=auto tests/path/to/test_file.py`

## Code Style Guidelines

- **Imports**: Group imports by stdlib, third-party, then local. Sort alphabetically within groups.
- **Formatting**: Use 4 spaces for indentation. Maximum line length is 120 characters.
- **Types**: Use type hints for function parameters and return values. Import typing modules.
- **Naming**: Use snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants.
- **Error Handling**: Use try/except blocks with specific exception types. Log errors with appropriate severity.
- **Async**: Use asyncio for asynchronous code. Prefer async/await over callbacks.
- **Logging**: Use the logging module with appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- **Documentation**: Use docstrings for classes and functions. Follow Google style guide format.