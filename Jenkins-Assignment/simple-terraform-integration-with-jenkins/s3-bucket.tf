resource "aws_s3_bucket" "remote_backend_s3" {
  bucket        = "remote-backend-s3-jan2026-Nagaraj"
  force_destroy = true    # only if you're planning to delete bucket in future
}


resource "aws_s3_bucket_versioning" "versioning_bucket" {
  bucket = aws_s3_bucket.remote_backend_s3-jan2026-Nagaraj.id
  versioning_configuration {
    status = "Enabled"
  }
}
