# terraform backend configuration for remote state storage in AWS S3 and state locking with DynamoDB

terraform {
    backend "s3" {
        bucket         = "ec2-shutdown-lambda-bucket"
        key            = "two-tier-arc/terraform.tfstate"
        region         = "us-east-1"
        use_lockfile   = true
        encrypt        = true
    }
    }   