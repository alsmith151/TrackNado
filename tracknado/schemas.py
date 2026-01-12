import pandera.pandas as pa
from pandera.typing import Series
from typing import Optional

class TrackDataFrameSchema(pa.DataFrameModel):
    """Schema for track DataFrames."""
    fn: Series[str] = pa.Field(description="File path")
    path: Optional[Series[str]] = pa.Field(nullable=True)
    name: Optional[Series[str]] = pa.Field(nullable=True)
    ext: Series[str] = pa.Field(isin=["bigWig", "bigBed", "bw", "bb", "bw", "bb", "bigwig", "bigbed", "bed"])
    
    class Config:
        coerce = True
        strict = False  # Allow extra columns (metadata)

class TrackDesignSchema(pa.DataFrameModel):
    """Schema for processed track design with groupings."""
    fn: Series[str]
    path: Series[str]
    name: Series[str]
    ext: Series[str]
    color: Optional[Series[object]] = pa.Field(nullable=True)
    supertrack: Optional[Series[str]] = pa.Field(nullable=True)
    composite: Optional[Series[str]] = pa.Field(nullable=True)
    overlay: Optional[Series[str]] = pa.Field(nullable=True)
    
    class Config:
        coerce = True
        strict = False
