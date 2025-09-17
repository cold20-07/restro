from supabase import create_client, Client
from app.core.config import settings
from typing import Optional

class SupabaseClient:
    """Supabase client wrapper for database operations"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._service_client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get Supabase client with anon key (for public operations)"""
        if self._client is None:
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return self._client
    
    @property
    def service_client(self) -> Client:
        """Get Supabase client with service key (for admin operations)"""
        if self._service_client is None:
            self._service_client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return self._service_client
    
    def get_authenticated_client(self, access_token: str) -> Client:
        """Get Supabase client with user authentication"""
        client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        client.auth.set_session(access_token, "")
        return client

# Global Supabase client instance
supabase_client = SupabaseClient()