# ECS Module for Oh My Coins
# Creates ECS Fargate cluster, task definitions, and services

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-cluster"
    }
  )
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}/backend"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.project_name}/frontend"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# Backend Task Definition
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "${var.backend_image}:${var.backend_image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "PROJECT_NAME"
          value = var.project_name
        },
        {
          name  = "POSTGRES_SERVER"
          value = var.db_host
        },
        {
          name  = "POSTGRES_PORT"
          value = tostring(var.db_port)
        },
        {
          name  = "POSTGRES_DB"
          value = var.db_name
        },
        {
          name  = "POSTGRES_USER"
          value = var.db_user
        },
        {
          name  = "REDIS_HOST"
          value = var.redis_host
        },
        {
          name  = "REDIS_PORT"
          value = tostring(var.redis_port)
        },
        {
          name  = "BACKEND_CORS_ORIGINS"
          value = var.backend_cors_origins
        },
        {
          name  = "DOMAIN"
          value = var.domain
        },
        {
          name  = "FRONTEND_HOST"
          value = var.frontend_host
        }
      ]

      secrets = [
        {
          name      = "SECRET_KEY"
          valueFrom = "${var.secrets_arn}:SECRET_KEY::"
        },
        {
          name      = "POSTGRES_PASSWORD"
          valueFrom = "${var.secrets_arn}:POSTGRES_PASSWORD::"
        },
        {
          name      = "FIRST_SUPERUSER"
          valueFrom = "${var.secrets_arn}:FIRST_SUPERUSER::"
        },
        {
          name      = "FIRST_SUPERUSER_PASSWORD"
          valueFrom = "${var.secrets_arn}:FIRST_SUPERUSER_PASSWORD::"
        },
        {
          name      = "SMTP_HOST"
          valueFrom = "${var.secrets_arn}:SMTP_HOST::"
        },
        {
          name      = "SMTP_USER"
          valueFrom = "${var.secrets_arn}:SMTP_USER::"
        },
        {
          name      = "SMTP_PASSWORD"
          valueFrom = "${var.secrets_arn}:SMTP_PASSWORD::"
        },
        {
          name      = "OPENAI_API_KEY"
          valueFrom = "${var.secrets_arn}:OPENAI_API_KEY::"
        },
        {
          name      = "CRYPTOPANIC_API_KEY"
          valueFrom = "${var.secrets_arn}:omc-CryptoPanic-testkey::"
        },
        {
          name      = "NEWSCATCHER_API_KEY"
          valueFrom = "${var.secrets_arn}:omc-newscatcher-testkey::"
        },
        {
          name      = "NANSEN_API_KEY"
          valueFrom = "${var.secrets_arn}:omc-nasen-testkey::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/utils/health-check/ || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = var.tags
}

# Frontend Task Definition
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.project_name}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = "${var.frontend_image}:${var.frontend_image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "VITE_API_URL"
          value = "https://${var.backend_domain}"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = var.tags
}

# Backend ECS Service
resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = var.ecs_security_group_ids
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.backend_target_group_arn
    container_name   = "backend"
    container_port   = 8000
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  enable_execute_command = var.enable_execute_command

  depends_on = [var.alb_listener_arn]

  tags = var.tags
}

# Frontend ECS Service
resource "aws_ecs_service" "frontend" {
  name            = "${var.project_name}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = var.ecs_security_group_ids
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.frontend_target_group_arn
    container_name   = "frontend"
    container_port   = 80
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  enable_execute_command = var.enable_execute_command

  depends_on = [var.alb_listener_arn]

  tags = var.tags
}

# Auto Scaling for Backend
resource "aws_appautoscaling_target" "backend" {
  count              = var.enable_autoscaling ? 1 : 0
  max_capacity       = var.backend_max_capacity
  min_capacity       = var.backend_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "backend_cpu" {
  count              = var.enable_autoscaling ? 1 : 0
  name               = "${var.project_name}-backend-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend[0].resource_id
  scalable_dimension = aws_appautoscaling_target.backend[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = var.cpu_scaling_target
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

resource "aws_appautoscaling_policy" "backend_memory" {
  count              = var.enable_autoscaling ? 1 : 0
  name               = "${var.project_name}-backend-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend[0].resource_id
  scalable_dimension = aws_appautoscaling_target.backend[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = var.memory_scaling_target
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
