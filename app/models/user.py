from sqlalchemy import Column, String, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Role and status
    role = Column(SQLEnum(UserRole), default=UserRole.USER, index=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(String, nullable=False)  # ISO format
    updated_at = Column(String, nullable=True)
    last_login = Column(String, nullable=True)
    
    # Relationships
    configurations = relationship("Configuration", back_populates="user", cascade="all, delete-orphan")

