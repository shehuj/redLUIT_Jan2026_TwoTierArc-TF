# redLUIT_Jan2026_TwoTierArc-TF

Deploys a two-tier production-ready AWS network architecture using Terraform, with a GitHub Actions CI/CD pipeline and supporting Python utility scripts.

---

## Architecture

```
VPC (10.0.0.0/16)
├── Public Subnet 1  (10.0.0.0/24) — us-east-1a
├── Public Subnet 2  (10.0.2.0/24) — us-east-1b
├── Private Subnet 1 (10.0.1.0/24) — us-east-1a
├── Private Subnet 2 (10.0.3.0/24) — us-east-1b
├── Internet Gateway
├── Public Route Table  → 0.0.0.0/0 via IGW (associated to both public subnets)
└── Private Route Table (associated to both private subnets)
```

---

## Repository Structure

```
.
├── .github/
│   └── workflows/
│       ├── terraform.yml          # CI/CD pipeline (validate, scan, plan, deploy)
│       └── terraform-destroy.yml  # Manual teardown workflow
├── scripts/
│   ├── ec2-create.py              # Provisions an SSM-enabled EC2 instance
│   ├── ec2-cleanup.py             # Terminates the EC2 instance and instance profile
│   └── vpc-prereq-cleanup.py      # Removes unmanaged SGs and ENIs before destroy
├── terraform/
│   ├── backend.tf                 # S3 remote state
│   ├── provider.tf                # AWS provider
│   ├── main.tf                    # Root module — wires all modules together
│   ├── variables.tf               # Input variables with defaults
│   ├── outputs.tf                 # Root outputs
│   └── modules/
│       ├── vpc/                   # VPC resource
│       ├── subnets/               # Public and private subnets
│       ├── IGW/                   # Internet Gateway
│       └── routes-table/          # Route tables, routes, and associations
└── tests/
    └── *.py                       # Python repo validation tests
```

---

## Prerequisites

| Tool | Minimum version |
|---|---|
| Terraform | 1.9+ |
| Python | 3.10+ |
| AWS CLI | v2 |
| boto3 | `pip install boto3` |

### AWS permissions required

The IAM user or role running this must have permissions for:
- **EC2** — full access (VPC, subnets, IGW, route tables, instances, ENIs, SGs)
- **IAM** — create/delete roles and instance profiles, attach policies
- **S3** — read/write access to the state bucket (`ec2-shutdown-lambda-bucket`)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/redLUIT_Jan2026_TwoTierArc-TF.git
cd redLUIT_Jan2026_TwoTierArc-TF
```

### 2. Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | Target region (e.g. `us-east-1`) |

### 3. Verify the S3 backend bucket exists

The Terraform state is stored in S3. Ensure the bucket exists before the first run:

```bash
aws s3api head-bucket --bucket ec2-shutdown-lambda-bucket
```

If it does not exist, create it:

```bash
aws s3api create-bucket \
  --bucket ec2-shutdown-lambda-bucket \
  --region us-east-1
aws s3api put-bucket-encryption \
  --bucket ec2-shutdown-lambda-bucket \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
```

---

## Deploying Infrastructure

### Option A — Via GitHub Actions (recommended)

#### Development / validation

Push to the `dev` branch or open a pull request targeting `dev` or `main`. The **Terraform CI/CD** workflow runs automatically:

1. `terraform fmt -check` — fails if files are not formatted
2. `terraform validate` — checks configuration validity
3. Trivy IaC scan — blocks on `CRITICAL` or `HIGH` findings
4. Python tests (`pytest tests/`)
5. `terraform plan` — output is posted as a PR comment

#### Deploy to production

Merge a pull request into `main`. The **Deploy** job runs automatically:

1. `terraform init`
2. `terraform validate`
3. Trivy IaC scan
4. `terraform apply -auto-approve`

### Option B — Local deployment

```bash
cd terraform

# Configure AWS credentials
export AWS_ACCESS_KEY_ID=<your-key>
export AWS_SECRET_ACCESS_KEY=<your-secret>
export AWS_DEFAULT_REGION=us-east-1

# Initialise and deploy
terraform init
terraform validate
terraform fmt -recursive
terraform plan
terraform apply
```

---

## Customising Variables

Override defaults by passing `-var` flags or creating a `terraform.tfvars` file in the `terraform/` directory:

```hcl
# terraform/terraform.tfvars
name_prefix          = "myapp-prod-"
cidr_block           = "10.10.0.0/16"
region               = "us-west-2"
availability_zone    = "us-west-2a"
availability_zone_2  = "us-west-2b"
public_subnet_cidr   = "10.10.0.0/24"
public_subnet_cidr_2 = "10.10.2.0/24"
private_subnet_cidr  = "10.10.1.0/24"
private_subnet_cidr_2= "10.10.3.0/24"
```

---

## EC2 Utility Scripts

These scripts manage an SSM-enabled EC2 instance independently of Terraform.

### Launch an EC2 instance

Edit the configuration block at the top of `scripts/ec2-create.py` to match your environment:

```python
REGION            = "us-east-1"
PUBLIC_SUBNET_ID  = "subnet-xxxxxxxx"   # must be inside the Terraform-managed VPC
SECURITY_GROUP_ID = "sg-xxxxxxxx"       # must allow outbound HTTPS (443) for SSM
INSTANCE_TYPE     = "m5.xlarge"
AMI_ID            = "ami-xxxxxxxx"      # Ubuntu 22.04 LTS — verify latest in AWS console
```

Then run:

```bash
pip install boto3
python scripts/ec2-create.py
```

The script will:
1. Create the IAM role `DemoSSMEC2Role` with `AmazonSSMManagedInstanceCore` (skips if exists)
2. Create and attach the instance profile
3. Launch the instance with a public IP and user data that installs the SSM agent
4. Print the instance ID on success

> The instance is reachable via **AWS Systems Manager → Session Manager** — no SSH key or open inbound ports required.

### Terminate the EC2 instance

```bash
python scripts/ec2-cleanup.py
```

This terminates all instances tagged `Name=SSM-Enabled-EC2`, waits for full termination, then removes the instance profile. The IAM role is preserved.

---

## Tearing Down Infrastructure

### Via GitHub Actions (recommended)

1. Go to **Actions → Terraform Destroy → Run workflow**
2. Type `destroy` in the confirmation field
3. Select the target environment
4. Click **Run workflow**

The workflow runs in order:
1. `ec2-cleanup.py` — terminates the EC2 instance and waits for it to be gone
2. `vpc-prereq-cleanup.py` — deletes unmanaged security groups and orphaned ENIs inside the VPC (prevents `DependencyViolation` on VPC deletion)
3. `terraform plan -destroy` — shows exactly what Terraform will remove
4. `terraform apply -destroy` — tears down all Terraform-managed resources

### Local teardown

```bash
# Step 1 — clean up resources Terraform does not manage
pip install boto3
python scripts/ec2-cleanup.py
python scripts/vpc-prereq-cleanup.py

# Step 2 — Terraform destroy
cd terraform
terraform init
terraform destroy
```

---

## CI/CD Workflow Summary

| Trigger | Workflow | Jobs |
|---|---|---|
| Push to `dev` | Terraform CI/CD | Test, Validate, Scan, Plan |
| PR to `dev` or `main` | Terraform CI/CD | Test, Validate, Scan, Plan + PR comment |
| Merge to `main` | Terraform CI/CD | Deploy (`terraform apply`) |
| Manual | Terraform Destroy | EC2 cleanup → VPC cleanup → Destroy |
