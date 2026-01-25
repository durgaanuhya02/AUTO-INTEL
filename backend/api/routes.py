from fastapi import APIRouter, Depends, HTTPException, Query, Request, File, UploadFile
from typing import List, Dict, Any, Optional
import json
import time
import os
from datetime import datetime, timedelta

from ..core.database import get_redis
from ..models.schemas import (
    MetricResponse, AlertResponse, DecisionResponse, 
    DashboardData, AgentStatus, MetricType
)
from ..utils.cache import cache_result, metrics_cache
from ..utils.validators import MetricValidation, DecisionValidation, InputSanitizer
from ..utils.monitoring import system_monitor
from ..middleware.logging import PerformanceLogger
from agents.agent_orchestrator import orchestrator
from ..services.real_time_data_ingestion import real_time_ingestion
from ..services.enterprise_integrations import enterprise_integrations
from ..services.advanced_analytics import advanced_analytics

# Try to import advanced forecasting, fallback to simple if not available
try:
    from ..services.advanced_forecasting_service import advanced_forecasting_service
    ADVANCED_FORECASTING_AVAILABLE = True
except ImportError:
    from ..services.simple_forecasting_service import simple_forecasting_service as advanced_forecasting_service
    ADVANCED_FORECASTING_AVAILABLE = False

router = APIRouter()

@router.get("/dashboard", response_model=DashboardData)
@cache_result(ttl=60, key_prefix="dashboard")
async def get_dashboard_data(request: Request):
    """Get comprehensive dashboard data with caching"""
    start_time = time.time()
    
    try:
        # Increment request counter
        system_monitor.increment_request_count()
        
        # Try to get from cache first
        cached_data = await metrics_cache.get_dashboard_data()
        if cached_data:
            return DashboardData(**cached_data)
        
        redis_client = await get_redis()
        
        # Get current metrics
        current_metrics = {}
        stored_metrics = await redis_client.get("agent_data:observer:current_metrics")
        if stored_metrics:
            current_metrics = json.loads(stored_metrics)
        
        # Validate metrics
        validated_metrics = {}
        for metric_type, value in current_metrics.items():
            if MetricValidation.validate_metric_value(value, metric_type):
                validated_metrics[metric_type] = value
        
        # Get recent alerts with validation
        alerts_data = await redis_client.lrange("alerts", 0, 9)
        alerts = []
        for alert_str in alerts_data:
            try:
                alert_dict = eval(alert_str.decode())
                # Sanitize alert data
                alert_dict = InputSanitizer.sanitize_dict(alert_dict)
                alerts.append(AlertResponse(**alert_dict))
            except Exception as e:
                continue  # Skip invalid alerts
        
        # Get recent decisions with validation
        decisions_data = await redis_client.lrange("governance_log", 0, 4)
        recent_decisions = []
        for decision_str in decisions_data:
            try:
                decision_dict = json.loads(decision_str.decode())
                
                # Validate decision data
                confidence_score = decision_dict.get("confidence_score", 0.0)
                financial_impact = decision_dict.get("financial_impact", 0.0)
                
                if not DecisionValidation.validate_confidence_score(confidence_score):
                    confidence_score = 0.0
                if not DecisionValidation.validate_financial_impact(financial_impact):
                    financial_impact = 0.0
                
                decision_response = {
                    "id": hash(decision_dict.get("decision_id", "unknown")),
                    "title": InputSanitizer.sanitize_string(decision_dict.get("decision_title", "Unknown Decision")),
                    "description": InputSanitizer.sanitize_string(f"Recommended: {decision_dict.get('recommended_scenario', 'N/A')}"),
                    "scenarios": [],
                    "recommended_scenario": InputSanitizer.sanitize_string(decision_dict.get("recommended_scenario", "")),
                    "confidence_score": confidence_score,
                    "financial_impact": financial_impact,
                    "requires_approval": decision_dict.get("action") == "request_human_approval",
                    "reasoning": InputSanitizer.sanitize_string(f"Status: {decision_dict.get('final_status', 'unknown')}"),
                    "status": decision_dict.get("final_status", "pending"),
                    "created_at": datetime.fromisoformat(decision_dict.get("timestamp", datetime.utcnow().isoformat())),
                    "approved_at": None,
                    "executed_at": None
                }
                recent_decisions.append(DecisionResponse(**decision_response))
            except Exception as e:
                continue  # Skip invalid decisions
        
        # Get agent statuses
        agent_statuses = []
        agent_names = ["observer", "analyst", "simulation", "decision", "governance"]
        
        for agent_name in agent_names:
            status_data = await redis_client.get(f"agent_status:{agent_name}")
            if status_data:
                try:
                    status_dict = json.loads(status_data)
                    # Sanitize status data
                    status_dict = InputSanitizer.sanitize_dict(status_dict)
                    agent_statuses.append(AgentStatus(**status_dict))
                except:
                    agent_statuses.append(AgentStatus(
                        agent_type=agent_name,
                        status="unknown",
                        last_activity=datetime.utcnow()
                    ))
            else:
                agent_statuses.append(AgentStatus(
                    agent_type=agent_name,
                    status="inactive",
                    last_activity=datetime.utcnow()
                ))
        
        # Generate trend data with validation
        trends = {}
        for metric_name in validated_metrics.keys():
            history = await redis_client.get(f"agent_data:analyst:metric_history_{metric_name}")
            if history:
                try:
                    history_data = json.loads(history)
                    # Validate historical data
                    valid_history = [
                        value for value in history_data 
                        if isinstance(value, (int, float)) and MetricValidation.validate_metric_value(value, metric_name)
                    ]
                    trends[metric_name] = valid_history[-20:] if len(valid_history) > 20 else valid_history
                except:
                    trends[metric_name] = [validated_metrics[metric_name]] * 10
            else:
                trends[metric_name] = [validated_metrics.get(metric_name, 0)] * 10
        
        dashboard_data = DashboardData(
            current_metrics=validated_metrics,
            alerts=alerts,
            recent_decisions=recent_decisions,
            agent_statuses=agent_statuses,
            trends=trends
        )
        
        # Cache the result
        await metrics_cache.set_dashboard_data(dashboard_data.dict())
        
        # Log performance
        duration = time.time() - start_time
        PerformanceLogger.log_slow_query("get_dashboard_data", duration, 0.5)
        
        return dashboard_data
        
    except Exception as e:
        system_monitor.increment_error_count()
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")

@router.get("/metrics")
async def get_metrics(
    metric_type: Optional[MetricType] = None,
    hours: int = Query(24, description="Hours of history to retrieve")
):
    """Get metric data with optional filtering"""
    try:
        redis_client = await get_redis()
        
        # Get current metrics
        current_metrics = {}
        stored_metrics = await redis_client.get("agent_data:observer:current_metrics")
        if stored_metrics:
            current_metrics = json.loads(stored_metrics)
        
        # Filter by metric type if specified
        if metric_type:
            current_metrics = {k: v for k, v in current_metrics.items() if k == metric_type.value}
        
        # Get historical data
        historical_data = {}
        for metric_name in current_metrics.keys():
            history = await redis_client.get(f"agent_data:analyst:metric_history_{metric_name}")
            if history:
                try:
                    history_data = json.loads(history)
                    # Limit to requested hours (assuming 1 data point per 30 minutes)
                    max_points = hours * 2
                    historical_data[metric_name] = history_data[-max_points:] if len(history_data) > max_points else history_data
                except:
                    historical_data[metric_name] = []
            else:
                historical_data[metric_name] = []
        
        return {
            "current_metrics": current_metrics,
            "historical_data": historical_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")

@router.get("/alerts")
async def get_alerts(limit: int = Query(50, description="Maximum number of alerts to retrieve")):
    """Get recent alerts"""
    try:
        redis_client = await get_redis()
        
        alerts_data = await redis_client.lrange("alerts", 0, limit - 1)
        alerts = []
        
        for alert_str in alerts_data:
            try:
                alert_dict = eval(alert_str.decode())
                alerts.append(alert_dict)
            except:
                pass
        
        return {
            "alerts": alerts,
            "count": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")

@router.get("/decisions")
async def get_decisions(limit: int = Query(20, description="Maximum number of decisions to retrieve")):
    """Get recent decisions"""
    try:
        redis_client = await get_redis()
        
        decisions_data = await redis_client.lrange("governance_log", 0, limit - 1)
        decisions = []
        
        for decision_str in decisions_data:
            try:
                decision_dict = json.loads(decision_str.decode())
                decisions.append(decision_dict)
            except:
                pass
        
        return {
            "decisions": decisions,
            "count": len(decisions),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching decisions: {str(e)}")

@router.get("/agents/status")
async def get_agent_status():
    """Get status of all agents"""
    try:
        system_status = await orchestrator.get_system_status()
        return system_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching agent status: {str(e)}")

@router.post("/agents/trigger")
async def trigger_analysis(
    metric_type: str,
    current_value: float,
    description: Optional[str] = None
):
    """Manually trigger analysis for testing"""
    try:
        result = await orchestrator.trigger_manual_analysis(metric_type, current_value)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering analysis: {str(e)}")

@router.get("/approval-queue")
async def get_approval_queue():
    """Get pending approvals"""
    try:
        redis_client = await get_redis()
        
        queue_data = await redis_client.lrange("approval_queue", 0, -1)
        approvals = []
        
        for approval_str in queue_data:
            try:
                approval_dict = json.loads(approval_str.decode())
                approvals.append(approval_dict)
            except:
                pass
        
        return {
            "pending_approvals": approvals,
            "count": len(approvals),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching approval queue: {str(e)}")

@router.post("/approve-decision")
async def approve_decision(
    decision_id: str,
    approved: bool,
    approver: str,
    comments: Optional[str] = None
):
    """Approve or reject a pending decision"""
    try:
        redis_client = await get_redis()
        
        # Send approval message to governance agent
        approval_message = {
            "decision_id": decision_id,
            "approved": approved,
            "approver": approver,
            "comments": comments or "",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await redis_client.publish("agent:governance", json.dumps({
            "from_agent": "human",
            "to_agent": "governance",
            "message_type": "human_approval",
            "content": approval_message
        }))
        
        return {
            "status": "processed",
            "decision_id": decision_id,
            "approved": approved,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing approval: {str(e)}")

@router.get("/insights")
async def get_insights():
    """Get AI-generated business insights"""
    try:
        redis_client = await get_redis()
        
        # Get recent insights from analyst agent
        insights_data = await redis_client.get("agent_data:analyst:recent_insights")
        insights = []
        
        if insights_data:
            try:
                insights = json.loads(insights_data)
            except:
                pass
        
        return {
            "insights": insights,
            "count": len(insights),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching insights: {str(e)}")

@router.get("/system/health")
async def system_health():
    """Detailed system health check"""
    try:
        redis_client = await get_redis()
        
        # Check Redis
        redis_healthy = True
        try:
            await redis_client.ping()
        except:
            redis_healthy = False
        
        # Check agents
        system_status = await orchestrator.get_system_status()
        
        # Count active agents
        active_agents = 0
        total_agents = len(system_status.get("agents", {}))
        
        for agent_status in system_status.get("agents", {}).values():
            if agent_status.get("status") == "active":
                active_agents += 1
        
        health_status = "healthy"
        if not redis_healthy:
            health_status = "critical"
        elif active_agents < total_agents * 0.8:
            health_status = "degraded"
        
        return {
            "status": health_status,
            "redis_healthy": redis_healthy,
            "agents_active": f"{active_agents}/{total_agents}",
            "orchestrator_running": system_status.get("orchestrator_running", False),
            "openai_available": system_status.get("openai_available", False),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "critical",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Enterprise Integration Endpoints

@router.get("/enterprise/integrations/status")
async def get_enterprise_integrations_status():
    """Get status of all enterprise integrations"""
    try:
        status = await enterprise_integrations.get_integration_status()
        return {
            "integrations": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching integration status: {str(e)}")

@router.post("/enterprise/integrations/setup")
async def setup_custom_integration(integration_config: dict):
    """Setup a custom enterprise integration"""
    try:
        await enterprise_integrations.setup_custom_integration(integration_config)
        return {
            "status": "success",
            "message": f"Integration '{integration_config.get('name')}' setup successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting up integration: {str(e)}")

@router.get("/data-ingestion/stats")
async def get_data_ingestion_stats():
    """Get real-time data ingestion statistics"""
    try:
        stats = await real_time_ingestion.get_ingestion_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ingestion stats: {str(e)}")

# Advanced Analytics Endpoints

@router.get("/analytics/status")
async def get_analytics_status():
    """Get status of the advanced analytics engine"""
    try:
        status = await advanced_analytics.get_analytics_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics status: {str(e)}")

@router.get("/analytics/forecasts")
async def get_forecasts():
    """Get all available forecasts"""
    try:
        redis_client = await get_redis()
        forecasts = {}
        
        # Get all forecast models
        model_names = ["revenue_forecast", "churn_prediction", "demand_forecast"]
        
        for model_name in model_names:
            forecast_data = await redis_client.get(f"forecast:{model_name}")
            if forecast_data:
                forecasts[model_name] = json.loads(forecast_data)
        
        return {
            "forecasts": forecasts,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forecasts: {str(e)}")

@router.get("/analytics/forecasts/{model_name}")
async def get_specific_forecast(model_name: str):
    """Get forecast for a specific model"""
    try:
        redis_client = await get_redis()
        forecast_data = await redis_client.get(f"forecast:{model_name}")
        
        if not forecast_data:
            raise HTTPException(status_code=404, detail=f"Forecast for {model_name} not found")
        
        forecast = json.loads(forecast_data)
        return {
            "forecast": forecast,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forecast: {str(e)}")

@router.get("/analytics/customer-segments")
async def get_customer_segments():
    """Get customer segmentation analysis"""
    try:
        redis_client = await get_redis()
        segments_data = await redis_client.get("customer_segments")
        
        if not segments_data:
            return {
                "segments": {},
                "message": "No segmentation data available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        segments = json.loads(segments_data)
        return {
            "segments": segments,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching customer segments: {str(e)}")

@router.get("/analytics/anomalies/advanced")
async def get_advanced_anomalies(limit: int = Query(20, description="Maximum number of anomalies to retrieve")):
    """Get advanced anomaly detection results"""
    try:
        redis_client = await get_redis()
        anomalies_data = await redis_client.lrange("advanced_anomalies", 0, limit - 1)
        
        anomalies = []
        for anomaly_str in anomalies_data:
            try:
                anomaly = json.loads(anomaly_str.decode())
                anomalies.append(anomaly)
            except:
                pass
        
        return {
            "anomalies": anomalies,
            "count": len(anomalies),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching advanced anomalies: {str(e)}")

@router.get("/analytics/bi-report")
async def get_business_intelligence_report():
    """Get the latest business intelligence report"""
    try:
        redis_client = await get_redis()
        report_data = await redis_client.get("latest_bi_report")
        
        if not report_data:
            return {
                "report": None,
                "message": "No BI report available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        report = json.loads(report_data)
        return {
            "report": report,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching BI report: {str(e)}")

@router.get("/analytics/bi-report/{date}")
async def get_historical_bi_report(date: str):
    """Get historical business intelligence report for a specific date"""
    try:
        # Validate date format
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        redis_client = await get_redis()
        report_data = await redis_client.get(f"bi_report:{date}")
        
        if not report_data:
            raise HTTPException(status_code=404, detail=f"No BI report found for {date}")
        
        report = json.loads(report_data)
        return {
            "report": report,
            "date": date,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical BI report: {str(e)}")

# Advanced Forecasting Endpoints

@router.get("/analytics/forecasts/advanced")
async def get_advanced_forecasts():
    """Get advanced forecasts using Prophet, ARIMA, and ensemble models"""
    try:
        # Initialize forecasting service if needed
        await advanced_forecasting_service.initialize()
        
        # Get historical data for forecasting
        redis_client = await get_redis()
        
        # Prepare sample data (in production, this would come from your database)
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Generate sample time series data for demonstration
        dates = [datetime.now() - timedelta(days=i) for i in range(90, 0, -1)]
        revenue_data = [10000 + i * 100 + (i % 7) * 500 for i in range(90)]
        orders_data = [100 + i * 2 + (i % 7) * 10 for i in range(90)]
        
        df = pd.DataFrame({
            'date': dates,
            'revenue': revenue_data,
            'orders': orders_data
        })
        
        # Generate forecasts
        forecasts = await advanced_forecasting_service.get_forecast_summary(df)
        
        return {
            "forecasts": forecasts,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating advanced forecasts: {str(e)}")

@router.get("/analytics/forecasts/advanced/{metric}")
async def get_advanced_forecast_for_metric(metric: str, forecast_days: int = Query(30, description="Number of days to forecast")):
    """Get advanced forecast for a specific metric"""
    try:
        # Initialize forecasting service if needed
        await advanced_forecasting_service.initialize()
        
        # Validate metric
        valid_metrics = ['revenue', 'orders', 'customers']
        if metric not in valid_metrics:
            raise HTTPException(status_code=400, detail=f"Invalid metric. Must be one of: {valid_metrics}")
        
        # Validate forecast days
        if forecast_days < 1 or forecast_days > 365:
            raise HTTPException(status_code=400, detail="Forecast days must be between 1 and 365")
        
        # Prepare sample data (in production, this would come from your database)
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Generate sample time series data
        dates = [datetime.now() - timedelta(days=i) for i in range(90, 0, -1)]
        
        if metric == 'revenue':
            values = [10000 + i * 100 + (i % 7) * 500 for i in range(90)]
        elif metric == 'orders':
            values = [100 + i * 2 + (i % 7) * 10 for i in range(90)]
        else:  # customers
            values = [50 + i * 1 + (i % 7) * 5 for i in range(90)]
        
        df = pd.DataFrame({
            'date': dates,
            metric: values
        })
        
        # Generate forecast
        forecast_result = await advanced_forecasting_service.generate_forecast(
            df, metric, forecast_days
        )
        
        if not forecast_result:
            raise HTTPException(status_code=500, detail="Failed to generate forecast")
        
        return {
            "forecast": {
                "metric": forecast_result.metric,
                "model_type": forecast_result.model_type,
                "current_value": forecast_result.current_value,
                "predicted_values": forecast_result.predicted_values,
                "dates": forecast_result.dates,
                "confidence_lower": forecast_result.confidence_lower,
                "confidence_upper": forecast_result.confidence_upper,
                "trend_direction": forecast_result.trend_direction,
                "seasonality_strength": forecast_result.seasonality_strength,
                "model_accuracy": forecast_result.model_accuracy,
                "feature_importance": forecast_result.feature_importance
            },
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecast for {metric}: {str(e)}")

# Real-time Metrics Endpoints

@router.get("/metrics/real-time")
async def get_real_time_metrics():
    """Get real-time metrics from all sources"""
    try:
        redis_client = await get_redis()
        
        # Get current metrics from all sources
        metric_types = ["revenue", "orders", "customer_satisfaction", "churn_risk", 
                       "sales_pipeline", "won_revenue", "sap_orders_value", 
                       "dynamics_pipeline", "oracle_invoices", "hubspot_deals"]
        
        real_time_metrics = {}
        for metric_type in metric_types:
            metric_data = await redis_client.get(f"current_metric:{metric_type}")
            if metric_data:
                real_time_metrics[metric_type] = json.loads(metric_data)
        
        return {
            "metrics": real_time_metrics,
            "timestamp": datetime.utcnow().isoformat(),
            "sources": ["internal", "salesforce", "sap", "dynamics365", "oracle_erp", "hubspot"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching real-time metrics: {str(e)}")

@router.post("/metrics/manual-ingest")
async def manual_metric_ingestion(metric_data: dict):
    """Manually ingest a metric (for testing or one-off data points)"""
    try:
        required_fields = ["metric_type", "value", "source"]
        missing_fields = [field for field in required_fields if field not in metric_data]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {missing_fields}"
            )
        
        # Store the metric
        redis_client = await get_redis()
        
        metric_entry = {
            "value": metric_data["value"],
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "source": metric_data["source"],
                "manual_entry": True,
                **metric_data.get("metadata", {})
            }
        }
        
        await redis_client.set(
            f"current_metric:{metric_data['metric_type']}",
            json.dumps(metric_entry),
            ex=3600
        )
        
        # Publish to agents
        await redis_client.publish(
            "metric_updates",
            json.dumps({
                "type": "manual_metric_update",
                "metric_type": metric_data["metric_type"],
                "value": metric_data["value"],
                "timestamp": metric_entry["timestamp"],
                "metadata": metric_entry["metadata"]
            })
        )
        
        return {
            "status": "success",
            "message": f"Metric {metric_data['metric_type']} ingested successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting metric: {str(e)}")

# ML Service Endpoints

@router.post("/ml/upload-csv")
async def upload_csv_file(file: UploadFile = File(...)):
    """Upload and analyze CSV file for ML training"""
    try:
        from ..services.ml_service import ml_service
        
        # Save uploaded file
        file_path = f"uploads/{file.filename}"
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Analyze the file
        analysis = await ml_service.process_csv_file(file_path)
        
        return {
            "status": "success",
            "file_path": file_path,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV file: {str(e)}")

@router.post("/ml/train-model")
async def train_ml_model(
    file_path: str,
    target_column: str,
    model_type: str = "auto",
    model_name: Optional[str] = None
):
    """Train ML model on uploaded data"""
    try:
        from ..services.ml_service import ml_service
        
        # Train the model
        result = await ml_service.train_model(
            file_path=file_path,
            target_column=target_column,
            model_type=model_type,
            model_name=model_name
        )
        
        return {
            "status": "success",
            "model_info": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training model: {str(e)}")

@router.get("/ml/models")
async def get_trained_models():
    """Get list of all trained models"""
    try:
        from ..services.ml_service import ml_service
        
        models = await ml_service.get_model_list()
        
        return {
            "models": models,
            "count": len(models),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")

@router.post("/ml/predict")
async def make_prediction(
    model_name: str,
    data: Dict[str, Any]
):
    """Make prediction using trained model"""
    try:
        from ..services.ml_service import ml_service
        
        result = await ml_service.make_predictions(model_name, data)
        
        return {
            "status": "success",
            "prediction": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error making prediction: {str(e)}")

@router.delete("/ml/models/{model_name}")
async def delete_model(model_name: str):
    """Delete a trained model"""
    try:
        from ..services.ml_service import ml_service
        
        success = await ml_service.delete_model(model_name)
        
        if success:
            return {
                "status": "success",
                "message": f"Model '{model_name}' deleted successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting model: {str(e)}")

# Advanced System Management

@router.get("/system/comprehensive-health")
async def comprehensive_system_health():
    """Get comprehensive system health including all services"""
    try:
        redis_client = await get_redis()
        
        # Check Redis
        redis_healthy = True
        try:
            await redis_client.ping()
        except:
            redis_healthy = False
        
        # Check agents
        system_status = await orchestrator.get_system_status()
        
        # Check enterprise integrations
        integration_status = await enterprise_integrations.get_integration_status()
        
        # Check analytics engine
        analytics_status = await advanced_analytics.get_analytics_status()
        
        # Check data ingestion
        ingestion_stats = await real_time_ingestion.get_ingestion_stats()
        
        # Count active components
        active_agents = sum(1 for agent in system_status.get("agents", {}).values() 
                          if agent.get("status") == "active")
        total_agents = len(system_status.get("agents", {}))
        
        active_integrations = sum(1 for integration in integration_status.values() 
                                if integration.get("status") == "connected")
        total_integrations = len(integration_status)
        
        trained_models = analytics_status.get("trained_models", 0)
        total_models = analytics_status.get("total_models", 0)
        
        # Determine overall health
        health_score = 0
        max_score = 5
        
        if redis_healthy:
            health_score += 1
        if active_agents >= total_agents * 0.8:
            health_score += 1
        if active_integrations >= total_integrations * 0.5:
            health_score += 1
        if analytics_status.get("running", False):
            health_score += 1
        if ingestion_stats.get("running", False):
            health_score += 1
        
        overall_status = "healthy" if health_score >= 4 else "degraded" if health_score >= 2 else "critical"
        
        return {
            "overall_status": overall_status,
            "health_score": f"{health_score}/{max_score}",
            "components": {
                "redis": {"status": "healthy" if redis_healthy else "critical"},
                "agents": {
                    "status": "healthy" if active_agents >= total_agents * 0.8 else "degraded",
                    "active": f"{active_agents}/{total_agents}"
                },
                "integrations": {
                    "status": "healthy" if active_integrations >= total_integrations * 0.5 else "degraded",
                    "connected": f"{active_integrations}/{total_integrations}"
                },
                "analytics": {
                    "status": "healthy" if analytics_status.get("running", False) else "critical",
                    "models_trained": f"{trained_models}/{total_models}"
                },
                "data_ingestion": {
                    "status": "healthy" if ingestion_stats.get("running", False) else "critical",
                    "total_records": ingestion_stats.get("total_records", 0),
                    "success_rate": f"{ingestion_stats.get('successful_ingestions', 0)}/{ingestion_stats.get('successful_ingestions', 0) + ingestion_stats.get('failed_ingestions', 0)}"
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "overall_status": "critical",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }