import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
from PIL import Image, ImageTk
import io

# CONECTANDO COM O DATABASE

conn = sqlite3.connect("turbine_data.db")


# FAZENDO OS CALCULOS

def calculate_vel(v_h, factor_wei, wei):
    result = (v_h / factor_wei) ** wei
    return result

def calculate_vel_h_hub(v_hub, factor_wei_h_hub, wei):
    result = (v_hub / factor_wei_h_hub) ** wei
    return result

def frequency(v_h, calculate_vel, factor_wei, wei):
    result = wei / factor_wei * (v_h / factor_wei) ** (wei - 1) * np.exp(-calculate_vel)
    return result

def frequency_h_hub(v_hub, calculate_vel_h_hub, factor_wei_h_hub, wei):
    result = wei / factor_wei_h_hub * (v_hub / factor_wei_h_hub) ** (wei - 1) * np.exp(-calculate_vel_h_hub)
    return result

def calculate_v_hub(v_medio, h_hub, h_ru, med):
    result = v_medio * (np.log(h_hub / h_ru) / np.log(med / h_ru))
    return result

def calculate_ro_local(max_output, power_ro_turbine, ro, power_x_velocity):
    result = []

    for val in power_x_velocity:
        if val < max_output:
            result.append((val * ro) / power_ro_turbine)
        else:
            result.append(val)

    return result

def future_kw(total_year_hours, freq_results_h_hub_kw, power_curve_results):
    freq_results_h_hub_array = np.array(freq_results_h_hub_kw)
    power_curve_results_array = np.array(power_curve_results)
    result = freq_results_h_hub_array*power_curve_results_array*total_year_hours
    return result

def eap_raw(future_kw_prevision):
    sum = 0
    for i in future_kw_prevision:
        sum = sum + i
    return sum


# BOTÃO DE AÇÃO

def on_submit():
    selected_turbine = combo.get()

    c.execute("SELECT * FROM turbine_data WHERE name=?", (selected_turbine,))
    turbine_data = c.fetchone()

    v_medio = float(entry_v_medio.get().replace(",", "."))
    med = float(entry_med.get().replace(",", "."))
    ro = float(entry_ro.get().replace(",", "."))
    h_ru = float(entry_h_ru.get().replace(",", "."))
    wei = float(entry_wei.get().replace(",", "."))
    h_hub = turbine_data[2]
    turbine_velocity_str = turbine_data[3]
    power_ro_turbine = turbine_data[6]
    max_output = turbine_data[7]
    power_x_velocity_str = turbine_data[4]
    total_year_hours = 8760


    power_x_velocity = [float(val.strip()) for val in power_x_velocity_str.split(',')]

    turbine_velocity = [float(val.strip()) for val in turbine_velocity_str.split(',')]

    v_hub = calculate_v_hub(v_medio, h_hub, h_ru, med)
    factor_wei = v_medio / 0.9
    factor_wei_h_hub = v_hub/0.9
    velocities = np.arange(0, 30.5, 0.5)
    velocities_kw = np.arange(1, 31, 1)

    power_curve_results = calculate_ro_local(max_output,power_ro_turbine,ro, power_x_velocity)

    freq_results = [frequency(v_h, calculate_vel(v_h, factor_wei, wei), factor_wei, wei) for v_h in velocities]

    freq_results_h_hub = [frequency_h_hub(v_hub, calculate_vel_h_hub(v_hub, factor_wei_h_hub, wei), factor_wei_h_hub, wei) for v_hub in velocities]

    freq_results_h_hub_kw = [frequency_h_hub(v_hub, calculate_vel_h_hub(v_hub, factor_wei_h_hub, wei), factor_wei_h_hub, wei) for v_hub in velocities_kw]

    future_kw_prevision = future_kw(total_year_hours,freq_results_h_hub_kw,power_curve_results)

    eap_raw_value = eap_raw(future_kw_prevision)

    factor_cap_raw = (eap_raw_value/total_year_hours/max_output)*100

    pot_med_raw = eap_raw_value/total_year_hours

    eap_raw_display.config(text=f"EAP Bruto: {eap_raw_value:.2f} kW")
    factor_cap_raw_display.config(text=f"Fator de Capacidade - Bruto: {factor_cap_raw:.2f} %")
    pot_med_raw_display.config(text=f"Potência média anual: {pot_med_raw:.2f} kW")


    # PLOTANDO O GRÁFICO

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 6))

    ax1.plot(velocities, freq_results, label='Altura Medição')
    ax1.plot(velocities, freq_results_h_hub, label='Altura Hub')
    ax1.set_xlabel('Velocidade do vento (m/s)')
    ax1.set_ylabel('Frequência')
    ax1.grid(True)
    ax1.legend()

    ax2.plot(turbine_velocity, power_curve_results, label='Curva de potênica')
    ax2.set_yticks(np.linspace(min(power_curve_results), max(power_curve_results), num=10))
    ax2.set_xlabel('Velocidade do vento (m/s)')
    ax2.set_ylabel('Potência (kW)')
    ax2.grid(True)
    ax2.legend()

    ax3.plot(turbine_velocity, future_kw_prevision, label='Energia Prevista')
    ax3.set_xlabel('Velocidade do vento (m/s)')
    ax3.set_ylabel('Energia (kW)')
    ax3.set_yticks(np.linspace(min(future_kw_prevision), max(future_kw_prevision), num=5))
    ax3.grid(True)
    ax3.legend()

    plt.subplots_adjust(hspace=0.5)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=10, column=0, columnspan=2, pady=30)


# CRIANDO O GUI

root = tk.Tk()
root.title("Wind-UFRGS")

c = conn.cursor()
c.execute("SELECT name FROM turbine_data")
turbine_names = [row[0] for row in c.fetchall()]

combo = ttk.Combobox(root, values=turbine_names, state="readonly")
combo.grid(row=5, column=0, padx=10, pady=10)
combo.set("Selecione a turbina")

label1 = tk.Label(root, text="Velocidade média do vento:")
label1.grid(row=0, column=0, padx=10, pady=10)

label1_1 = tk.Label(root, text="m/s")
label1_1.grid(row=0, column=2)

label2 = tk.Label(root, text="Altura da medição:")
label2.grid(row=1, column=0, padx=10, pady=10)

label2_1 = tk.Label(root, text="m")
label2_1.grid(row=1, column=2)

label3 = tk.Label(root, text="Massa especifica media:")
label3.grid(row=2, column=0, padx=10, pady=10)

label3_1 = tk.Label(root, text="kg/m³")
label3_1.grid(row=2, column=2)

label4 = tk.Label(root, text="Altura de rugosidade:")
label4.grid(row=3, column=0, padx=10, pady=10)

label4_1 = tk.Label(root, text="m")
label4_1.grid(row=3, column=2)

label5 = tk.Label(root, text="Fator de forma de Weibull:")
label5.grid(row=4, column=0, padx=10, pady=10)

entry_v_medio = tk.Entry(root)
entry_v_medio.grid(row=0, column=1, padx=10, pady=10)

entry_med = tk.Entry(root)
entry_med.grid(row=1, column=1, padx=10, pady=10)

entry_ro = tk.Entry(root)
entry_ro.grid(row=2, column=1, padx=10, pady=10)

entry_h_ru = tk.Entry(root)
entry_h_ru.grid(row=3, column=1, padx=10, pady=10)

entry_wei = tk.Entry(root)
entry_wei.grid(row=4, column=1, padx=10, pady=10)

eap_raw_display = tk.Label(root, text="EAP Bruta:")
eap_raw_display.grid(row=6, column=0, columnspan=2, pady=1)

factor_cap_raw_display = tk.Label(root, text="Fator de Capacidade - Bruto:")
factor_cap_raw_display.grid(row=7, column=0, columnspan=2, pady=1)

pot_med_raw_display = tk.Label(root, text="Potência média anual:")
pot_med_raw_display.grid(row=8, column=0, columnspan=2, pady=1)

submit_button = tk.Button(root, text="Calcular", command=on_submit)
submit_button.grid(row=9, column=0, columnspan=2, pady=10)

root.mainloop()

# Close the database connection
conn.close()
