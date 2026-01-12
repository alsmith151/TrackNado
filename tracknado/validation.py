from __future__ import annotations
import os
from pathlib import Path
import subprocess
import shutil
from typing import Optional
from loguru import logger

def validate_hub(hub_path: Path, strict: bool = False) -> tuple[bool, str]:
    """Validate a hub using UCSC's hubCheck tool.
    
    Args:
        hub_path: Path to hub.txt file
        strict: If True, fail on warnings too
    
    Returns:
        (is_valid, message) tuple
    """
    hub_path = Path(hub_path)
    if not hub_path.exists():
        return False, f"Hub file not found: {hub_path}"

    hubcheck = shutil.which("hubCheck")
    if not hubcheck:
        # Check standard user local bin too
        user_bin = Path.home() / "bin" / "hubCheck"
        if user_bin.exists():
            hubcheck = str(user_bin)
    
    if not hubcheck:
        return False, ("hubCheck not found in PATH or ~/bin/hubCheck. "
                      "Install from: http://hgdownload.cse.ucsc.edu/admin/exe/")
    
    cmd = [hubcheck]
    if strict:
        cmd.append("-strict")
    cmd.append(str(hub_path))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        is_valid = result.returncode == 0
        message = result.stderr or result.stdout
        if not message and is_valid:
            message = "Hub is valid."
        return is_valid, message
    except Exception as e:
        return False, f"Error running hubCheck: {e}"

class HubValidator:
    """Validates hub structure without external tools."""
    
    def __init__(self, hub_dir: str | Path):
        self.hub_dir = Path(hub_dir)
        self.errors = []
        self.warnings = []

    def validate_all(self) -> bool:
        """Run all validations."""
        self.validate_structure()
        self.validate_track_files_exist()
        return len(self.errors) == 0

    def validate_structure(self) -> list[str]:
        """Check hub has required files."""
        hub_txt = self.hub_dir / f"{self.hub_dir.name}.hub.txt"
        # Since hub names can vary, we look for *.hub.txt
        hub_files = list(self.hub_dir.glob("*.hub.txt"))
        if not hub_files:
            self.errors.append("No hub.txt file found in directory.")
        
        # Check for genomes.txt referenced in hub.txt would be better, 
        # but for now we look for common file names or hub-specific ones
        genomes_files = (list(self.hub_dir.glob("**/genomes.txt")) + 
                         list(self.hub_dir.glob("**/*.genomes.txt")))
        if not genomes_files:
            self.errors.append("No genomes.txt file found.")
            
        trackdb_files = list(self.hub_dir.glob("**/trackDb.txt"))
        if not trackdb_files:
            self.errors.append("No trackDb.txt file found.")
            
        return self.errors

    def validate_track_files_exist(self) -> list[str]:
        """Ensure all referenced track files exist locally.
        
        Note: This only works if tracks are local paths, which is true during staging.
        """
        for trackdb in self.hub_dir.glob("**/trackDb.txt"):
            with open(trackdb, 'r') as f:
                content = f.read()
                # Simple regex to find 'bigDataUrl' entries
                import re
                urls = re.findall(r"bigDataUrl\s+(.+)", content)
                for url in urls:
                    # Resolve relative to trackdb or hub_dir
                    # Hubs usually use relative paths from trackdb
                    track_path = trackdb.parent / url
                    if not track_path.exists():
                        self.warnings.append(f"Track file not found: {url} (referenced in {trackdb.name})")
        return self.warnings
