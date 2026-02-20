output "public_subnet_id" {
  value       = aws_subnet.public_subnet.id
  description = "The ID of the public subnet"
}

output "private_subnet_id" {
  value       = aws_subnet.private_subnet.id
  description = "The ID of the private subnet"
}

output "public_subnet_id_2" {
  value       = aws_subnet.public_subnet_2.id
  description = "The ID of the second public subnet"
}

output "private_subnet_id_2" {
  value       = aws_subnet.private_subnet_2.id
  description = "The ID of the second private subnet"
}
