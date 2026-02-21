#!/usr/bin/env python3

import boto3

# -------- CONFIGURATION (must match ec2-create.py) --------
REGION               = "us-east-1"
ROLE_NAME            = "DemoSSMEC2Role"
INSTANCE_PROFILE_NAME = "DemoSSMEC2Role"
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

    # ── Step 3: Remove ALL roles from instance profile ────────────────────────
    # Fetch the live role list and remove each one. Avoids the stale-list bug
    # where get_instance_profile returns empty Roles due to IAM eventual consistency.
    print(f"Step 3: Removing all roles from instance profile '{INSTANCE_PROFILE_NAME}'...")
    try:
        profile = iam.get_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)["InstanceProfile"]
        attached_roles = [r["RoleName"] for r in profile["Roles"]]
        if attached_roles:
            for role in attached_roles:
                iam.remove_role_from_instance_profile(
                    InstanceProfileName=INSTANCE_PROFILE_NAME,
                    RoleName=role
                )
                print(f"  Role '{role}' removed from profile.")
        else:
            # Roles list may be stale — attempt removal anyway and ignore if not found
            try:
                iam.remove_role_from_instance_profile(
                    InstanceProfileName=INSTANCE_PROFILE_NAME,
                    RoleName=ROLE_NAME
                )
                print(f"  Role '{ROLE_NAME}' removed from profile (eventual consistency fallback).")
            except iam.exceptions.NoSuchEntityException:
                print("  No roles attached to profile, skipping.")
    except iam.exceptions.NoSuchEntityException:
        print(f"  Instance profile '{INSTANCE_PROFILE_NAME}' not found, skipping.")

    # ── Step 4: Delete instance profile ──────────────────────────────────────
    print(f"Step 4: Deleting instance profile '{INSTANCE_PROFILE_NAME}'...")
    try:
        iam.delete_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)
        print(f"  Instance profile '{INSTANCE_PROFILE_NAME}' deleted.")
    except iam.exceptions.NoSuchEntityException:
        print(f"  Instance profile '{INSTANCE_PROFILE_NAME}' not found, skipping.")

    print("\nCleanup complete.")
