#!/usr/bin/env python3
"""
Cleans up VPC dependencies that Terraform does not manage, allowing
'terraform destroy' to delete the VPC without a DependencyViolation.

Resources removed:
  - Available (detached) network interfaces inside the VPC
  - Non-default security groups inside the VPC

Run this AFTER ec2-cleanup.py and BEFORE terraform destroy.
"""

import boto3
import sys

# -------- CONFIGURATION --------
REGION     = "us-east-1"
VPC_NAME   = "twotier-dev--vpc"   # matches "${name_prefix}-vpc" in Terraform
# --------------------------------

ec2 = boto3.client("ec2", region_name=REGION)

if __name__ == "__main__":

    # ── Find the VPC ──────────────────────────────────────────────────────────
    print(f"Looking up VPC with Name tag '{VPC_NAME}'...")
    response = ec2.describe_vpcs(
        Filters=[{"Name": "tag:Name", "Values": [VPC_NAME]}]
    )
    vpcs = response["Vpcs"]
    if not vpcs:
        print(f"  No VPC found with Name='{VPC_NAME}'. Nothing to clean up.")
        sys.exit(0)

    vpc_id = vpcs[0]["VpcId"]
    print(f"  Found VPC: {vpc_id}")

    # ── Delete orphaned (available) network interfaces ─────────────────────────
    print("Deleting available (detached) network interfaces...")
    enis = ec2.describe_network_interfaces(
        Filters=[
            {"Name": "vpc-id",  "Values": [vpc_id]},
            {"Name": "status",  "Values": ["available"]},
        ]
    )["NetworkInterfaces"]

    if enis:
        for eni in enis:
            eni_id = eni["NetworkInterfaceId"]
            ec2.delete_network_interface(NetworkInterfaceId=eni_id)
            print(f"  Deleted ENI: {eni_id}")
    else:
        print("  No detached ENIs found, skipping.")

    # ── Delete non-default security groups ────────────────────────────────────
    # The default SG cannot be deleted; all others blocking VPC deletion are removed.
    print("Deleting non-default security groups...")
    sgs = ec2.describe_security_groups(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    )["SecurityGroups"]

    deleted, skipped = 0, 0
    for sg in sgs:
        if sg["GroupName"] == "default":
            skipped += 1
            continue
        ec2.delete_security_group(GroupId=sg["GroupId"])
        print(f"  Deleted SG: {sg['GroupId']} ({sg['GroupName']})")
        deleted += 1

    if deleted == 0 and skipped == len(sgs):
        print("  No non-default security groups found, skipping.")

    print("\nVPC pre-destroy cleanup complete.")
