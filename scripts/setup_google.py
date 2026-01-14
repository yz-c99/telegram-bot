#!/usr/bin/env python3
"""Setup script for Google Docs OAuth authentication.

This script performs initial authentication with Google Docs API and creates a token file.
Run this only once during initial setup.
"""

import os
import pickle
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes for Google Docs API
SCOPES = ['https://www.googleapis.com/auth/documents']


def setup_google_docs():
    """Perform initial Google Docs OAuth authentication."""
    print("=" * 60)
    print("Google Docs OAuth Authentication Setup")
    print("=" * 60)
    print()

    # Load environment variables
    env_path = project_root / ".env"
    if not env_path.exists():
        print("⚠️  Warning: .env file not found")
        print(f"   Using default credentials path: ./credentials/google_credentials.json")
    else:
        load_dotenv(env_path)

    # Get credentials path
    credentials_path = os.getenv(
        "GOOGLE_CREDENTIALS_PATH",
        "./credentials/google_credentials.json"
    )

    # Check if credentials file exists
    creds_file = project_root / credentials_path
    if not creds_file.exists():
        print("❌ Error: Google credentials file not found!")
        print(f"   Expected location: {creds_file}")
        print()
        print("   To get credentials:")
        print("   1. Go to https://console.cloud.google.com/")
        print("   2. Create a new project (or select existing)")
        print("   3. Enable Google Docs API")
        print("   4. Create OAuth 2.0 credentials (Desktop app)")
        print("   5. Download credentials.json")
        print(f"   6. Save to: {creds_file}")
        print()
        return False

    print(f"✓ Found credentials file: {creds_file}")
    print()

    # Set up token path
    token_dir = project_root / "credentials"
    token_dir.mkdir(parents=True, exist_ok=True)
    token_path = token_dir / "token.pickle"

    # Check if already authenticated
    if token_path.exists():
        print("ℹ️  Existing token found")
        response = input("Do you want to re-authenticate? (y/N): ").strip().lower()
        if response != 'y':
            print()
            print("Using existing token. Setup complete!")
            return True
        print()
        print("Removing existing token and re-authenticating...")
        token_path.unlink()

    # Start OAuth flow
    print()
    print("Starting OAuth authentication flow...")
    print()
    print("A browser window will open for you to:")
    print("  1. Sign in to your Google account")
    print("  2. Grant access to Google Docs")
    print()
    input("Press Enter to open browser and continue...")
    print()

    try:
        # Create OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(creds_file),
            SCOPES
        )

        # Run local server for OAuth callback
        creds = flow.run_local_server(port=0)

        # Save credentials
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

        print()
        print("✓ Authentication successful!")
        print(f"✓ Token saved to: {token_path}")
        print()
        print("You can now create Google Docs documents.")

        return True

    except Exception as e:
        print()
        print(f"❌ Authentication failed: {e}")
        print()
        print("Common issues:")
        print("  - Make sure you're signed in to the correct Google account")
        print("  - Verify that Google Docs API is enabled in your project")
        print("  - Check that OAuth consent screen is configured")
        print()
        return False


def main():
    """Main entry point."""
    success = setup_google_docs()

    print()
    print("=" * 60)

    if success:
        print("Setup completed successfully!")
        print()
        print("Next steps:")
        print("  1. Run: python scripts/test_connection.py")
        print("  2. Run: python src/main.py --test")
    else:
        print("Setup failed. Please fix the errors and try again.")

    print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
