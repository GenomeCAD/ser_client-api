import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from hl7apy.exceptions import HL7apyException
from hl7apy.parser import parse_message
from hl7apy import load_message_profile
from hl7apy.consts import VALIDATION_LEVEL

logger = logging.getLogger(__name__)


# Constants for HL7v2 ACK processing
class MsaStatus:
    """MSA-1 Acknowledgment Code values"""

    APPLICATION_ACCEPT = "AA"
    APPLICATION_ERROR = "AE"
    APPLICATION_REJECT = "AR"


class ErrorSeverity:
    """ERR-4 Severity values"""

    ERROR = "E"
    WARNING = "W"
    INFO = "I"


@dataclass
class AckAnalysisResult:
    """Raw analysis result from HL7v2 ACK message"""

    msa_status: str
    message_control_id: str
    critical_errors: List[str]
    warnings: List[str]
    infos: List[str]


def parse_hl7_message_robust(ack_content: str, profile_path: str):
    """Parse HL7v2 message with automatic line ending normalization

    Handles \r, \n, \r\n and converts to standard HL7v2 \r format
    before calling hl7apy.parser.parse_message()

    Args:
        ack_content: Raw HL7v2 content with potentially mixed line endings
        profile_path: Path to the compiled HL7v2 ACK message profile

    Returns:
        Parsed HL7apy message object
    """
    # Normalize line endings: \r\n -> \r, then \n -> \r (HL7v2 standard)
    normalized_content = ack_content.replace("\r\n", "\r").replace("\n", "\r")

    # Debug logging for troubleshooting
    cr_char = chr(13)  # \r
    lf_char = chr(10)  # \n

    logger.debug(f"Original content length: {len(ack_content)}")
    logger.debug(f"Normalized content length: {len(normalized_content)}")
    logger.debug(
        f"Original line endings: \\r={ack_content.count(cr_char)}, \\n={ack_content.count(lf_char)}"
    )
    logger.debug(
        f"Normalized line endings: \\r={normalized_content.count(cr_char)}, \\n={normalized_content.count(lf_char)}"
    )

    message_profile = load_message_profile(profile_path)
    return parse_message(normalized_content, message_profile=message_profile, validation_level=VALIDATION_LEVEL.STRICT)


def _extract_msa_info(ack_msg) -> Tuple[str, str]:
    """Extract MSA status and message control ID from HL7 message"""
    msa_status = ack_msg.msa.msa_1.value.strip()
    message_control_id = (
        ack_msg.msa.msa_2.value.strip() if ack_msg.msa.msa_2 else "unknown"
    )
    return msa_status, message_control_id


def _analyze_error_segments(ack_msg) -> Tuple[List[str], List[str], List[str]]:
    """Analyze ERR segments and categorize by severity"""
    critical_error_messages = []
    warning_messages = []
    info_messages = []

    for hl7_error_segment in ack_msg.err:
        # HL7v2 ERR segment fields:
        # err_4 = Severity (E=Error, W=Warning, I=Info)
        # err_8 = Diagnostic Information (human-readable message)
        # err_3 = Error Location (file path/reference)

        severity_level = (
            hl7_error_segment.err_4.value.strip()
            if hl7_error_segment.err_4
            else "Unknown"
        )
        diagnostic_message = (
            hl7_error_segment.err_8.value.strip()
            if hl7_error_segment.err_8
            else "No description"
        )
        affected_file_path = (
            hl7_error_segment.err_3.value.strip()
            if hl7_error_segment.err_3
            else "Unknown file"
        )

        formatted_diagnostic = f"File {affected_file_path}: {diagnostic_message}"

        if severity_level == ErrorSeverity.ERROR:
            critical_error_messages.append(formatted_diagnostic)
        elif severity_level == ErrorSeverity.WARNING:
            warning_messages.append(formatted_diagnostic)
        elif severity_level == ErrorSeverity.INFO:
            info_messages.append(formatted_diagnostic)

    return critical_error_messages, warning_messages, info_messages


def _determine_transfer_status(analysis: AckAnalysisResult) -> str:
    """Determine final transfer status based on MSA status and error analysis"""
    # 0 OK
    # 1 ERROR retry
    # 2 Failed do not retry
    if analysis.msa_status == MsaStatus.APPLICATION_ACCEPT:
        return 0
    elif analysis.msa_status == MsaStatus.APPLICATION_ERROR:
        # AE with only warnings/infos = success, AE with critical errors = failure
        return 0 if len(analysis.critical_errors) == 0 else 2
    elif analysis.msa_status == MsaStatus.APPLICATION_REJECT:
        return 2
    else:
        # Unknown MSA status
        return 2


def _log_ack_results(
    filename: str, analysis: AckAnalysisResult, transfer_status: str
) -> None:
    """Log ACK processing results - simplified"""
    # Base context
    context = f"ACK File: {filename} | Control ID:" f" {analysis.message_control_id}"

    # Main result (one line)
    if transfer_status == 0:
        logger.info(
            f"{context} | SUCCESS ({analysis.msa_status}) | Errors: {len(analysis.critical_errors)}, Warnings: {len(analysis.warnings)}, Infos: {len(analysis.infos)}"
        )
    else:
        logger.error(
            f"{context} | FAILED ({analysis.msa_status}) | Errors: {len(analysis.critical_errors)}, Warnings: {len(analysis.warnings)}, Infos: {len(analysis.infos)}"
        )

    # Details (if any)
    for error in analysis.critical_errors:
        logger.error(f"  Error: {error}")
    for warning in analysis.warnings:
        logger.warning(f"  Warning: {warning}")
    for info in analysis.infos:
        logger.info(f"  Info: {info}")


def extract_msh10(hl7_content: str) -> str:
    """Extract MSH-10 from an HL7v2 message string."""
    normalized = hl7_content.replace("\r\n", "\r").replace("\n", "\r")
    for segment in normalized.split("\r"):
        if segment.startswith("MSH|"):
            fields = segment.split("|")
            if len(fields) > 9:
                return fields[9].strip()
    raise ValueError("MSH segment not found or MSH-10 missing in HL7 content")


def _validate_msh(ack_msg, expected_uuid: Optional[str] = None) -> Tuple[List[str], List[str]]:
    """Validate MSH fields of the ACK message.

    Checks:
    - MSH-7: timestamp is present and valid
    - MSH-10: ACK's own message control ID is present
    - MSA-2: echoed UUID matches the expected UUID from the original ORU
    """
    critical_errors = []
    warnings = []

    try:
        timestamp = ack_msg.msh.msh_7.value.strip() if ack_msg.msh.msh_7 else ""
        if not timestamp:
            warnings.append("MSH-7 (timestamp) is missing or empty")
        else:
            datetime.strptime(timestamp[:8], "%Y%m%d")
    except (ValueError, AttributeError):
        warnings.append(f"MSH-7 (timestamp) is not a valid HL7 timestamp: {timestamp!r}")

    try:
        ack_control_id = ack_msg.msh.msh_10.value.strip() if ack_msg.msh.msh_10 else ""
        if not ack_control_id:
            warnings.append("MSH-10 (message control ID) is missing or empty")
    except AttributeError:
        warnings.append("MSH-10 (message control ID) could not be read")

    if expected_uuid is not None:
        try:
            echoed_uuid = ack_msg.msa.msa_2.value.strip() if ack_msg.msa.msa_2 else ""
            if not echoed_uuid:
                critical_errors.append("MSA-2 (echoed control ID) is missing or empty")
            elif echoed_uuid != expected_uuid:
                critical_errors.append(
                    f"MSA-2 control ID mismatch: expected {expected_uuid!r}, got {echoed_uuid!r}"
                )
        except AttributeError:
            critical_errors.append("MSA-2 (echoed control ID) could not be read")

    return critical_errors, warnings


def _analyze_ack_message(ack_msg, expected_uuid: Optional[str] = None) -> AckAnalysisResult:
    """Analyze complete ACK message and return structured result"""
    msa_status, message_control_id = _extract_msa_info(ack_msg)
    critical_error_messages, warning_messages, info_messages = _analyze_error_segments(
        ack_msg
    )
    msh_critical_errors, msh_warnings = _validate_msh(ack_msg, expected_uuid)
    critical_error_messages.extend(msh_critical_errors)
    warning_messages.extend(msh_warnings)

    return AckAnalysisResult(
        msa_status=msa_status,
        message_control_id=message_control_id,
        critical_errors=critical_error_messages,
        warnings=warning_messages,
        infos=info_messages,
    )


def process_ack_file_with_hl7apy(ack_filename: str, ack_content: str, profile_path: str, expected_uuid: Optional[str] = None) -> int:
    # return system
    try:
        ack_msg = parse_hl7_message_robust(ack_content, profile_path)
        analysis = _analyze_ack_message(ack_msg, expected_uuid)
        transfer_status: int = _determine_transfer_status(analysis)
        _log_ack_results(ack_filename, analysis, transfer_status)
        return transfer_status
    except HL7apyException as e:
        """Handle HL7 parsing errors"""
        logger.error(f"HL7 parsing error in ACK file {ack_filename}: {e}")
        logger.error(f"ACK content preview: {ack_content[:200]}...")
        return 2  # failed, do not retry
    except Exception as e:
        logger.error(f"Unexpected error processing ACK file {ack_filename}: {e}")
        return 1  # error, do retry
