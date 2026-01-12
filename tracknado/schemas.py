from __future__ import annotations
import pandera.pandas as pa
from pandera.typing import Series

class TrackDataFrameSchema(pa.DataFrameModel):
    """Schema for track DataFrames."""
    fn: Series[str] = pa.Field(description="File path")
    path: Series[str] | None = pa.Field(nullable=True)
    name: Series[str] | None = pa.Field(nullable=True)
    ext: Series[str] = pa.Field(isin=["bigWig", "bigBed", "bw", "bb", "bigwig", "bigbed", "bed", "gtf", "gff", "bigGenePred"])
    
    class Config:
        coerce = True
        strict = False  # Allow extra columns (metadata)

class TrackDesignSchema(pa.DataFrameModel):
    """Schema for processed track design with groupings."""
    fn: Series[str]
    path: Series[str]
    name: Series[str]
    ext: Series[str]
    color: Series[object] | None = pa.Field(nullable=True)
    supertrack: Series[str] | None = pa.Field(nullable=True)
    composite: Series[str] | None = pa.Field(nullable=True)
    overlay: Series[str] | None = pa.Field(nullable=True)
    
    class Config:
        coerce = True
        strict = False
