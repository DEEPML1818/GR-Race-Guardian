/**
 * Data Validity Checker for Node.js
 * 
 * Validates input data for all API endpoints.
 */

class DataValidator {
  constructor() {
    this.errors = [];
    this.warnings = [];
  }

  /**
   * Validate Driver Twin request
   */
  validateDriverTwinRequest(data) {
    this.errors = [];
    this.warnings = [];

    if (!data.driver_id) {
      this.errors.push('driver_id is required');
    }

    if (!data.lap_times || !Array.isArray(data.lap_times)) {
      this.errors.push('lap_times must be a non-empty array');
    } else if (data.lap_times.length === 0) {
      this.errors.push('lap_times cannot be empty');
    } else {
      data.lap_times.forEach((lapTime, i) => {
        const num = parseFloat(lapTime);
        if (isNaN(num) || num <= 0) {
          this.errors.push(`lap_times[${i}] must be a positive number`);
        }
        if (num > 300) {
          this.errors.push(`lap_times[${i}] is unreasonably high: ${num}s`);
        }
      });
    }

    if (data.lap_times && data.lap_times.length < 3) {
      this.warnings.push('Less than 3 lap times provided - analysis may be less accurate');
    }

    return {
      isValid: this.errors.length === 0,
      errors: this.errors,
      warnings: this.warnings
    };
  }

  /**
   * Validate Race Twin request
   */
  validateRaceTwinRequest(data) {
    this.errors = [];
    this.warnings = [];

    if (!data.race_id) {
      this.errors.push('race_id is required');
    }

    if (!data.drivers || !Array.isArray(data.drivers)) {
      this.errors.push('drivers must be a non-empty array');
    } else if (data.drivers.length === 0) {
      this.errors.push('drivers cannot be empty');
    } else {
      data.drivers.forEach((driver, i) => {
        if (!driver.id) {
          this.errors.push(`drivers[${i}].id is required`);
        }
        if (driver.position !== undefined) {
          const pos = parseInt(driver.position);
          if (isNaN(pos) || pos < 1) {
            this.errors.push(`drivers[${i}].position must be >= 1`);
          }
        }
      });
    }

    if (!data.total_laps) {
      this.errors.push('total_laps is required');
    } else {
      const totalLaps = parseInt(data.total_laps);
      if (isNaN(totalLaps) || totalLaps < 1) {
        this.errors.push('total_laps must be >= 1');
      }
      if (totalLaps > 200) {
        this.errors.push('total_laps is unreasonably high');
      }
    }

    if (data.drivers && data.drivers.length < 2) {
      this.warnings.push('Less than 2 drivers provided - race simulation may be less meaningful');
    }

    return {
      isValid: this.errors.length === 0,
      errors: this.errors,
      warnings: this.warnings
    };
  }

  /**
   * Validate Pit Decision request
   */
  validatePitDecisionRequest(data) {
    this.errors = [];
    this.warnings = [];

    const requiredFields = ['race_id', 'driver_id', 'current_lap', 'tire_age', 'tire_compound', 'position'];
    requiredFields.forEach(field => {
      if (data[field] === undefined || data[field] === null) {
        this.errors.push(`${field} is required`);
      }
    });

    if (data.tire_age !== undefined) {
      const tireAge = parseInt(data.tire_age);
      if (isNaN(tireAge) || tireAge < 0) {
        this.errors.push('tire_age must be a non-negative integer');
      }
      if (tireAge > 100) {
        this.errors.push('tire_age is unreasonably high');
      }
    }

    if (data.position !== undefined) {
      const position = parseInt(data.position);
      if (isNaN(position) || position < 1) {
        this.errors.push('position must be >= 1');
      }
    }

    const validCompounds = ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET'];
    if (data.tire_compound && !validCompounds.includes(data.tire_compound)) {
      this.errors.push(`tire_compound must be one of: ${validCompounds.join(', ')}`);
    }

    if (data.degradation_rate !== undefined) {
      const rate = parseFloat(data.degradation_rate);
      if (isNaN(rate) || rate < 0 || rate > 0.1) {
        this.errors.push('degradation_rate must be between 0 and 0.1');
      }
    }

    if (data.traffic_density !== undefined) {
      const density = parseFloat(data.traffic_density);
      if (isNaN(density) || density < 0 || density > 1) {
        this.errors.push('traffic_density must be between 0 and 1');
      }
    }

    return {
      isValid: this.errors.length === 0,
      errors: this.errors,
      warnings: this.warnings
    };
  }

  /**
   * Validate lap data array
   */
  validateLapData(lapData) {
    this.errors = [];
    this.warnings = [];

    if (!lapData || !Array.isArray(lapData)) {
      this.errors.push('lap_data must be a non-empty array');
      return {
        isValid: false,
        errors: this.errors,
        warnings: this.warnings
      };
    }

    lapData.forEach((lap, i) => {
      if (typeof lap !== 'object' || Array.isArray(lap)) {
        this.errors.push(`lap_data[${i}] must be an object`);
        return;
      }

      if (lap.lap_time !== undefined) {
        const lapTime = parseFloat(lap.lap_time);
        if (isNaN(lapTime) || lapTime <= 0) {
          this.errors.push(`lap_data[${i}].lap_time must be a positive number`);
        }
      }

      if (lap.lap !== undefined) {
        const lapNum = parseInt(lap.lap);
        if (isNaN(lapNum) || lapNum < 1) {
          this.errors.push(`lap_data[${i}].lap must be >= 1`);
        }
      }
    });

    return {
      isValid: this.errors.length === 0,
      errors: this.errors,
      warnings: this.warnings
    };
  }

  /**
   * Check data quality
   */
  checkDataQuality(data, dataType) {
    const report = {
      qualityScore: 1.0,
      warnings: [],
      suggestions: []
    };

    if (dataType === 'driver_twin') {
      const lapTimes = data.lap_times || [];
      if (lapTimes.length < 5) {
        report.qualityScore -= 0.2;
        report.warnings.push('Less than 5 lap times - reduced accuracy');
        report.suggestions.push('Provide more lap times for better analysis');
      }

      if (!data.sector_times) {
        report.qualityScore -= 0.1;
        report.warnings.push('No sector times provided');
        report.suggestions.push('Include sector times for detailed analysis');
      }
    } else if (dataType === 'race_twin') {
      const drivers = data.drivers || [];
      if (drivers.length < 3) {
        report.qualityScore -= 0.2;
        report.warnings.push('Less than 3 drivers - limited race simulation');
        report.suggestions.push('Include more drivers for realistic simulation');
      }
    }

    report.qualityScore = Math.max(0.0, report.qualityScore);

    return report;
  }
}

module.exports = new DataValidator();

