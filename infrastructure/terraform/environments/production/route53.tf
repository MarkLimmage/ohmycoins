# Route53 DNS Configuration for Production
# Creates DNS records pointing to the production ALB

data "aws_route53_zone" "ohmycoins" {
  name         = "ohmycoins.com."
  private_zone = false
}

# Get ALB zone ID from the ALB module output
data "aws_lb" "main" {
  arn = module.alb.alb_arn
}

# Production root domain - ohmycoins.com
resource "aws_route53_record" "root" {
  zone_id = data.aws_route53_zone.ohmycoins.zone_id
  name    = "ohmycoins.com"
  type    = "A"

  alias {
    name                   = module.alb.alb_dns_name
    zone_id                = data.aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Production www subdomain - www.ohmycoins.com
resource "aws_route53_record" "www" {
  zone_id = data.aws_route53_zone.ohmycoins.zone_id
  name    = "www.ohmycoins.com"
  type    = "A"

  alias {
    name                   = module.alb.alb_dns_name
    zone_id                = data.aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Production API subdomain - api.ohmycoins.com
resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.ohmycoins.zone_id
  name    = "api.ohmycoins.com"
  type    = "A"

  alias {
    name                   = module.alb.alb_dns_name
    zone_id                = data.aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Production dashboard subdomain - dashboard.ohmycoins.com
resource "aws_route53_record" "dashboard" {
  zone_id = data.aws_route53_zone.ohmycoins.zone_id
  name    = "dashboard.ohmycoins.com"
  type    = "A"

  alias {
    name                   = module.alb.alb_dns_name
    zone_id                = data.aws_lb.main.zone_id
    evaluate_target_health = true
  }
}
