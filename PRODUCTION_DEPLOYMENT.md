# Production Deployment Guide

## 🚀 Real-World Production Deployment

This guide covers deploying the Agentic AI Business Decision System in production environments for real business use.

## 📋 Prerequisites

### Infrastructure Requirements
- **CPU**: Minimum 4 cores, Recommended 8+ cores
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: Minimum 100GB SSD, Recommended 500GB+ SSD
- **Network**: Stable internet connection for AI API calls

### Software Requirements
- Docker & Docker Compose
- SSL certificates (for HTTPS)
- Domain name (optional but recommended)

## 🔧 Production Configuration

### 1. Environment Setup

Create production environment file:
```bash
cp .env.example .env.prod
```

Configure production variables:
```bash
# Database (Use strong passwords)
POSTGRES_USER=agentic_prod_user
POSTGRES_PASSWORD=your_super_secure_password_here
DATABASE_URL=postgresql://agentic_prod_user:your_password@postgres:5432/agentic_ai_prod

# Redis
REDIS_URL=redis://redis:6379

# AI Services (REQUIRED for production)
OPENAI_API_KEY=your_production_openai_api_key

# Security
SECRET_KEY=your_256_bit_secret_key_here
ENVIRONMENT=production

# External URLs
FRONTEND_API_URL=https://yourdomain.com/api/v1

# Monitoring
GRAFANA_PASSWORD=your_grafana_admin_password
```

### 2. SSL Certificate Setup

For HTTPS (recommended for production):
```bash
# Create SSL directory
mkdir -p docker/ssl

# Option 1: Use Let's Encrypt (recommended)
certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/ssl/

# Option 2: Self-signed certificate (development only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/ssl/privkey.pem \
  -out docker/ssl/fullchain.pem
```

### 3. Database Optimization

Create PostgreSQL configuration:
```bash
# docker/postgresql.conf
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

## 🚀 Deployment Steps

### 1. Production Deployment
```bash
# Deploy with production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 2. Database Migration
```bash
# Initialize production database
docker exec -i agentic_ai_postgres psql -U agentic_prod_user -d agentic_ai_prod < database/schema.sql

# Verify database setup
docker exec -it agentic_ai_postgres psql -U agentic_prod_user -d agentic_ai_prod -c "\dt"
```

### 3. Health Check
```bash
# Check system health
curl http://localhost/health

# Check comprehensive health
curl http://localhost/api/v1/system/comprehensive-health
```

## 🔌 Enterprise Integrations Setup

### Salesforce Integration
```bash
# Configure Salesforce OAuth
# 1. Create Connected App in Salesforce
# 2. Get Client ID and Secret
# 3. Configure in environment:

SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_INSTANCE_URL=https://your-domain.salesforce.com
```

### SAP Integration
```bash
# Configure SAP connection
SAP_BASE_URL=https://your-sap-system.com:8000
SAP_USERNAME=your_sap_user
SAP_PASSWORD=your_sap_password
```

### Microsoft Dynamics 365
```bash
# Configure Dynamics 365
DYNAMICS_TENANT_ID=your_tenant_id
DYNAMICS_CLIENT_ID=your_client_id
DYNAMICS_CLIENT_SECRET=your_client_secret
DYNAMICS_RESOURCE_URL=https://your-org.crm.dynamics.com
```

## 📊 Monitoring & Observability

### 1. Access Monitoring Dashboards
- **Grafana**: http://localhost:3001 (admin/your_password)
- **Prometheus**: http://localhost:9090
- **Application**: http://localhost

### 2. Key Metrics to Monitor
- **System Health**: Agent status, database connections, Redis memory
- **Business Metrics**: Revenue, orders, customer satisfaction
- **AI Performance**: Model accuracy, prediction confidence, decision success rate
- **Integration Health**: API response times, error rates, data freshness

### 3. Alerting Setup
Configure alerts for:
- System downtime
- High error rates
- Model performance degradation
- Critical business metric anomalies

## 🔒 Security Considerations

### 1. Network Security
```bash
# Configure firewall (example for Ubuntu)
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw deny 5432   # Block direct database access
ufw deny 6379   # Block direct Redis access
ufw enable
```

### 2. API Security
- Rate limiting (configured in nginx.conf)
- API key authentication for external integrations
- HTTPS enforcement
- CORS configuration

### 3. Data Security
- Encrypted database connections
- Redis password protection
- Secure credential storage
- Regular security updates

## 📈 Scaling Considerations

### 1. Horizontal Scaling
```bash
# Scale backend services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=4

# Scale with load balancer
# Add multiple backend replicas in docker-compose.prod.yml
```

### 2. Database Scaling
- Read replicas for analytics queries
- Connection pooling
- Database partitioning for large datasets

### 3. Redis Scaling
- Redis Cluster for high availability
- Separate Redis instances for different data types

## 🔄 Backup & Recovery

### 1. Database Backup
```bash
# Automated daily backup
docker exec agentic_ai_postgres pg_dump -U agentic_prod_user agentic_ai_prod > backup_$(date +%Y%m%d).sql

# Restore from backup
docker exec -i agentic_ai_postgres psql -U agentic_prod_user agentic_ai_prod < backup_20240101.sql
```

### 2. Redis Backup
```bash
# Redis persistence is enabled in production config
# Backup Redis data
docker exec agentic_ai_redis redis-cli BGSAVE
```

## 🚨 Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   docker stats
   
   # Optimize Redis memory
   docker exec agentic_ai_redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

2. **Slow Database Queries**
   ```bash
   # Check slow queries
   docker exec -it agentic_ai_postgres psql -U agentic_prod_user -d agentic_ai_prod
   SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
   ```

3. **AI API Rate Limits**
   - Monitor OpenAI API usage
   - Implement request queuing
   - Use multiple API keys for higher limits

### Log Analysis
```bash
# View application logs
docker-compose logs -f backend | grep ERROR

# View system metrics
docker exec agentic_ai_postgres psql -U agentic_prod_user -d agentic_ai_prod -c "SELECT * FROM pg_stat_activity;"
```

## 📞 Production Support

### Health Monitoring Endpoints
- `/health` - Basic health check
- `/api/v1/system/comprehensive-health` - Detailed system status
- `/api/v1/analytics/status` - AI/ML system status
- `/api/v1/enterprise/integrations/status` - Integration status

### Performance Optimization
1. **Database Indexing**: Ensure proper indexes on frequently queried columns
2. **Redis Optimization**: Configure appropriate memory policies
3. **API Caching**: Implement response caching for expensive operations
4. **Connection Pooling**: Use connection pools for database and external APIs

## 🎯 Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database optimized and backed up
- [ ] Monitoring dashboards configured
- [ ] Security measures implemented
- [ ] Integration credentials configured
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Backup procedures tested
- [ ] Documentation updated

## 📧 Support & Maintenance

For production support:
1. Monitor system health dashboards
2. Set up automated alerts
3. Regular security updates
4. Performance optimization reviews
5. Business metric validation

This system is designed for real-world production use with enterprise-grade reliability, security, and scalability.