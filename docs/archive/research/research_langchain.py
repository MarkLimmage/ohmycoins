import requests
import pandas as pd
from datetime import datetime
from packaging import version
import json

def get_pypi_history(package_name):
    """
    Fetches the release history and metadata for a given package from PyPI.
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    print(f"Fetching history for {package_name}...")
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        releases = data.get("releases", {})
        
        history = []
        for ver, files in releases.items():
            if not files:
                continue
            upload_time = files[0]["upload_time"]
            history.append({
                "package": package_name,
                "version": ver,
                "release_date": datetime.strptime(upload_time, "%Y-%m-%dT%H:%M:%S")
            })
        
        # Sort by release date
        df = pd.DataFrame(history)
        if not df.empty:
            df = df.sort_values("release_date", ascending=False)
        return df, data
    else:
        print(f"Failed to fetch data for {package_name}")
        return pd.DataFrame(), {}

# Fetch history for langchain and langchain-core
df_langchain, meta_langchain = get_pypi_history("langchain")
df_core, meta_core = get_pypi_history("langchain-core")

print("LangChain Latest Version:", df_langchain.iloc[0]['version'] if not df_langchain.empty else "N/A")
print("LangChain Core Latest Version:", df_core.iloc[0]['version'] if not df_core.empty else "N/A")

def get_specific_release_info(package_name, target_version):
    """
    Fetches dependencies for a specific version.
    """
    url = f"https://pypi.org/pypi/{package_name}/{target_version}/json"
    print(f"Fetching info for {package_name} v{target_version}...")
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        info = data.get("info", {})
        requires_dist = info.get("requires_dist", [])
        return {
            "version": target_version,
            "upload_time": datetime.strptime(data["urls"][0]["upload_time"], "%Y-%m-%dT%H:%M:%S") if data["urls"] else None,
            "requires_dist": requires_dist
        }
    return None

# Check specific versions
langchain_v1_2_10 = get_specific_release_info("langchain", "1.2.10")
langchain_core_v1_2_13 = get_specific_release_info("langchain-core", "1.2.13")

print("--- LangChain 1.2.10 ---")
if langchain_v1_2_10:
    print(f"Date: {langchain_v1_2_10.get('upload_time')}")
    # Filter for langchain-core requirement
    core_req = [req for req in langchain_v1_2_10.get('requires_dist', []) if 'langchain-core' in req]
    print(f"Depends on langchain-core: {core_req}")
else:
    print("Version not found.")

print("\n--- LangChain-Core 1.2.13 ---")
if langchain_core_v1_2_13:
    print(f"Date: {langchain_core_v1_2_13.get('upload_time')}")
    # Filter for pydantic requirement
    pydantic_req = [req for req in langchain_core_v1_2_13.get('requires_dist', []) if 'pydantic' in req]
    print(f"Depends on pydantic: {pydantic_req}")
else:
    print("Version not found.")

def check_osv_vulnerabilities(package_name, version_str):
    url = "https://api.osv.dev/v1/query"
    print(f"Checking CVEs for {package_name} v{version_str}...")
    payload = {
        "version": version_str,
        "package": {
            "name": package_name,
            "ecosystem": "PyPI"
        }
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    return {}

# Check for CVEs
cve_langchain = check_osv_vulnerabilities("langchain", "1.2.10")
cve_core = check_osv_vulnerabilities("langchain-core", "1.2.13")

print("--- CVEs for LangChain 1.2.10 ---")
if 'vulns' in cve_langchain:
    for vuln in cve_langchain['vulns']:
        print(f"ID: {vuln['id']}, Summary: {vuln.get('summary', 'No summary')}")
else:
    print("No known vulnerabilities found.")

print("\n--- CVEs for LangChain-Core 1.2.13 ---")
if 'vulns' in cve_core:
    for vuln in cve_core['vulns']:
        print(f"ID: {vuln['id']}, Summary: {vuln.get('summary', 'No summary')}")
else:
    print("No known vulnerabilities found.")
