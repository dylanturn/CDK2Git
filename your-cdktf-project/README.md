# Example CDKTF Project

This is an example CDKTF project that creates a basic AWS infrastructure:
- VPC with public subnets
- NAT Gateway
- EC2 instance in a public subnet

## Infrastructure Details

- **VPC**:
  - CIDR: 10.0.0.0/16
  - 2 public subnets
  - DNS support enabled
  - Single NAT Gateway

- **EC2 Instance**:
  - Amazon Linux 2 AMI
  - t2.micro instance type
  - Deployed in public subnet

## Outputs
- VPC ID
- EC2 Instance ID

## Requirements
- Python 3.7+
- CDKTF CLI
- AWS credentials configured

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Deploy:
   ```bash
   cdktf deploy
   ```

3. Destroy:
   ```bash
   cdktf destroy
   ```
