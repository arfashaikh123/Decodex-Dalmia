# How to Launch the VoltRide Interactive Dashboard

We have built a custom **Operational Command Center** using Streamlit, which serves as a powerful alternative to PowerBI. It includes interactive filtering, real-time KPI generation, and simulation capabilities.

## Quick Start
1.  **Open your Terminal** (Command Prompt or PowerShell).
2.  **Navigate to the project folder:**
    ```powershell
    cd "d:/ARFA PROJECTS/Decodex Dalmia"
    ```
3.  **Run the Dashboard Command:**
    ```powershell
    streamlit run dashboard.py
    ```
4.  **View in Browser:**
    The dashboard will automatically open in your default web browser (usually at `http://localhost:8501`).

## Dashboard Features
*   **Operational Filters (Sidebar):** Filter the entire dashboard by City to isolate regional performance.
*   **KPI Cards:** Real-time metrics for Requests, Completion Rate, Surge, and Revenue Loss.
*   **Stress Map (Tab 1):** Interactive scatter plot—hover over bubbles to see Zone-level details.
*   **Simulation Lab (Tab 3):** Use the slider to simulate "Peak-Shifting" scenarios and see the projected impact on Revenue and Completion Rate instantly.
