#!/usr/bin/env python3
"""
Script to crawl documentation with Firecrawl and upload to Cloudflare R2 for AutoRAG
"""

import asyncio
import os
import json
import boto3
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from services.firecrawl_service import crawl_all_documentation_sources, create_firecrawl_service

# Cloudflare R2 configuration
R2_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID") 
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "xgaming-docs-autorag")

def setup_r2_client():
    """Set up boto3 client for Cloudflare R2"""
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        raise ValueError("Missing R2 credentials: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")
    
    return boto3.client(
        's3',
        endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )

def save_document_locally(doc: dict, output_dir: Path) -> str:
    """Save a document locally as markdown with enhanced metadata"""
    # Create safe filename from source name and URL
    source_name = doc.get("source_name", "Unknown")
    url = doc.get("url", "")
    
    # Create a descriptive filename based on source name
    safe_source = source_name.replace(" ", "_").replace("/", "_").replace("?", "_").lower()
    
    # If we have a URL, add some of it to make filename unique
    if url:
        url_part = url.replace("https://", "").replace("http://", "").replace("/", "_").replace("?", "_")
        # Take last meaningful part of URL
        url_parts = [p for p in url_part.split("_") if p and len(p) > 2]
        if url_parts:
            safe_filename = f"{safe_source}_{url_parts[-1]}"[:80]
        else:
            safe_filename = safe_source[:80]
    else:
        safe_filename = safe_source[:80]
    
    # Ensure .md extension
    if not safe_filename.endswith(".md"):
        safe_filename += ".md"
    
    file_path = output_dir / safe_filename
    
    # Detect game type from source name for better categorization
    source_name = doc.get('source_name', 'Unknown')
    game_type = "General"
    
    if "minecraft" in source_name.lower() or "paper" in source_name.lower() or "spigot" in source_name.lower():
        game_type = "Minecraft"
    elif "arma" in source_name.lower():
        game_type = "Arma Reforger"
    elif "rust" in source_name.lower():
        game_type = "Rust"
    elif "cs2" in source_name.lower() or "counter-strike" in source_name.lower():
        game_type = "Counter-Strike"
    elif "valheim" in source_name.lower():
        game_type = "Valheim"
    elif "pterodactyl" in source_name.lower():
        game_type = "Pterodactyl"
    elif "shockbyte" in source_name.lower() or "bisecthosting" in source_name.lower():
        game_type = "Hosting Provider"
    
    # Determine category based on game type
    if game_type == "Pterodactyl":
        category = "Panel Management"
    elif game_type == "Hosting Provider":
        category = "Hosting Support"
    else:
        category = "Game Server"
    
    # Create markdown content with enhanced metadata
    content = f"""---
url: {doc.get('url', '')}
title: {doc.get('title', 'Untitled')}
source: {source_name}
game_type: {game_type}
category: {category}
crawled_at: {doc.get('crawled_at', datetime.now().isoformat())}
---

# {doc.get('title', 'Untitled')}

**Source:** {source_name}  
**Game Type:** {game_type}  
**URL:** {doc.get('url', '')}

---

{doc.get('markdown', doc.get('content', 'No content available'))}
"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(file_path)

def get_folder_from_game_type(game_type: str) -> str:
    """Get R2 folder name based on game type"""
    folder_mapping = {
        "Pterodactyl": "panel",
        "Minecraft": "minecraft", 
        "Arma Reforger": "arma_reforger",
        "Rust": "rust",
        "Counter-Strike": "counter_strike",
        "Valheim": "valheim",
        "Hosting Provider": "hosting_providers",
        "General": "general"
    }
    return folder_mapping.get(game_type, "general")

def upload_to_r2(file_path: str, s3_client, game_type: str = "General", object_key: str = None):
    """Upload file to Cloudflare R2 with organized folder structure"""
    if not object_key:
        folder = get_folder_from_game_type(game_type)
        filename = Path(file_path).name
        object_key = f"docs/{folder}/{filename}"
    
    try:
        s3_client.upload_file(file_path, R2_BUCKET_NAME, object_key)
        print(f"✅ Uploaded to R2: {object_key}")
        return True
    except Exception as e:
        print(f"❌ Failed to upload {file_path}: {e}")
        return False

async def main():
    """Main function to crawl docs and populate AutoRAG"""
    print("🚀 Starting documentation crawling and AutoRAG population...")
    
    # Create output directory
    output_dir = Path("./crawled_docs")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Set up R2 client
        s3_client = setup_r2_client()
        print("✅ R2 client configured")
        
        # Crawl all documentation sources
        print("📡 Starting Firecrawl documentation crawling...")
        documents = await crawl_all_documentation_sources()
        print(f"✅ Crawled {len(documents)} documents")
        
        if not documents:
            print("❌ No documents were crawled")
            return
        
        # Save documents locally and upload to R2 with organized folders
        uploaded_count = 0
        failed_count = 0
        folder_stats = {}
        
        for i, doc in enumerate(documents, 1):
            title = doc.get('title', 'Untitled')[:50]
            source = doc.get('source_name', 'Unknown')
            print(f"Processing document {i}/{len(documents)}: {title} from {source}")
            
            try:
                # Save locally
                file_path = save_document_locally(doc, output_dir)
                
                # Determine game type for folder organization
                source_name = doc.get('source_name', 'Unknown')
                if 'minecraft' in source_name.lower() or 'paper' in source_name.lower() or 'spigot' in source_name.lower():
                    game_type = 'Minecraft'
                elif 'arma' in source_name.lower():
                    game_type = 'Arma Reforger'
                elif 'rust' in source_name.lower():
                    game_type = 'Rust'
                elif 'cs2' in source_name.lower() or 'counter-strike' in source_name.lower():
                    game_type = 'Counter-Strike'
                elif 'valheim' in source_name.lower():
                    game_type = 'Valheim'
                elif 'pterodactyl' in source_name.lower():
                    game_type = 'Pterodactyl'
                elif 'shockbyte' in source_name.lower() or 'bisecthosting' in source_name.lower():
                    game_type = 'Hosting Provider'
                else:
                    game_type = 'General'
                
                # Upload to R2 with organized folder structure
                success = upload_to_r2(file_path, s3_client, game_type)
                
                if success:
                    uploaded_count += 1
                    folder = get_folder_from_game_type(game_type)
                    folder_stats[folder] = folder_stats.get(folder, 0) + 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"❌ Error processing document {i}: {e}")
                failed_count += 1
        
        print(f"\n🎉 Crawling and upload complete!")
        print(f"✅ Successfully processed: {uploaded_count} documents")
        print(f"❌ Failed: {failed_count} documents")
        print(f"📁 Local files saved in: {output_dir.absolute()}")
        print(f"☁️  Files uploaded to R2 bucket: {R2_BUCKET_NAME}")
        
        if folder_stats:
            print(f"\n📂 **Folder Organization:**")
            for folder, count in sorted(folder_stats.items()):
                print(f"   docs/{folder}/: {count} documents")
        
        print(f"\n📋 Next steps:")
        print(f"1. Check your Cloudflare AutoRAG dashboard")
        print(f"2. AutoRAG should automatically detect and index the new files")
        print(f"3. Test queries using the query_documentation tool")
        print(f"4. Documents are organized by category for better retrieval")
        
    except Exception as e:
        print(f"❌ Error in main process: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())