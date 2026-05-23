from google import genai
client_gemini = genai.Client(api_key="AIzaSyC5wwGOtS8RvE6BLCw2m0KL_uvp3IVxI78")

for model in client_gemini.models.list():
    print(model.name)