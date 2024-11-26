import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import folium
import webbrowser
import os
from sonar_class import Sonar

class SonarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sonar Data Processing")
        
        self.sonar_loaded = False
        self.sonar = None
        self.combined_data = pd.DataFrame()
        self.processed_files = []
        
        self.create_top_frame()

        self.create_export_buttons()

        self.output_text = tk.Text(root, height=10, width=80)
        self.output_text.pack(pady=20)

    def create_top_frame(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(pady=10, padx=10, fill=tk.X)

        self.process_button = ttk.Button(top_frame, text="Select Sonar Files", command=self.process_files)
        self.process_button.pack(side=tk.LEFT, padx=5)

        ttk.Label(top_frame, text="Channel:").pack(side=tk.LEFT, padx=5)
        self.channel_var = tk.StringVar()
        self.channel_combobox = ttk.Combobox(top_frame, textvariable=self.channel_var)
        self.channel_combobox.pack(side=tk.LEFT, padx=5)

        ttk.Label(top_frame, text="Water Depth Adjustment:").pack(side=tk.LEFT, padx=5)
        self.depth_adjustment_var = tk.DoubleVar(value=0)
        self.depth_adjustment_entry = ttk.Entry(top_frame, textvariable=self.depth_adjustment_var)
        self.depth_adjustment_entry.pack(side=tk.LEFT, padx=5)

    def create_export_buttons(self):
        self.csv_button = tk.Button(self.root, text="Export Combined CSV", command=self.export_combined_csv, state=tk.DISABLED)
        self.csv_button.pack(pady=10)
        
        self.map_button = tk.Button(self.root, text="Export GPS Path Maps", command=self.export_gps_path_maps, state=tk.DISABLED)
        self.map_button.pack(pady=10)

    def process_files(self):
        self.clear_output()
        files = filedialog.askopenfilenames(
            title="Select Sonar Files",
            filetypes=[("Sonar files", "*.sl2 *.sl3"), ("All files", "*.*")]
        )
        if not files:
            messagebox.showwarning("No files selected", "Please select at least one Sonar file.")
            return

        self.combined_data = pd.DataFrame()
        self.processed_files = []

        for file_path in files:
            self.process_file(file_path)

        if self.processed_files:
            self.channel_combobox['values'] = self.sonar.valid_channels
            self.csv_button.config(state=tk.NORMAL)
            self.map_button.config(state=tk.NORMAL)
            self.sonar_loaded = True

    def process_file(self, file_path):
        try:
            self.sonar = Sonar(file_path, clean=True, augment_coords=False)
            self.output_text.insert(tk.END, f"Processing file: {file_path}\n")
            data = self.sonar.df
            required_columns = ['longitude', 'latitude', 'water_depth',
                                'datetime', 'gps_speed', 'water_speed', 'water_temperature',
                                'magnetic_heading', 'gps_heading']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                raise ValueError(f"Missing columns {missing_columns} in file '{file_path}'")

            extracted_data = data[required_columns].copy()
            self.combined_data = pd.concat([self.combined_data, extracted_data])
            self.processed_files.append(file_path)
            self.output_text.insert(tk.END, f"Data appended from file: {file_path}\n")

        except Exception as e:
            self.output_text.insert(tk.END, f"Error processing file '{file_path}': {str(e)}\n")
            messagebox.showerror("Error", f"Error processing file '{file_path}':\n{str(e)}")

    def create_gps_path_map(self, file_path, data):
        try:
            gps_data = data[['latitude', 'longitude']].dropna()
            if gps_data.empty:
                self.output_text.insert(tk.END, f"No GPS data found in the file '{file_path}'.\n")
                return

            map_center = [gps_data['latitude'].mean(), gps_data['longitude'].mean()]
            my_map = folium.Map(location=map_center, zoom_start=13)
            folium.PolyLine(locations=gps_data.values.tolist(), color='blue', weight=2.5, opacity=1).add_to(my_map)
            directory = os.path.dirname(file_path)
            base_name = os.path.basename(file_path)
            file_name, _ = os.path.splitext(base_name)
            map_file = os.path.join(directory, f"{file_name}_gps_path.html")
            my_map.save(map_file)
            self.output_text.insert(tk.END, f"GPS path map exported to {map_file}\n")

        except Exception as e:
            self.output_text.insert(tk.END, f"Error creating GPS path map for file '{file_path}':\n{str(e)}\n")

    def export_combined_csv(self):
        try:
            if self.combined_data.empty:
                messagebox.showwarning("No Data", "No combined data available to export.")
                return

            depth_adjustment = self.depth_adjustment_var.get()
            adjusted_data = self.combined_data.copy()
            adjusted_data['water_depth'] += depth_adjustment
            adjusted_data.rename(columns={'water_depth': 'z'}, inplace=True)
            output_file = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if output_file:
                adjusted_data.to_csv(output_file, index=False)
                self.output_text.insert(tk.END, f"Combined CSV file '{output_file}' exported successfully with water depth adjustment of {depth_adjustment}.\n")
                messagebox.showinfo("CSV Export", "Combined CSV file export complete.")
            else:
                self.output_text.insert(tk.END, "No output file selected.\n")

        except Exception as e:
            messagebox.showerror("Error", f"Error exporting CSV: {str(e)}")

    def export_gps_path_maps(self):
        if not self.processed_files:
            messagebox.showwarning("No Files Processed", "No files have been processed to create maps.")
            return

        for file_path in self.processed_files:
            try:
                self.sonar = Sonar(file_path, clean=True, augment_coords=False)
                data = self.sonar.df
                self.create_gps_path_map(file_path, data)
            except Exception as e:
                self.output_text.insert(tk.END, f"Error generating map for file '{file_path}': {str(e)}\n")

        messagebox.showinfo("Maps Export", "GPS path maps for all processed files have been created.")

    def extract_water(self):
        self.extract_data(self.sonar.water, "water")

    def extract_bottom(self):
        self.extract_data(self.sonar.bottom, "bottom")

    def extract_bottom_intensity(self):
        self.extract_data(self.sonar.bottom_intensity, "bottom intensity")

    def extract_data(self, extraction_method, data_type):
        channel = self.channel_var.get()
        if not self.sonar_loaded or not channel:
            messagebox.showerror("Error", "No sonar file loaded or channel not selected!")
            return

        try:
            data = extraction_method(channel)
            setattr(self, f"{data_type.replace(' ', '_')}_data", data)
            self.output_text.insert(tk.END, f"Extracted {data_type} data from channel {channel}.\n")

        except Exception as e:
            messagebox.showerror("Error", f"Error extracting {data_type} data: {str(e)}")

    def clear_output(self):
        self.output_text.delete('1.0', tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = SonarApp(root)
    root.mainloop()
