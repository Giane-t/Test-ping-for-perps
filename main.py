import csv
import json
import os
import platform
import re
import socket
import subprocess
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("=" * 60)
    print("ERROR: Python package 'requests' is not installed.")
    print("Install it with: pip install -r requirements.txt")
    print("=" * 60)
    sys.exit(1)

from settings import (
    EXCHANGES,
    GEOIP_API,
    GEOIP_PAUSE_SECONDS,
    GEOIP_TIMEOUT_SECONDS,
    HTTP_TIMEOUT_SECONDS,
    PING_COMMAND_TIMEOUT_SECONDS,
    PING_COUNT,
    RESULTS_DIR,
)


def ensure_results_dir() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def resolve_hostname(hostname: str) -> str:
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror as exc:
        return f"DNS Error: {exc}"


def parse_windows_ping_output(output: str, count: int, result: dict) -> None:
    loss_match = re.search(r"\((\d+)%\s*(loss|potery|потерь)", output, re.IGNORECASE)
    if loss_match:
        result["packet_loss"] = float(loss_match.group(1))
        result["packets_received"] = int(count * (100 - result["packet_loss"]) / 100)

    time_match = re.search(
        r"(?:Minimum|Минимальное)\s*=\s*(\d+)\s*(?:ms|мс).*?"
        r"(?:Maximum|Максимальное)\s*=\s*(\d+)\s*(?:ms|мс).*?"
        r"(?:Average|Среднее)\s*=\s*(\d+)\s*(?:ms|мс)",
        output,
        re.IGNORECASE | re.DOTALL,
    )
    if time_match:
        result["min_ms"] = float(time_match.group(1))
        result["max_ms"] = float(time_match.group(2))
        result["avg_ms"] = float(time_match.group(3))

    if result["avg_ms"] is None:
        alt_match = re.search(r"Average\s*=\s*(\d+)ms", output, re.IGNORECASE)
        if alt_match:
            result["avg_ms"] = float(alt_match.group(1))


def parse_linux_ping_output(output: str, result: dict) -> None:
    packets_match = re.search(
        r"(\d+)\s+packets transmitted,\s+(\d+)\s+(?:packets )?received,?\s+([\d.]+)%\s+packet loss",
        output,
        re.IGNORECASE,
    )
    if packets_match:
        result["packets_sent"] = int(packets_match.group(1))
        result["packets_received"] = int(packets_match.group(2))
        result["packet_loss"] = float(packets_match.group(3))

    time_match = re.search(
        r"(?:rtt|round-trip)\s+min/avg/max/(?:mdev|stddev)\s*=\s*"
        r"([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)\s+ms",
        output,
        re.IGNORECASE,
    )
    if time_match:
        result["min_ms"] = float(time_match.group(1))
        result["avg_ms"] = float(time_match.group(2))
        result["max_ms"] = float(time_match.group(3))


def ping_host(hostname: str, count: int = PING_COUNT) -> dict:
    result = {
        "host": hostname,
        "ip": None,
        "packets_sent": count,
        "packets_received": 0,
        "packet_loss": 100.0,
        "min_ms": None,
        "max_ms": None,
        "avg_ms": None,
        "error": None,
    }

    try:
        ip = resolve_hostname(hostname)
        if ip.startswith("DNS Error"):
            result["error"] = ip
            return result
        result["ip"] = ip

        system_name = platform.system().lower()
        env = None

        if system_name == "windows":
            cmd = ["ping", "-n", str(count), "-w", "3000", hostname]
            encoding = "cp866"
        else:
            cmd = ["ping", "-c", str(count), "-W", "3", hostname]
            encoding = "utf-8"
            env = os.environ.copy()
            env["LANG"] = "C"
            env["LC_ALL"] = "C"

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=PING_COMMAND_TIMEOUT_SECONDS,
            encoding=encoding,
            env=env,
            errors="ignore",
        )

        output = process.stdout + ("\n" + process.stderr if process.stderr else "")

        if system_name == "windows":
            parse_windows_ping_output(output, count, result)
        else:
            parse_linux_ping_output(output, result)

        if result["packets_received"] == 0 and not result["error"]:
            result["error"] = "All packets lost (host unreachable or blocking ICMP)"

    except FileNotFoundError:
        result["error"] = "Ping command not found. Install it with: sudo apt install iputils-ping"
    except subprocess.TimeoutExpired:
        result["error"] = f"Ping timeout (>{PING_COMMAND_TIMEOUT_SECONDS}s)"
    except Exception as exc:
        result["error"] = str(exc)

    return result


def get_geolocation(ip: str) -> dict:
    geo_result = {
        "country": None,
        "country_code": None,
        "region": None,
        "city": None,
        "lat": None,
        "lon": None,
        "isp": None,
        "org": None,
        "as": None,
        "error": None,
    }

    if not ip or ip.startswith("DNS Error"):
        geo_result["error"] = "No valid IP"
        return geo_result

    try:
        response = requests.get(GEOIP_API.format(ip=ip), timeout=GEOIP_TIMEOUT_SECONDS)
        data = response.json()

        if data.get("status") == "success":
            geo_result["country"] = data.get("country")
            geo_result["country_code"] = data.get("countryCode")
            geo_result["region"] = data.get("regionName")
            geo_result["city"] = data.get("city")
            geo_result["lat"] = data.get("lat")
            geo_result["lon"] = data.get("lon")
            geo_result["isp"] = data.get("isp")
            geo_result["org"] = data.get("org")
            geo_result["as"] = data.get("as")
        else:
            geo_result["error"] = data.get("message", "Unknown error")

    except requests.RequestException as exc:
        geo_result["error"] = f"Request error: {exc}"
    except Exception as exc:
        geo_result["error"] = str(exc)

    return geo_result


def check_http_latency(url: str, timeout: int = HTTP_TIMEOUT_SECONDS) -> dict:
    result = {
        "url": url,
        "http_latency_ms": None,
        "status_code": None,
        "error": None,
    }

    try:
        start_time = datetime.now()
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        end_time = datetime.now()

        latency = (end_time - start_time).total_seconds() * 1000
        result["http_latency_ms"] = round(latency, 2)
        result["status_code"] = response.status_code

    except requests.Timeout:
        result["error"] = "HTTP timeout"
    except requests.ConnectionError as exc:
        result["error"] = f"Connection error: {str(exc)[:80]}"
    except Exception as exc:
        result["error"] = str(exc)[:80]

    return result


def analyze_exchange(exchange_name: str, exchange_data: dict) -> dict:
    print(f"\n{'=' * 60}")
    print(f"Analyzing: {exchange_name}")
    print(f"Description: {exchange_data['description']}")
    print(f"{'=' * 60}")

    exchange_result = {
        "name": exchange_name,
        "description": exchange_data["description"],
        "endpoints": [],
        "best_endpoint": None,
        "estimated_location": None,
    }

    for url in exchange_data["endpoints"]:
        print(f"\n  Checking: {url}")
        hostname = urlparse(url).netloc

        endpoint_result = {
            "url": url,
            "hostname": hostname,
            "ping": None,
            "http": None,
            "geolocation": None,
        }

        print("    [1/3] ICMP ping...", end=" ", flush=True)
        ping_result = ping_host(hostname)
        endpoint_result["ping"] = ping_result
        if ping_result["avg_ms"] is not None:
            print(f"OK ({ping_result['avg_ms']} ms avg)")
        else:
            print("BLOCKED/TIMEOUT")

        print("    [2/3] HTTP latency...", end=" ", flush=True)
        http_result = check_http_latency(url)
        endpoint_result["http"] = http_result
        if http_result["http_latency_ms"] is not None:
            print(f"OK ({http_result['http_latency_ms']} ms)")
        else:
            print(f"ERROR: {http_result.get('error', 'Unknown')}")

        print("    [3/3] Geolocation...", end=" ", flush=True)
        if ping_result["ip"] and not ping_result["ip"].startswith("DNS"):
            geo_result = get_geolocation(ping_result["ip"])
            endpoint_result["geolocation"] = geo_result
            if geo_result["city"]:
                print(f"OK ({geo_result['city']}, {geo_result['country']})")
            else:
                print(f"PARTIAL: {geo_result.get('country', 'Unknown')}")
        else:
            print("SKIPPED (no IP)")

        exchange_result["endpoints"].append(endpoint_result)
        time.sleep(GEOIP_PAUSE_SECONDS)

    best_latency = float("inf")
    best_endpoint = None
    locations = []

    for endpoint in exchange_result["endpoints"]:
        geo = endpoint["geolocation"]
        if geo and geo["city"]:
            location = f"{geo['city']}, {geo['country']}"
            if location not in locations:
                locations.append(location)

        http_result = endpoint["http"]
        if http_result and http_result["http_latency_ms"] is not None:
            if http_result["http_latency_ms"] < best_latency:
                best_latency = http_result["http_latency_ms"]
                best_endpoint = endpoint["url"]

    exchange_result["best_endpoint"] = best_endpoint
    exchange_result["estimated_location"] = locations if locations else ["Unknown"]
    return exchange_result


def print_summary(results: list) -> None:
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"\n{'Exchange':<15} {'IP':<16} {'ICMP Ping':<12} {'HTTP':<12} {'Location':<30}")
    print("-" * 85)

    for exchange in results:
        name = exchange["name"]
        for endpoint in exchange["endpoints"]:
            ping_result = endpoint["ping"]
            http_result = endpoint["http"]
            geo_result = endpoint["geolocation"]

            ip = ping_result["ip"] if ping_result["ip"] and not str(ping_result["ip"]).startswith("DNS") else "N/A"
            icmp = f"{ping_result['avg_ms']} ms" if ping_result["avg_ms"] is not None else "blocked"
            http = f"{http_result['http_latency_ms']} ms" if http_result and http_result["http_latency_ms"] is not None else "error"

            if geo_result and geo_result["city"]:
                location = f"{geo_result['city']}, {geo_result['country_code']}"
            elif geo_result and geo_result["country"]:
                location = geo_result["country"]
            else:
                location = "Unknown"

            print(f"{name:<15} {ip:<16} {icmp:<12} {http:<12} {location:<30}")
            name = ""

    print("-" * 85)


def get_hosting_recommendation(locations: list[str]) -> str:
    if not locations or locations[0] == "Unknown":
        return "Location could not be determined"

    loc_str = " ".join(locations).lower()
    if "tokyo" in loc_str or "japan" in loc_str or "asia" in loc_str:
        return "AWS ap-northeast-1 (Tokyo), Vultr Tokyo"
    if "london" in loc_str or "uk" in loc_str or "united kingdom" in loc_str:
        return "AWS eu-west-2 (London), Equinix LD4/LD5"
    if "frankfurt" in loc_str or "germany" in loc_str:
        return "AWS eu-central-1 (Frankfurt), Hetzner"
    if "amsterdam" in loc_str or "netherlands" in loc_str:
        return "AWS eu-west-1, DigitalOcean AMS"
    if any(item in loc_str for item in ["us", "united states", "virginia", "california", "oregon", "ohio", "florida"]):
        return "AWS us-east-1 (N. Virginia), Vultr NJ/Chicago"
    return f"Host closer to {locations[0]}"


def save_results(results: list, timestamp: str) -> None:
    ensure_results_dir()

    json_path = RESULTS_DIR / f"ping_results_{timestamp}.json"
    csv_path = RESULTS_DIR / f"ping_results_{timestamp}.csv"
    summary_path = RESULTS_DIR / f"ping_summary_{timestamp}.txt"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump({"timestamp": timestamp, "results": results}, file, ensure_ascii=False, indent=2)
    print(f"\nSaved JSON: {json_path}")

    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "Exchange",
                "Endpoint",
                "Hostname",
                "IP",
                "ICMP Ping (ms)",
                "HTTP Latency (ms)",
                "Country",
                "City",
                "ISP/Org",
                "AS",
            ]
        )

        for exchange in results:
            for endpoint in exchange["endpoints"]:
                ping_result = endpoint["ping"]
                http_result = endpoint["http"]
                geo_result = endpoint["geolocation"] or {}

                writer.writerow(
                    [
                        exchange["name"],
                        endpoint["url"],
                        endpoint["hostname"],
                        ping_result["ip"] if ping_result["ip"] and not str(ping_result["ip"]).startswith("DNS") else "",
                        ping_result["avg_ms"] or "",
                        http_result["http_latency_ms"] if http_result else "",
                        geo_result.get("country", ""),
                        geo_result.get("city", ""),
                        geo_result.get("org") or geo_result.get("isp", ""),
                        geo_result.get("as", ""),
                    ]
                )
    print(f"Saved CSV: {csv_path}")

    with summary_path.open("w", encoding="utf-8") as file:
        file.write("=" * 80 + "\n")
        file.write(f"EXCHANGE SERVER SUMMARY - {timestamp}\n")
        file.write("=" * 80 + "\n\n")

        for exchange in results:
            file.write(f"{exchange['name'].upper()}\n")
            file.write("-" * 40 + "\n")
            file.write(f"Description: {exchange['description']}\n")
            file.write(f"Estimated location: {', '.join(exchange['estimated_location'])}\n")
            file.write(f"Best endpoint: {exchange['best_endpoint']}\n")
            file.write("Endpoints:\n")

            for endpoint in exchange["endpoints"]:
                ping_result = endpoint["ping"]
                http_result = endpoint["http"]
                geo_result = endpoint["geolocation"]

                file.write(f"\n  URL: {endpoint['url']}\n")
                file.write(f"  IP: {ping_result['ip']}\n")
                file.write(
                    f"  ICMP Ping: {ping_result['avg_ms']} ms (avg)\n"
                    if ping_result["avg_ms"] is not None
                    else "  ICMP Ping: blocked/timeout\n"
                )
                file.write(
                    f"  HTTP Latency: {http_result['http_latency_ms']} ms\n"
                    if http_result and http_result["http_latency_ms"] is not None
                    else "  HTTP Latency: error\n"
                )

                if geo_result and geo_result["city"]:
                    file.write(f"  Location: {geo_result['city']}, {geo_result['region']}, {geo_result['country']}\n")
                    file.write(f"  Coordinates: {geo_result['lat']}, {geo_result['lon']}\n")
                    file.write(f"  ISP/Org: {geo_result['org'] or geo_result['isp']}\n")
                    file.write(f"  AS: {geo_result['as']}\n")

            file.write("\n")

        file.write("=" * 80 + "\n")
        file.write("HOSTING RECOMMENDATIONS\n")
        file.write("=" * 80 + "\n\n")

        for exchange in results:
            recommendation = get_hosting_recommendation(exchange["estimated_location"])
            file.write(f"{exchange['name']}: {recommendation}\n")

    print(f"Saved summary: {summary_path}")


def main() -> None:
    print("=" * 60)
    print("EXCHANGE SERVER PING & GEOLOCATION CHECKER")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Exchanges: {', '.join(EXCHANGES.keys())}")

    results = []
    for exchange_name, exchange_data in EXCHANGES.items():
        results.append(analyze_exchange(exchange_name, exchange_data))

    print_summary(results)
    save_results(results, timestamp)

    print("\n" + "=" * 60)
    print("CHECK COMPLETE")
    print("=" * 60)
    print(f"Results folder: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
