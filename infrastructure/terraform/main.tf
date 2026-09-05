terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type        = string
  description = "AWS region for KLIBRA object storage."
  default     = "ap-southeast-1"
}

variable "name_prefix" {
  type        = string
  description = "Globally unique prefix for KLIBRA buckets."
  default     = "klibra"
}

resource "aws_s3_bucket" "klibra_raw" {
  bucket = "${var.name_prefix}-raw"
}

resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.klibra_raw.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "klibra_data" {
  for_each = toset(["silver", "gold", "quarantine"])
  bucket   = "${var.name_prefix}-${each.key}"
}

resource "aws_s3_bucket_versioning" "data" {
  for_each = aws_s3_bucket.klibra_data
  bucket   = each.value.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw" {
  bucket = aws_s3_bucket.klibra_raw.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  for_each = aws_s3_bucket.klibra_data
  bucket   = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "raw" {
  bucket = aws_s3_bucket.klibra_raw.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "data" {
  for_each = aws_s3_bucket.klibra_data
  bucket   = each.value.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "raw" {
  bucket = aws_s3_bucket.klibra_raw.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_ownership_controls" "data" {
  for_each = aws_s3_bucket.klibra_data
  bucket   = each.value.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}
