"""
Business Models - Pure business logic without technical dependencies
Represents the core genomics concepts in a technology-agnostic way
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional


@dataclass
class ConditionData:
    """Data model for Preindication information.

    Contains preindication details for HL7v2 PV1 segment generation.
    """

    name: str
    key: str
    cat_name: str
    cat_key: str


@dataclass
class CareTeamData:
    """Data model for RCP (Réunion de Concertation Pluridisciplinaire) information.

    Contains RCP information for HL7v2 PRT segment generation.
    """

    rcp_id: str  # RCP unique identifier
    rcp_nom: str  # RCP name/organization

    def __post_init__(self):
        """Validate required business rules.

        :raises ValueError: If required fields are missing
        """
        if not self.rcp_id:
            raise ValueError("RCP ID is required")
        if not self.rcp_nom:
            raise ValueError("RCP name is required")


@dataclass
class PatientData:
    """Data model for HL7v2 PID segment.

    Conforms to HL7v2 profile constraints.
    Contains patient information for HL7v2 message generation.
    """

    set_id: int = None
    patient_id: str = None
    patient_given_name: str = None
    patient_family_name: str = None
    birth_date: date = None
    sex: Optional[str] = None
    date_prelevement: datetime = None

    @property
    def hl7_birth_date(self) -> str:
        """Format birth date for HL7v2 (YYYYMMDD format).

        :return: Date in HL7v2 format or empty string
        :rtype: str
        """
        if self.birth_date:
            return self.birth_date.strftime("%Y%m%d")
        return ""


@dataclass
class PersonData:
    """Data model for Person information in PRT segment.

    Contains prescripteur and membreRCP information for PRT-5 Person field.
    """

    prescripteur: Optional[str] = None  # Prescripteur ID for PRT-5
    membre_rcp: Optional[str] = None  # Membre RCP ID for PRT-5


@dataclass
class ProcedureData:
    """Data model for Analysis/Device information in PRT segment.

    Contains analysis_id for PRT-10 Device field.
    """

    analysis_id: Optional[str] = None  # Analysis ID for PRT-10


@dataclass
class PeriodData:
    """Data model for Timing information in PRT segment.

    Contains start and end timestamps for PRT-11/PRT-12 fields.
    """

    start: Optional[datetime] = None  # PRT-11 Begin Date/Time
    end: Optional[datetime] = None  # PRT-12 End Date/Time


@dataclass
class ObservationData:
    """Data model for Results information.

    Contains results data from the source system.
    """

    membre_lmg: Optional[str] = None


@dataclass
class ConsentData:
    """Data model for CON segment (Consent).

    Contains consent information for HL7v2 CON segment generation.
    Only generated when is_data_reusable_for_research=True.
    """

    is_data_reusable_for_research: bool = False
    date_consent: Optional[datetime] = None
    consenter_family_name: Optional[str] = None
    consenter_given_name: Optional[str] = None


@dataclass
class RelatedPersonData:
    """Data model for NK1 segment (Next of Kin).

    Contains family/relationship information for HL7v2 NK1 segment generation.
    Used to represent father (père) and mother (mère) in trio scenarios.
    """

    set_id: int  # NK1-1: 1=père, 2=mère
    relationship_code: str  # NK1-3: FTH (Father) or MTH (Mother)
    family_name: Optional[str] = None
    given_name: Optional[str] = None
    birth_date: Optional[date] = None  # NK1-16
    sex: Optional[str] = None  # NK1-15
    patient_id: Optional[str] = None  # IPP for file association

    @property
    def folder_name(self) -> str:
        """Return folder name for this individual's files.

        :return: Folder name in format FAMILY_GIVEN or None
        :rtype: str
        """
        if self.family_name and self.given_name:
            return f"{self.family_name}_{self.given_name}"
        return None

    @property
    def hl7_birth_date(self) -> str:
        """Format birth date for HL7v2 (YYYYMMDD format).

        :return: Date in HL7v2 format or empty string
        :rtype: str
        """
        if self.birth_date:
            return self.birth_date.strftime("%Y%m%d")
        return ""


@dataclass
class CompositionData:
    """Main report model - Contains all the useful parsed data"""

    report_id: str
    patient: PatientData
    person: PersonData = None
    analysis: ProcedureData = None
    timing: PeriodData = None
    rcp: CareTeamData = None
    preindication: ConditionData = None
    results: ObservationData = None
    consent: ConsentData = None
    next_of_kin: Optional[List[RelatedPersonData]] = None
