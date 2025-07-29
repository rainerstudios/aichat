#!/usr/bin/env python3
"""
Performance test script for the AutoRAG optimization
"""
import asyncio
import aiohttp
import time
import json
from typing import Dict, Any

async def test_query_performance():
    """Test query performance with the new optimizations"""
    
    # First, get authentication token
    auth_url = "http://localhost:8000/api/auth/admin-login"
    auth_data = {
        "admin_key": "your-admin-key-here"  # Replace with actual admin key
    }
    
    test_queries = [
        {
            "query": "How do I set up an Arma Reforger server with mods?",
            "game_type": "Arma Reforger"
        },
        {
            "query": "What are the system requirements for Minecraft Paper server?",
            "game_type": "Minecraft"
        },
        {
            "query": "How do I configure Pterodactyl Panel?",
            "game_type": "Panel"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        print("🚀 Testing AutoRAG Performance Optimizations")
        print("=" * 50)
        
        # Test each query and measure time
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n📋 Test {i}: {test_case['query'][:50]}...")
            
            # Measure time for first request (cache miss)
            start_time = time.time()
            
            chat_data = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": test_case["query"]}]
                    }
                ],
                "system": "You are an AI assistant for XGaming server support.",
                "ptero_context": {
                    "userId": "1",
                    "serverId": "test-server-123"
                }
            }
            
            try:
                # For testing without auth, directly call the query function
                print("⏱️  Testing query without full HTTP stack...")
                
                # Import and test the query function directly
                import sys
                sys.path.append('/var/www/aichat/backend')
                from app.langgraph.tools import query_documentation
                
                result = await query_documentation.ainvoke({
                    "query": test_case["query"],
                    "game_type": test_case["game_type"]
                })
                
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"✅ First request: {duration:.2f}s")
                print(f"📄 Response length: {len(result)} chars")
                
                # Test second identical request (should hit cache)
                start_time = time.time()
                result2 = await query_documentation.ainvoke({
                    "query": test_case["query"],
                    "game_type": test_case["game_type"]
                })
                end_time = time.time()
                duration2 = end_time - start_time
                
                print(f"🚀 Cached request: {duration2:.2f}s")
                print(f"📈 Speed improvement: {((duration - duration2) / duration * 100):.1f}%")
                
                # Check if response indicates caching
                if "[Cached response for faster performance]" in result2:
                    print("✅ Cache working correctly")
                else:
                    print("⚠️  Cache may not be working as expected")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print("🎯 Performance Test Summary:")
        print("- Implemented response caching (5-minute TTL)")
        print("- Added request deduplication")
        print("- Optimized AutoRAG service (15s timeout, connection pooling)")
        print("- Reduced response size limits")
        
        # Test cache statistics
        try:
            from app.services.cache_service import get_cache
            cache = get_cache()
            stats = await cache.stats()
            print(f"\n📊 Cache Stats: {stats}")
        except Exception as e:
            print(f"Cache stats error: {e}")

if __name__ == "__main__":
    asyncio.run(test_query_performance())