from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from ..services.similarity_cache import get_similarity_cache
from ..services.cache_service import get_cache as get_legacy_cache
import json

router = APIRouter(prefix="/api/cache", tags=["cache"])

@router.get("/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get comprehensive cache statistics"""
    try:
        # Get similarity cache stats
        similarity_cache = get_similarity_cache()
        similarity_stats = await similarity_cache.get_stats()
        
        # Get legacy cache stats for comparison
        legacy_cache = get_legacy_cache()
        legacy_stats = await legacy_cache.stats()
        
        return {
            "similarity_cache": similarity_stats,
            "legacy_cache": legacy_stats,
            "recommendations": _get_performance_recommendations(similarity_stats)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.post("/clear")
async def clear_cache(cache_type: str = "similarity") -> Dict[str, str]:
    """Clear cache entries"""
    try:
        if cache_type == "similarity":
            cache = get_similarity_cache()
            await cache.clear()
            return {"status": "success", "message": "Similarity cache cleared"}
        elif cache_type == "legacy":
            cache = get_legacy_cache()
            await cache.clear()
            return {"status": "success", "message": "Legacy cache cleared"}
        elif cache_type == "all":
            similarity_cache = get_similarity_cache()
            legacy_cache = get_legacy_cache()
            await similarity_cache.clear()
            await legacy_cache.clear()
            return {"status": "success", "message": "All caches cleared"}
        else:
            raise HTTPException(status_code=400, detail="Invalid cache_type. Use 'similarity', 'legacy', or 'all'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.post("/threshold")
async def set_similarity_threshold(threshold: str) -> Dict[str, str]:
    """Set similarity cache threshold"""
    valid_thresholds = ['exact', 'strong', 'broad', 'loose']
    if threshold not in valid_thresholds:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid threshold. Use one of: {', '.join(valid_thresholds)}"
        )
    
    try:
        cache = get_similarity_cache()
        await cache.set_threshold(threshold)
        return {
            "status": "success", 
            "message": f"Similarity threshold set to {threshold}",
            "threshold_value": str(cache.threshold_value)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set threshold: {str(e)}")

@router.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics and optimization suggestions"""
    try:
        cache = get_similarity_cache()
        stats = await cache.get_stats()
        
        # Calculate key performance metrics
        hit_rate = float(stats.get('hit_rate', '0%').replace('%', ''))
        memory_usage_mb = stats.get('memory_usage', 0) / (1024 * 1024)
        
        # Performance analysis
        performance_score = _calculate_performance_score(stats)
        recommendations = _get_performance_recommendations(stats)
        
        return {
            "performance_score": performance_score,
            "hit_rate": hit_rate,
            "memory_usage_mb": round(memory_usage_mb, 2),
            "total_queries": stats.get('total_queries', 0),
            "cache_efficiency": _calculate_cache_efficiency(stats),
            "recommendations": recommendations,
            "threshold_analysis": _analyze_threshold_performance(stats)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.post("/optimize")
async def optimize_cache() -> Dict[str, Any]:
    """Automatically optimize cache settings"""
    try:
        cache = get_similarity_cache()
        stats = await cache.get_stats()
        
        # Analyze current performance
        hit_rate = float(stats.get('hit_rate', '0%').replace('%', ''))
        
        # Optimization logic
        optimizations = []
        
        if hit_rate < 30:
            # Low hit rate - suggest looser threshold
            await cache.set_threshold('broad')
            optimizations.append("Lowered similarity threshold to 'broad' for better hit rate")
        elif hit_rate > 80:
            # High hit rate - can use stricter threshold for better precision
            await cache.set_threshold('strong')
            optimizations.append("Set similarity threshold to 'strong' for better precision")
        
        # Get updated stats
        updated_stats = await cache.get_stats()
        
        return {
            "status": "success",
            "optimizations_applied": optimizations,
            "before": {"hit_rate": f"{hit_rate}%"},
            "after": {"hit_rate": updated_stats.get('hit_rate', '0%')},
            "recommendations": _get_performance_recommendations(updated_stats)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to optimize cache: {str(e)}")

def _calculate_performance_score(stats: Dict[str, Any]) -> int:
    """Calculate overall performance score (0-100)"""
    hit_rate = float(stats.get('hit_rate', '0%').replace('%', ''))
    memory_efficiency = min(100, (1000 - stats.get('total_entries', 0)) / 10)  # Penalize high memory usage
    query_volume = min(100, stats.get('total_queries', 0) / 10)  # Reward high usage
    
    # Weighted score
    score = (hit_rate * 0.6) + (memory_efficiency * 0.2) + (query_volume * 0.2)
    return int(min(100, max(0, score)))

def _calculate_cache_efficiency(stats: Dict[str, Any]) -> str:
    """Calculate cache efficiency rating"""
    hit_rate = float(stats.get('hit_rate', '0%').replace('%', ''))
    
    if hit_rate >= 70:
        return "Excellent"
    elif hit_rate >= 50:
        return "Good"
    elif hit_rate >= 30:
        return "Fair"
    else:
        return "Poor"

def _get_performance_recommendations(stats: Dict[str, Any]) -> list:
    """Get performance optimization recommendations"""
    recommendations = []
    hit_rate = float(stats.get('hit_rate', '0%').replace('%', ''))
    total_entries = stats.get('total_entries', 0)
    
    if hit_rate < 30:
        recommendations.append({
            "type": "threshold",
            "message": "Consider using 'broad' or 'loose' similarity threshold for better hit rates",
            "action": "POST /api/cache/threshold with 'broad'"
        })
    
    if hit_rate > 85:
        recommendations.append({
            "type": "threshold", 
            "message": "Excellent hit rate! Consider 'strong' threshold for better precision",
            "action": "POST /api/cache/threshold with 'strong'"
        })
    
    if total_entries > 800:
        recommendations.append({
            "type": "memory",
            "message": "Cache is near capacity. Consider clearing old entries or increasing max_size",
            "action": "POST /api/cache/clear"
        })
    
    if stats.get('total_queries', 0) < 50:
        recommendations.append({
            "type": "usage",
            "message": "Low query volume. Cache effectiveness will improve with more usage",
            "action": "Continue normal operations"
        })
    
    return recommendations

def _analyze_threshold_performance(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze performance across different threshold settings"""
    current_threshold = stats.get('similarity_threshold', 'unknown')
    hit_rate = float(stats.get('hit_rate', '0%').replace('%', ''))
    
    analysis = {
        "current": {
            "threshold": current_threshold,
            "hit_rate": f"{hit_rate}%"
        },
        "predictions": {}
    }
    
    # Predict performance with different thresholds
    if 'strong' in current_threshold:
        analysis["predictions"]["broad"] = f"~{min(100, hit_rate * 1.3):.0f}% hit rate (more matches)"
        analysis["predictions"]["loose"] = f"~{min(100, hit_rate * 1.6):.0f}% hit rate (many matches)"
        analysis["predictions"]["exact"] = f"~{max(0, hit_rate * 0.4):.0f}% hit rate (fewer matches)"
    
    return analysis