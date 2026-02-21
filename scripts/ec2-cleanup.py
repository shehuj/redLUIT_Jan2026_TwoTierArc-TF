#!/usr/bin/env python3

import boto3
import botocore.exceptions
import time

# -------- CONFIGURATION (must match ec2-create.py) --------
REGION               = "us-east-1"
ROLE_NAME            = "DemoSSMEC2Role"
INSTANCE_PROFILE_NAME = "DemoSSMEC2Role"
SSM_POLICY_ARN       = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
INSTANCE_NAME_TAG    = "SSM-Enabled-EC2"
# ----------------------------------------------------------

iam = boto3.client("iam")
ec2 = boto3.client("ec2", region_name=REGION)

if __name__ == "__main__":

    # ── Step 1: Find EC2 instances by Name tag ────────────────────────────────
    print(f"Step 1: Finding EC2 instances tagged Name='{INSTANCE_NAME_TAG}'...")
    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [INSTANCE_NAME_TAG]},
            {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]},
        ]
    )
    instance_ids = [
        i["InstanceId"]
        for r in response["Reservations"]
        for i in r["Instances"]
    ]

    if instance_ids:
        print(f"  Found instances: {instance_ids}")
    else:
        print("  No matching instances found, skipping termination.")

    # ── Step 2: Terminate EC2 instances ──────────────────────────────────────
    if instance_ids:
        print("Step 2: Terminating EC2 instances...")
        ec2.terminate_instances(InstanceIds=instance_ids)
        print(f"  Termination requested for: {instance_ids}")

        print("  Waiting for instances to reach 'terminated' state...")
        waiter = ec2.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=instance_ids)
        print("  All instances terminated.")
    else:
        print("Step 2: No instances to terminate, skipping.")

    # ── Step 3: Remove role from instance profile ─────────────────────────────
    print(f"Step 3: Removing role '{ROLE_NAME}' from instance profile '{INSTANCE_PROFILE_NAME}'...")
    try:
        profile = iam.get_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)["InstanceProfile"]
        attached_roles = [r["RoleName"] for r in profile["Roles"]]
        if ROLE_NAME in attached_roles:
            iam.remove_role_from_instance_profile(
                InstanceProfileName=INSTANCE_PROFILE_NAME,
                RoleName=ROLE_NAME
            )
            print(f"  Role '{ROLE_NAME}' removed from profile.")
        else:
            print(f"  Role '{ROLE_NAME}' not attached to profile, skipping.")
    except iam.exceptions.NoSuchEntityException:
        print(f"  Instance profile '{INSTANCE_PROFILE_NAME}' not found, skipping.")

    # ── Step 4: Delete instance profile ──────────────────────────────────────
    print(f"Step 4: Deleting instance profile '{INSTANCE_PROFILE_NAME}'...")
    try:
        iam.delete_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)
        print(f"  Instance profile '{INSTANCE_PROFILE_NAME}' deleted.")
    except iam.exceptions.NoSuchEntityException:
        print(f"  Instance profile '{INSTANCE_PROFILE_NAME}' not found, skipping.")

    # ── Step 5: Detach SSM policy from role ───────────────────────────────────
    print(f"Step 5: Detaching SSM policy from role '{ROLE_NAME}'...")
    try:
        attached = iam.list_attached_role_policies(RoleName=ROLE_NAME)["AttachedPolicies"]
        if any(p["PolicyArn"] == SSM_POLICY_ARN for p in attached):
            iam.detach_role_policy(RoleName=ROLE_NAME, PolicyArn=SSM_POLICY_ARN)
            print("  SSM policy detached.")
        else:
            print("  SSM policy not attached, skipping.")
    except iam.exceptions.NoSuchEntityException:
        print(f"  IAM role '{ROLE_NAME}' not found, skipping.")

    # ── Step 6: Delete IAM role ───────────────────────────────────────────────
    print(f"Step 6: Deleting IAM role '{ROLE_NAME}'...")
    try:
        iam.delete_role(RoleName=ROLE_NAME)
        print(f"  IAM role '{ROLE_NAME}' deleted.")
    except iam.exceptions.NoSuchEntityException:
        print(f"  IAM role '{ROLE_NAME}' not found, skipping.")
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "DeleteConflict":
            print(f"  Role still has attached policies or profiles — detach them first.")
            raise
        raise

    print("\nCleanup complete.")
