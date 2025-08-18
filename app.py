import requests
from flask import Flask, request, render_template, jsonify

API_KEY = "1fa8858be3892a61152a001529071734"

user_input = input("Enter city: ")

# Fetch the weather API
weather_data = requests.get(
    f"https://api.openweathermap.org/data/2.5/weather?q={user_input}&appid={API_KEY}&units=metric")

if weather_data["cod"] == "404":
    print("No City Found")
else:
    weather = weather_data.json()["weather"][0]["Main"]
    temp = weather_data.json()["main"]["temp"]
