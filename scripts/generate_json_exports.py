"""
Generate JSON exports from metric views for website integration.

This script queries the pre-computed PostgreSQL views and exports
standardized JSON files that any website can consume.

Usage:
    python scripts/generate_json_exports.py

Output:
    data/json/subnet_health_30d.json
    data/json/risk_signals_7d.json
    data/json/subnet_comparison.json
    data/json/data_freshness.json

For website integration:
    1. Host these JSON files on CDN/GitHub Pages
    2. Website fetches: fetch('https://your-cdn.com/subnet_health_30d.json')
    3. Files update every hour via cron
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def get_db_engine():
    """Create database engine from environment variables."""
    connection_string = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(connection_string)


def export_subnet_health(engine, output_dir):
    """Export subnet health metrics (30-day window)."""
    logger.info("Exporting subnet health metrics...")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM v_subnet_health_30d"))
        rows = result.fetchall()
        columns = result.keys()

        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                if isinstance(value, datetime):
                    row_dict[col] = value.isoformat()
                elif isinstance(value, Decimal):
                    row_dict[col] = float(value)
                else:
                    row_dict[col] = value
            data.append(row_dict)

    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "record_count": len(data),
            "time_window": "30_days",
            "source_view": "v_subnet_health_30d"
        },
        "data": data
    }

    output_path = output_dir / "subnet_health_30d.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=decimal_to_float)

    logger.info(f"✓ Exported {len(data)} subnet health records to {output_path}")
    return len(data)


def export_risk_signals(engine, output_dir):
    """Export risk signals (7-day window)."""
    logger.info("Exporting risk signals...")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM v_risk_signals_7d"))
        rows = result.fetchall()
        columns = result.keys()

        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                if isinstance(value, datetime):
                    row_dict[col] = value.isoformat()
                elif isinstance(value, Decimal):
                    row_dict[col] = float(value)
                else:
                    row_dict[col] = value
            data.append(row_dict)

    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "record_count": len(data),
            "time_window": "7_days",
            "source_view": "v_risk_signals_7d"
        },
        "data": data
    }

    output_path = output_dir / "risk_signals_7d.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=decimal_to_float)

    logger.info(f"✓ Exported {len(data)} risk signal records to {output_path}")
    return len(data)


def export_subnet_comparison(engine, output_dir):
    """Export subnet comparison matrix."""
    logger.info("Exporting subnet comparison matrix...")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM v_subnet_comparison"))
        rows = result.fetchall()
        columns = result.keys()

        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                if isinstance(value, datetime):
                    row_dict[col] = value.isoformat()
                elif isinstance(value, Decimal):
                    row_dict[col] = float(value)
                else:
                    row_dict[col] = value
            data.append(row_dict)

    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "record_count": len(data),
            "source_view": "v_subnet_comparison"
        },
        "data": data
    }

    output_path = output_dir / "subnet_comparison.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=decimal_to_float)

    logger.info(f"✓ Exported {len(data)} subnet comparison records to {output_path}")
    return len(data)


def export_data_freshness(engine, output_dir):
    """Export data freshness monitoring."""
    logger.info("Exporting data freshness status...")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM v_data_freshness"))
        rows = result.fetchall()
        columns = result.keys()

        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                if isinstance(value, datetime):
                    row_dict[col] = value.isoformat()
                elif isinstance(value, Decimal):
                    row_dict[col] = float(value)
                else:
                    row_dict[col] = value
            data.append(row_dict)

    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "record_count": len(data),
            "source_view": "v_data_freshness"
        },
        "data": data
    }

    output_path = output_dir / "data_freshness.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=decimal_to_float)

    logger.info(f"✓ Exported {len(data)} data freshness records to {output_path}")
    return len(data)


def export_single_subnet_detail(engine, output_dir, subnet_id):
    """Export detailed view for a single subnet (all metrics combined)."""
    logger.info(f"Exporting detailed data for subnet {subnet_id}...")

    with engine.connect() as conn:
        # Get health metrics
        health = conn.execute(text(
            "SELECT * FROM v_subnet_health_30d WHERE subnet_id = :id"
        ), {"id": subnet_id}).fetchone()

        # Get risk signals
        risks = conn.execute(text(
            "SELECT * FROM v_risk_signals_7d WHERE subnet_id = :id"
        ), {"id": subnet_id}).fetchone()

        # Get top contributors
        contributors_result = conn.execute(text(
            "SELECT * FROM v_top_contributors_30d WHERE subnet_id = :id ORDER BY rank LIMIT 10"
        ), {"id": subnet_id})
        contributors = []
        for row in contributors_result.fetchall():
            contrib = {}
            for i, col in enumerate(contributors_result.keys()):
                value = row[i]
                if isinstance(value, datetime):
                    contrib[col] = value.isoformat()
                elif isinstance(value, Decimal):
                    contrib[col] = float(value)
                else:
                    contrib[col] = value
            contributors.append(contrib)

        # Get 30-day trend
        trends_result = conn.execute(text("""
            SELECT * FROM v_community_trends_90d
            WHERE subnet_id = :id
            ORDER BY activity_date DESC
            LIMIT 30
        """), {"id": subnet_id})
        trends = []
        for row in trends_result.fetchall():
            trend = {}
            for i, col in enumerate(trends_result.keys()):
                value = row[i]
                if isinstance(value, datetime):
                    trend[col] = value.isoformat()
                elif isinstance(value, Decimal):
                    trend[col] = float(value)
                else:
                    trend[col] = value
            trends.append(trend)

    # Combine into single object
    output = {
        "metadata": {
            "subnet_id": subnet_id,
            "generated_at": datetime.now().isoformat(),
        },
        "health_metrics": {},
        "risk_signals": {},
        "top_contributors": contributors,
        "activity_trends": trends
    }

    # Convert health metrics
    if health:
        for i, col in enumerate(health.keys()):
            value = health[i]
            if isinstance(value, datetime):
                output["health_metrics"][col] = value.isoformat()
            elif isinstance(value, Decimal):
                output["health_metrics"][col] = float(value)
            else:
                output["health_metrics"][col] = value

    # Convert risk signals
    if risks:
        for i, col in enumerate(risks.keys()):
            value = risks[i]
            if isinstance(value, datetime):
                output["risk_signals"][col] = value.isoformat()
            elif isinstance(value, Decimal):
                output["risk_signals"][col] = float(value)
            else:
                output["risk_signals"][col] = value

    # Create subnet-specific directory
    subnet_dir = output_dir / "subnets"
    subnet_dir.mkdir(exist_ok=True)

    output_path = subnet_dir / f"subnet_{subnet_id}.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=decimal_to_float)

    logger.info(f"✓ Exported detailed data for subnet {subnet_id} to {output_path}")


def main():
    """Main export function."""
    try:
        # Create output directory
        output_dir = Path(__file__).parent.parent / "data" / "json"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 60)
        logger.info("Starting JSON export from PostgreSQL views")
        logger.info("=" * 60)

        # Get database engine
        engine = get_db_engine()

        # Export aggregate views
        health_count = export_subnet_health(engine, output_dir)
        risk_count = export_risk_signals(engine, output_dir)
        comparison_count = export_subnet_comparison(engine, output_dir)
        freshness_count = export_data_freshness(engine, output_dir)

        # Export individual subnet details (for subnets with data)
        logger.info("\nExporting individual subnet details...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT DISTINCT subnet_id FROM v_subnet_health_30d WHERE subnet_id IS NOT NULL"))
            subnet_ids = [row[0] for row in result.fetchall()]

        for subnet_id in subnet_ids:
            export_single_subnet_detail(engine, output_dir, subnet_id)

        logger.info("\n" + "=" * 60)
        logger.info("✓ Export completed successfully!")
        logger.info(f"  - Subnet health: {health_count} records")
        logger.info(f"  - Risk signals: {risk_count} records")
        logger.info(f"  - Subnet comparison: {comparison_count} records")
        logger.info(f"  - Data freshness: {freshness_count} records")
        logger.info(f"  - Individual subnets: {len(subnet_ids)} files")
        logger.info(f"\nOutput directory: {output_dir.absolute()}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
