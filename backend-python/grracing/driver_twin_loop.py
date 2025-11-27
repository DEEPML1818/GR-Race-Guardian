"""
Driver Twin Update Loop

Recalculates Driver Twin each lap and emits to Node.js backend.
"""

import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

from .driver_twin import DriverTwinGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DriverTwinUpdateLoop:
    """
    Manages real-time Driver Twin updates.
    
    Recalculates Driver Twin each lap and emits updates to Node.js backend.
    """
    
    def __init__(self, node_api_url: str = "http://localhost:3001"):
        self.generator = DriverTwinGenerator()
        self.node_api_url = node_api_url
        self.driver_history = {}  # Store lap history per driver
        self.last_twins = {}  # Cache last twin for comparison
        
    def update_driver_twin(
        self,
        driver_id: str,
        lap_time: float,
        sector_times: Dict[str, float],
        telemetry_data: Optional[Dict] = None,
        tire_compound: str = "MEDIUM",
        current_lap: int = 1
    ) -> Dict:
        """
        Update Driver Twin with new lap data.
        
        Args:
            driver_id: Driver identifier
            lap_time: New lap time
            sector_times: Sector times (S1, S2, S3)
            telemetry_data: Optional telemetry data
            tire_compound: Current tire compound
            current_lap: Current lap number
            
        Returns:
            Updated Driver Twin
        """
        # Initialize driver history if needed
        if driver_id not in self.driver_history:
            self.driver_history[driver_id] = {
                "lap_times": [],
                "sector_times": [],
                "telemetry_data": []
            }
        
        # Add new lap data
        self.driver_history[driver_id]["lap_times"].append(lap_time)
        self.driver_history[driver_id]["sector_times"].append(sector_times)
        if telemetry_data:
            self.driver_history[driver_id]["telemetry_data"].append(telemetry_data)
        
        # Keep only last 50 laps for performance
        max_history = 50
        if len(self.driver_history[driver_id]["lap_times"]) > max_history:
            self.driver_history[driver_id]["lap_times"] = \
                self.driver_history[driver_id]["lap_times"][-max_history:]
            self.driver_history[driver_id]["sector_times"] = \
                self.driver_history[driver_id]["sector_times"][-max_history:]
            if self.driver_history[driver_id]["telemetry_data"]:
                self.driver_history[driver_id]["telemetry_data"] = \
                    self.driver_history[driver_id]["telemetry_data"][-max_history:]
        
        # Generate updated Driver Twin
        twin = self.generator.generate_driver_twin(
            driver_id=driver_id,
            lap_times=self.driver_history[driver_id]["lap_times"],
            sector_times=self.driver_history[driver_id]["sector_times"],
            telemetry_data=self.driver_history[driver_id]["telemetry_data"] if \
                self.driver_history[driver_id]["telemetry_data"] else None,
            tire_compound=tire_compound,
            current_lap=current_lap
        )
        
        # Calculate changes from last twin
        changes = self._calculate_changes(driver_id, twin)
        twin["changes"] = changes
        
        # Store for next comparison
        self.last_twins[driver_id] = twin.copy()
        
        logger.info(f"Updated Driver Twin for {driver_id} at lap {current_lap}")
        
        return twin
    
    def _calculate_changes(self, driver_id: str, new_twin: Dict) -> Dict:
        """
        Calculate changes from previous twin.
        
        Returns delta values for key metrics.
        """
        if driver_id not in self.last_twins:
            return {
                "pace_vector_delta": 0.0,
                "consistency_delta": 0.0,
                "aggression_delta": 0.0,
                "is_new": True
            }
        
        old_twin = self.last_twins[driver_id]
        
        changes = {
            "pace_vector_delta": float(new_twin.get("pace_vector", 0.0) - 
                                      old_twin.get("pace_vector", 0.0)),
            "consistency_delta": float(new_twin.get("consistency_index", 0.0) - 
                                     old_twin.get("consistency_index", 0.0)),
            "aggression_delta": float(new_twin.get("aggression_score", 0.0) - 
                                    old_twin.get("aggression_score", 0.0)),
            "is_new": False
        }
        
        # Sector strength changes
        if "sector_strengths" in new_twin and "sector_strengths" in old_twin:
            sector_changes = {}
            for sector in ["S1", "S2", "S3"]:
                new_val = new_twin["sector_strengths"].get(sector, 1.0)
                old_val = old_twin["sector_strengths"].get(sector, 1.0)
                sector_changes[sector] = float(new_val - old_val)
            changes["sector_changes"] = sector_changes
        
        return changes
    
    async def emit_to_nodejs(self, driver_id: str, twin: Dict) -> bool:
        """
        Emit Driver Twin update to Node.js backend via HTTP.
        
        Returns True if successful, False otherwise.
        """
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.node_api_url}/api/driver-twin/update",
                    json={
                        "driver_id": driver_id,
                        "twin": twin,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    },
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Emitted Driver Twin for {driver_id} to Node.js")
                        return True
                    else:
                        logger.warning(f"Failed to emit Driver Twin: {response.status}")
                        return False
        except ImportError:
            logger.warning("aiohttp not available, cannot emit to Node.js")
            return False
        except Exception as e:
            logger.error(f"Error emitting Driver Twin: {e}")
            return False
    
    def get_driver_twin(self, driver_id: str) -> Optional[Dict]:
        """
        Get current Driver Twin for a driver.
        """
        return self.last_twins.get(driver_id)
    
    def get_all_twins(self) -> Dict[str, Dict]:
        """
        Get all current Driver Twins.
        """
        return self.last_twins.copy()
    
    def reset_driver(self, driver_id: str):
        """
        Reset driver history (e.g., for new race).
        """
        if driver_id in self.driver_history:
            del self.driver_history[driver_id]
        if driver_id in self.last_twins:
            del self.last_twins[driver_id]
        logger.info(f"Reset Driver Twin for {driver_id}")


# Global instance
_driver_twin_loop = None

def get_driver_twin_loop() -> DriverTwinUpdateLoop:
    """Get or create global Driver Twin update loop instance."""
    global _driver_twin_loop
    if _driver_twin_loop is None:
        _driver_twin_loop = DriverTwinUpdateLoop()
    return _driver_twin_loop


if __name__ == "__main__":
    # Test Driver Twin update loop
    loop = DriverTwinUpdateLoop()
    
    # Simulate lap updates
    for lap in range(1, 11):
        twin = loop.update_driver_twin(
            driver_id="driver_1",
            lap_time=95.0 + (lap * 0.1),  # Degrading pace
            sector_times={"S1": 31.5, "S2": 32.0, "S3": 31.7},
            tire_compound="MEDIUM",
            current_lap=lap
        )
        
        print(f"Lap {lap}: Pace Vector = {twin['pace_vector']:.4f}, "
              f"Consistency = {twin['consistency_index']:.3f}")
        if "changes" in twin and not twin["changes"]["is_new"]:
            print(f"  Changes: Pace Δ = {twin['changes']['pace_vector_delta']:.4f}")

