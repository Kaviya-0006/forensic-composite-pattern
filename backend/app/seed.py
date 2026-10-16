"""Seeds sample investigations on first run (hierarchy rows + chain-of-custody + activity)."""
import hashlib
from datetime import datetime, timedelta

# (name, type, status, source_device, file_size) for leaves; ("group", name, group_type, [children]) for groups
L = lambda name, type, status, src, size: ("leaf", name, type, status, src, size)
G = lambda name, gtype, kids: ("group", name, gtype, kids)

CASES = [
    ("CASE-2026-001", "Unauthorized Network Access", "Intrusion into the corporate network from a compromised workstation.", "Kaviya J", "HIGH", "ACTIVE", 2.5, [
        G("Computer Evidence", "Computer Evidence", [
            L("Disk Image", "Disk Image", "VERIFIED", "Suspect-PC-07", "512 GB"),
            L("Browser History", "Browser History", "ANALYZED", "Suspect-PC-07", "2.4 MB"),
            L("System Logs", "System Log", "PENDING", "Suspect-PC-07", "1.2 GB"),
            G("Forensic Collection", "Forensic Collection", [
                L("Registry Hive Export", "Other", "PENDING", "Suspect-PC-07", "96 MB"),
                L("Security Event Log", "System Log", "PENDING", "Suspect-PC-07", "640 MB")])]),
        G("Mobile Evidence", "Mobile Evidence", [
            L("Device Image", "Device Image", "VERIFIED", "Handset-12", "128 GB"),
            L("Messages", "Mobile Message", "PENDING", "Handset-12", "240 MB"),
            L("Call Records", "Call Record", "ANALYZED", "Handset-12", "3 MB")]),
        G("Network Evidence", "Network Evidence", [
            L("PCAP Capture", "Network PCAP", "PENDING", "Core Switch Tap", "1.8 GB"),
            L("Firewall Logs", "Firewall Log", "VERIFIED", "Perimeter Firewall", "2.4 GB"),
            L("DNS Logs", "DNS Log", "PENDING", "Internal DNS Server", "610 MB")])]),
    ("CASE-2026-002", "Corporate Data Exfiltration", "Suspected exfiltration of customer records by a departing employee.", "Arjun Rao", "MEDIUM", "UNDER REVIEW", 5, [
        G("Workstation Evidence", "Computer Evidence", [
            L("Laptop Disk Image", "Disk Image", "ANALYZED", "Employee-Laptop-22", "256 GB"),
            L("Browser History", "Browser History", "PENDING", "Employee-Laptop-22", "3.1 MB")]),
        G("Cloud Access Evidence", "Network Evidence", [L("Cloud Gateway Log", "Firewall Log", "VERIFIED", "Cloud Gateway", "900 MB")])]),
    ("CASE-2026-003", "Mobile Device Investigation", "Examination of a seized phone linked to a phishing campaign.", "Meera Nair", "LOW", "COMPLETED", 4, [
        G("Mobile Evidence", "Mobile Evidence", [
            L("Device Image", "Device Image", "ANALYZED", "Handset-31", "64 GB"),
            L("Messages", "Mobile Message", "ANALYZED", "Handset-31", "120 MB"),
            L("Call Records", "Call Record", "ANALYZED", "Handset-31", "2 MB")])]),
    ("CASE-2026-004", "Suspicious Network Activity", "Anomalous outbound traffic detected from a finance subnet.", "Kaviya J", "HIGH", "ACTIVE", 1.8, [
        G("Network Evidence", "Network Evidence", [
            L("Flow Capture", "Network PCAP", "PENDING", "Finance Subnet Tap", "6.3 GB"),
            L("DNS Logs", "DNS Log", "PENDING", "Internal DNS Server", "420 MB")])]),
]


def seed(repo) -> bool:
    if repo.count_cases() > 0:
        return False
    tick = datetime.now() - timedelta(days=3)
    n = {"ev": 420, "gr": 0}

    def insert(row):
        nonlocal tick
        tick += timedelta(seconds=1)
        repo.insert_evidence({"created_at": tick, "updated_at": tick, "description": "", "hash": "", "file_size": "", "source_device": "", "collected_by": "", **row})

    for case_id, title, desc, inv, prio, status, days_ago, kids in CASES:
        start = datetime.now() - timedelta(days=days_ago)
        repo.create_case({"id": case_id, "name": title, "description": desc, "investigator": inv, "priority": prio, "status": status, "created_at": start, "updated_at": start})
        insert({"id": case_id, "case_id": case_id, "parent_id": None, "name": title, "type": "Investigation Case", "kind": "group", "status": "PENDING", "collected_at": start})
        clock = [start]

        def add(spec, parent):
            if spec[0] == "group":
                n["gr"] += 1
                gid = f"EV-GROUP-{n['gr']:03d}"
                insert({"id": gid, "case_id": case_id, "parent_id": parent, "name": spec[1], "type": spec[2], "kind": "group", "status": "PENDING", "collected_at": start})
                for kid in spec[3]:
                    add(kid, gid)
                return
            n["ev"] += 1
            eid = f"EV-2026-{n['ev']:05d}"
            collected = clock[0] = clock[0] + timedelta(minutes=4)
            _, name, typ, st, src, size = spec
            h = hashlib.sha256(eid.encode()).hexdigest()
            insert({"id": eid, "case_id": case_id, "parent_id": parent, "name": name, "type": typ, "kind": "leaf", "status": st, "source_device": src,
                    "file_size": size, "hash": h, "collected_by": inv, "collected_at": collected, "description": f"{typ} acquired from {src}."})
            ev = [("Evidence collected", inv, "INTACT", f"Acquired from {src}", 0), ("SHA-256 generated", "FORENSICVAULT", "INTACT", h[:16] + "...", 2),
                  ("Transferred to forensic laboratory", "Lab Custodian R. Menon", "INTACT", "Sealed transfer", 43)]
            if st in ("VERIFIED", "ANALYZED"):
                ev.append(("SHA-256 verified", inv, "VERIFIED", "Stored hash matches recomputed hash (simulated)", 1000))
            if st == "ANALYZED":
                ev += [("Analysis started", inv, "INTACT", "analyze() invoked", 1320), ("Analysis completed", inv, "INTACT", "Metadata extracted, file system analyzed", 1395)]
            for action, actor, integ, details, mins in ev:
                repo.add_custody({"evidence_id": eid, "evidence_name": name, "action": action, "actor": actor, "integrity": integ, "details": details,
                                  "occurred_at": collected + timedelta(minutes=mins)})

        for spec in kids:
            add(spec, case_id)
    now = datetime.now()
    for mins, actor, action, msg, cid in [(8, "Kaviya J", "ANALYSIS_COMPLETED", "Disk Image analyzed", "CASE-2026-001"), (14, "Kaviya J", "EVIDENCE_ADDED", "Network PCAP added to CASE-2026-001", "CASE-2026-001"),
                                          (20, "Kaviya J", "GROUP_CREATED", "Mobile Evidence group created", "CASE-2026-001"), (29, "Arjun Rao", "HASH_VERIFIED", "Evidence hash verified", "CASE-2026-002"),
                                          (95, "Meera Nair", "ANALYSIS_COMPLETED", "Mobile Evidence analyzed recursively", "CASE-2026-003")][::-1]:
        repo.add_activity({"case_id": cid, "actor": actor, "action": action, "entity_id": cid, "message": msg, "created_at": now - timedelta(minutes=mins)})
    return True
