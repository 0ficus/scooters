"""
Metabase Dashboard Setup Script

This script automatically creates the ClickHouse database connection
and dashboards in Metabase using the Metabase API.

Usage:
    python setup_dashboards.py [--metabase-url URL] [--email EMAIL] [--password PASSWORD]

Prerequisites:
    - Metabase must be running and accessible
    - Initial admin setup must be completed in Metabase UI first
    - ClickHouse must be running and accessible from Metabase
"""

import argparse
import json
import sys
import time
import requests
from pathlib import Path


class MetabaseSetup:
    def __init__(self, base_url: str, email: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session_token = None
        self.database_id = None

    def login(self) -> bool:
        """Authenticate with Metabase and get session token"""
        print(f"Logging in to Metabase at {self.base_url}...")
        try:
            response = self.session.post(
                f"{self.base_url}/api/session",
                json={"username": self.email, "password": self.password}
            )
            if response.status_code == 200:
                self.session_token = response.json().get("id")
                self.session.headers.update({"X-Metabase-Session": self.session_token})
                print("✓ Login successful")
                return True
            else:
                print(f"✗ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"✗ Login error: {e}")
            return False

    def wait_for_metabase(self, timeout: int = 120) -> bool:
        """Wait for Metabase to be ready"""
        print(f"Waiting for Metabase to be ready (timeout: {timeout}s)...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{self.base_url}/api/health")
                if response.status_code == 200:
                    status = response.json().get("status")
                    if status == "ok":
                        print("✓ Metabase is ready")
                        return True
            except Exception:
                pass
            time.sleep(2)
        print("✗ Metabase did not become ready in time")
        return False

    def create_clickhouse_database(self) -> bool:
        """Create ClickHouse database connection"""
        print("Creating ClickHouse database connection...")
        
        response = self.session.get(f"{self.base_url}/api/database")
        if response.status_code == 200:
            databases = response.json().get("data", [])
            for db in databases:
                if db.get("name") == "ClickHouse DWH":
                    self.database_id = db.get("id")
                    print(f"✓ Database already exists (ID: {self.database_id})")
                    return True

        db_config = {
            "name": "ClickHouse DWH",
            "engine": "clickhouse",
            "details": {
                "host": "clickhouse",
                "port": 8123,
                "dbname": "default",
                "user": "default",
                "password": "",
                "ssl": False
            },
            "auto_run_queries": True,
            "is_full_sync": True,
            "schedules": {}
        }

        response = self.session.post(
            f"{self.base_url}/api/database",
            json=db_config
        )

        if response.status_code in [200, 201]:
            self.database_id = response.json().get("id")
            print(f"✓ Database created (ID: {self.database_id})")
            return True
        else:
            print(f"✗ Failed to create database: {response.status_code} - {response.text}")
            return False

    def sync_database(self) -> bool:
        """Trigger database schema sync"""
        if not self.database_id:
            return False
        
        print("Syncing database schema...")
        response = self.session.post(
            f"{self.base_url}/api/database/{self.database_id}/sync_schema"
        )
        
        if response.status_code in [200, 204]:
            print("✓ Database sync triggered")
            time.sleep(5)
            return True
        else:
            print(f"✗ Failed to sync database: {response.status_code}")
            return False

    def create_dashboard(self, name: str, description: str) -> int:
        """Create a new dashboard"""
        print(f"Creating dashboard: {name}...")
        
        response = self.session.get(f"{self.base_url}/api/dashboard")
        if response.status_code == 200:
            dashboards = response.json()
            for dash in dashboards:
                if dash.get("name") == name:
                    print(f"✓ Dashboard already exists (ID: {dash.get('id')})")
                    return dash.get("id")

        response = self.session.post(
            f"{self.base_url}/api/dashboard",
            json={"name": name, "description": description}
        )

        if response.status_code in [200, 201]:
            dashboard_id = response.json().get("id")
            print(f"✓ Dashboard created (ID: {dashboard_id})")
            return dashboard_id
        else:
            print(f"✗ Failed to create dashboard: {response.status_code} - {response.text}")
            return None

    def create_native_question(self, name: str, query: str, visualization: str = "scalar", x_col: str = None, y_col: str = None) -> int:
        """Create a native SQL question (card)"""
        print(f"  Creating question: {name}...")
        
        if not self.database_id:
            print("  ✗ No database ID available")
            return None

        viz_map = {
            "scalar": "scalar",
            "line": "line",
            "bar": "bar",
            "table": "table",
            "pie": "pie"
        }

        viz_settings = {}
        if visualization in ["bar", "line"] and x_col and y_col:
            viz_settings = {
                "graph.dimensions": [x_col],
                "graph.metrics": [y_col],
                "graph.x_axis.title_text": x_col,
                "graph.y_axis.title_text": y_col
            }

        card_config = {
            "name": name,
            "dataset_query": {
                "type": "native",
                "native": {
                    "query": query
                },
                "database": self.database_id
            },
            "display": viz_map.get(visualization, "table"),
            "visualization_settings": viz_settings
        }

        response = self.session.post(
            f"{self.base_url}/api/card",
            json=card_config
        )

        if response.status_code in [200, 201]:
            card_id = response.json().get("id")
            print(f"  ✓ Question created (ID: {card_id})")
            return card_id
        else:
            print(f"  ✗ Failed to create question: {response.status_code} - {response.text}")
            return None

    def add_card_to_dashboard(self, dashboard_id: int, card_id: int, row: int, col: int, size_x: int = 4, size_y: int = 3) -> bool:
        """Add a card to a dashboard using Metabase v0.48+ API"""
        print(f"    Adding card {card_id} to dashboard {dashboard_id} at position ({row}, {col})...")
        
        response = self.session.get(f"{self.base_url}/api/dashboard/{dashboard_id}")
        if response.status_code != 200:
            print(f"    ✗ Failed to get dashboard: {response.status_code}")
            return False
        
        dashboard = response.json()
        current_cards = dashboard.get("dashcards", dashboard.get("ordered_cards", []))
        
        new_dashcard = {
            "id": -1,
            "card_id": card_id,
            "row": row,
            "col": col,
            "size_x": size_x,
            "size_y": size_y,
            "parameter_mappings": [],
            "visualization_settings": {}
        }
        
        updated_cards = list(current_cards) + [new_dashcard]
        
        response = self.session.put(
            f"{self.base_url}/api/dashboard/{dashboard_id}",
            json={
                "dashcards": updated_cards
            }
        )
        
        if response.status_code in [200, 201, 202]:
            print(f"    ✓ Card added to dashboard")
            return True
        else:
            print(f"    ✗ Failed to add card: {response.status_code} - {response.text}")
            return False

    def setup_from_config(self, config_path: str) -> bool:
        """Setup dashboards from JSON configuration file"""
        print(f"\nLoading configuration from {config_path}...")
        
        with open(config_path, 'r') as f:
            config = json.load(f)

        if not self.create_clickhouse_database():
            return False

        self.sync_database()

        for dashboard_config in config.get("dashboards", []):
            dashboard_id = self.create_dashboard(
                dashboard_config.get("name"),
                dashboard_config.get("description", "")
            )

            if not dashboard_id:
                continue

            row = 0
            col = 0
            for card_config in dashboard_config.get("cards", []):
                card_id = self.create_native_question(
                    card_config.get("name"),
                    card_config.get("query", {}).get("native", {}).get("query", ""),
                    card_config.get("visualization", "table"),
                    card_config.get("x_col"),
                    card_config.get("y_col")
                )

                if card_id:
                    viz = card_config.get("visualization", "table")
                    if viz == "scalar":
                        size_x, size_y = 4, 3
                    elif viz in ["line", "bar"]:
                        size_x, size_y = 8, 4
                    else:
                        size_x, size_y = 6, 4

                    self.add_card_to_dashboard(dashboard_id, card_id, row, col, size_x, size_y)
                    
                    col += size_x
                    if col >= 12:
                        col = 0
                        row += size_y

        print("\n✓ Dashboard setup complete!")
        return True


def main():
    parser = argparse.ArgumentParser(description="Setup Metabase dashboards for Scooter Rental DWH")
    parser.add_argument("--metabase-url", default="http://localhost:3001", help="Metabase URL")
    parser.add_argument("--email", required=True, help="Metabase admin email")
    parser.add_argument("--password", required=True, help="Metabase admin password")
    parser.add_argument("--config", default=None, help="Path to dashboards.json config file")
    parser.add_argument("--wait", action="store_true", help="Wait for Metabase to be ready")
    
    args = parser.parse_args()

    if args.config:
        config_path = args.config
    else:
        script_dir = Path(__file__).parent
        config_path = script_dir / "dashboards.json"
        if not config_path.exists():
            config_path = Path("dashboards.json")

    if not Path(config_path).exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    setup = MetabaseSetup(args.metabase_url, args.email, args.password)

    if args.wait:
        if not setup.wait_for_metabase():
            sys.exit(1)

    if not setup.login():
        print("\nNote: You need to complete the initial Metabase setup first:")
        print("1. Open http://localhost:3001")
        print("2. Create an admin account")
        print("3. Run this script again with your credentials")
        sys.exit(1)

    if not setup.setup_from_config(str(config_path)):
        sys.exit(1)

    print("\n" + "="*50)
    print("Dashboard setup complete!")
    print(f"View your dashboards at: {args.metabase_url}")
    print("="*50)


if __name__ == "__main__":
    main()
