output "public_subnet_id" {
#  value       = aws_subnet.public_subnet.id
  value       = aws_subnet.public_subnet[count.index]
  description = "The ID of the public subnet"
}

output "private_subnet_id" {
#  value       = aws_subnet.private_subnet.id
  value       = aws_subnet.private_subnet[count.index]
  description = "The ID of the private subnet"
}
