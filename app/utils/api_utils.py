import os
import json
import requests
import urllib.parse
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from .prompts import DEVELOPER_PROMPT, SYSTEM_MESSAGE

# Load environment variables
_ = load_dotenv(find_dotenv())

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def set_api_key(api_key: str):
    """
    Set the OpenAI API key.
    
    Args:
        api_key: OpenAI API key
    """
    os.environ["OPENAI_API_KEY"] = api_key
    global client
    client = OpenAI(api_key=api_key)

def chat_completion(user_input: str, model="gpt-4o"):
    """
    Get a chat completion response from OpenAI.
    
    Args:
        user_input: User input text
        model: Model to use for completion
    
    Returns:
        str: Model response
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": user_input}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error getting chat completion: {e}")
        return f"Error: {str(e)}"

def get_response(user_input: str, model="gpt-4o"):
    """
    Get a response from the OpenAI API using the Responses API.
    
    Args:
        user_input: User input text
        model: Model to use for response
    
    Returns:
        str: Model response text
    """
    try:
        response = client.responses.create(
            model=model,
            instructions=DEVELOPER_PROMPT,
            input=user_input
        )
        return response.output_text
    except Exception as e:
        print(f"Error getting response: {e}")
        return f"Error: {str(e)}"

def web_search(query: str, model="gpt-4o"):
    """
    Perform a web search using the OpenAI API.
    
    Args:
        query: Search query
        model: Model to use
    
    Returns:
        str: Search results
    """
    try:
        response = client.responses.create(
            model=model,
            instructions=DEVELOPER_PROMPT,
            input=query,
            tools=[{"type": "web_search_preview"}]
        )
        return response.output_text
    except Exception as e:
        print(f"Error performing web search: {e}")
        return f"Error: {str(e)}"

def get_location_coordinates(location: str):
    """
    Get coordinates (latitude, longitude) for a location using OpenStreetMap Nominatim API.
    
    Args:
        location: Location name to search for
        
    Returns:
        tuple: (latitude, longitude, display_name) as floats and string, or None if location not found
    """
    try:
        # URL encode the location for the API request
        encoded_location = urllib.parse.quote(location)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_location}&format=json&limit=1"
        
        # Add a user agent to be nice to the API
        headers = {
            "User-Agent": "RAGAgentic/1.0",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                display_name = data[0].get('display_name', location)
                return lat, lon, display_name
        
        return None
    except Exception as e:
        print(f"Error getting location coordinates: {e}")
        return None

def get_weather(location: str, unit="celsius", model="gpt-4o"):
    """
    Get weather information for a location using OpenStreetMap and Open-Meteo APIs.
    
    Args:
        location: Location to get weather for
        unit: Temperature unit (celsius or fahrenheit)
        model: Model to use for generating response
    
    Returns:
        str: Weather information
    """
    try:
        # Get coordinates for the location
        coordinates = get_location_coordinates(location)
        
        if not coordinates:
            # Try with function calling if direct lookup fails
            return get_weather_with_function_calling(location, unit, model)
        
        lat, lon, display_name = coordinates
        
        # Get weather data from Open-Meteo API
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m&hourly=temperature_2m,precipitation_probability,weather_code&temperature_unit={unit}&wind_speed_unit=km/h"
        
        weather_response = requests.get(weather_url)
        
        if weather_response.status_code == 200:
            weather_data = weather_response.json()
            
            # Current weather data
            current = weather_data.get('current', {})
            
            if current:
                temperature = current.get('temperature_2m')
                windspeed = current.get('wind_speed_10m')
                weathercode = current.get('weather_code')
                
                # Map weather codes to descriptions
                weather_descriptions = {
                    0: "Clear sky",
                    1: "Mainly clear",
                    2: "Partly cloudy",
                    3: "Overcast",
                    45: "Fog",
                    48: "Depositing rime fog",
                    51: "Light drizzle",
                    53: "Moderate drizzle",
                    55: "Dense drizzle",
                    56: "Light freezing drizzle",
                    57: "Dense freezing drizzle",
                    61: "Slight rain",
                    63: "Moderate rain",
                    65: "Heavy rain",
                    66: "Light freezing rain",
                    67: "Heavy freezing rain",
                    71: "Slight snow fall",
                    73: "Moderate snow fall",
                    75: "Heavy snow fall",
                    77: "Snow grains",
                    80: "Slight rain showers",
                    81: "Moderate rain showers",
                    82: "Violent rain showers",
                    85: "Slight snow showers",
                    86: "Heavy snow showers",
                    95: "Thunderstorm",
                    96: "Thunderstorm with slight hail",
                    99: "Thunderstorm with heavy hail"
                }
                
                weather_description = weather_descriptions.get(weathercode, "Unknown")
                
                # Get hourly forecast for precipitation probability
                hourly = weather_data.get('hourly', {})
                precipitation_probs = hourly.get('precipitation_probability', [])
                next_hours_precip = precipitation_probs[:12] if precipitation_probs else []
                
                # Calculate chance of precipitation
                if next_hours_precip:
                    max_precip_prob = max(next_hours_precip)
                    precip_info = f"\n- **Precipitation Chance:** {max_precip_prob}% (next 12 hours)" if max_precip_prob > 0 else ""
                else:
                    precip_info = ""
                
                # Format the weather information
                formatted_weather = f"""
## Weather in {display_name}
- **Temperature:** {temperature}°{unit[0].upper()}
- **Conditions:** {weather_description}
- **Wind Speed:** {windspeed} km/h{precip_info}
                """
                
                return formatted_weather.strip()
            
        # Fallback to using web search if API fails or returns unexpected data
        return get_weather_with_function_calling(location, unit, model)
    
    except Exception as e:
        print(f"Error getting weather: {e}")
        # Fallback to function calling on error
        return get_weather_with_function_calling(location, unit, model)

def get_weather_with_function_calling(location: str, unit="celsius", model="gpt-4o"):
    """
    Get weather information for a location using function calling with the OpenAI API.
    
    Args:
        location: Location to get weather for
        unit: Temperature unit (celsius or fahrenheit)
        model: Model to use for generating response
    
    Returns:
        str: Weather information
    """
    try:
        # Define the weather function
        weather_function = {
            "type": "function",
            "name": "get_weather",
            "description": "Get current weather information for a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and country (if known), e.g., 'Paris, France' or just 'Paris'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
        
        # Call the API with function calling
        response = client.responses.create(
            model=model,
            input=f"What is the weather like in {location}?",
            tools=[weather_function],
            tool_choice={"type": "function", "name": "get_weather"}
        )
        
        # Extract the extracted location from function call
        extracted_location = location  # Default to original location
        
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.name == "get_weather" and tool_call.arguments:
                    args = json.loads(tool_call.arguments)
                    if "location" in args:
                        extracted_location = args["location"]
                        # Try again with the extracted location
                        coordinates = get_location_coordinates(extracted_location)
                        if coordinates:
                            lat, lon, display_name = coordinates
                            # Now get the weather data with these coordinates
                            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m&hourly=temperature_2m,precipitation_probability,weather_code&temperature_unit={unit}&wind_speed_unit=km/h"
                            weather_response = requests.get(weather_url)
                            
                            if weather_response.status_code == 200:
                                weather_data = weather_response.json()
                                current = weather_data.get('current', {})
                                
                                if current:
                                    temperature = current.get('temperature_2m')
                                    windspeed = current.get('wind_speed_10m')
                                    weathercode = current.get('weather_code')
                                    
                                    # Map weather codes to descriptions
                                    weather_descriptions = {
                                        0: "Clear sky",
                                        1: "Mainly clear",
                                        2: "Partly cloudy",
                                        3: "Overcast",
                                        45: "Fog",
                                        48: "Depositing rime fog",
                                        51: "Light drizzle",
                                        53: "Moderate drizzle",
                                        55: "Dense drizzle",
                                        56: "Light freezing drizzle",
                                        57: "Dense freezing drizzle",
                                        61: "Slight rain",
                                        63: "Moderate rain",
                                        65: "Heavy rain",
                                        66: "Light freezing rain",
                                        67: "Heavy freezing rain",
                                        71: "Slight snow fall",
                                        73: "Moderate snow fall",
                                        75: "Heavy snow fall",
                                        77: "Snow grains",
                                        80: "Slight rain showers",
                                        81: "Moderate rain showers",
                                        82: "Violent rain showers",
                                        85: "Slight snow showers",
                                        86: "Heavy snow showers",
                                        95: "Thunderstorm",
                                        96: "Thunderstorm with slight hail",
                                        99: "Thunderstorm with heavy hail"
                                    }
                                    
                                    weather_description = weather_descriptions.get(weathercode, "Unknown")
                                    
                                    # Get hourly forecast for precipitation probability
                                    hourly = weather_data.get('hourly', {})
                                    precipitation_probs = hourly.get('precipitation_probability', [])
                                    next_hours_precip = precipitation_probs[:12] if precipitation_probs else []
                                    
                                    # Calculate chance of precipitation
                                    if next_hours_precip:
                                        max_precip_prob = max(next_hours_precip)
                                        precip_info = f"\n- **Precipitation Chance:** {max_precip_prob}% (next 12 hours)" if max_precip_prob > 0 else ""
                                    else:
                                        precip_info = ""
                                    
                                    # Format the weather information
                                    formatted_weather = f"""
## Weather in {display_name}
- **Temperature:** {temperature}°{unit[0].upper()}
- **Conditions:** {weather_description}
- **Wind Speed:** {windspeed} km/h{precip_info}
                                    """
                                    
                                    return formatted_weather.strip()
        
        # Fallback to web search
        return web_search(f"What's the current weather in {extracted_location}?", model)
    
    except Exception as e:
        print(f"Error with function calling for weather: {e}")
        return web_search(f"What's the current weather in {location}?", model)

def file_search_response(user_input: str, vector_store_ids: list, model="gpt-4o-mini"):
    """
    Get a response from the OpenAI API using file search.
    
    Args:
        user_input: User input text
        vector_store_ids: List of vector store IDs to search
        model: Model to use
        
    Returns:
        tuple: Response text and source files used
    """
    import time
    
    # Maximum number of retries
    max_retries = 3
    retry_count = 0
    base_delay = 2  # Base delay in seconds
    
    while retry_count < max_retries:
        try:
            # Use a more efficient model for file search to save on tokens
            # If model is explicitly set to gpt-4o, we'll still use it, but default to a smaller model
            search_model = model if model == "gpt-4o" else "gpt-4o-mini"
            
            # Create API request
            response = client.responses.create(
                input=user_input,
                model=search_model,
                instructions=DEVELOPER_PROMPT,
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": vector_store_ids,
                }],
                temperature=0.7,  # Lower temperature for more focused responses
            )
            
            # Extract annotations to get source filenames
            source_files = set()
            if hasattr(response, 'output') and len(response.output) > 1:
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'annotations'):
                                annotations = content_item.annotations
                                for annotation in annotations:
                                    if hasattr(annotation, 'filename'):
                                        source_files.add(annotation.filename)
            
            return response.output_text, source_files
            
        except Exception as e:
            error_message = str(e)
            print(f"Error with file search (attempt {retry_count+1}/{max_retries}): {error_message}")
            
            # Check if it's a rate limit error or parameter error
            if ("rate_limit_exceeded" in error_message or 
                "Request too large" in error_message or
                "unknown_parameter" in error_message):
                retry_count += 1
                if retry_count < max_retries:
                    # Calculate delay with exponential backoff
                    delay = base_delay * (2 ** (retry_count - 1))
                    print(f"Error detected. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    
                    # If we're hitting token limits, try with an even smaller model on next attempt
                    if "gpt-4" in search_model:
                        search_model = "gpt-3.5-turbo"
                    elif search_model == "gpt-3.5-turbo" and retry_count > 1:
                        search_model = "gpt-3.5-turbo-16k"
                    continue
                else:
                    # If we've exhausted retries, return a helpful error message
                    return "I apologize, but I'm having trouble searching through the files due to API limitations. Could you try again with a more specific question or wait a moment before asking again?", set()
            else:
                # For other errors, return immediately
                return f"Error with file search: {error_message}", set()
    
    # If we've exhausted retries
    return "I'm sorry, but I'm currently experiencing technical difficulties and can't complete the file search. Please try again later.", set()

def use_tool_response(user_input: str, tools_config: dict, model="gpt-4o"):
    """
    Get a response using enabled tools.
    
    Args:
        user_input: User input text
        tools_config: Dictionary of enabled tools 
        model: Model to use
        
    Returns:
        tuple: Response text and metadata
    """
    import time
    
    # Setup for retries
    max_retries = 3
    retry_count = 0
    base_delay = 2  # Base delay in seconds
    
    tools = []
    
    if tools_config.get("web_search"):
        tools.append({"type": "web_search_preview"})
    
    if tools_config.get("file_search") and tools_config.get("vector_store_id"):
        tools.append({
            "type": "file_search",
            "vector_store_ids": [tools_config.get("vector_store_id")]
            # Note: chunk_size is not supported by the OpenAI API
        })
    
    if tools_config.get("function_calling"):
        # Add the weather function
        tools.append({
            "type": "function",
            "name": "get_weather",
            "description": "Get current weather information for a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and country (if known), e.g., 'Paris, France' or just 'Paris'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        })
    
    # If we have many tools enabled, use a smaller model by default to avoid rate limits
    if len(tools) > 1 and model == "gpt-4o":
        # Default to a smaller model when multiple tools are used
        response_model = "gpt-4o-mini"
    else:
        response_model = model
    
    while retry_count < max_retries:
        try:
            # Check if this might be a weather query
            is_weather_query = any(keyword in user_input.lower() for keyword in ["weather", "temperature", "forecast", "climate"])
            
            # Create the response
            if tools_config.get("function_calling") and is_weather_query:
                # For likely weather queries, explicitly set tool_choice
                response = client.responses.create(
                    model=response_model,
                    input=user_input,
                    instructions=DEVELOPER_PROMPT,
                    tools=tools,
                    tool_choice={"type": "function", "name": "get_weather"},
                    temperature=0.7,  # Lower temperature
                )
            else:
                # For general queries, let the model decide which tool to use
                response = client.responses.create(
                    model=response_model,
                    input=user_input,
                    instructions=DEVELOPER_PROMPT,
                    tools=tools,
                    temperature=0.7,  # Lower temperature
                )
            
            # Check for any tool calls in the response
            metadata = {}
            
            # Handle function calls if present
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call.name == "get_weather" and tool_call.arguments:
                        try:
                            args = json.loads(tool_call.arguments)
                            if "location" in args:
                                location = args["location"]
                                unit = args.get("unit", "celsius")
                                # Get weather for the extracted location
                                weather_response = get_weather(location, unit, model)
                                return weather_response, {"function": "weather", "location": location}
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error in tool call arguments: {e}")
                            print(f"Raw arguments: {tool_call.arguments}")
                        except Exception as e:
                            print(f"Error processing weather function call: {e}")
            
            # Extract source files if file search was used
            source_files = set()
            if tools_config.get("file_search") and hasattr(response, 'output') and len(response.output) > 1:
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'annotations'):
                                annotations = content_item.annotations
                                for annotation in annotations:
                                    if hasattr(annotation, 'filename'):
                                        source_files.add(annotation.filename)
                metadata["source_files"] = source_files
            
            return response.output_text, metadata
        
        except Exception as e:
            error_message = str(e)
            print(f"Error with tool response (attempt {retry_count+1}/{max_retries}): {error_message}")
            
            # Check if it's a rate limit error or unknown parameter error
            if ("rate_limit_exceeded" in error_message or 
                "Request too large" in error_message or
                "unknown_parameter" in error_message):
                retry_count += 1
                if retry_count < max_retries:
                    # Calculate delay with exponential backoff
                    delay = base_delay * (2 ** (retry_count - 1))
                    print(f"Error detected. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    
                    # If we're hitting token limits, downgrade to an even smaller model
                    if "gpt-4" in response_model:
                        response_model = "gpt-3.5-turbo"
                    elif response_model == "gpt-3.5-turbo" and retry_count > 1:
                        response_model = "gpt-3.5-turbo-16k"
                    
                    continue
                else:
                    # If we've exhausted retries
                    return "I apologize, but I'm experiencing API limitations. Please try asking a more specific question or wait a moment before trying again.", {}
            else:
                # For other errors, return immediately
                return f"Error with tools: {error_message}", {}
    
    # If we've exhausted retries
    return "I'm sorry, but I'm currently experiencing technical difficulties and can't complete your request. Please try again later with a more specific question.", {}
