from pymongo import MongoClient
import certifi

uri = "mongodb+srv://shibapkuanar:C85hBDmYWdLrbujq@cluster0.7iohjz5.mongodb.net/?retryWrites=true&w=majority&tls=true&appName=Cluster0"

try:
    client = MongoClient(uri, tlsCAFile=certifi.where())
    print("Databases:", client.list_database_names())
except Exception as e:
    print("❌ MongoDB Connection Error:", e)
