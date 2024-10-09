from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey
from .base import Base

class IndexedDocument(Base):
    __tablename__ = "indexed_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    index_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    indexing_method: Mapped[str] = mapped_column(String(50), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="indexed_documents")

    def __repr__(self):
        return f"<IndexedDocument(id={self.id}, user_id={self.user_id}, document_name={self.document_name}, index_id={self.index_id}, indexing_method={self.indexing_method})>"