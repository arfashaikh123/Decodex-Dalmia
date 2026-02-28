# 🔌 GRIDSHIELD Analytics Dashboard

> **High-end, dark-themed Power Distribution Analytics Dashboard for Mumbai Load Forecasting**  
> Built with React, Tailwind CSS, Recharts, and Lucide React

![GRIDSHIELD Dashboard](https://img.shields.io/badge/Status-Production%20Ready-success)
![React](https://img.shields.io/badge/React-18.2-blue)
![Tailwind](https://img.shields.io/badge/Tailwind-3.4-38bdf8)

---

## 🎯 Mission

Present a **49.4% penalty reduction** in electrical load forecasting for Mumbai's power distribution grid. This dashboard visualizes how **cost-aware forecasting** (minimizing financial penalties) beats traditional error minimization (RMSE/MAE).

### Key Differentiator
Standard ML models optimize **accuracy**. GRIDSHIELD optimizes **cost**.

Under ABT regulations:
- Under-forecast penalty: **₹4/kWh** (expensive!)
- Over-forecast penalty: **₹2/kWh** (cheaper)
- Optimal quantile: **0.667** = 4/(4+2)

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18.x or higher
- **npm** 9.x or higher

### Installation

```bash
# Navigate to dashboard directory
cd "C:\Users\mansu\Downloads\02 – Case GRIDSHIELD\gridshield-dashboard"

# Install dependencies
npm install

# Start development server
npm run dev
```

The dashboard will open at **http://localhost:3000**

### Build for Production

```bash
# Create optimized build
npm run build

# Preview production build
npm run preview
```

---

## 📊 Dashboard Features

### 1. **KPI Ribbon** (Top Panel)
- **Penalty Risk Reduction**: 49.4% savings highlight
- **Peak Window Status**: Live countdown to 18:00-22:00 peak hours
- **Current Load vs Forecast**: Real-time delta tracking
- **Weather Impact**: Heat Index indicator for AC load

### 2. **Live Forecast Chart** (Main Stage)
- 48-hour forecast visualization (192 time slots @ 15-min resolution)
- Peak hour shading (18:00-22:00 in red)
- Holiday overlay (Maharashtra Din on May 1)
- Strategy comparison: MSE vs Q67 vs Q90 vs HYBRID

### 3. **Financial Asymmetry Sidebar**
- **Penalty comparison bar chart**: All 5 strategies
- **Money saved counter**: ₹222K vs naive baseline
- **Annual projection**: ₹800K+ savings
- **Strategy breakdown**: Detailed metrics for Q0.67

### 4. **Feature Influence Heatmap**
- Top 15 model drivers visualized
- Category color-coding:
  - 🔵 Lag Features (load_lag_7d, load_lag_14d)
  - 🟠 Temporal (day_of_week, month)
  - 🟡 Weather (ACT_HEAT_INDEX, COOL_FACTOR)
  - 🟢 Events (covid_regime, holiday)

### 5. **Interactive Controls**
- **Strategy selector**: Switch between MSE/Q67/Q90/HYBRID
- **Holiday toggle**: Maharashtra Din (May 1) effect
- **Quantile slider**: Interactive α exploration (0.50-0.95)
- **COVID regime indicator**: Pre/post structural shift
- **Export button**: Generate SLDC submission CSV

### 6. **Peak Hour Drill-down**
Click on 18:00-22:00 window to see:
- Specific kW predictions for each hour
- Risk level classification (Medium/High/Critical)
- Conservative Q90 strategy applied

---

## 🎨 Design System

### Color Palette: "Grid-Dark"
```css
--grid-dark-950: #0a0a0f    /* Background */
--grid-dark-900: #121218    /* Elevated surfaces */
--grid-dark-800: #1a1a24    /* Cards */
--grid-dark-700: #232330    /* Borders */

--electric-blue: #00d4ff    /* Primary accent */
--safety-orange: #ff6b35    /* Warnings */
--peak-red: #ff3366         /* High risk */
--success-green: #00ff88    /* Positive metrics */
```

### Typography
- **Headings**: Inter (Google Fonts)
- **Data/Metrics**: JetBrains Mono (monospace)
- **Body**: Inter

### Icons
- Lucide React (consistent, modern, tree-shakeable)

---

## 📁 Project Structure

```
gridshield-dashboard/
├── src/
│   ├── components/
│   │   ├── KPICard.jsx              # Reusable metric card
│   │   ├── KPIRibbon.jsx            # Top 4 KPIs
│   │   ├── ForecastChart.jsx        # Main area chart (Recharts)
│   │   ├── FinancialSidebar.jsx     # Penalty comparison
│   │   ├── FeatureImportance.jsx    # Horizontal bar chart
│   │   └── InteractiveControls.jsx  # Strategy/Holiday toggles
│   ├── data/
│   │   └── sampleData.js            # 192 forecast points + metrics
│   ├── App.jsx                      # Main dashboard layout
│   ├── main.jsx                     # React entry point
│   └── index.css                    # Tailwind + custom styles
├── index.html
├── package.json
├── tailwind.config.js               # Custom Grid-Dark theme
├── vite.config.js
└── README.md
```

---

## 🧠 Data Model

### Forecast Data (192 rows)
```javascript
{
  datetime: "2021-05-01T00:00:00",
  timeSlot: 0,
  hour: 0,
  isPeak: false,
  isHoliday: true,
  actual: 1234.5,
  forecastMSE: 1245.2,
  forecastQ67: 1258.3,
  forecastQ90: 1289.7,
  forecastHybrid: 1258.3
}
```

### Backtest Metrics
```javascript
{
  naive: { totalPenalty: 449383, mae: 60.31, ... },
  mse: { totalPenalty: 252565, mae: 37.24, ... },
  q67: { totalPenalty: 227257, mae: 37.90, ... },  // WINNER
  q90: { totalPenalty: 281755, mae: 62.46, ... },
  hybrid: { totalPenalty: 229037, mae: 40.47, ... }
}
```

### Feature Importance (Top 5)
1. **load_lag_7d**: 613.2 (Same time last week)
2. **load_lag_14d**: 487.6 (2 weeks ago)
3. **day_of_week**: 312.4 (Mon-Sun pattern)
4. **ACT_HEAT_INDEX**: 298.7 (Cooling demand)
5. **time_slot**: 276.3 (Intraday pattern)

---

## 🎤 Presentation Tips

### For Stage 1 Demo

1. **Open with the KPI ribbon**:
   > "Our model achieves a 49.4% penalty reduction, saving ₹222K in just 3 months."

2. **Show the Forecast Chart**:
   > "Notice the peak hour shading (6-10 PM) where we use conservative Q90 strategy."

3. **Explain Financial Asymmetry**:
   > "Under-forecasting costs 2x more (₹4 vs ₹2), so we deliberately bias upward."

4. **Feature Importance**:
   > "Weekly patterns (load_lag_7d) are the strongest predictor. Heat Index drives AC load."

5. **Interactive Controls**:
   > "The quantile slider shows: At α=0.67, we balance under-forecast risk with over-forecast cost."

6. **COVID Regime**:
   > "March 2020 lockdown created a permanent -8.2% load shift. Our model captures this."

### Key Talking Points
- ✅ **Cost-aware** beats accuracy-focused
- ✅ **49.4% penalty reduction** (₹222K → ₹888K annually)
- ✅ **COVID regime switching** (most teams will miss this)
- ✅ **HYBRID strategy**: Q67 off-peak + Q90 during peaks
- ✅ **Quantile 0.667**: Mathematically optimal for ₹4:₹2 ratio

---

## 🔧 Customization

### Change Forecast Data
Edit `src/data/sampleData.js`:
```javascript
// Replace with your actual model outputs
export const forecastData = yourActualData.map(row => ({
  datetime: row.DATETIME,
  forecastHybrid: row.Forecast_HYBRID,
  // ... etc
}));
```

### Adjust Color Theme
Edit `tailwind.config.js`:
```javascript
colors: {
  'grid-dark': { ... },
  'electric-blue': { 500: '#YOUR_COLOR' },
  // ... etc
}
```

### Add New Components
1. Create `src/components/YourComponent.jsx`
2. Import in `src/App.jsx`
3. Add to tab structure or sidebar

---

## 📦 Dependencies

### Core
- **React** 18.2 - UI framework
- **Recharts** 2.10 - Business charts
- **Tailwind CSS** 3.4 - Utility-first styling
- **Lucide React** 0.298 - Icon library

### Dev Tools
- **Vite** 5.0 - Fast build tool
- **PostCSS** 8.4 - CSS processor
- **Autoprefixer** 10.4 - Browser compatibility

### Utilities
- **date-fns** 3.0 - Date formatting
- **clsx** 2.1 - Class name utilities

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 3000
npx kill-port 3000

# Or change port in vite.config.js
server: { port: 3001 }
```

### Charts Not Rendering
- Ensure `ResponsiveContainer` has explicit height
- Check browser console for Recharts errors
- Verify data structure matches expected format

### Tailwind Classes Not Working
```bash
# Rebuild CSS
npm run dev
```

### Google Fonts Not Loading
- Check internet connection
- Fonts are referenced in `index.html` `<head>`

---

## 🚀 Deployment

### Vercel (Recommended)
```bash
npm run build
vercel --prod
```

### Netlify
```bash
npm run build
# Drag-drop 'dist' folder to Netlify
```

### GitHub Pages
```bash
npm run build
# Deploy 'dist' folder
```

---

## 📄 License

MIT License - Free for hackathon and educational use.

---

## 🏆 Credits

**Built for**: Decode X-2026 | Case 2: GRIDSHIELD  
**Team**: [Your Team Name]  
**Tech Stack**: React + Tailwind + Recharts + Lucide  
**Data Source**: Mumbai Load Data (2013-2021, 283K observations)

---

## 📞 Support

For questions during the hackathon:
- Check `USER_GUIDE.md` for model + GUI documentation
- Review `gridshield_model.py` for data pipeline
- Inspect browser console for React errors

---

**Ready to impress the judges? Launch the dashboard and show them the 49.4% penalty reduction! 🎯⚡**
