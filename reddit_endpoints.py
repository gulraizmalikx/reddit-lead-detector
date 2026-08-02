"""
Reddit Lead Detection API Endpoints
Dashboard and lead management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from reddit_models import RedditLead, RedditMonitoringLog
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3/reddit", tags=["Reddit Leads"])


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/leads/dashboard", tags=["Dashboard"])
async def get_reddit_dashboard(db: Session = Depends(get_db)):
    """
    Get Reddit leads dashboard with summary stats
    """

    total_leads = db.query(RedditLead).count()
    high_quality = db.query(RedditLead).filter(RedditLead.lead_quality == 'high').count()
    medium_quality = db.query(RedditLead).filter(RedditLead.lead_quality == 'medium').count()
    low_quality = db.query(RedditLead).filter(RedditLead.lead_quality == 'low').count()

    new_leads = db.query(RedditLead).filter(RedditLead.status == 'new').count()
    contacted_leads = db.query(RedditLead).filter(RedditLead.status == 'contacted').count()
    qualified_leads = db.query(RedditLead).filter(RedditLead.status == 'qualified').count()
    converted_leads = db.query(RedditLead).filter(RedditLead.is_converted == True).count()

    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0

    today = datetime.utcnow().date()
    todays_leads = db.query(RedditLead).filter(
        db.func.date(RedditLead.created_at) == today
    ).count()

    week_ago = datetime.utcnow() - timedelta(days=7)
    week_leads = db.query(RedditLead).filter(RedditLead.created_at >= week_ago).count()

    avg_lead_score = db.query(db.func.avg(RedditLead.lead_score)).scalar() or 0

    return {
        "summary": {
            "total_leads": total_leads,
            "todays_leads": todays_leads,
            "weeks_leads": week_leads,
            "conversion_rate": round(conversion_rate, 2),
            "avg_lead_score": round(avg_lead_score, 2),
        },
        "quality_breakdown": {
            "high": high_quality,
            "medium": medium_quality,
            "low": low_quality,
        },
        "status_breakdown": {
            "new": new_leads,
            "contacted": contacted_leads,
            "qualified": qualified_leads,
            "converted": converted_leads,
        },
    }


# ============================================================================
# LEADS LIST ENDPOINTS
# ============================================================================

@router.get("/leads", tags=["Leads"])
async def get_reddit_leads(
    status: str = Query(None),
    quality: str = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get Reddit leads with filtering
    """

    query = db.query(RedditLead).order_by(RedditLead.created_at.desc())

    if status:
        query = query.filter(RedditLead.status == status)

    if quality:
        query = query.filter(RedditLead.lead_quality == quality)

    total = query.count()
    leads = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "leads": [
            {
                "id": lead.id,
                "username": lead.reddit_username,
                "quality": lead.lead_quality,
                "intent": lead.intent,
                "property_type": lead.property_type,
                "budget": lead.budget_range,
                "location": lead.location_preference,
                "timeline": lead.timeline,
                "status": lead.status,
                "confidence": lead.confidence_score,
                "created_at": lead.created_at.isoformat(),
                "post_url": lead.reddit_post_url,
            }
            for lead in leads
        ]
    }


@router.get("/leads/{lead_id}", tags=["Leads"])
async def get_reddit_lead_detail(lead_id: str, db: Session = Depends(get_db)):
    """
    Get detailed view of a specific Reddit lead
    """

    lead = db.query(RedditLead).filter(RedditLead.id == lead_id).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {
        "id": lead.id,
        "reddit": {
            "username": lead.reddit_username,
            "post_url": lead.reddit_post_url,
            "post_title": lead.post_title,
            "post_body": lead.post_body,
            "subreddit": lead.subreddit,
            "profile_url": lead.profile_url,
        },
        "analysis": {
            "is_property_inquiry": lead.is_property_inquiry,
            "confidence_score": lead.confidence_score,
            "lead_quality": lead.lead_quality,
            "intent": lead.intent,
            "summary": lead.summary,
        },
        "property_preferences": {
            "type": lead.property_type,
            "budget_range": lead.budget_range,
            "location": lead.location_preference,
            "timeline": lead.timeline,
            "key_needs": lead.key_needs,
        },
        "contact": {
            "email": lead.email,
            "phone": lead.phone,
        },
        "status": {
            "status": lead.status,
            "lead_score": lead.lead_score,
            "is_converted": lead.is_converted,
            "conversion_notes": lead.conversion_notes,
        },
        "timeline": {
            "created_at": lead.created_at.isoformat(),
            "contacted_at": lead.contacted_at.isoformat() if lead.contacted_at else None,
            "last_interaction": lead.last_interaction.isoformat() if lead.last_interaction else None,
            "contacted_via": lead.contacted_via,
        },
    }


# ============================================================================
# LEAD MANAGEMENT ENDPOINTS
# ============================================================================

@router.put("/leads/{lead_id}/status", tags=["Lead Management"])
async def update_lead_status(
    lead_id: str,
    status: str,
    notes: str = None,
    db: Session = Depends(get_db),
):
    """
    Update lead status
    """

    lead = db.query(RedditLead).filter(RedditLead.id == lead_id).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    valid_statuses = ['new', 'contacted', 'qualified', 'converted', 'rejected']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status")

    lead.status = status

    if status == 'contacted':
        lead.contacted_at = datetime.utcnow()
        lead.last_interaction = datetime.utcnow()

    if status == 'converted':
        lead.is_converted = True
        lead.conversion_notes = notes or "Converted via Reddit lead"

    db.commit()

    return {
        "id": lead.id,
        "status": lead.status,
        "updated_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# MONITORING STATUS ENDPOINTS
# ============================================================================

@router.get("/monitoring/status", tags=["Monitoring"])
async def get_monitoring_status(db: Session = Depends(get_db)):
    """
    Get status of Reddit monitoring system
    """

    last_cycle = db.query(RedditMonitoringLog).order_by(
        RedditMonitoringLog.cycle_timestamp.desc()
    ).first()

    total_cycles = db.query(RedditMonitoringLog).count()

    return {
        "monitoring_active": True,
        "last_cycle": {
            "timestamp": last_cycle.cycle_timestamp.isoformat() if last_cycle else None,
            "posts_fetched": last_cycle.posts_fetched if last_cycle else 0,
            "posts_analyzed": last_cycle.posts_analyzed if last_cycle else 0,
            "leads_found": last_cycle.leads_found if last_cycle else 0,
        },
        "total_cycles": total_cycles,
        "uptime": "24/7 monitoring active",
    }
