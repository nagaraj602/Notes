# Default Provider


provider "aws" {
  region = "us-east-1"
}


# Aliased Provider for Mumbai
provider "aws" {
  alias  = "mumbai"
  region = "ap-south-1"
}
