
from flask import Flask, render_template, request
import numpy as np
import matplotlib.pyplot as plt
import io, base64

app = Flask(__name__)

# Функции для расчётов
def dilution_rate(F, V):
    return F / V

def substrate_concentration(D, Ks, mu_max, time):
    if D >= mu_max:
        return 0
    S0 = (Ks * D) / (mu_max - D)
    S = S0 * np.exp(-mu_max * time)
    return max(S, 0)

def biomass_concentration(S, S_in, Yxs):
    return Yxs * (S_in - S)

def generate_growth_charts(S_in, F, mu_max, Ks, Yxs, V):
    time = np.linspace(0, 168, 100)
    D = dilution_rate(F, V)

    if D >= mu_max:
        return None, None, None, None, None

    S_values = []
    X_values = []
    for t in time:
        S = substrate_concentration(D, Ks, mu_max, t)
        X = biomass_concentration(S, S_in, Yxs)
        S_values.append(S)
        X_values.append(X)

    plt.figure(figsize=(10, 6))
    plt.plot(time, X_values, label="Концентрация биомассы (г/л)", color="green")
    plt.title("Динамика концентрации биомассы во времени")
    plt.xlabel("Время (часы)")
    plt.ylabel("Концентрация биомассы (г/л)")
    plt.grid(True)
    plt.legend()
    img_biomass = io.BytesIO()
    plt.savefig(img_biomass, format='png')
    img_biomass.seek(0)
    plot_url_biomass = base64.b64encode(img_biomass.getvalue()).decode()
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(time, S_values, label="Концентрация субстрата (г/л)", color="blue")
    plt.title("Динамика концентрации субстрата во времени")
    plt.xlabel("Время (часы)")
    plt.ylabel("Концентрация субстрата (г/л)")
    plt.grid(True)
    plt.legend()
    img_substrate = io.BytesIO()
    plt.savefig(img_substrate, format='png')
    img_substrate.seek(0)
    plot_url_substrate = base64.b64encode(img_substrate.getvalue()).decode()
    plt.close()

    return plot_url_biomass, plot_url_substrate, S_values, X_values, time

@app.route('/', methods=['GET', 'POST'])
def index():
    result, plot_url_biomass, plot_url_substrate, S_values, X_values, time = None, None, None, None, None, None
    control_points = []
    if request.method == 'POST':
        try:
            S_in = float(request.form['substrate_concentration'])
            F = float(request.form['flow_rate'])
            mu_max = float(request.form['mu_max'])
            Ks = float(request.form['Ks'])
            Yxs = float(request.form['Yxs'])
            V = float(request.form['V'])

            plot_url_biomass, plot_url_substrate, S_values, X_values, time = generate_growth_charts(S_in, F, mu_max, Ks, Yxs, V)

            if plot_url_biomass is None:
                result = "Ошибка: Скорость подачи слишком велика для данной системы."
            else:
                for t, S, X in zip(time[::24], S_values[::24], X_values[::24]):
                    control_points.append((round(t, 0), round(S, 2), round(X, 2)))

                result = f"Концентрация субстрата и биомассы изменяется с течением времени.\nКонцентрация субстрата: {round(S_values[-1], 2)} г/л\nКонцентрация биомассы: {round(X_values[-1], 2)} г/л"
        except ValueError:
            result = "Ошибка: Введите корректные числовые значения."

    return render_template('index.html', result=result, plot_url_biomass=plot_url_biomass, plot_url_substrate=plot_url_substrate, control_points=control_points)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
