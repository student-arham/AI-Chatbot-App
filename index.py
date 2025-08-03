from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer, ChatterBotCorpusTrainer
from flask import Flask,  render_template, request
import requests
import re
import math

app = Flask(__name__)

bot = ChatBot("chatbot", read_only=False,
              logic_adapters=[
                  
            {
                "import_path":"chatterbot.logic.BestMatch",
                "default_response":"Sorry I don't have an answer",
                "maximum_similarity_threshold":0.9

                  }
              ])

trainer = ChatterBotCorpusTrainer(bot)

trainer.train("chatterbot.corpus.english")

allowed_names = {name: getattr(math, name) for name in dir(math) if not name.startswith("__")}
allowed_names.update({"abs": abs, "round": round})

def safe_eval(expression):

    if not re.match(r'^[0-9a-zA-Z\.\+\-\*/\(\)\s,]+$', expression):
        return "Invalid expression"
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return round(result, 4)
    except Exception:
        return "Error in calculation"
    
@app.route("/")
def main():
    return render_template("index.html")

# while True:
#   user_response = input("User: ")  
#  print("ChatBot:" +str(bot.get_response(user_response)))

@app.route("/get")
def get_chatbot_reponse():
    userText = request.args.get('userMessage').strip()
    api_key = "99129aa2091528f3c5f2375d77c28dfe"

    if re.search(r'[\d\+\-\*/]|sqrt|sin|cos|tan|log|exp|pow', userText.lower()):
        math_result = safe_eval(userText)
        if isinstance(math_result, (int, float)):
            return {"type": "math", "result": math_result}
        elif math_result != "Invalid expression":
            return {"type": "math", "result": math_result}
  
    if "weather" in userText.lower():
        
        city = userText.lower().replace("weather", "").replace("in", "").strip()
        if city == "":
            city = "Delhi"  
    else:
        city = userText  

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    try:
        rawData = requests.get(weather_url, timeout=5)
        result = rawData.json()
    except requests.exceptions.RequestException:
        return {"type": "error", "message": "Unable to connect to weather service."}


    if result.get("cod") == 200:
        city_name = result.get("name", city)
        country = result["sys"].get("country", "N/A")
        temp_celsius = round(result["main"]["temp"] - 273.15, 2)
        weather_desc = result["weather"][0]["description"].capitalize()

        return {
            "type": "weather",
            "city": city_name,
            "country": country,
            "temperature_celsius": temp_celsius,
            "weather_description": weather_desc
        }


    else:
        bot_response = str(bot.get_response(userText))
        return {"type": "chat", "message": bot_response}    


if __name__ == "__main__":
    app.run(debug=True)
