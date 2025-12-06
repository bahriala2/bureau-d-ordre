import streamlit as st
import numpy as np
import joblib

# pour voir les élément disponible : https://docs.streamlit.io/develop/api-reference/widgets

# Chargement du modèle
model = joblib.load('linear_regression.joblib')  # nom exact du fichier

# Titre
st.title("🏠 Prédiction du prix d'une maison en Tunisie")

st.write("Remplissez les informations ci-dessous pour estimer le prix d'une maison.")

# Entrées utilisateur
area = st.number_input("Surface (m²)", min_value=10.0, max_value=1000.0, step=1.0)
rooms = st.number_input("Nombre de chambres", min_value=1, max_value=10, step=1)
age = st.number_input("Âge de la maison (en années)", min_value=0, max_value=200, step=1)
city = st.selectbox("Ville", ["Sousse", "Tunis", "Sfax"])

# Encodage de la ville 
# Exemple : encodage one-hot
city_encoded = {
    "Sfax": [1, 0, 0],
    "Sousse": [0, 1, 0],
    "Tunis": [0, 0, 1]
}[city]

# Quand on clique sur le bouton
if st.button("Prédire le prix"):
    # Créer le vecteur d'entrée complet
    X = np.array([[area, rooms, age] + city_encoded])

    # Prédiction
    prediction = model.predict(X)[0]

    # Résultat
    st.success(f"💰 Prix estimé : {prediction:,.2f} €")
