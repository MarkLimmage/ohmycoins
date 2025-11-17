# Security Groups Module for Oh My Coins
# Creates security groups for ALB, ECS, RDS, and Redis

# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = var.vpc_id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-alb-sg"
    }
  )
}

# Allow HTTP from anywhere
resource "aws_security_group_rule" "alb_http_ingress" {
  type              = "ingress"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.alb.id
  description       = "Allow HTTP from anywhere"
}

# Allow HTTPS from anywhere
resource "aws_security_group_rule" "alb_https_ingress" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.alb.id
  description       = "Allow HTTPS from anywhere"
}

# Allow all outbound traffic
resource "aws_security_group_rule" "alb_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.alb.id
  description       = "Allow all outbound traffic"
}

# ECS Security Group
resource "aws_security_group" "ecs" {
  name        = "${var.project_name}-ecs-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-ecs-sg"
    }
  )
}

# Allow traffic from ALB to backend
resource "aws_security_group_rule" "ecs_backend_from_alb" {
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
  security_group_id        = aws_security_group.ecs.id
  description              = "Allow backend traffic from ALB"
}

# Allow traffic from ALB to frontend
resource "aws_security_group_rule" "ecs_frontend_from_alb" {
  type                     = "ingress"
  from_port                = 80
  to_port                  = 80
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
  security_group_id        = aws_security_group.ecs.id
  description              = "Allow frontend traffic from ALB"
}

# Allow all outbound traffic from ECS
resource "aws_security_group_rule" "ecs_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.ecs.id
  description       = "Allow all outbound traffic"
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-rds-sg"
    }
  )
}

# Allow PostgreSQL from ECS
resource "aws_security_group_rule" "rds_from_ecs" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.ecs.id
  security_group_id        = aws_security_group.rds.id
  description              = "Allow PostgreSQL from ECS"
}

# Optionally allow PostgreSQL from specific CIDR (for management)
resource "aws_security_group_rule" "rds_from_cidr" {
  count             = length(var.management_cidr_blocks) > 0 ? 1 : 0
  type              = "ingress"
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  cidr_blocks       = var.management_cidr_blocks
  security_group_id = aws_security_group.rds.id
  description       = "Allow PostgreSQL from management CIDR"
}

# Allow outbound traffic (for replication, etc.)
resource "aws_security_group_rule" "rds_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.rds.id
  description       = "Allow all outbound traffic"
}

# Redis Security Group
resource "aws_security_group" "redis" {
  name        = "${var.project_name}-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = var.vpc_id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-redis-sg"
    }
  )
}

# Allow Redis from ECS
resource "aws_security_group_rule" "redis_from_ecs" {
  type                     = "ingress"
  from_port                = 6379
  to_port                  = 6379
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.ecs.id
  security_group_id        = aws_security_group.redis.id
  description              = "Allow Redis from ECS"
}

# Allow outbound traffic
resource "aws_security_group_rule" "redis_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.redis.id
  description       = "Allow all outbound traffic"
}
