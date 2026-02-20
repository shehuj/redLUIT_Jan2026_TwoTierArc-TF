# output the Internet Gateway ID
output "igw_id" {
  value = aws_internet_gateway.igw.id
  description = "The ID of the Internet Gateway"
}