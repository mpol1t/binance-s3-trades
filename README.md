# Project Name
> A brief description of what the project does and who it's for.

## Installation
This project uses [Poetry](https://python-poetry.org/) for dependency management and packaging. To install this project, first ensure that you have Poetry installed on your system. If you do not have Poetry installed, you can install it by following the instructions on the [official Poetry documentation](https://python-poetry.org/docs/).

Once Poetry is installed, you can install this project by running:
```bash
poetry install
```

This command will install all dependencies required for the project.

## Usage
Here's a quick start guide or basic usage example:
```python
from project_name import main_function
main_function()
```

Ensure to replace `project_name` and `main_function` with actual names relevant to your project.

## Development Setup
To set up a local development environment for this project, follow these steps:

1. Clone the project repository:
```bash
git clone https://github.com/yourusername/projectname.git
cd projectname
```

2. Install the project and its dependencies using Poetry:
```bash
poetry install
```

## Running Tests
This project uses pytest for testing. To run tests, use the following command:
```bash
poetry run pytest
```

## Pre-commit Hooks
This project uses pre-commit hooks to ensure code quality and consistency. After cloning the project, you need to set up pre-commit on your local machine:

1. Install the git hook scripts by running:
```bash
pre-commit install
```

This command sets up the pre-commit hooks for your local repository. Now, pre-commit will run automatically on `git commit` to check your changes against the configured hooks.

## Contributing
We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests to us.

## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.


## After Cloning [!]

Must update all dependecies using:

```bash
poetry update
```

Change/set up secrets!
