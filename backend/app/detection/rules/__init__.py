"""Rule-based detectors. Import order defines catalogue order."""

from app.detection.rules.brute_force import BruteForceDetector
from app.detection.rules.password_spray import PasswordSprayDetector
from app.detection.rules.port_scan import PortScanDetector
from app.detection.rules.privilege_escalation import PrivilegeEscalationDetector
from app.detection.rules.suspicious_sql import SuspiciousSQLDetector
from app.detection.rules.data_exfiltration import DataExfiltrationDetector
from app.detection.rules.auth_anomaly import AuthAnomalyDetector

RULE_DETECTORS = [
    BruteForceDetector,
    PasswordSprayDetector,
    PortScanDetector,
    PrivilegeEscalationDetector,
    SuspiciousSQLDetector,
    DataExfiltrationDetector,
    AuthAnomalyDetector,
]

__all__ = ["RULE_DETECTORS", *[d.__name__ for d in RULE_DETECTORS]]
