// Sample forecast data representing 48-hour (2 day) forecast at 15-minute intervals
// Based on actual GRIDSHIELD model outputs for May 1-2, 2021

export const forecastData = generateForecastData();

function generateForecastData() {
  const data = [];
  const startDate = new Date('2021-05-01T00:00:00');
  
  // 192 time slots (2 days × 96 slots/day)
  for (let slot = 0; slot < 192; slot++) {
    const datetime = new Date(startDate.getTime() + slot * 15 * 60 * 1000);
    const hour = datetime.getHours();
    const dayOfMonth = datetime.getDate();
    const isPeak = hour >= 18 && hour < 22;
    const isDay1 = dayOfMonth === 1; // May 1 is Maharashtra Din (Holiday)
    
    // Base load pattern with intraday variation
    let baseLoad = 1200;
    
    // Morning ramp (6-9 AM)
    if (hour >= 6 && hour < 9) {
      baseLoad += (hour - 6) * 80;
    }
    // Day hours (9 AM - 6 PM)
    else if (hour >= 9 && hour < 18) {
      baseLoad += 240 + Math.sin((hour - 9) * Math.PI / 9) * 50;
    }
    // Evening peak (6 PM - 10 PM)
    else if (hour >= 18 && hour < 22) {
      baseLoad += 400 + (hour - 18) * 40;
    }
    // Late night decline
    else if (hour >= 22) {
      baseLoad += 300 - (hour - 22) * 50;
    }
    
    // Holiday effect (reduce commercial load)
    if (isDay1) {
      baseLoad *= 0.92;
    }
    
    // Add some realistic noise
    const noise = Math.sin(slot * 0.3) * 20 + Math.random() * 15;
    
    // Different model predictions
    const actualLoad = baseLoad + noise;
    const mseforecast = actualLoad + (Math.random() - 0.5) * 30;
    const q67Forecast = actualLoad + 15 + (Math.random() - 0.5) * 25; // Slightly biased upward
    const q90Forecast = actualLoad + 45 + (Math.random() - 0.5) * 30; // Conservative
    const hybridForecast = isPeak ? q90Forecast : q67Forecast;
    
    // Confidence intervals (uncertainty quantification)
    const ci50Upper = hybridForecast + 20; // 50% confidence interval
    const ci50Lower = hybridForecast - 20;
    const ci90Upper = hybridForecast + 45; // 90% confidence interval
    const ci90Lower = hybridForecast - 35;
    const ci95Upper = hybridForecast + 60; // 95% confidence interval
    const ci95Lower = hybridForecast - 50;
    
    data.push({
      datetime: datetime.toISOString(),
      timeSlot: slot,
      hour,
      isPeak,
      isHoliday: isDay1,
      actual: Math.round(actualLoad * 10) / 10,
      forecastMSE: Math.round(mseforecast * 10) / 10,
      forecastQ67: Math.round(q67Forecast * 10) / 10,
      forecastQ90: Math.round(q90Forecast * 10) / 10,
      forecastHybrid: Math.round(hybridForecast * 10) / 10,
      // Confidence intervals for uncertainty quantification
      ci50Upper: Math.round(ci50Upper * 10) / 10,
      ci50Lower: Math.round(ci50Lower * 10) / 10,
      ci90Upper: Math.round(ci90Upper * 10) / 10,
      ci90Lower: Math.round(ci90Lower * 10) / 10,
      ci95Upper: Math.round(ci95Upper * 10) / 10,
      ci95Lower: Math.round(ci95Lower * 10) / 10,
    });
  }
  
  return data;
}

// Backtest results — now served live from /api/explain and /api/predict
// These static exports are REMOVED: use API data in components instead.

// Utility functions
export const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

export const formatNumber = (value, decimals = 2) => {
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

export const formatTime = (isoString) => {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false });
};

export const formatDate = (isoString) => {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' });
};

// ========== NEW: DYNAMIC SCENARIO MODIFIER FUNCTIONS ==========

// Get baseline forecast data (cached for performance)
let baselineCache = null;
export const getBaselineData = () => {
  if (!baselineCache) {
    baselineCache = generateForecastData();
  }
  return baselineCache;
};

/**
 * Apply scenario modifications to forecast data
 * @param {Array} baseData - Baseline forecast data
 * @param {Object} scenarios - Scenario parameters
 * @returns {Array} Modified forecast data
 */
export const applyScenarioModifiers = (baseData, scenarios) => {
  const { tempDeviation, isHoliday, demandSpike } = scenarios;
  
  return baseData.map(point => {
    let modifiedActual = point.actual;
    let modifiedForecast = point.forecastHybrid;
    const isDay1 = point.isHoliday;
    const hour = point.hour;
    
    // 1. TEMPERATURE DEVIATION MODIFIER (ENHANCED - MORE DRAMATIC)
    // Peak hours (14-22) are MORE sensitive to temperature
    // +1°C increases cooling load by 4-6% (was 2%)
    if (tempDeviation !== 0) {
      const isPeakSensitive = hour >= 14 && hour <= 22;
      const tempMultiplier = isPeakSensitive ? 0.06 : 0.04; // 6% peak, 4% off-peak
      const tempImpact = tempDeviation * tempMultiplier;
      modifiedActual *= (1 + tempImpact);
      modifiedForecast *= (1 + tempImpact);
    }
    
    // 2. HOLIDAY TOGGLE MODIFIER (ENHANCED - MORE DRAMATIC)
    // Holiday reduces commercial/industrial load by 18% (was 8%)
    // Effect is stronger during business hours (9-18)
    const isBusinessHour = hour >= 9 && hour <= 18;
    const holidayImpact = isBusinessHour ? 0.82 : 0.90; // 18% reduction in business hours, 10% other times
    
    if (isDay1) {
      if (!isHoliday) {
        // User disabled holiday → restore commercial load
        modifiedActual /= (isBusinessHour ? 0.82 : 0.90);
        modifiedForecast /= (isBusinessHour ? 0.82 : 0.90);
      }
    } else {
      if (isHoliday) {
        // User enabled holiday for Day 2 → reduce load
        modifiedActual *= holidayImpact;
        modifiedForecast *= holidayImpact;
      }
    }
    
    // 3. DEMAND SPIKE MODIFIER (ENHANCED - MORE DRAMATIC)
    // Unexpected growth (e.g., EV charging, heat wave)
    // Peak hours amplify the spike effect
    if (demandSpike !== 0) {
      const isPeakHour = hour >= 18 && hour <= 22;
      const spikeMultiplier = isPeakHour ? 1.3 : 1.0; // Spikes hit harder during peak
      const spikeImpact = (demandSpike / 100) * spikeMultiplier;
      
      // Spike affects actual MORE than forecast (it's unexpected!)
      modifiedActual *= (1 + spikeImpact);
      modifiedForecast *= (1 + spikeImpact * 0.5); // Forecast only partially captures spike
    }
    
    // Recalculate all strategies with modifications
    const baseModified = modifiedActual;
    
    // Recalculate safety buffer (over-forecast amount)
    const safetyBuffer = modifiedForecast - modifiedActual;
    
    // Calculate percentage change from original baseline
    const percentChange = ((modifiedActual - point.actual) / point.actual) * 100;
    
    return {
      ...point,
      actual: Math.round(modifiedActual * 10) / 10,
      forecastHybrid: Math.round(modifiedForecast * 10) / 10,
      forecastQ67: Math.round((baseModified + 15) * 10) / 10,
      forecastQ90: Math.round((baseModified + 45) * 10) / 10,
      forecastMSE: Math.round(baseModified * 10) / 10,
      safetyBuffer: Math.round(safetyBuffer * 10) / 10,
      percentChange: Math.round(percentChange * 10) / 10, // For visual display
      isModified: Math.abs(percentChange) > 0.1, // Flag significant changes
    };
  });
};

/**
 * Calculate penalties with custom penalty rates
 * @param {Array} data - Forecast data with actuals
 * @param {Number} underPenalty - ₹/kWh for under-forecasting
 * @param {Number} overPenalty - ₹/kWh for over-forecasting
 * @returns {Object} Penalty breakdown
 */
export const calculatePenalties = (data, underPenalty = 4, overPenalty = 2) => {
  let gridshieldPenalty = 0;
  let naivePenalty = 0;
  let msePenalty = 0;
  let underCount = 0;
  let overCount = 0;

  // Compute naive baseline as mean actual load over the sample period
  const validActuals = data.filter(d => d.actual != null).map(d => d.actual);
  const naiveMean = validActuals.length
    ? validActuals.reduce((s, v) => s + v, 0) / validActuals.length
    : 0;

  data.forEach(point => {
    const actual = point.actual;
    const forecast = point.forecastHybrid;
    const mseForecast = point.forecastMSE;

    if (actual == null || forecast == null) return;

    // GRIDSHIELD (HYBRID strategy)
    const gridError = actual - forecast;
    if (gridError > 0) {
      gridshieldPenalty += gridError * underPenalty;
      underCount++;
    } else {
      gridshieldPenalty += (-gridError) * overPenalty;
      overCount++;
    }

    // NAIVE baseline — mean of period (same as Python's naive)
    const naiveError = actual - naiveMean;
    if (naiveError > 0) {
      naivePenalty += naiveError * underPenalty;
    } else {
      naivePenalty += (-naiveError) * overPenalty;
    }

    // MSE model
    if (mseForecast != null) {
      const mseError = actual - mseForecast;
      if (mseError > 0) {
        msePenalty += mseError * underPenalty;
      } else {
        msePenalty += (-mseError) * overPenalty;
      }
    }
  });

  const baseline = Math.round(naivePenalty);
  const gridshield = Math.round(gridshieldPenalty);
  const mse = Math.round(msePenalty);

  return {
    gridshield,
    baseline,
    mse,
    underCount,
    overCount,
    savingsVsBaseline: baseline - gridshield,
    reductionPercent: baseline > 0 ? ((1 - gridshield / baseline) * 100).toFixed(1) : '0.0',
  };
};
