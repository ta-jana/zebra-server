from flask import Flask, request, jsonify, render_template
import zebra_print

app = Flask(__name__)

# Create an instance of the Zebra printer
z = zebra_print.Zebra()

# Specify your printer name
z.setqueue("ZDesigner TLP 2844")

# Function to determine font size and position based on text length
def determine_font_size(text, max_length):
    base_x_position = 20  # Starting x position for default font size
    if len(text) > max_length:
        font_size = 1  # Smaller font size
        x_position = base_x_position + 80 - (len(text) - max_length) * 10  # Adjust x position incrementally
    else:
        font_size = 2  # Default font size
        x_position = base_x_position
    return font_size, x_position

# Function to generate EPL2 code for the label
def generate_label(product_name, price, weight_or_volume, unit, price_per_unit):
    if unit == 'mass':
        weight_label = f"1ks= {weight_or_volume}g"
        price_label = f"1kg= {price_per_unit:.2f}Kč"
    elif unit == 'volume':
        weight_label = f"1ks= {weight_or_volume}l"
        price_label = f"1l= {price_per_unit:.2f}Kč"

    # Convert price to string and determine font size
    price_str = f"{price:.2f}"
    font_size, x_position = determine_font_size(price_str, max_length=5)  # Adjust max_length as needed

# NO WHITESPACE INFRONT OF PRINTER COMMANDS
    epl2_commands = f"""
N
I8,B,001
S4
D10
A20,20,0,4,1,1,N,"{product_name}"
A{x_position},80,0,5,{font_size},2,N,"{price_str}"
A20,200,0,3,1,1,N,"{weight_label} | {price_label}"
P1
"""
    
    return epl2_commands.encode('cp1250')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/print_label', methods=['POST'])
def print_label():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid input: JSON data required"}), 400

        product_name = data.get('product_name')
        price = data.get('price')
        unit = data.get('unit')
        weight_or_volume = data.get('weight_or_volume')

        # Validate input
        if not product_name:
            return jsonify({"error": "Invalid input: 'product_name' is required"}), 400
        if not isinstance(price, (float, int)):
            return jsonify({"error": "Invalid input: 'price' must be a number"}), 400
        if unit not in ['mass', 'volume']:
            return jsonify({"error": "Invalid input: 'unit' must be either 'mass' or 'volume'"}), 400
        if not isinstance(weight_or_volume, (float, int)):
            return jsonify({"error": "Invalid input: 'weight_or_volume' must be a number"}), 400

        price = float(price)
        weight_or_volume = float(weight_or_volume)

        if unit == 'mass':
            price_per_unit = price / (weight_or_volume / 1000)
        elif unit == 'volume':
            price_per_unit = price / weight_or_volume

        epl2 = generate_label(product_name, price, weight_or_volume, unit, price_per_unit)

        z.setup(direct_thermal=True, label_height=(240,16), label_width=400)
        z.output(epl2)

        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 50

@app.route('/is_server', methods=['GET'])
def is_server():
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
