"""PostgreSQL local instance manager for CampusPulse.

Provides zero-Docker native PostgreSQL instance management for local development,
migrations, and integration testing using pgembed.
"""

import argparse
import os
import pathlib
import sys
import tempfile
import time
import psycopg2

try:
    from pgembed import get_server
    from pgembed.postgres_server import PostmasterInfo
except ImportError:
    print("ERROR: pgembed is not installed. Run: pip install pgembed", file=sys.stderr)
    sys.exit(1)

DEFAULT_DATA_DIR = pathlib.Path(tempfile.gettempdir()) / "campuspulse_postgres_data"


def get_instance(data_dir: pathlib.Path = DEFAULT_DATA_DIR, cleanup_mode="stop"):
    if data_dir.exists() and (data_dir / "postmaster.pid").exists():
        try:
            pinfo = PostmasterInfo.read_from_pgdata(data_dir)
            if not (pinfo and pinfo.is_running()):
                for fname in ["postmaster.pid", "postmaster.opts"]:
                    try:
                        fpath = data_dir / fname
                        if fpath.exists():
                            fpath.unlink()
                    except Exception:
                        pass
        except Exception:
            pass
    data_dir.mkdir(parents=True, exist_ok=True)
    return get_server(data_dir, cleanup_mode=cleanup_mode)


def ensure_databases(server):
    """Ensure campuspulse_dev and campuspulse_test databases exist."""
    admin_uri = server.get_uri("postgres")
    conn = psycopg2.connect(admin_uri)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'campuspulse_dev';")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE campuspulse_dev;")
        print("[PostgreSQL] Created database: campuspulse_dev")

    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'campuspulse_test';")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE campuspulse_test;")
        print("[PostgreSQL] Created database: campuspulse_test")

    cur.close()
    conn.close()


def write_env_local(dev_uri: str, test_uri: str):
    root_dir = pathlib.Path(__file__).resolve().parent.parent
    env_local_path = root_dir / ".env.local"
    with open(env_local_path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated local PostgreSQL URLs\n")
        f.write(f"DATABASE_URL={dev_uri}\n")
        f.write(f"TEST_DATABASE_URL={test_uri}\n")
        f.write("NEXT_PUBLIC_API_URL=http://localhost:8000\n")
    print(f"[PostgreSQL] Wrote connection strings to {env_local_path}")


def cmd_run(args):
    """Run PostgreSQL server until process termination."""
    server = get_instance(cleanup_mode="stop")
    server.ensure_postgres_running()
    ensure_databases(server)
    dev_uri = server.get_uri("campuspulse_dev")
    test_uri = server.get_uri("campuspulse_test")
    write_env_local(dev_uri, test_uri)

    print(f"[PostgreSQL] Ready and accepting connections.", flush=True)
    print(f"[PostgreSQL] DATABASE_URL={dev_uri}", flush=True)
    print(f"[PostgreSQL] TEST_DATABASE_URL={test_uri}", flush=True)

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("\n[PostgreSQL] Stopping server...")
        server.cleanup()
        print("[PostgreSQL] Stopped cleanly.")


def cmd_status(args):
    pinfo = PostmasterInfo.read_from_pgdata(DEFAULT_DATA_DIR)
    if pinfo and pinfo.is_running():
        print(f"[PostgreSQL] Status: RUNNING (PID: {pinfo.pid})")
        print(f"[PostgreSQL] Host: {pinfo.hostname} Port: {pinfo.port}")
    else:
        print("[PostgreSQL] Status: STOPPED")


def main():
    parser = argparse.ArgumentParser(description="CampusPulse Local PostgreSQL Manager")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("run", help="Run local PostgreSQL server in foreground/daemon")
    subparsers.add_parser("status", help="Check local PostgreSQL server status")

    args = parser.parse_args()
    if args.command == "status":
        cmd_status(args)
    else:
        cmd_run(args)


if __name__ == "__main__":
    main()
