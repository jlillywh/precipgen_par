---
inclusion: always
---

# PrecipGen Project Principles

## Core Mission
Make it easy for hydrologic practitioners to find, download, and analyze daily precipitation time series from NOAA GHCN database to produce solid input parameters for PrecipGen stochastic simulation.

## Guiding Principles

### Simplicity First
- Keep the tool focused on its core mission
- Don't add features beyond current scope
- Make the interface intuitive and easy to understand
- Clear, straightforward workflows for practitioners

### Code Organization
- Structure should impress a German C++ programmer
- Clean package hierarchy with clear separation of concerns
- Consistent naming conventions
- Well-documented modules and functions

### Robustness
- Reliable data handling and error management
- Comprehensive testing coverage
- Graceful degradation when services are unavailable
- Clear error messages for users

### Scalability Ready
- Architecture that can grow if needed
- Modular design for easy extension
- Efficient data processing patterns
- Performance considerations built-in

## Architecture Guidelines
- `precipgen.data`: Data acquisition and management
- `precipgen.core`: Analysis algorithms and statistics
- `precipgen.cli`: Command-line interface

## Quality Standards
- All imports use package structure (`from precipgen.x import y`)
- Tests pass before any release
- CHANGELOG.md updated with every version
- Documentation kept current with code changes
