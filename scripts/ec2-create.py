#!/usr/bin/env python3

import boto3
import botocore.exceptions
import time
import json

# -------- CONFIGURATION --------
REGION = "us-east-1"                  # change region if needed
PUBLIC_SUBNET_ID = "subnet-0f0249199aa52d7ea"
SECURITY_GROUP_ID = "sg-07a2626f9cb4dcd3e"  # must allow outbound HTTPS for SSM
INSTANCE_TYPE = "m5.xlarge"
AMI_ID = "ami-0b6c6ebed2801a5cb"              # Ubuntu 22.04 LTS (us-east-1) — verify latest via AWS console
ROLE_NAME = "DemoSSMEC2Role"
INSTANCE_PROFILE_NAME = "DemoSSMEC2Role"
SSM_POLICY_ARN = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
# --------------------------------

iam = boto3.client("iam")
ec2 = boto3.client("ec2", region_name=REGION)

# User Data to install SSM agent — Ubuntu (snap/apt) and Amazon Linux / RHEL (yum/dnf)
user_data_script = """#!/bin/bash
. /etc/os-release

install_ssm_agent() {
  case "$ID" in
    ubuntu|debian)
      if command -v snap >/dev/null 2>&1; then
        snap install amazon-ssm-agent --classic
      else
        apt-get update -y && apt-get install -y amazon-ssm-agent
      fi
      ;;
    amzn|rhel|centos|fedora|ol)
      if command -v dnf >/dev/null 2>&1; then
        dnf install -y amazon-ssm-agent
      else
        yum install -y amazon-ssm-agent
      fi
      ;;
  esac
}

# Install only if not already present
if ! command -v amazon-ssm-agent >/dev/null 2>&1 && ! snap list amazon-ssm-agent >/dev/null 2>&1; then
  install_ssm_agent
fi

# Enable and start — service name differs for snap vs package installs
if snap list amazon-ssm-agent >/dev/null 2>&1; then
  systemctl enable --now snap.amazon-ssm-agent.amazon-ssm-agent.service
else
  systemctl enable --now amazon-ssm-agent
fi
"""

if __name__ == "__main__":

    # ── Step 1: Create IAM Role ───────────────────────────────────────────────
    print(f"Step 1: Creating IAM role '{ROLE_NAME}'...")
    assume_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    try:
        iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(assume_policy)
        )
        print(f"  IAM role '{ROLE_NAME}' created.")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"  IAM role '{ROLE_NAME}' already exists, skipping.")

    # ── Step 2: Attach SSM policy to role ─────────────────────────────────────
    print("Step 2: Attaching SSM policy to role...")
    attached = iam.list_attached_role_policies(RoleName=ROLE_NAME)["AttachedPolicies"]
    if not any(p["PolicyArn"] == SSM_POLICY_ARN for p in attached):
        iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn=SSM_POLICY_ARN)
        print("  SSM policy attached.")
    else:
        print("  SSM policy already attached, skipping.")

    # ── Step 3: Create instance profile ──────────────────────────────────────
    print(f"Step 3: Creating instance profile '{INSTANCE_PROFILE_NAME}'...")
    try:
        iam.create_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)
        print(f"  Instance profile '{INSTANCE_PROFILE_NAME}' created.")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"  Instance profile '{INSTANCE_PROFILE_NAME}' already exists, skipping.")

    # ── Step 4: Attach role to instance profile ───────────────────────────────
    print("Step 4: Attaching role to instance profile...")
    profile = iam.get_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)["InstanceProfile"]
    profile_arn = profile["Arn"]
    attached_roles = [r["RoleName"] for r in profile["Roles"]]
    if ROLE_NAME not in attached_roles:
        try:
            iam.add_role_to_instance_profile(
                InstanceProfileName=INSTANCE_PROFILE_NAME,
                RoleName=ROLE_NAME
            )
            print(f"  Role '{ROLE_NAME}' attached to profile.")
        except iam.exceptions.LimitExceededException:
            print("  Role already attached (IAM eventual consistency), skipping.")
    else:
        print(f"  Role '{ROLE_NAME}' already attached, skipping.")

    # ── Step 5: Wait for IAM propagation ─────────────────────────────────────
    print("Step 5: Waiting for IAM propagation...")
    time.sleep(10)

    # ── Step 6: Launch EC2 instance ───────────────────────────────────────────
    print("Step 6: Launching EC2 instance...")
    max_attempts = 5
    retry_delay = 15  # seconds between retries
    for attempt in range(1, max_attempts + 1):
        try:
            response = ec2.run_instances(
                ImageId=AMI_ID,
                InstanceType=INSTANCE_TYPE,
                NetworkInterfaces=[{
                    "DeviceIndex": 0,
                    "SubnetId": PUBLIC_SUBNET_ID,
                    "Groups": [SECURITY_GROUP_ID],
                    "AssociatePublicIpAddress": True,
                }],
                IamInstanceProfile={"Arn": profile_arn},
                UserData=user_data_script,
                MinCount=1,
                MaxCount=1,
                TagSpecifications=[{
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": "SSM-Enabled-EC2"}]
                }],
            )
            break
        except botocore.exceptions.ClientError as e:
            code = e.response["Error"]["Code"]
            msg = e.response["Error"]["Message"]
            if code == "InvalidParameterValue" and "iamInstanceProfile" in msg and attempt < max_attempts:
                print(f"  IAM profile not yet propagated, retrying in {retry_delay}s (attempt {attempt}/{max_attempts})...")
                time.sleep(retry_delay)
            else:
                raise

    instance_id = response["Instances"][0]["InstanceId"]
    print(f"  Launched EC2 instance: {instance_id}")
    print("Done! The instance will configure SSM on startup.")
