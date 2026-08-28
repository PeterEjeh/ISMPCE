"""SQLAlchemy ORM model for emission data."""

from sqlalchemy import Column, Float, Integer, String

from ..database import Base


class Emission(Base):
    __tablename__ = "emissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    year = Column(Integer, nullable=False, index=True)
    country = Column(String, nullable=False, default="Nigeria", index=True)
    state = Column(String, nullable=True, index=True)
    sector = Column(String, nullable=True, index=True)
    co2_value = Column(Float, nullable=False)
    co2_per_capita = Column(Float, nullable=True)
    gdp = Column(Float, nullable=True)
    population = Column(Float, nullable=True)
    primary_energy_consumption = Column(Float, nullable=True)
    coal_co2 = Column(Float, nullable=True)
    oil_co2 = Column(Float, nullable=True)
    gas_co2 = Column(Float, nullable=True)
    flaring_co2 = Column(Float, nullable=True)
    cement_co2 = Column(Float, nullable=True)
    energy_co2 = Column(Float, nullable=True)
    oil_transport_co2 = Column(Float, nullable=True)
    industrial_co2 = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Emission(year={self.year}, country={self.country}, co2={self.co2_value})>"
