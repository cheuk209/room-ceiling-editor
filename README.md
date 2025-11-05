# room-ceiling-editor
Brief Instructions
1. Submit your answers in a git repository and share them with us by emailing the link 
of the git repository or inviting us to your git repository. 
2. Follow good development practices and use this take home as a opportunity to 
demonstrate your knowledge of good practices.
3. Do not need to be fully featured, A simple prototype that demonstrates your skills is 
sufficient.
4. Feel free to use any tools and frameworks that will help you do the work efficiently.
Task: Room ceiling editor
Figure 1Example of a ceiling grid data for a room
The components are as follows:
1. Lights 
2. Air supply points
3. Air return points
4. Smoke detectors
5. Invalid ceiling grids – Empty but not valid position for any components.

We have a machine learning pipeline that supports multiple models that take the input 
ceiling grid data (may or may not be with components) and use multiple machine learning 
models to generate the result. In some cases, you will have multiple models that does the 
same task that is multiple models for placing lights and picks out the best or valid one. In 
addition, you will have to run multiple models in a series to have a completed building json.
Design and implement a ML pipeline for this task. It doesn’t have to be complete, use 
illustrations and diagrams to complete your project.

  ## Quick Start

  ### Prerequisites
  - Python 3.11+
  - [uv](https://github.com/astral-sh/uv) (recommended) or pip
  - Docker & Docker Compose

  ### Local Development Setup

  #### Using uv (Recommended)
  ```bash
  # Install dependencies
  uv sync

  # Run the application
  uv run python -m src.api.app