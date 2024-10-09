from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean
from .base import Base

class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    email_verified: Mapped[bool] = mapped_column(default=False)


    indexed_documents: Mapped[list["IndexedDocument"]] = relationship("IndexedDocument", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User={self.email}>"