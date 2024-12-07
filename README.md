# CDK2Git

CDK2Git is a Python Flask API that makes it possible to use [CDK](https://cdk.tf/) with with legacy infrastructure pipeline tools that only support Git.

When a Git client attempts to clone a repository from a CDK2Git API endpoint, the API will synthesize the CDKTF code into a Terraform module before sending it back to the client as a Git repository module.

## Features

- **CDKTF Synthesis**: Automatically synthesizes Terraform configurations from CDKTF code
- **Git Protocol Support**: 
  - Serves synthesized configurations via native Git protocol
  - Proper HEAD and branch references
  - Full Git object handling (blobs, trees, commits)
  - Pack file generation and streaming
- **Error Handling**: Comprehensive error handling and logging throughout the process
- **Temporary Directory Management**: Clean handling of synthesis output in temporary directories

## Usage

Clone a CDKTF project:
```bash
git clone http://localhost:5000/your-cdktf-project
```

The server will:
1. Synthesize the Terraform configuration from your CDKTF code
2. Create Git objects from the synthesized files
3. Serve the configuration via Git protocol

## Architecture

- **Flask Server**: Handles HTTP requests and Git protocol endpoints
- **CDKTF Handler**: Manages CDKTF synthesis process
- **Git Handler**: 
  - Handles Git protocol implementation
  - Manages object creation and pack generation
  - Provides proper Git references and capabilities

## Development Status

- Basic Git protocol implementation
- CDKTF synthesis integration
- Git object handling
- HEAD and branch references
- Push operation support
- Branch management
- Authentication and access control

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Development Guidelines

Before making any changes to the codebase:
1. Review `STANDARDS.md` for project coding standards and guidelines
2. Consider the following aspects:
   - Does the change duplicate existing functionality?
   - How does it integrate with the existing codebase?
   - Are there potential limitations or issues with the approach?
3. Document all changes in `CHECKPOINTS.md`
4. Follow the UI/UX guidelines for any user-facing changes

## Development Environment Setup

1. Create and activate the virtual environment:
   ```bash
   python -m venv ./venv
   source ./venv/bin/activate  # On Unix/macOS
   ```
2. Install dependencies:
   ```bash
   ./venv/bin/pip install -r requirements.txt
   ```

## Project Documentation

For detailed information about the project:
- `STANDARDS.md`: Coding standards and UI/UX guidelines
- `CHECKPOINTS.md`: Change tracking and project history
- `git-http-protocol.md`: Git protocol implementation details

## Quick Start

1. Install dependencies:
   ```bash
   python -m venv ./venv
   source ./venv/bin/activate  # On Unix/macOS
   ./venv/bin/pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   python app.py
   ```
   The server will start on `http://localhost:5000`

3. Clone the generated Terraform configuration:
   ```bash
   git clone http://localhost:5000/your-cdktf-project
   ```

## Usage Examples

### Basic Usage

1. Place your CDKTF code in a directory that CDK2Git can access. Example structure:
   ```
   your-cdktf-project/
   ├── main.py
   ├── cdktf.json
   └── package.json
   ```

2. In your CI/CD pipeline, instead of running `cdktf synth` directly, use:
   ```bash
   git clone http://localhost:5000/path/to/your-cdktf-project
   ```

3. The cloned repository will contain the synthesized Terraform configuration.

### Integration with CI/CD Tools

#### Jenkins Pipeline Example
```groovy
pipeline {
    agent any
    stages {
        stage('Get Terraform Configuration') {
            steps {
                git url: 'http://cdk2git-server:5000/your-cdktf-project'
            }
        }
        stage('Apply Terraform') {
            steps {
                sh 'terraform init'
                sh 'terraform apply -auto-approve'
            }
        }
    }
}
```

#### GitLab CI Example
```yaml
stages:
  - terraform

terraform:
  stage: terraform
  script:
    - git clone http://cdk2git-server:5000/your-cdktf-project
    - cd your-cdktf-project
    - terraform init
    - terraform apply -auto-approve
```

## Configuration

### Environment Variables

- `CDKTF_VERSION`: Set the CDKTF version (default: 0.20.10)
- `SERVER_PORT`: Set the server port (default: 5000)
- `LOG_LEVEL`: Set logging level (default: INFO)

### Server Configuration

The server can be configured by modifying `app.py`:

```python
app.run(
    host='0.0.0.0',  # Listen on all interfaces
    port=int(os.environ.get('SERVER_PORT', 5000)),
    debug=False  # Set to False in production
)
```

## Troubleshooting

### Common Issues

1. **Git clone fails with "repository not found"**
   - Ensure the server is running
   - Check server logs for synthesis errors
   - Verify the URL is correct

2. **CDKTF synthesis fails**
   - Check if CDKTF is installed correctly
   - Verify CDKTF code syntax
   - Check server logs for detailed error messages

3. **Permission issues**
   - Ensure the server has access to the CDKTF code
   - Check file permissions in temporary directories

### Logs

The server logs provide detailed information about requests and errors:

```bash
tail -f cdk2git.log
```

Common log messages and their meanings:
- `Starting CDKTF synthesis`: Beginning the synthesis process
- `CDKTF synthesis completed`: Successfully generated Terraform configuration
- `Error during synthesis`: Failed to generate Terraform configuration
