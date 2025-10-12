import json
import pyodide
from pyscript import document
from js import console
##
def run(name, age):
    # Get the chart element
    chart = document.getElementById("chart")

    if(not name):
        chart.innerHTML = "<p><i>name</i> not defined</p>"
        return
    if(not age):
        chart.innerHTML = "<p><i>age</i> not defined</p>"
        return
    ##
    output = f"<p>Hello <b>{name}</b>. Nice to meet you.</p>"
    if(age < 18):
        output += "<p>We welcome all script kiddies</p>"
    if(age > 18 and age < 33):
        output += "<p>It seems you are a senior dev</p>"
    if(age > 40):
        output += "<p>I thought Dinos were extinct!</p>"
    output += "<p><i>just kidding lmao</i></p>"

    chart.innerHTML = output
##
chart = document.getElementById("chart")
if chart:
    chart.innerHTML = "<p>🐍: Hi from Python. Fill the form in JS to get a return from Py</p>"
