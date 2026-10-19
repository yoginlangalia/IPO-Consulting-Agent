from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.session import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(255), nullable=True)
    sector = Column(String(255), nullable=True)
    incorporation_date = Column(Date, nullable=True)
    incorporation_year = Column(Integer, nullable=True)
    entity_type = Column(String(100), nullable=True)  # Pvt Ltd, Public Ltd, etc.
    target_track = Column(String(50), default="REG_6_1")
    target_ipo_date = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    financial_data = Column(JSON, default=dict)
    readiness_score = Column(Float, nullable=True)
    eligibility_status = Column(String(50), default="PENDING")
    status = Column(String(50), default="draft")  # draft, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="company", cascade="all, delete-orphan")
    questionnaire_responses = relationship("QuestionnaireResponse", back_populates="company", cascade="all, delete-orphan")
    eligibility_results = relationship("EligibilityResult", back_populates="company", cascade="all, delete-orphan")
    readiness_scores = relationship("ReadinessScore", back_populates="company", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="company", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    doc_type = Column(String(100), nullable=False)  # financial, cap_table, governance, compliance, contracts, business_plan
    file_size = Column(Integer, nullable=True)
    extracted_text = Column(Text, nullable=True)
    parsed_data = Column(JSON, nullable=True)
    upload_status = Column(String(50), default="uploaded")  # uploaded, parsing, parsed, error
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="documents")


class QuestionnaireResponse(Base):
    __tablename__ = "questionnaire_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    responses = Column(JSON, nullable=False, default=dict)
    completed = Column(Integer, default=0)  # 0 = incomplete, 1 = complete
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="questionnaire_responses")


class SebiRule(Base):
    __tablename__ = "sebi_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_code = Column(String(100), unique=True, nullable=False)
    regulation = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # financial_eligibility, governance, promoter, structural
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    threshold_value = Column(String(255), nullable=True)
    check_type = Column(String(50), nullable=False)  # code, ai
    data_source = Column(String(255), nullable=True)
    route = Column(String(50), nullable=True)  # route_1, route_2, general, None

    # Relationships
    eligibility_results = relationship("EligibilityResult", back_populates="rule")


class EligibilityResult(Base):
    __tablename__ = "eligibility_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("sebi_rules.id"), nullable=False)
    status = Column(String(50), nullable=False)  # pass, fail, insufficient_data
    actual_value = Column(String(500), nullable=True)
    evidence = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="eligibility_results")
    rule = relationship("SebiRule", back_populates="eligibility_results")


class ReadinessScore(Base):
    __tablename__ = "readiness_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    category = Column(String(100), nullable=False)  # financial_health, governance, legal_compliance, business_fundamentals
    sub_category = Column(String(255), nullable=True)
    score = Column(Float, nullable=False)  # 0-100
    max_score = Column(Float, default=100.0)
    assessment_type = Column(String(50), nullable=False)  # code, ai
    evidence = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    scored_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="readiness_scores")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    report_content = Column(Text, nullable=False)
    report_type = Column(String(100), default="full_assessment")
    summary = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="reports")
