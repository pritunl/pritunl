#!/usr/bin/env python3
import pymongo
import sys
import time
import logging
import argparse
from urllib.parse import urlparse

SOURCE_MONGO_URI = "mongodb://localhost:27017/pritunl"
TARGET_MONGO_URIS = [
    "mongodb://localhost:27017/pritunl",
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def connect_to_mongo(uri):
    try:
        client = pymongo.MongoClient(uri)
        db = client.get_default_database()
        client.server_info()
        parsed_uri = urlparse(uri)
        hosts = parsed_uri.netloc.split('@')[-1]
        db_name = db.name
        logger.info(f"Successfully connected to {db_name} on {hosts}")
        return db
    except pymongo.errors.ConnectionFailure as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred while connecting to MongoDB: {e}")
        raise

def copy_devices(dry_run=False):
    if dry_run:
        logger.info("DRY RUN MODE: No changes will be made to the "
            "target databases")

    source_db = connect_to_mongo(SOURCE_MONGO_URI)

    target_dbs = []
    for uri in TARGET_MONGO_URIS:
        try:
            db = connect_to_mongo(uri)
            target_dbs.append(db)
        except Exception as e:
            logger.error(f"Failed to connect to target database {uri}: {e}")

    if not target_dbs:
        logger.error("No target databases available. Exiting.")
        return

    users_cursor = source_db["users"].find({})

    stats = {
        "users_processed": 0,
        "users_matched": 0,
        "devices_copied": 0,
        "errors": 0,
        "targets_updated": 0
    }

    for user in users_cursor:
        stats["users_processed"] += 1
        user_name = user.get("name")

        if not user_name:
            logger.warning(f"Skipping user with no name: {user.get('_id')}")
            continue

        if not user.get("devices"):
            logger.info(f"User '{user_name}' has no devices, skipping")
            continue

        user_found = False
        device_names = []
        for device in user["devices"]:
            device_names.append(device.get("name", "UNKNOWN"))

        for i, target_db in enumerate(target_dbs):
            target_users = target_db["users"]

            target_user = target_users.find_one({"name": user_name})
            if not target_user:
                logger.warning(f"No matching user found in target "
                    f"database #{i+1} for '{user_name}'")
                continue

            user_found = True
            try:
                if dry_run:
                    num_devices = len(user["devices"])
                    for j, device_name in enumerate(device_names):
                        logger.info(f"DRY RUN: Device {j+1}/{num_devices} "
                            f"for user '{user_name}' to copy to target "
                            f"#{i+1}: '{device_name}'")

                    stats["devices_copied"] += num_devices
                    stats["targets_updated"] += 1
                else:
                    result = target_users.update_many(
                        {"name": user_name},
                        {"$set": {"devices": user["devices"]}}
                    )

                    if result.modified_count > 0:
                        num_devices = len(user["devices"])
                        stats["devices_copied"] += num_devices
                        stats["targets_updated"] += 1
                        logger.info(f"Copied {num_devices} device(s) for "
                            f"user '{user_name}' to target #{i+1}, "
                            f"{result.modified_count} document(s) updated")
                    else:
                        logger.warning(f"No changes made for user "
                            f"'{user_name}' in target #{i+1}")

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Error updating devices for user "
                    f"'{user_name}' in target #{i+1}: {e}")

        if user_found:
            stats["users_matched"] += 1

    mode_prefix = "DRY RUN: Would have" if dry_run else "Operation completed."
    logger.info(f"{mode_prefix} Summary:")
    logger.info(f"  Users processed: {stats['users_processed']}")
    logger.info(f"  Users matched: {stats['users_matched']}")
    logger.info(f"  Devices "
        f"{'that would be copied' if dry_run else 'copied'}: "
        f"{stats['devices_copied']}")
    logger.info(f"  Target databases "
        f"{'that would be updated' if dry_run else 'updated'}: "
        f"{stats['targets_updated']}")
    logger.info(f"  Errors encountered: {stats['errors']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Copy devices from source to target MongoDB databases.',
    )
    parser.add_argument(
        '--live-run',
        action='store_true',
        help='Run in live-run mode (changes will be made)',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no changes will be made)',
    )
    args = parser.parse_args()

    if args.live_run and args.dry_run:
        logger.error("Error: Cannot specify both --live-run and --dry-run")
        sys.exit(1)

    if len(sys.argv) == 1 or (not args.live_run and not args.dry_run):
        parser.print_help(sys.stderr)
        sys.exit(1)

    dry_run = not args.live_run

    if args.dry_run:
        dry_run = True

    mode = "DRY RUN MODE" if dry_run else "LIVE MODE"

    if not dry_run:
        logger.warning("LIVE RUN MODE: Changes will be made to "
            "target databases")
        logger.warning("Press Ctrl+C within 3 seconds to abort...")
        try:
            for i in range(3, 0, -1):
                logger.warning(f"Starting live run in {i} seconds...")
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Operation aborted by user")
            sys.exit(0)

    try:
        logger.info(f"Starting device copying process ({mode})")
        logger.info(f"Source: {SOURCE_MONGO_URI}")
        logger.info(f"Number of targets: {len(TARGET_MONGO_URIS)}")
        copy_devices(dry_run=dry_run)
        logger.info(f"Device copying process completed successfully ({mode})")
    except Exception as e:
        logger.error(f"An error occurred during the copying process: {e}")
        raise
