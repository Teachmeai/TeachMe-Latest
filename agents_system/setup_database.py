#!/usr/bin/env python3
"""
Database setup script for Super Admin Agent system.

This script sets up the required database tables and views in Supabase.
Run this script once to initialize the database schema.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from utils.supabase_client import supabase_client
from models.database import DATABASE_SCHEMA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_database():
    """Set up the database schema for the agent system."""
    try:
        logger.info("Starting database setup...")
        
        # Execute the database schema
        logger.info("Creating tables and indexes...")
        
        # Split the schema into individual statements
        statements = [stmt.strip() for stmt in DATABASE_SCHEMA.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            try:
                logger.info(f"Executing statement {i+1}/{len(statements)}...")
                
                # Use the Supabase client to execute SQL
                result = supabase_client.client.rpc('exec_sql', {'sql': statement}).execute()
                
                if result.data:
                    logger.info(f"Statement {i+1} executed successfully")
                else:
                    logger.warning(f"Statement {i+1} returned no data")
                    
            except Exception as e:
                # Some statements might fail if objects already exist
                logger.warning(f"Statement {i+1} failed (may be expected): {str(e)}")
                continue
        
        logger.info("Database schema setup completed!")
        
        # Verify tables were created
        logger.info("Verifying table creation...")
        
        tables_to_check = [
            'agent_chat_sessions',
            'agent_messages', 
            'course_assistants',
            'agent_files'
        ]
        
        for table in tables_to_check:
            try:
                result = supabase_client.client.table(table).select('*').limit(1).execute()
                logger.info(f"✓ Table '{table}' is accessible")
            except Exception as e:
                logger.error(f"✗ Table '{table}' check failed: {str(e)}")
        
        logger.info("Database setup verification completed!")
        
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False


async def create_sample_data():
    """Create some sample data for testing (optional)."""
    try:
        logger.info("Creating sample data...")
        
        # This would require a valid user_id from your auth.users table
        # For now, we'll skip this as it requires existing users
        
        logger.info("Sample data creation skipped (requires existing users)")
        return True
        
    except Exception as e:
        logger.error(f"Sample data creation failed: {str(e)}")
        return False


def create_supabase_function():
    """SQL function to execute raw SQL (if not exists)."""
    function_sql = """
    CREATE OR REPLACE FUNCTION exec_sql(sql text)
    RETURNS text
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        EXECUTE sql;
        RETURN 'OK';
    EXCEPTION
        WHEN OTHERS THEN
            RETURN SQLERRM;
    END;
    $$;
    """
    return function_sql


async def main():
    """Main function to run database setup."""
    print("🚀 Super Admin Agent Database Setup")
    print("=" * 50)
    
    # Check connection
    try:
        logger.info("Testing database connection...")
        result = supabase_client.client.table('profiles').select('id').limit(1).execute()
        logger.info("✓ Database connection successful")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {str(e)}")
        logger.error("Please check your Supabase configuration in the .env file")
        return False
    
    # Setup database
    success = await setup_database()
    
    if success:
        print("\n✅ Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Start the agent server: python -m uvicorn agents.main:app --reload --port 8001")
        print("2. Test the APIs using the test scripts in agents/tests/")
        print("3. Access the API documentation at: http://localhost:8001/docs")
        
        # Optionally create sample data
        create_samples = input("\nWould you like to create sample data? (y/N): ").lower().strip()
        if create_samples == 'y':
            await create_sample_data()
    else:
        print("\n❌ Database setup failed!")
        print("Please check the logs above for error details.")
        return False
    
    return True


if __name__ == "__main__":
    # Run the setup
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
