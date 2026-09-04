# S3 lifecycle policies — ADR-008, PRD §34, TDD §50.

# ── Raw: immutable, longest retention ─────────────────────────
resource "aws_s3_bucket_lifecycle_configuration" "raw" {
  bucket = aws_s3_bucket.klibra_raw.id

  rule {
    id     = "raw-tiering"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
    transition {
      days          = 365
      storage_class = "GLACIER"
    }
    transition {
      days          = 730
      storage_class = "DEEP_ARCHIVE"
    }

    noncurrent_version_expiration { noncurrent_days = 730 }

    abort_incomplete_multipart_upload { days_after_initiation = 7 }
  }
}

# ── Silver/Gold/Quarantine: standard tiering per ADR-008 ──────
resource "aws_s3_bucket_lifecycle_configuration" "silver_gold" {
  for_each = toset(["silver", "gold", "quarantine"])

  bucket = aws_s3_bucket.klibra_data[each.key].id

  rule {
    id     = "${each.key}-tiering"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    transition {
      days          = 365
      storage_class = "GLACIER"
    }
    transition {
      days          = 730
      storage_class = "DEEP_ARCHIVE"
    }

    noncurrent_version_expiration { noncurrent_days = 90 }

    abort_incomplete_multipart_upload { days_after_initiation = 7 }
  }
}
