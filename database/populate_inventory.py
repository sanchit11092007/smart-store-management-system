import random
import re
from database.db_connection import get_db_connection

random.seed(42)  # same data every run. Remove this line if you want fresh random data each time.

# ---------------------------------------------------------------
# PACK SIZES: (label, price multiplier). Base price = multiplier 1.0
# ---------------------------------------------------------------
SIZES = {
    "kg":    [("500g", 0.55), ("1kg", 1.0), ("5kg", 4.6)],
    "g":     [("100g", 0.4), ("250g", 1.0), ("500g", 1.9)],
    "snack": [("40g", 0.4), ("100g", 1.0), ("200g", 1.9)],
    "l":     [("500ml", 0.55), ("1L", 1.0), ("5L", 4.6)],
    "ml":    [("100ml", 0.5), ("200ml", 1.0), ("500ml", 2.2)],
    "bottle":[("250ml", 0.6), ("750ml", 1.0), ("2L", 2.3)],
    "pack":  [("Pack of 1", 1.0), ("Pack of 3", 2.8), ("Pack of 5", 4.5)],
    "tabs":  [("10 Tabs", 0.6), ("30 Tabs", 1.0), ("60 Tabs", 1.8)],
    "gb":    [("32GB", 0.6), ("64GB", 1.0), ("128GB", 1.7)],
    "cloth": [("S", 1.0), ("M", 1.0), ("L", 1.0), ("XL", 1.05)],
    "color": [("Black", 1.0), ("Blue", 1.0), ("Red", 1.0)],
    "var":   [("Regular", 1.0), ("Value Pack", 1.8), ("Premium", 1.3)],
    "one":   [("", 1.0)],
}

# Each product is: (product name, [brands that really make it], min price, max price, size key)
# Brands are tied to the product, so you never get "Lays Coffee" or "Amul Apple".
STORE_CATALOG = {
    "Grocery & Staples": [
        ("Basmati Rice", ["India Gate", "Daawat", "Fortune", "Kohinoor", "Tata Sampann"], 95, 180, "kg"),
        ("Sona Masoori Rice", ["Fortune", "Aashirvaad", "24 Mantra", "Rajdhani"], 55, 85, "kg"),
        ("Sharbati Atta", ["Aashirvaad", "Pillsbury", "Fortune", "Annapurna", "Patanjali"], 45, 62, "kg"),
        ("Multigrain Atta", ["Aashirvaad", "Pillsbury", "24 Mantra", "Patanjali"], 60, 85, "kg"),
        ("Maida", ["Rajdhani", "Fortune", "Patanjali", "Annapurna"], 38, 55, "kg"),
        ("Suji Rawa", ["Rajdhani", "Aashirvaad", "Fortune", "Patanjali"], 42, 60, "kg"),
        ("Besan", ["Rajdhani", "Fortune", "Tata Sampann", "Patanjali"], 90, 130, "kg"),
        ("Poha Thick", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra"], 60, 90, "kg"),
        ("Toor Dal", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra", "Catch"], 130, 190, "kg"),
        ("Moong Dal", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra"], 110, 160, "kg"),
        ("Masoor Dal", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra"], 85, 120, "kg"),
        ("Chana Dal", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra"], 85, 130, "kg"),
        ("Urad Dal", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra"], 120, 170, "kg"),
        ("Rajma", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra"], 120, 175, "kg"),
        ("Kabuli Chana", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra"], 140, 210, "kg"),
        ("Refined Sugar", ["Madhur", "Uttam", "Trust", "Dhampur"], 44, 56, "kg"),
        ("Jaggery Powder", ["Organic Tattva", "Sri Sri Tattva", "Patanjali", "Dhampur"], 70, 110, "kg"),
        ("Iodized Salt", ["Tata Salt", "Aashirvaad", "Annapurna", "Catch"], 20, 30, "kg"),
        ("Mustard Oil", ["Fortune", "Patanjali", "Dhara", "Engine"], 140, 195, "l"),
        ("Sunflower Oil", ["Fortune", "Saffola", "Gemini", "Sundrop"], 130, 185, "l"),
        ("Groundnut Oil", ["Fortune", "Gold Winner", "Dhara", "Postman"], 190, 260, "l"),
        ("Desi Ghee", ["Amul", "Patanjali", "Mother Dairy", "Gowardhan"], 520, 680, "l"),
        ("Turmeric Powder", ["Everest", "MDH", "Catch", "Tata Sampann"], 60, 95, "g"),
        ("Red Chilli Powder", ["Everest", "MDH", "Catch", "Tata Sampann"], 70, 110, "g"),
        ("Coriander Powder", ["Everest", "MDH", "Catch", "Tata Sampann"], 50, 85, "g"),
        ("Garam Masala", ["Everest", "MDH", "Catch", "Badshah"], 80, 130, "g"),
        ("Jeera Whole", ["Everest", "MDH", "Catch", "Tata Sampann"], 90, 150, "g"),
        ("Black Pepper", ["Everest", "Catch", "Tata Sampann", "Organic Tattva"], 110, 170, "g"),
        ("Cashew Whole", ["Nutraj", "Happilo", "Tata Sampann", "Farmley"], 180, 280, "g"),
        ("Almonds", ["Nutraj", "Happilo", "Tata Sampann", "Farmley"], 200, 320, "g"),
        ("Raisins", ["Nutraj", "Happilo", "Tata Sampann", "Farmley"], 90, 160, "g"),
        ("Tea Leaves CTC", ["Tata Tea", "Red Label", "Taj Mahal", "Wagh Bakri", "Society"], 120, 260, "kg"),
    ],
    "Dairy, Bakery, Fruits & Vegetables": [
        ("Toned Milk", ["Amul", "Mother Dairy", "Parag", "Gowardhan"], 28, 32, "l"),
        ("Full Cream Milk", ["Amul", "Mother Dairy", "Parag", "Gowardhan"], 33, 38, "l"),
        ("Fresh Curd", ["Amul", "Mother Dairy", "Nestle", "Epigamia"], 35, 60, "g"),
        ("Fresh Paneer", ["Amul", "Mother Dairy", "Milky Mist", "Gowardhan"], 80, 120, "g"),
        ("Salted Butter", ["Amul", "Mother Dairy", "Britannia", "Gowardhan"], 52, 70, "g"),
        ("Cheese Slices", ["Amul", "Britannia", "Go", "Mother Dairy"], 110, 160, "g"),
        ("Cheese Spread", ["Amul", "Britannia", "Go", "Kraft"], 85, 140, "g"),
        ("Lassi", ["Amul", "Mother Dairy", "Gowardhan", "Nestle"], 20, 35, "ml"),
        ("Buttermilk", ["Amul", "Mother Dairy", "Gowardhan", "Nestle"], 12, 25, "ml"),
        ("White Bread", ["Britannia", "English Oven", "Modern", "Harvest Gold"], 38, 50, "g"),
        ("Brown Bread", ["Britannia", "English Oven", "Modern", "Harvest Gold"], 42, 58, "g"),
        ("Multigrain Bread", ["Britannia", "English Oven", "Modern", "Harvest Gold"], 50, 70, "g"),
        ("Pav Buns", ["Britannia", "English Oven", "Modern", "Harvest Gold"], 30, 45, "pack"),
        ("Rusk Toast", ["Britannia", "Parle", "Cremica", "Modern"], 40, 70, "g"),
        ("Eggless Cake Slice", ["Britannia", "Winkies", "English Oven", "Monginis"], 25, 60, "pack"),
        ("Apple", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 120, 220, "kg"),
        ("Banana", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 40, 65, "kg"),
        ("Orange", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 60, 100, "kg"),
        ("Grapes", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 70, 130, "kg"),
        ("Pomegranate", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 120, 200, "kg"),
        ("Papaya", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 30, 55, "kg"),
        ("Watermelon", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 20, 40, "kg"),
        ("Tomato", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 30, 60, "kg"),
        ("Potato", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 25, 45, "kg"),
        ("Onion", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 25, 50, "kg"),
        ("Cauliflower", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 30, 60, "kg"),
        ("Green Peas", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 60, 120, "kg"),
        ("Spinach Palak", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 20, 45, "kg"),
        ("Carrot", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 35, 60, "kg"),
        ("Capsicum", ["Fresho", "Farm Fresh", "Local Mandi", "Nature Basket"], 50, 90, "kg"),
    ],
    "Beverages, Snacks & Confectionery": [
        ("Classic Salted Chips", ["Lays", "Bingo", "Uncle Chipps", "Pringles"], 20, 60, "snack"),
        ("Magic Masala Chips", ["Lays", "Bingo", "Uncle Chipps", "Haldiram"], 20, 60, "snack"),
        ("Aloo Bhujia", ["Haldiram", "Bikaji", "Bikano", "Balaji"], 45, 100, "snack"),
        ("Namkeen Mixture", ["Haldiram", "Bikaji", "Bikano", "Balaji"], 45, 100, "snack"),
        ("Roasted Peanuts", ["Haldiram", "Bikaji", "Balaji", "Tata Sampann"], 40, 90, "snack"),
        ("Makhana Roasted", ["Farmley", "Happilo", "Haldiram", "Tata Sampann"], 80, 180, "snack"),
        ("Popcorn Butter", ["Act II", "Orville", "Haldiram", "Bingo"], 30, 80, "snack"),
        ("Dairy Milk Chocolate", ["Cadbury"], 40, 175, "var"),
        ("KitKat Chocolate", ["Nestle"], 30, 80, "var"),
        ("Dark Chocolate Bar", ["Amul", "Cadbury Bournville", "Hershey's", "Ferrero"], 90, 220, "var"),
        ("Chocolate Wafer", ["Cadbury", "Parle", "Nestle", "Britannia"], 10, 50, "pack"),
        ("Glucose Biscuits", ["Parle-G", "Britannia", "Sunfeast", "Priyagold"], 10, 30, "g"),
        ("Digestive Biscuits", ["Britannia", "McVities", "Sunfeast", "Parle"], 35, 90, "g"),
        ("Cream Biscuits", ["Britannia", "Oreo", "Sunfeast", "Parle"], 25, 60, "g"),
        ("Cookies Butter", ["Britannia", "Unibic", "Sunfeast", "Parle"], 30, 100, "g"),
        ("Cola Drink", ["Coca Cola", "Pepsi", "Thums Up", "Limca"], 40, 45, "bottle"),
        ("Mango Drink", ["Maaza", "Slice", "Frooti", "Real"], 20, 90, "bottle"),
        ("Fruit Juice Mixed", ["Real", "Tropicana", "Paper Boat", "B Natural"], 20, 120, "bottle"),
        ("Packaged Drinking Water", ["Bisleri", "Kinley", "Aquafina", "Himalayan"], 20, 25, "bottle"),
        ("Instant Coffee", ["Nescafe", "Bru", "Continental", "Tata Coffee"], 80, 210, "g"),
        ("Green Tea Bags", ["Lipton", "Tetley", "Twinings", "Organic India"], 120, 260, "pack"),
        ("Candy Toffee Pouch", ["Parle", "Pulse", "Alpenliebe", "Centerfresh"], 20, 60, "pack"),
        ("Mouth Freshener", ["Haldiram", "Pass Pass", "Catch", "Rasna"], 10, 40, "pack"),
    ],
    "Personal Care": [
        ("Bath Soap", ["Dettol", "Dove", "Pears", "Lux", "Lifebuoy", "Santoor"], 30, 80, "pack"),
        ("Shampoo", ["Head & Shoulders", "Dove", "Clinic Plus", "Pantene", "Tresemme"], 80, 260, "ml"),
        ("Hair Conditioner", ["Dove", "Pantene", "Tresemme", "Sunsilk"], 120, 280, "ml"),
        ("Hair Oil", ["Parachute", "Bajaj Almond Drops", "Dabur Amla", "Indulekha"], 60, 250, "ml"),
        ("Toothpaste", ["Colgate", "Pepsodent", "Closeup", "Sensodyne"], 55, 150, "g"),
        ("Toothbrush", ["Colgate", "Oral-B", "Pepsodent", "Sensodyne"], 30, 150, "pack"),
        ("Body Wash", ["Dove", "Nivea", "Fiama", "Pears"], 120, 280, "ml"),
        ("Face Wash", ["Himalaya", "Garnier", "Nivea", "Clean & Clear"], 90, 220, "ml"),
        ("Body Lotion", ["Nivea", "Vaseline", "Dove", "Parachute Advansed"], 150, 320, "ml"),
        ("Face Cream", ["Fair & Lovely", "Pond's", "Nivea", "Ponds Light"], 70, 250, "g"),
        ("Deodorant Spray", ["Fogg", "Nivea", "Axe", "Engage"], 130, 280, "ml"),
        ("Shaving Foam", ["Gillette", "Old Spice", "Nivea Men", "Park Avenue"], 110, 230, "ml"),
        ("Razor Blades", ["Gillette", "Super-Max", "7 O'Clock", "Park Avenue"], 30, 400, "pack"),
        ("Hand Wash Liquid", ["Dettol", "Lifebuoy", "Savlon", "Dove"], 55, 130, "ml"),
        ("Sanitary Pads", ["Whisper", "Stayfree", "Sofy", "Carefree"], 45, 220, "pack"),
        ("Talcum Powder", ["Pond's", "Nycil", "Navratna", "Johnson's"], 60, 200, "g"),
    ],
    "Girls Accessories & Makeup": [
        ("Matte Lipstick", ["Maybelline", "Lakme", "Nykaa", "Colorbar", "Faces Canada"], 199, 699, "color"),
        ("Kajal", ["Lakme", "Maybelline", "Himalaya", "Faces Canada"], 99, 299, "color"),
        ("Waterproof Mascara", ["Maybelline", "Lakme", "Nykaa", "Colorbar"], 250, 499, "color"),
        ("Liquid Eye Liner", ["Maybelline", "Lakme", "Faces Canada", "Colorbar"], 180, 350, "color"),
        ("Compact Powder", ["Lakme", "Maybelline", "Colorbar", "Faces Canada"], 220, 450, "var"),
        ("Foundation", ["Maybelline", "Lakme", "Nykaa", "Colorbar"], 350, 750, "var"),
        ("Nail Enamel", ["Lakme", "Maybelline", "Colorbar", "Nykaa"], 99, 220, "color"),
        ("Makeup Remover", ["Garnier", "Lakme", "Maybelline", "Nykaa"], 199, 399, "ml"),
        ("Hair Scrunchies Set", ["Gitti", "Nykaa", "Ayesha", "Kaneesh"], 60, 150, "pack"),
        ("Hair Claw Clip", ["Gitti", "Nykaa", "Ayesha", "Kaneesh"], 50, 120, "color"),
        ("Hair Band", ["Gitti", "Nykaa", "Ayesha", "Kaneesh"], 30, 100, "color"),
        ("Bangles Set", ["Kaneesh", "Ayesha", "Gitti", "Local Craft"], 80, 300, "color"),
        ("Earrings Pair", ["Kaneesh", "Ayesha", "Gitti", "Local Craft"], 100, 450, "color"),
        ("Bindi Pack", ["Kaneesh", "Ayesha", "Gitti", "Local Craft"], 10, 40, "pack"),
    ],
    "Tech Based Items": [
        ("USB-C Cable 1.5m", ["boAt", "Portronics", "Ambrane", "Mi", "Zebronics"], 199, 399, "color"),
        ("Micro USB Cable", ["boAt", "Portronics", "Ambrane", "Zebronics"], 99, 249, "color"),
        ("Wall Charger 20W", ["boAt", "Mi", "Ambrane", "Realme", "Portronics"], 450, 899, "color"),
        ("MicroSD Card", ["SanDisk", "Samsung", "Kingston", "HP"], 450, 650, "gb"),
        ("USB Flash Drive", ["SanDisk", "HP", "Kingston", "Lexar"], 400, 700, "gb"),
        ("Wireless Mouse", ["Logitech", "HP", "Zebronics", "Portronics"], 399, 850, "color"),
        ("Wired Keyboard", ["Logitech", "HP", "Zebronics", "Portronics"], 450, 950, "color"),
        ("Smart WiFi LED Bulb", ["Wipro", "Philips", "Syska", "Mi"], 399, 699, "var"),
        ("Power Strip Surge Protector", ["Belkin", "Havells", "Anchor", "Zebronics"], 499, 999, "var"),
        ("Wifi Router", ["TP-Link", "D-Link", "Tenda", "Netgear"], 1100, 2500, "var"),
        ("Webcam HD", ["Logitech", "Zebronics", "HP", "Lenovo"], 899, 2200, "var"),
        ("Mouse Pad", ["Logitech", "HP", "Zebronics", "Portronics"], 150, 450, "color"),
        ("Phone Stand", ["Portronics", "Ambrane", "Zebronics", "boAt"], 150, 450, "color"),
        ("OTG Adapter", ["boAt", "Portronics", "Ambrane", "Zebronics"], 99, 299, "color"),
    ],
    "Health & Wellness": [
        ("Chyawanprash", ["Dabur", "Baidyanath", "Patanjali", "Zandu"], 340, 480, "g"),
        ("Honey", ["Dabur", "Patanjali", "Kapiva", "Zandu"], 210, 320, "g"),
        ("Whey Protein Vegetarian", ["Optimum Nutrition", "MuscleBlaze", "Kapiva", "Boldfit"], 1800, 2900, "var"),
        ("Plant Protein Powder", ["Kapiva", "Boldfit", "OZiva", "Yogabar"], 1500, 2600, "var"),
        ("Vegetarian Multivitamin", ["HealthKart", "Kapiva", "Himalaya", "Boldfit"], 450, 750, "tabs"),
        ("Flaxseed Omega-3 Capsules", ["HealthKart", "Kapiva", "Himalaya", "Boldfit"], 499, 899, "tabs"),
        ("Aloe Vera Juice", ["Patanjali", "Kapiva", "Dabur", "Himalaya"], 180, 270, "l"),
        ("Amla Juice", ["Patanjali", "Kapiva", "Dabur", "Baidyanath"], 150, 260, "l"),
        ("Giloy Juice", ["Patanjali", "Kapiva", "Dabur", "Baidyanath"], 150, 260, "l"),
        ("Vitamin C Effervescent", ["Limcee", "HealthKart", "Zandu", "Himalaya"], 220, 350, "tabs"),
        ("Ashwagandha Tablets", ["Himalaya", "Kapiva", "Patanjali", "Dabur"], 250, 450, "tabs"),
        ("Triphala Powder", ["Patanjali", "Baidyanath", "Dabur", "Kapiva"], 90, 200, "g"),
        ("Oats", ["Quaker", "Saffola", "Kellogg's", "Tata Sampann"], 90, 190, "g"),
        ("Muesli Fruit", ["Kellogg's", "Saffola", "Yogabar", "Quaker"], 180, 380, "g"),
        ("Protein Bar", ["RiteBite", "Yogabar", "Max Protein", "Fit Bar"], 40, 120, "pack"),
    ],
    "All Medicines & First Aid": [
        ("Paracetamol 650mg", ["Dolo", "Crocin", "Calpol", "P-650"], 30, 45, "tabs"),
        ("Herbal Cough Syrup", ["Dabur", "Himalaya", "Baidyanath", "Zandu"], 85, 130, "ml"),
        ("Antacid Liquid", ["Digene", "Gelusil", "Eno", "Pudin Hara"], 60, 160, "ml"),
        ("Pain Relief Gel", ["Volini", "Moov", "Iodex", "Zandu"], 75, 130, "g"),
        ("Pain Relief Balm", ["Amrutanjan", "Zandu", "Vicks", "Tiger Balm"], 40, 110, "g"),
        ("Antiseptic Liquid", ["Dettol", "Savlon", "Betadine", "Hansaplast"], 95, 140, "ml"),
        ("Waterproof Bandages", ["Band-Aid", "Hansaplast", "Dettol", "Hansson"], 40, 70, "pack"),
        ("Digital Thermometer", ["Dr. Morepen", "Omron", "Hicks", "Hansson"], 150, 280, "one"),
        ("Electrolyte Powder ORS", ["Electral", "Enerzal", "Dr. Reddy's", "Hydrate"], 20, 95, "pack"),
        ("Cotton Roll", ["Dettol", "Hansaplast", "Hansson", "Johnson's"], 30, 90, "g"),
        ("Crepe Bandage", ["Hansaplast", "Dr. Morepen", "Hansson", "Tynor"], 60, 160, "var"),
        ("Cold Relief Tablets", ["Sinarest", "Vicks", "Cipla", "D Cold Total"], 40, 90, "tabs"),
        ("Vapor Rub", ["Vicks", "Amrutanjan", "Zandu", "Dabur"], 30, 110, "g"),
        ("Hand Sanitizer", ["Dettol", "Savlon", "Lifebuoy", "Himalaya"], 40, 140, "ml"),
        ("Glucose Powder", ["Glucon-D", "Dabur Glucose", "Dr. Reddy's", "Enerzal"], 40, 150, "g"),
        ("Face Mask", ["3M", "Savlon", "Dettol", "Hansaplast"], 30, 200, "pack"),
    ],
    "Household Essentials": [
        ("Detergent Powder", ["Surf Excel", "Ariel", "Tide", "Wheel", "Rin"], 140, 230, "kg"),
        ("Liquid Detergent", ["Surf Excel", "Ariel", "Tide", "Comfort"], 180, 320, "l"),
        ("Dishwash Gel", ["Vim", "Pril", "Exo", "Scotch-Brite"], 55, 155, "ml"),
        ("Dishwash Bar", ["Vim", "Exo", "Pril", "Scotch-Brite"], 10, 40, "pack"),
        ("Floor Cleaner", ["Lizol", "Colin", "Domex", "Harpic"], 100, 210, "l"),
        ("Toilet Cleaner", ["Harpic", "Domex", "Colin", "Lizol"], 86, 115, "ml"),
        ("Glass Cleaner", ["Colin", "Lizol", "Domex", "Harpic"], 95, 135, "ml"),
        ("Mosquito Refill", ["Good Knight", "All Out", "Mortein", "Hit"], 75, 130, "pack"),
        ("Fabric Conditioner", ["Comfort", "Downy", "Surf Excel", "Ariel"], 190, 250, "ml"),
        ("Garbage Bags", ["Ezee", "Scotch-Brite", "Pigeon", "Cello"], 45, 130, "pack"),
        ("Room Freshener", ["Odonil", "Godrej Aer", "Ambi Pur", "Air Wick"], 80, 220, "ml"),
        ("Scrub Pad", ["Scotch-Brite", "Gala", "Vim", "Exo"], 10, 70, "pack"),
        ("Phenyl", ["Lizol", "Domex", "Colin", "Odonil"], 50, 140, "l"),
        ("Matchbox", ["Ship", "Homelite", "Ahmed", "Mangal"], 5, 40, "pack"),
        ("Tissue Paper", ["Origami", "Kleenex", "Selpak", "Paseo"], 30, 150, "pack"),
        ("Kitchen Towel", ["Origami", "Paseo", "Selpak", "Kleenex"], 60, 200, "pack"),
    ],
    "Home & Kitchen": [
        ("Insulated Water Bottle", ["Milton", "Cello", "Borosil", "Pigeon"], 299, 599, "bottle"),
        ("Glass Bowl Microwave Safe", ["Borosil", "Cello", "Milton", "Treo"], 250, 450, "var"),
        ("Non-Stick Frying Pan", ["Prestige", "Pigeon", "Hawkins", "Milton"], 550, 950, "var"),
        ("Pressure Cooker", ["Prestige", "Hawkins", "Pigeon", "Butterfly"], 1100, 2500, "var"),
        ("Steel Knife Set", ["Prestige", "Pigeon", "Cello", "Milton"], 199, 399, "var"),
        ("Plastic Storage Containers", ["Cello", "Milton", "Tupperware", "Nayasa"], 220, 420, "pack"),
        ("Manual Hand Juicer", ["Prestige", "Pigeon", "Cello", "Milton"], 250, 499, "var"),
        ("Silicone Spatula Set", ["Prestige", "Pigeon", "Cello", "Milton"], 150, 280, "var"),
        ("Dinner Plate Set", ["Cello", "Borosil", "Milton", "Larah"], 300, 1500, "pack"),
        ("Steel Tiffin Box", ["Milton", "Cello", "Borosil", "Pigeon"], 299, 899, "var"),
        ("Electric Kettle", ["Prestige", "Pigeon", "Philips", "Havells"], 599, 1600, "var"),
        ("Mixer Grinder", ["Prestige", "Pigeon", "Bajaj", "Philips"], 1800, 4500, "var"),
        ("Gas Lighter", ["Prestige", "Pigeon", "Wonderchef", "Cello"], 80, 250, "one"),
        ("Steel Glass Set", ["Prestige", "Pigeon", "Cello", "Milton"], 150, 600, "pack"),
        ("Kitchen Towel Holder", ["Prestige", "Pigeon", "Cello", "Milton"], 150, 500, "var"),
    ],
    "Stationery & Office Supplies": [
        ("Spiral Notebook A4", ["Classmate", "Camlin", "Navneet", "Oddy"], 70, 160, "pack"),
        ("Ruled Notebook", ["Classmate", "Camlin", "Navneet", "Oddy"], 30, 90, "pack"),
        ("Gel Pen Blue", ["Reynolds", "Cello", "Pilot", "Montex"], 50, 150, "pack"),
        ("Ball Pen", ["Reynolds", "Cello", "Linc", "Flair"], 30, 120, "pack"),
        ("Pencil HB", ["Natraj", "Camlin", "Apsara", "Faber-Castell"], 30, 90, "pack"),
        ("Eraser", ["Natraj", "Camlin", "Apsara", "Faber-Castell"], 10, 40, "pack"),
        ("Sharpener", ["Natraj", "Camlin", "Apsara", "Faber-Castell"], 10, 40, "pack"),
        ("Permanent Markers", ["Camlin", "Luxor", "Faber-Castell", "Reynolds"], 80, 200, "pack"),
        ("Highlighter Pack", ["Camlin", "Luxor", "Faber-Castell", "Reynolds"], 110, 180, "pack"),
        ("Sticky Notes", ["Post-it", "Oddy", "Kangaro", "Camlin"], 50, 120, "pack"),
        ("Stapler", ["Kangaro", "Maped", "Camlin", "Oddy"], 95, 200, "color"),
        ("Glue Stick", ["Fevistik", "Camlin", "Kangaro", "Oddy"], 35, 70, "pack"),
        ("Correction Tape", ["Kangaro", "Camlin", "Oddy", "Faber-Castell"], 45, 100, "pack"),
        ("Geometry Box", ["Camlin", "Classmate", "Navneet", "Faber-Castell"], 90, 250, "one"),
        ("Colour Pencil Set", ["Camlin", "Faber-Castell", "Apsara", "Natraj"], 60, 250, "var"),
        ("Plastic File Folder", ["Kangaro", "Solo", "Oddy", "Camlin"], 20, 100, "pack"),
        ("A4 Paper Ream", ["JK Copier", "Navneet", "Oddy", "Camlin"], 220, 380, "var"),
    ],
    "Electronics & Accessories": [
        ("Bluetooth Neckband", ["boAt", "Noise", "Boult", "Realme", "Zebronics"], 699, 1499, "color"),
        ("True Wireless Earbuds", ["boAt", "Noise", "Boult", "Realme", "Ambrane"], 1199, 2499, "color"),
        ("Fitness Band", ["boAt", "Noise", "Realme", "Mi"], 1299, 2499, "color"),
        ("Power Bank 10000mAh", ["Ambrane", "Mi", "Realme", "Portronics", "boAt"], 899, 1499, "color"),
        ("Bluetooth Speaker", ["boAt", "Zebronics", "JBL", "Portronics"], 799, 1699, "color"),
        ("Laptop Sleeve 15.6 inch", ["Wildcraft", "HP", "Zebronics", "Lenovo"], 350, 750, "color"),
        ("Laptop Stand", ["Portronics", "Zebronics", "HP", "Ambrane"], 450, 890, "color"),
        ("Wired Earphones", ["boAt", "Realme", "Mi", "Zebronics"], 199, 599, "color"),
        ("Phone Back Cover", ["Spigen", "Ringke", "Ambrane", "Zebronics"], 149, 599, "color"),
        ("Tempered Glass", ["Spigen", "Ambrane", "Zebronics", "Portronics"], 99, 399, "pack"),
        ("Table Fan USB", ["Portronics", "Zebronics", "Ambrane", "Mi"], 299, 799, "color"),
        ("Headphones Over Ear", ["boAt", "JBL", "Zebronics", "Boult"], 999, 2499, "color"),
        ("Car Phone Holder", ["Portronics", "Zebronics", "Ambrane", "boAt"], 199, 599, "color"),
    ],
    "Clothing & Fashion": [
        ("Round Neck T-Shirt", ["Max", "Jockey", "U.S. Polo", "Allen Solly", "Levi's"], 350, 699, "cloth"),
        ("Polo T-Shirt", ["Van Heusen", "U.S. Polo", "Allen Solly", "Levi's"], 550, 1199, "cloth"),
        ("Slim Fit Jeans", ["Levi's", "Max", "U.S. Polo", "Pepe"], 999, 2199, "cloth"),
        ("Cotton Track Pants", ["Max", "Jockey", "U.S. Polo", "Puma"], 499, 999, "cloth"),
        ("Formal Shirt", ["Van Heusen", "Allen Solly", "Peter England", "Raymond"], 799, 1599, "cloth"),
        ("Cotton Socks 3 Pairs", ["Jockey", "Max", "Puma", "Adidas"], 160, 299, "var"),
        ("Canvas Sneakers", ["Max", "Puma", "Adidas", "Campus"], 899, 1899, "var"),
        ("Cotton Kurta", ["Max", "Fabindia", "Libas", "Biba"], 499, 1599, "cloth"),
        ("Cotton Innerwear Vest", ["Jockey", "Lux Cozi", "Rupa", "Dollar"], 99, 399, "cloth"),
        ("Cotton Boxers", ["Jockey", "Lux Cozi", "Rupa", "Dollar"], 149, 449, "cloth"),
        ("Hoodie Sweatshirt", ["Max", "U.S. Polo", "Puma", "Adidas"], 799, 1999, "cloth"),
        ("Cotton Dupatta", ["Libas", "Biba", "Fabindia", "Max"], 199, 799, "color"),
        ("Cotton Handkerchief Set", ["Jockey", "Max", "Raymond", "Park Avenue"], 99, 299, "pack"),
        ("Leggings Cotton", ["Max", "Jockey", "Go Colors", "Biba"], 299, 799, "cloth"),
    ],
    "Seasonal & Festival Items": [
        ("Incense Dhoop Cones", ["Cycle", "Zed Black", "Patanjali", "Hem"], 40, 160, "pack"),
        ("Agarbatti Incense Sticks", ["Cycle", "Zed Black", "Patanjali", "Hem"], 30, 120, "pack"),
        ("Brass Diya Set", ["LocalCraft", "Prestige Decor", "Gala", "FestiveGlow"], 180, 350, "pack"),
        ("Clay Diya Set", ["LocalCraft", "Gala", "FestiveGlow", "Phool"], 50, 200, "pack"),
        ("LED String Lights", ["Gala", "FestiveGlow", "Philips", "Wipro"], 120, 250, "var"),
        ("Scented Jar Candle", ["Phool", "Gala", "FestiveGlow", "Prestige Decor"], 150, 299, "var"),
        ("Windproof Umbrella", ["Gala", "Prestige Decor", "Popy", "John's"], 250, 480, "color"),
        ("Woolen Beanie Cap", ["Gala", "Prestige Decor", "FestiveGlow", "LocalCraft"], 180, 320, "color"),
        ("Sweet Box Air Tight", ["Gala", "Cello", "Milton", "LocalCraft"], 220, 450, "var"),
        ("Rangoli Colours", ["Gala", "LocalCraft", "Phool", "FestiveGlow"], 40, 150, "pack"),
        ("Flower Garland Artificial", ["Gala", "Phool", "LocalCraft", "FestiveGlow"], 80, 300, "pack"),
        ("Rakhi", ["Gala", "FestiveGlow", "LocalCraft", "Prestige Decor"], 30, 250, "pack"),
        ("Gift Wrapping Paper", ["Gala", "Archies", "LocalCraft", "FestiveGlow"], 20, 120, "pack"),
        ("Pooja Thali Set", ["LocalCraft", "Prestige Decor", "Gala", "Cello"], 250, 900, "var"),
        ("Woolen Muffler", ["Gala", "Prestige Decor", "LocalCraft", "FestiveGlow"], 200, 500, "color"),
    ],
    "Ready to Eat": [
        ("Poha Ready Mix Cup", ["MTR", "Tata Sampann", "Haldiram", "Kwality"], 40, 60, "var"),
        ("Upma Instant Cup", ["MTR", "Tata Sampann", "Haldiram", "Kwality"], 40, 60, "var"),
        ("Ready Dal Makhani", ["MTR", "Haldiram", "Kitchens of India", "Tasty Bite"], 90, 130, "var"),
        ("Paneer Butter Masala", ["MTR", "Haldiram", "Kitchens of India", "Tasty Bite"], 110, 160, "var"),
        ("Palak Paneer Ready", ["MTR", "Haldiram", "Kitchens of India", "Tasty Bite"], 100, 150, "var"),
        ("Rajma Masala Ready", ["MTR", "Haldiram", "Kitchens of India", "Tasty Bite"], 90, 130, "var"),
        ("Masala Cup Noodles", ["Maggi", "Top Ramen", "Cup Noodles", "Yippee"], 45, 60, "var"),
        ("Instant Noodles", ["Maggi", "Top Ramen", "Yippee", "Knorr"], 12, 120, "pack"),
        ("Veg Pasta Instant", ["Maggi", "Knorr", "Chings", "Kwality"], 15, 60, "pack"),
        ("Instant Veg Biryani", ["MTR", "Haldiram", "Kwality", "Tasty Bite"], 95, 145, "var"),
        ("Gulab Jamun Mix", ["MTR", "Haldiram", "Gits", "Tata Sampann"], 60, 120, "g"),
        ("Gulab Jamun Tin", ["Haldiram", "Gits", "MTR", "Bikaji"], 180, 260, "var"),
        ("Idli Dosa Batter", ["iD Fresh", "MTR", "Gits", "Kwality"], 40, 90, "g"),
        ("Soup Instant Mix", ["Knorr", "Maggi", "Chings", "Kwality"], 10, 70, "pack"),
        ("Frozen Veg Paratha", ["Haldiram", "Kwality", "McCain", "Amul"], 80, 160, "pack"),
        ("Frozen French Fries", ["McCain", "Mother Dairy", "Safal", "Kwality"], 90, 180, "g"),
        ("Pasta Sauce", ["Maggi", "Del Monte", "Kissan", "Chings"], 60, 180, "g"),
        ("Tomato Ketchup", ["Maggi", "Kissan", "Del Monte", "Heinz"], 70, 160, "g"),
        ("Mixed Fruit Jam", ["Kissan", "Del Monte", "Mapro", "Tata Sampann"], 70, 180, "g"),
        ("Peanut Butter", ["Sundrop", "Pintola", "MyFitness", "Alpino"], 150, 380, "g"),
    ],
    "Sports & Fitness": [
        ("Rubber Football", ["Nivia", "Cosco", "Strauss", "Decathlon"], 399, 799, "var"),
        ("Badminton Racquet Pair", ["Yonex", "Cosco", "Nivia", "Li-Ning"], 550, 2500, "var"),
        ("Nylon Shuttles", ["Yonex", "Cosco", "Nivia", "Li-Ning"], 140, 400, "pack"),
        ("Yoga Mat", ["Boldfit", "Strauss", "Decathlon", "Nivia"], 499, 950, "color"),
        ("Skipping Rope", ["Boldfit", "Strauss", "Cosco", "Nivia"], 160, 320, "color"),
        ("Hand Grip Strengthener", ["Boldfit", "Strauss", "Cosco", "Nivia"], 150, 299, "var"),
        ("Gym Shaker Bottle", ["Boldfit", "Strauss", "Decathlon", "Cosco"], 199, 399, "color"),
        ("Cricket Bat Kashmir Willow", ["SG", "SS", "Cosco", "Nivia"], 600, 2500, "var"),
        ("Tennis Ball Cricket", ["SG", "Cosco", "Nivia", "Decathlon"], 40, 200, "pack"),
        ("Resistance Band", ["Boldfit", "Strauss", "Decathlon", "Cosco"], 199, 599, "var"),
        ("Dumbbell Pair PVC", ["Boldfit", "Strauss", "Decathlon", "Cosco"], 400, 1800, "var"),
        ("Sports Water Bottle", ["Boldfit", "Cosco", "Decathlon", "Strauss"], 150, 450, "color"),
        ("Volleyball", ["Nivia", "Cosco", "Strauss", "Decathlon"], 400, 900, "var"),
        ("Carrom Board Coins", ["Cosco", "Surco", "Nivia", "Strauss"], 150, 500, "var"),
        ("Chess Board Set", ["Cosco", "Funskool", "Nivia", "Strauss"], 150, 700, "var"),
    ],
}

# Safety net for "veg only". The script stops if any of these WHOLE words appear in a name.
NON_VEG_WORDS = ["egg", "chicken", "mutton", "fish", "prawn", "meat", "beef", "pork",
                 "lamb", "keema", "gelatin", "bacon", "ham", "salami", "crab", "tuna"]


def build_all_items():
    """Makes EVERY possible unique item: brand x product x size."""
    all_items = []
    seen = set()
    for category, products in STORE_CATALOG.items():
        for product, brands, p_min, p_max, size_key in products:
            for brand in brands:
                for label, mult in SIZES[size_key]:
                    name = f"{brand} {product} {label}".strip()
                    if name in seen:
                        continue
                    seen.add(name)

                    low = name.lower()
                    for bad in NON_VEG_WORDS:
                        # whole word match, so "Leggings" and "Eggless" are fine
                        if re.search(rf"\b{bad}s?\b", low):
                            raise ValueError(f"Non-veg word '{bad}' found in: {name}")

                    price = round(random.uniform(p_min, p_max) * mult, 2)
                    stock = random.randint(10, 120)
                    all_items.append((name, category, price, stock))
    return all_items


def generate_items(target_count=3000):
    all_items = build_all_items()
    if target_count > len(all_items):
        print(f"Only {len(all_items)} unique items possible. Using all of them.")
        target_count = len(all_items)
    chosen = random.sample(all_items, target_count)
    chosen.sort(key=lambda x: (x[1], x[0]))  # organised: sorted by category, then name
    return chosen


def insert_bulk_inventory(target_count=3000):
    conn = get_db_connection()
    if not conn:
        print("Database connection failed. Please check db_connection.py.")
        return

    cursor = None
    try:
        cursor = conn.cursor()

        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE sale_items;")
        cursor.execute("TRUNCATE TABLE sales;")
        cursor.execute("TRUNCATE TABLE inventory;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        items = generate_items(target_count)

        insert_query = """
            INSERT INTO inventory (name, category, price, stock_quantity)
            VALUES (%s, %s, %s, %s)
        """
        cursor.executemany(insert_query, items)
        conn.commit()

        print(f"Success! Inserted {len(items)} vegetarian items across {len(STORE_CATALOG)} departments.")
    except Exception as e:
        print(f"Error populating inventory: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    insert_bulk_inventory(target_count=3000)