import customtkinter as ctk
import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from forecast_logic import LoadForecaster

# Appearance and Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PredictGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("⚡ Dalmia Load Forecast v2")
        self.geometry("1000x800")

        # Initialize Forecaster
        try:
            self.forecaster = LoadForecaster(model_dir=os.getcwd())
        except Exception as e:
            self.show_error(f"Initialization Error: {e}")
            return

        # UI Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_frame()

    def setup_sidebar(self):
        self.sidebar = ctk.CTkScrollableFrame(self, width=320, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.sidebar, text="Forecast Parameters", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        # Datetime
        self.create_input_field("Timestamp (YYYY-MM-DD HH:MM):", "entry_datetime", datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Weather Inputs (Numerical)
        self.create_input_field("Temperature (°C):", "entry_temp", "30.0")
        self.create_input_field("Humidity (%):", "entry_hum", "71.0")
        self.create_input_field("Heat Index:", "entry_heat", "32.0")
        self.create_input_field("Cool Factor:", "entry_cool", "0.0")
        self.create_input_field("Rainfall Index:", "entry_rain", "0.0")

        # Event
        ctk.CTkLabel(self.sidebar, text="Event Name:").pack(padx=20, anchor="w")
        events = sorted(list(self.forecaster.le_event.classes_))
        self.event_dropdown = ctk.CTkOptionMenu(self.sidebar, values=events)
        if "Normal Day" in events:
            self.event_dropdown.set("Normal Day")
        self.event_dropdown.pack(padx=20, pady=(0, 10), fill="x")

        # Holiday Switch
        self.holiday_switch = ctk.CTkSwitch(self.sidebar, text="Holiday Indicator")
        self.holiday_switch.pack(padx=20, pady=10)

        # Predict Button
        self.predict_btn = ctk.CTkButton(self.sidebar, text="⚡ Get Prediction & Analysis", command=self.run_prediction, 
                                        fg_color="#1f538d", hover_color="#14375e", font=ctk.CTkFont(size=14, weight="bold"))
        self.predict_btn.pack(padx=20, pady=30, fill="x")

    def create_input_field(self, label, attr_name, default_val):
        ctk.CTkLabel(self.sidebar, text=label).pack(padx=20, anchor="w")
        entry = ctk.CTkEntry(self.sidebar)
        entry.insert(0, default_val)
        entry.pack(padx=20, pady=(0, 10), fill="x")
        setattr(self, attr_name, entry)

    def setup_main_frame(self):
        self.main = ctk.CTkFrame(self)
        self.main.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self.main, text="Forecast Insight", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)

        # Top Results (Cards)
        self.cards_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=20)
        self.cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.p10_card = self.create_result_card(self.cards_frame, "P10 (Lower)", "---", "#3a7ebf", 0)
        self.p50_card = self.create_result_card(self.cards_frame, "P50 (Median)", "---", "#2fa572", 1)
        self.p90_card = self.create_result_card(self.cards_frame, "P90 (Upper)", "---", "#df5234", 2)

        # Chart Container
        self.chart_frame = ctk.CTkFrame(self.main, border_width=1)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.chart_label = ctk.CTkLabel(self.chart_frame, text="Prediction range chart will appear here...")
        self.chart_label.pack(expand=True)

        # Recommended Bar
        self.rec_frame = ctk.CTkFrame(self.main, border_width=2, border_color="#ff9800")
        self.rec_frame.pack(pady=(0, 20), padx=50, fill="x")
        ctk.CTkLabel(self.rec_frame, text="Recommended Load Submission (MW)", font=ctk.CTkFont(size=14)).pack(pady=(10, 0))
        self.rec_label = ctk.CTkLabel(self.rec_frame, text="---", font=ctk.CTkFont(size=28, weight="bold"), text_color="#ff9800")
        self.rec_label.pack(pady=(0, 10))

    def create_result_card(self, parent, title, value, color, col, unit="MW"):
        card = ctk.CTkFrame(parent, border_width=1, border_color=color)
        card.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11)).pack(pady=(10, 2))
        lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=20, weight="bold"), text_color=color)
        lbl.pack(pady=(0, 1))
        ctk.CTkLabel(card, text=unit, font=ctk.CTkFont(size=10)).pack(pady=(0, 10))
        return lbl

    def run_prediction(self):
        try:
            # Gather inputs
            dt_str = self.entry_datetime.get()
            temp = float(self.entry_temp.get())
            hum = float(self.entry_hum.get())
            heat = float(self.entry_heat.get())
            cool = float(self.entry_cool.get())
            rain = float(self.entry_rain.get())
            event = self.event_dropdown.get()
            holiday = 1 if self.holiday_switch.get() else 0
            
            # Prediction
            res = self.forecaster.predict_single(dt_str, temp, hum, rain, heat, cool, event, holiday)
            
            # Update Cards
            self.p10_card.configure(text=f"{res['P10']:.2f}")
            self.p50_card.configure(text=f"{res['P50']:.2f}")
            self.p90_card.configure(text=f"{res['P90']:.2f}")
            
            rec = res['P90'] * 0.95
            self.rec_label.configure(text=f"{rec:.2f} MW")

            # Plotting
            self.update_plot(res['P10'], res['P50'], res['P90'])

        except Exception as e:
            self.show_error(f"Analysis Failed: {e}")

    def update_plot(self, p10, p50, p90):
        # Clear frame
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')

        labels = ['Quantile Forecast']
        ax.bar(labels, [p90], color='#df5234', alpha=0.3, label='P90 (Upper)')
        ax.bar(labels, [p50], color='#2fa572', alpha=0.6, label='P50 (Median)')
        ax.bar(labels, [p10], color='#3a7ebf', alpha=1.0, label='P10 (Lower)')

        ax.set_ylabel('Load (MW)', color='white')
        ax.tick_params(axis='y', colors='white')
        ax.tick_params(axis='x', colors='white')
        ax.set_title('Forecast Confidence Intervals', color='white', pad=20)
        ax.legend(facecolor='#2b2b2b', labelcolor='white')
        
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def show_error(self, message):
        error_win = ctk.CTkToplevel(self)
        error_win.title("Error")
        error_win.geometry("400x200")
        ctk.CTkLabel(error_win, text=message, wraplength=350).pack(expand=True, padx=20, pady=20)
        ctk.CTkButton(error_win, text="OK", command=error_win.destroy).pack(pady=10)

if __name__ == "__main__":
    app = PredictGUI()
    app.mainloop()
