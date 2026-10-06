import random
import re
from database.db_connection import get_db_connection

random.seed(42)  # Deterministic seed for reproducible product catalog

# ---------------------------------------------------------------
# PACK SIZES: Expanded size variants to reach 10,000+ items
# ---------------------------------------------------------------
SIZES = {
    "kg":     [("100g", 0.15), ("250g", 0.3), ("500g", 0.55), ("1kg", 1.0), ("2kg", 1.9), ("3kg", 2.8), ("5kg", 4.6), ("10kg", 9.0)],
    "g":      [("25g", 0.15), ("50g", 0.25), ("100g", 0.4), ("150g", 0.6), ("200g", 0.75), ("250g", 1.0), ("500g", 1.9), ("1kg", 3.6)],
    "snack":  [("20g", 0.25), ("30g", 0.35), ("50g", 0.5), ("80g", 0.8), ("100g", 1.0), ("150g", 1.45), ("200g", 1.9), ("300g", 2.8), ("400g", 3.6)],
    "l":      [("100ml", 0.15), ("200ml", 0.25), ("500ml", 0.55), ("1L", 1.0), ("2L", 1.95), ("3L", 2.9), ("5L", 4.6)],
    "ml":     [("30ml", 0.2), ("50ml", 0.3), ("100ml", 0.5), ("150ml", 0.75), ("200ml", 1.0), ("300ml", 1.4), ("500ml", 2.2), ("1L", 4.1)],
    "bottle": [("200ml", 0.5), ("250ml", 0.6), ("500ml", 0.85), ("750ml", 1.0), ("1L", 1.25), ("1.25L", 1.5), ("2L", 2.3)],
    "pack":   [("Single Piece", 0.4), ("Pack of 1", 1.0), ("Pack of 2", 1.9), ("Pack of 3", 2.8), ("Pack of 4", 3.7), ("Pack of 5", 4.5), ("Pack of 6", 5.4), ("Pack of 10", 8.8)],
    "tabs":   [("10 Tabs", 0.6), ("15 Tabs", 0.75), ("20 Tabs", 0.85), ("30 Tabs", 1.0), ("45 Tabs", 1.4), ("60 Tabs", 1.8), ("90 Tabs", 2.5), ("100 Tabs", 2.8)],
    "gb":     [("16GB", 0.4), ("32GB", 0.6), ("64GB", 1.0), ("128GB", 1.7), ("256GB", 3.1), ("512GB", 5.8)],
    "cloth":  [("XS", 0.95), ("S", 1.0), ("M", 1.0), ("L", 1.0), ("XL", 1.05), ("XXL", 1.1), ("3XL", 1.15)],
    "color":  [("Classic Black", 1.0), ("Royal Blue", 1.0), ("Crimson Red", 1.0), ("Emerald Green", 1.0), ("Rose Pink", 1.0), ("Pure White", 1.0)],
    "var":    [("Regular", 1.0), ("Value Saver", 1.4), ("Value Pack", 1.7), ("Family Pack", 2.1), ("Family Saver", 2.5), ("Premium Gold", 1.35)],
    "one":    [("", 1.0)],
}

STORE_CATALOG = {
    "Grocery & Staples": [
        ("Basmati Rice Royal", ["India Gate", "Daawat", "Fortune", "Kohinoor", "Tata Sampann", "Lal Qilla", "Heritage"], 110, 220, "kg"),
        ("Sona Masoori Rice Raw", ["Fortune", "Aashirvaad", "24 Mantra", "Rajdhani", "Unity", "Nature Fresh"], 60, 90, "kg"),
        ("Sharbati Whole Wheat Atta", ["Aashirvaad", "Pillsbury", "Fortune", "Annapurna", "Patanjali", "Nature Fresh", "Laxmi"], 48, 68, "kg"),
        ("Multigrain Fiber Atta", ["Aashirvaad", "Pillsbury", "24 Mantra", "Patanjali", "Organic Tattva", "Sri Sri"], 65, 95, "kg"),
        ("Fine Maida Flour", ["Rajdhani", "Fortune", "Patanjali", "Annapurna", "Laxmi", "Ganesh"], 40, 58, "kg"),
        ("Suji Semolina", ["Rajdhani", "Aashirvaad", "Fortune", "Patanjali", "Tata Sampann", "Ganesh"], 45, 65, "kg"),
        ("Pure Chana Besan", ["Rajdhani", "Fortune", "Tata Sampann", "Patanjali", "Catch", "Laxmi"], 95, 135, "kg"),
        ("Poha Medium Thick", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra", "Organic Tattva", "Patanjali"], 65, 95, "kg"),
        ("Unpolished Toor Arhar Dal", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra", "Catch", "Organic Tattva"], 140, 195, "kg"),
        ("Split Yellow Moong Dal", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra", "Patanjali", "Sri Sri"], 115, 165, "kg"),
        ("Whole Masoor Red Dal", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra", "Catch", "Organic Tattva"], 90, 130, "kg"),
        ("Premium Chana Dal", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra", "Patanjali", "Catch"], 90, 135, "kg"),
        ("Black Urad Dal Whole", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra", "Organic Tattva", "Patanjali"], 130, 180, "kg"),
        ("Desi Rajma Chitra", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra", "Patanjali", "Organic Tattva"], 130, 185, "kg"),
        ("Organic Kabuli Chana", ["Tata Sampann", "Rajdhani", "Fortune", "24 Mantra", "Catch", "Sri Sri"], 145, 215, "kg"),
        ("Pure Refined Sugar", ["Madhur", "Uttam", "Trust", "Dhampur", "Mawana", "Parry's"], 46, 58, "kg"),
        ("Natural Jaggery Gur Powder", ["Organic Tattva", "Sri Sri Tattva", "Patanjali", "Dhampur", "24 Mantra"], 75, 115, "kg"),
        ("Vacuum Evaporated Salt", ["Tata Salt", "Aashirvaad", "Annapurna", "Catch", "Patanjali", "Saffola"], 22, 32, "kg"),
        ("Kachi Ghani Mustard Oil", ["Fortune", "Patanjali", "Dhara", "Engine", "Bail Kolhu", "Mahakosh", "Saloni"], 145, 198, "l"),
        ("Pure Sunflower Refined Oil", ["Fortune", "Saffola", "Gemini", "Sundrop", "Dhara", "Freedom"], 135, 188, "l"),
        ("Cold Pressed Groundnut Oil", ["Fortune", "Gold Winner", "Dhara", "Postman", "24 Mantra", "Gemini"], 195, 265, "l"),
        ("Pure Cow Desi Ghee", ["Amul", "Patanjali", "Mother Dairy", "Gowardhan", "Ananda", "Paras", "Verka"], 540, 690, "l"),
        ("Natural Turmeric Haldi Powder", ["Everest", "MDH", "Catch", "Tata Sampann", "Goldiee", "Rambandhu"], 65, 98, "g"),
        ("Tikhalal Red Chilli Powder", ["Everest", "MDH", "Catch", "Tata Sampann", "Goldiee", "Rambandhu"], 75, 115, "g"),
        ("Coriander Dhaniya Powder", ["Everest", "MDH", "Catch", "Tata Sampann", "Goldiee", "Rambandhu"], 55, 88, "g"),
        ("Special Garam Masala", ["Everest", "MDH", "Catch", "Badshah", "Goldiee", "Rambandhu"], 85, 135, "g"),
        ("Whole Cumin Jeera Seeds", ["Everest", "MDH", "Catch", "Tata Sampann", "Organic Tattva", "Badshah"], 95, 155, "g"),
        ("Whole Black Pepper Kali Mirch", ["Everest", "Catch", "Tata Sampann", "Organic Tattva", "MDH"], 115, 175, "g"),
        ("Premium Whole Cashew Kaju", ["Nutraj", "Happilo", "Tata Sampann", "Farmley", "Bala Ji", "Solimo"], 190, 290, "g"),
        ("California Whole Almonds Badam", ["Nutraj", "Happilo", "Tata Sampann", "Farmley", "Bala Ji", "Solimo"], 210, 330, "g"),
        ("Afghan Green Kishmish Raisins", ["Nutraj", "Happilo", "Tata Sampann", "Farmley", "Bala Ji", "Solimo"], 95, 165, "g"),
        ("Premium CTC Assam Tea", ["Tata Tea", "Red Label", "Taj Mahal", "Wagh Bakri", "Society", "Marvel", "Goodricke"], 130, 270, "kg"),
    ],
    "Dairy, Milk & Paneer": [
        ("Pasteurised Toned Milk", ["Amul", "Mother Dairy", "Parag", "Gowardhan", "Ananda", "Namaste India"], 30, 34, "l"),
        ("Full Cream Fresh Milk", ["Amul", "Mother Dairy", "Parag", "Gowardhan", "Ananda", "Namaste India"], 34, 40, "l"),
        ("Fresh Creamy Dahi Curd", ["Amul", "Mother Dairy", "Nestle", "Epigamia", "Ananda", "Milky Mist"], 38, 65, "g"),
        ("Malai Fresh Paneer Block", ["Amul", "Mother Dairy", "Milky Mist", "Gowardhan", "Ananda", "Parag"], 85, 128, "g"),
        ("Salted Pasteurized Butter", ["Amul", "Mother Dairy", "Britannia", "Gowardhan", "Nootan", "Verka"], 55, 72, "g"),
        ("Processed Cheese Slices", ["Amul", "Britannia", "Go", "Mother Dairy", "Milky Mist"], 115, 165, "g"),
        ("Creamy Cheese Spread", ["Amul", "Britannia", "Go", "Kraft", "Milky Mist"], 90, 145, "g"),
        ("Rose Flavoured Sweet Lassi", ["Amul", "Mother Dairy", "Gowardhan", "Nestle", "Ananda"], 22, 38, "ml"),
        ("Masala Spiced Buttermilk Chaach", ["Amul", "Mother Dairy", "Gowardhan", "Nestle", "Ananda"], 14, 28, "ml"),
        ("Pure Milk Khoya Mawa", ["Amul", "Mother Dairy", "Ananda", "Gowardhan", "Parag"], 120, 220, "g"),
    ],
    "Fresh Vegetables & Greens": [
        ("Fresh Agra Potato Aloo", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 22, 38, "kg"),
        ("Red Onion Pyaz", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 25, 48, "kg"),
        ("Ripe Red Tomato Tamatar", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 28, 55, "kg"),
        ("Fresh Cauliflower Gobi", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 32, 62, "kg"),
        ("Sweet Green Peas Matar", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 65, 125, "kg"),
        ("Green Capsicum Shimla Mirch", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 48, 88, "kg"),
        ("Organic Spinach Palak Bunch", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 22, 48, "kg"),
        ("Crunchy Red Carrot Gajar", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 36, 62, "kg"),
        ("Fresh Garlic Lehsun", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 120, 240, "kg"),
        ("Fresh Ginger Adrak", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 80, 160, "kg"),
        ("Green Coriander Dhaniya Bunch", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 15, 35, "g"),
        ("Round Brinjal Baingan", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 30, 58, "kg"),
        ("Fresh Bottle Gourd Lauki", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 25, 50, "kg"),
        ("Tender Lady Finger Bhindi", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 35, 75, "kg"),
        ("White Button Mushroom Pack", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 45, 80, "pack"),
        ("Salad Cucumber Kheera", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 30, 55, "kg"),
    ],
    "Fresh Fruits & Berries": [
        ("Royal Gala Red Apple", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 125, 230, "kg"),
        ("Robusta Yellow Banana", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 42, 68, "kg"),
        ("Nagpur Sweet Orange Santra", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 65, 105, "kg"),
        ("Seedless Black Grapes", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 75, 135, "kg"),
        ("Red Ruby Pomegranate Anar", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 125, 210, "kg"),
        ("Ripe Sweet Papaya", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 32, 58, "kg"),
        ("Juicy Red Watermelon Tarbooz", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 22, 42, "kg"),
        ("Fresh Green Guava Amrood", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 45, 85, "kg"),
        ("Imported Green Kiwi Pack", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Zespri"], 95, 160, "pack"),
        ("Fresh Dragon Fruit", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 80, 140, "pack"),
        ("Sweet Sapota Chikoo", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 50, 90, "kg"),
        ("Muskmelon Kharbooza", ["Fresho", "Farm Fresh", "Agra Mandi", "Nature Basket", "Safal"], 35, 65, "kg"),
    ],
    "Bakery & Breakfast": [
        ("Fresh White Sandwich Bread", ["Britannia", "English Oven", "Modern", "Harvest Gold", "Bonn", "Perfect"], 40, 52, "g"),
        ("Whole Wheat Brown Bread", ["Britannia", "English Oven", "Modern", "Harvest Gold", "Bonn", "Perfect"], 45, 60, "g"),
        ("Multigrain Fiber Bread", ["Britannia", "English Oven", "Modern", "Harvest Gold", "Bonn"], 55, 75, "g"),
        ("Soft Pav Buns Pack", ["Britannia", "English Oven", "Modern", "Harvest Gold", "Bonn"], 32, 48, "pack"),
        ("Crispy Elaichi Rusk Toast", ["Britannia", "Parle", "Cremica", "Modern", "Bonn", "Priyagold"], 42, 75, "g"),
        ("Eggless Fruit Cake Slice", ["Britannia", "Winkies", "English Oven", "Monginis", "Bonn"], 28, 65, "pack"),
        ("Rolled Whole Oats", ["Quaker", "Saffola", "Kellogg's", "Tata Sampann", "Baggry's", "True Elements"], 95, 195, "g"),
        ("Fruit & Nut Muesli", ["Kellogg's", "Saffola", "Yogabar", "Quaker", "Baggry's", "True Elements"], 185, 390, "g"),
        ("Crispy Corn Flakes", ["Kellogg's", "Baggry's", "Nestle", "Patanjali", "True Elements"], 110, 240, "g"),
        ("Creamy Peanut Butter", ["Sundrop", "Pintola", "MyFitness", "Alpino", "Disano", "Dr. Oetker"], 155, 390, "g"),
        ("Mixed Fruit Jam", ["Kissan", "Del Monte", "Mapro", "Tata Sampann", "Bonn", "Cremica"], 75, 185, "g"),
    ],
    "Snacks, Chips & Namkeen": [
        ("Classic Salted Potato Chips", ["Lays", "Bingo", "Uncle Chipps", "Pringles", "Balaji", "Haldiram"], 20, 60, "snack"),
        ("Magic Masala Potato Chips", ["Lays", "Bingo", "Uncle Chipps", "Haldiram", "Balaji", "Crax"], 20, 60, "snack"),
        ("Crispy Aloo Bhujia", ["Haldiram", "Bikaji", "Bikano", "Balaji", "Chhappan Bhog", "Garden"], 48, 105, "snack"),
        ("All-in-One Namkeen Mixture", ["Haldiram", "Bikaji", "Bikano", "Balaji", "Chhappan Bhog"], 48, 105, "snack"),
        ("Salted Roasted Peanuts", ["Haldiram", "Bikaji", "Balaji", "Tata Sampann", "Happilo"], 42, 95, "snack"),
        ("Pudina Roasted Makhana", ["Farmley", "Happilo", "Haldiram", "Tata Sampann", "True Elements"], 85, 185, "snack"),
        ("Butter Salted Popcorn", ["Act II", "Orville", "Haldiram", "Bingo", "4700BC"], 32, 85, "snack"),
        ("Spicy Kurkure Masala Munch", ["Kurkure", "Haldiram", "Bingo", "Balaji", "Crax"], 20, 50, "snack"),
        ("Rajasthani Mathri Snack", ["Haldiram", "Bikaji", "Bikano", "Chhappan Bhog", "Garden"], 50, 110, "snack"),
        ("Moong Dal Fried Crunchy", ["Haldiram", "Bikaji", "Bikano", "Balaji", "Garden"], 45, 95, "snack"),
    ],
    "Chocolates, Sweets & Biscuits": [
        ("Dairy Milk Silk Chocolate", ["Cadbury"], 45, 180, "var"),
        ("Crispy KitKat Chocolate", ["Nestle"], 30, 85, "var"),
        ("Rich Dark Chocolate Bar", ["Amul", "Cadbury Bournville", "Hershey's", "Ferrero", "Lindt"], 95, 230, "var"),
        ("Chocolate Cream Wafer", ["Cadbury", "Parle", "Nestle", "Britannia", "Pickwick"], 12, 55, "pack"),
        ("Original Glucose Biscuits", ["Parle-G", "Britannia", "Sunfeast", "Priyagold", "Bisk Farm"], 10, 32, "g"),
        ("Whole Wheat Digestive Biscuits", ["Britannia", "McVities", "Sunfeast", "Parle", "NutriChoice"], 38, 95, "g"),
        ("Bourbon Cream Biscuits", ["Britannia", "Oreo", "Sunfeast", "Parle", "Priyagold"], 28, 65, "g"),
        ("Butter Delite Cookies", ["Britannia", "Unibic", "Sunfeast", "Parle", "Cookie Man"], 32, 105, "g"),
        ("Desi Ghee Soan Papdi Box", ["Haldiram", "Bikaji", "Bikano", "Chhappan Bhog", "Gits"], 95, 220, "g"),
        ("Gulab Jamun Tin Box", ["Haldiram", "Gits", "MTR", "Bikaji", "Bikano"], 185, 275, "var"),
        ("Rasgulla Syrup Tin Box", ["Haldiram", "Gits", "MTR", "Bikaji", "Bikano"], 185, 275, "var"),
    ],
    "Tea, Coffee & Beverages": [
        ("Fizz Sparkling Cola Drink", ["Coca Cola", "Pepsi", "Thums Up", "Limca", "Sprite", "Fanta"], 40, 48, "bottle"),
        ("Alphonso Mango Drink", ["Maaza", "Slice", "Frooti", "Real", "Paper Boat", "B Natural"], 22, 95, "bottle"),
        ("100 Percent Mixed Fruit Juice", ["Real", "Tropicana", "Paper Boat", "B Natural", "Minute Maid"], 22, 125, "bottle"),
        ("Purified Packaged Drinking Water", ["Bisleri", "Kinley", "Aquafina", "Himalayan", "Bailley"], 20, 28, "bottle"),
        ("Classic Instant Coffee Powder", ["Nescafe", "Bru", "Continental", "Tata Coffee", "Davidoff"], 85, 220, "g"),
        ("Pure Green Tea Bags", ["Lipton", "Tetley", "Twinings", "Organic India", "Girnar"], 125, 270, "pack"),
        ("Tender Coconut Water Pack", ["Raw Pressery", "Paper Boat", "Real", "Fresho", "Alo Frut"], 45, 80, "bottle"),
        ("Jeera Masala Soda", ["Lahori", "Paper Boat", "Catch", "Campal", "Bisleri"], 20, 45, "bottle"),
    ],
    "Personal Care & Grooming": [
        ("Moisturizing Bath Soap", ["Dettol", "Dove", "Pears", "Lux", "Lifebuoy", "Santoor", "Fiama", "Medimix"], 32, 85, "pack"),
        ("Nourishing Shampoo", ["Head & Shoulders", "Dove", "Clinic Plus", "Pantene", "Tresemme", "SunSilk", "L'Oreal"], 85, 270, "ml"),
        ("Smooth Hair Conditioner", ["Dove", "Pantene", "Tresemme", "Sunsilk", "L'Oreal"], 125, 290, "ml"),
        ("Pure Coconut Hair Oil", ["Parachute", "Bajaj Almond Drops", "Dabur Amla", "Indulekha", "Nihar"], 65, 260, "ml"),
        ("Total Care Toothpaste", ["Colgate", "Pepsodent", "Closeup", "Sensodyne", "Dabur Red", "Himalaya"], 58, 160, "g"),
        ("Soft Bristle Toothbrush", ["Colgate", "Oral-B", "Pepsodent", "Sensodyne", "Trisa"], 32, 160, "pack"),
        ("Refreshing Body Wash", ["Dove", "Nivea", "Fiama", "Pears", "Palmolive"], 125, 290, "ml"),
        ("Neem Purifying Face Wash", ["Himalaya", "Garnier", "Nivea", "Clean & Clear", "Lotus"], 95, 230, "ml"),
        ("Deep Moisture Body Lotion", ["Nivea", "Vaseline", "Dove", "Parachute Advansed", "Joy"], 155, 330, "ml"),
        ("Glow & Lovely Face Cream", ["Fair & Lovely", "Pond's", "Nivea", "Garnier", "Olay"], 75, 260, "g"),
        ("Fresh Deodorant Spray", ["Fogg", "Nivea", "Axe", "Engage", "Wild Stone", "Park Avenue"], 135, 290, "ml"),
        ("Liquid Hand Wash Refill", ["Dettol", "Lifebuoy", "Savlon", "Dove", "Godrej Protekt"], 58, 135, "ml"),
        ("Cooling Talcum Powder", ["Pond's", "Nycil", "Navratna", "Dermicool", "Wild Stone"], 65, 210, "g"),
    ],
    "Girls Accessories & Makeup": [
        ("Matte Finish Lipstick", ["Maybelline", "Lakme", "Nykaa", "Colorbar", "Faces Canada", "SUGAR"], 210, 720, "color"),
        ("Intense Black Kajal", ["Lakme", "Maybelline", "Himalaya", "Faces Canada", "Plum"], 105, 310, "color"),
        ("Waterproof Eye Mascara", ["Maybelline", "Lakme", "Nykaa", "Colorbar", "SUGAR"], 260, 520, "color"),
        ("Precision Liquid Eyeliner", ["Maybelline", "Lakme", "Faces Canada", "Colorbar", "Plum"], 190, 370, "color"),
        ("Smooth Compact Powder", ["Lakme", "Maybelline", "Colorbar", "Faces Canada", "SUGAR"], 230, 470, "var"),
        ("Liquid Skin Foundation", ["Maybelline", "Lakme", "Nykaa", "Colorbar", "L'Oreal"], 370, 780, "var"),
        ("Glossy Nail Enamel", ["Lakme", "Maybelline", "Colorbar", "Nykaa", "Faces Canada"], 105, 230, "color"),
        ("Gentle Makeup Remover", ["Garnier", "Lakme", "Maybelline", "Nykaa", "Bioderma"], 210, 420, "ml"),
        ("Satin Hair Scrunchies Set", ["Gitti", "Nykaa", "Ayesha", "Kaneesh", "YouBella"], 65, 160, "pack"),
        ("Trendy Hair Claw Clip", ["Gitti", "Nykaa", "Ayesha", "Kaneesh", "YouBella"], 55, 130, "color"),
        ("Designer Bangles Set", ["Kaneesh", "Ayesha", "Gitti", "Local Craft", "YouBella"], 85, 320, "color"),
        ("Fashion Earrings Pair", ["Kaneesh", "Ayesha", "Gitti", "Local Craft", "YouBella"], 110, 480, "color"),
        ("Traditional Bindi Pack", ["Kaneesh", "Ayesha", "Gitti", "Local Craft", "Shilpa"], 12, 45, "pack"),
    ],
    "Tech & Mobile Accessories": [
        ("Fast USB-C Cable 1.5m", ["boAt", "Portronics", "Ambrane", "Mi", "Zebronics", "Realme"], 210, 420, "color"),
        ("Micro USB Charging Cable", ["boAt", "Portronics", "Ambrane", "Zebronics", "Syska"], 105, 260, "color"),
        ("Quick Wall Charger 20W", ["boAt", "Mi", "Ambrane", "Realme", "Portronics", "Anker"], 470, 920, "color"),
        ("High Speed MicroSD Card", ["SanDisk", "Samsung", "Kingston", "HP", "Strontium"], 470, 680, "gb"),
        ("USB 3.0 Flash Pen Drive", ["SanDisk", "HP", "Kingston", "Lexar", "Sony"], 420, 740, "gb"),
        ("Ergonomic Wireless Mouse", ["Logitech", "HP", "Zebronics", "Portronics", "Dell"], 420, 890, "color"),
        ("Full Size Wired Keyboard", ["Logitech", "HP", "Zebronics", "Portronics", "Dell"], 470, 980, "color"),
        ("Smart WiFi LED Bulb 12W", ["Wipro", "Philips", "Syska", "Mi", "Havells"], 420, 730, "var"),
        ("Heavy Power Strip Surge", ["Belkin", "Havells", "Anchor", "Zebronics", "Honeywell"], 520, 1050, "var"),
        ("Dual Band WiFi Router", ["TP-Link", "D-Link", "Tenda", "Netgear", "Mercusys"], 1150, 2600, "var"),
        ("HD Webcam with Mic", ["Logitech", "Zebronics", "HP", "Lenovo", "AverMedia"], 920, 2300, "var"),
        ("Non-Slip Mouse Pad", ["Logitech", "HP", "Zebronics", "Portronics", "Razer"], 160, 470, "color"),
        ("Desktop Phone Stand Holder", ["Portronics", "Ambrane", "Zebronics", "boAt", "Elago"], 160, 470, "color"),
        ("Metal OTG Adapter", ["boAt", "Portronics", "Ambrane", "Zebronics", "Ugreen"], 105, 310, "color"),
    ],
    "Health, Wellness & Supplements": [
        ("Special Chyawanprash", ["Dabur", "Baidyanath", "Patanjali", "Zandu", "Hamdard"], 350, 495, "g"),
        ("100 Percent Pure Organic Honey", ["Dabur", "Patanjali", "Kapiva", "Zandu", "Saffola", "Baidyanath"], 220, 335, "g"),
        ("Plant Protein Powder Veg", ["Kapiva", "Boldfit", "OZiva", "Yogabar", "Fast&Up"], 1550, 2700, "var"),
        ("Vegetarian Multivitamin Tabs", ["HealthKart", "Kapiva", "Himalaya", "Boldfit", "Revital H"], 470, 780, "tabs"),
        ("Flaxseed Omega-3 Capsules", ["HealthKart", "Kapiva", "Himalaya", "Boldfit", "TrueBasics"], 520, 920, "tabs"),
        ("Pure Aloe Vera Juice", ["Patanjali", "Kapiva", "Dabur", "Himalaya", "Baidyanath"], 190, 280, "l"),
        ("Pure Amla Juice", ["Patanjali", "Kapiva", "Dabur", "Baidyanath", "Sri Sri"], 160, 270, "l"),
        ("Vitamin C Effervescent Tabs", ["Limcee", "HealthKart", "Zandu", "Himalaya", "Fast&Up"], 230, 370, "tabs"),
        ("Ashwagandha Immunity Tablets", ["Himalaya", "Kapiva", "Patanjali", "Dabur", "Zandu"], 260, 470, "tabs"),
        ("Triphala Churna Powder", ["Patanjali", "Baidyanath", "Dabur", "Kapiva", "Zandu"], 95, 210, "g"),
        ("High Protein Snack Bar", ["RiteBite", "Yogabar", "Max Protein", "Fit Bar", "HYP"], 42, 125, "pack"),
    ],
    "All Medicines & First Aid": [
        ("Paracetamol Fever 650mg", ["Dolo", "Crocin", "Calpol", "P-650", "Pacimol"], 32, 48, "tabs"),
        ("Herbal Cough Relief Syrup", ["Dabur", "Himalaya", "Baidyanath", "Zandu", "Benadryl"], 90, 135, "ml"),
        ("Antacid Liquid Gel", ["Digene", "Gelusil", "Eno", "Pudin Hara", "Mucaine"], 65, 165, "ml"),
        ("Pain Relief Gel Tube", ["Volini", "Moov", "Iodex", "Zandu", "Omnigel"], 78, 135, "g"),
        ("Pain Relief Balm Pot", ["Amrutanjan", "Zandu", "Vicks", "Tiger Balm", "Axe"], 42, 115, "g"),
        ("Antiseptic Liquid Bottle", ["Dettol", "Savlon", "Betadine", "Hansaplast", "Apollo"], 98, 145, "ml"),
        ("Waterproof Bandages Strip", ["Band-Aid", "Hansaplast", "Dettol", "Hansson", "Apollo"], 42, 75, "pack"),
        ("Digital Clinical Thermometer", ["Dr. Morepen", "Omron", "Hicks", "Hansson", "Beurer"], 160, 290, "one"),
        ("Electrolyte ORS Powder", ["Electral", "Enerzal", "Dr. Reddy's", "Hydrate", "Cipla"], 22, 98, "pack"),
        ("Sterilized Cotton Roll", ["Dettol", "Hansaplast", "Hansson", "Johnson's", "Apollo"], 32, 95, "g"),
        ("Elastic Crepe Bandage", ["Hansaplast", "Dr. Morepen", "Hansson", "Tynor", "Flamingo"], 65, 168, "var"),
        ("Vapor Rub Gel", ["Vicks", "Amrutanjan", "Zandu", "Dabur", "Relispray"], 32, 115, "g"),
        ("Instant Glucose Energy Powder", ["Glucon-D", "Dabur Glucose", "Dr. Reddy's", "Enerzal"], 42, 155, "g"),
        ("Protective Face Mask 3-Ply", ["3M", "Savlon", "Dettol", "Hansaplast", "Wildcraft"], 32, 210, "pack"),
    ],
    "Household & Cleaning": [
        ("Detergent Washing Powder", ["Surf Excel", "Ariel", "Tide", "Wheel", "Rin", "Henko"], 145, 240, "kg"),
        ("Liquid Fabric Detergent", ["Surf Excel", "Ariel", "Tide", "Comfort", "Genteel"], 185, 330, "l"),
        ("Dishwash Gel Concentrate", ["Vim", "Pril", "Exo", "Scotch-Brite", "Pitambari"], 58, 160, "ml"),
        ("Anti-Bacterial Dishwash Bar", ["Vim", "Exo", "Pril", "Scotch-Brite", "Nip"], 12, 42, "pack"),
        ("Disinfectant Floor Cleaner", ["Lizol", "Colin", "Domex", "Harpic", "Nimyle"], 105, 215, "l"),
        ("Power Toilet Cleaner", ["Harpic", "Domex", "Colin", "Lizol", "Sanifresh"], 88, 120, "ml"),
        ("Glass & Surface Cleaner", ["Colin", "Lizol", "Domex", "Harpic", "Windex"], 98, 140, "ml"),
        ("Mosquito Repellent Refill", ["Good Knight", "All Out", "Mortein", "Hit", "Baygon"], 78, 135, "pack"),
        ("Fabric After-Wash Conditioner", ["Comfort", "Downy", "Surf Excel", "Ariel", "Lenor"], 195, 260, "ml"),
        ("Heavy Garbage Bags Roll", ["Ezee", "Scotch-Brite", "Pigeon", "Cello", "Shine"], 48, 135, "pack"),
        ("Automatic Room Freshener", ["Odonil", "Godrej Aer", "Ambi Pur", "Air Wick", "Glade"], 85, 225, "ml"),
        ("Utensil Scrub Pad", ["Scotch-Brite", "Gala", "Vim", "Exo", "Tidy"], 12, 75, "pack"),
        ("Facial Tissue Paper Box", ["Origami", "Kleenex", "Selpak", "Paseo", "Premier"], 32, 155, "pack"),
        ("Kitchen Paper Towel Roll", ["Origami", "Paseo", "Selpak", "Kleenex", "Premier"], 65, 210, "pack"),
    ],
    "Home & Kitchenware": [
        ("Insulated Stainless Water Bottle", ["Milton", "Cello", "Borosil", "Pigeon", "Signoraware"], 310, 620, "bottle"),
        ("Microwave Safe Glass Bowl", ["Borosil", "Cello", "Milton", "Treo", "Larah"], 260, 470, "var"),
        ("Non-Stick Frying Pan", ["Prestige", "Pigeon", "Hawkins", "Milton", "Wonderchef"], 570, 980, "var"),
        ("Aluminum Pressure Cooker", ["Prestige", "Hawkins", "Pigeon", "Butterfly", "Preethi"], 1150, 2600, "var"),
        ("Stainless Steel Knife Set", ["Prestige", "Pigeon", "Cello", "Milton", "Victorinox"], 210, 420, "var"),
        ("Plastic Air Tight Containers", ["Cello", "Milton", "Tupperware", "Nayasa", "Signoraware"], 230, 440, "pack"),
        ("Dinner Plate Set 6 Pc", ["Cello", "Borosil", "Milton", "Larah", "Corelle"], 320, 1550, "pack"),
        ("Stainless Steel Tiffin Box", ["Milton", "Cello", "Borosil", "Pigeon", "Signoraware"], 310, 920, "var"),
        ("Automatic Electric Kettle", ["Prestige", "Pigeon", "Philips", "Havells", "Bajaj"], 620, 1650, "var"),
        ("3-Jar Mixer Grinder 750W", ["Prestige", "Pigeon", "Bajaj", "Philips", "Sujata"], 1850, 4600, "var"),
        ("Piezo Spark Gas Lighter", ["Prestige", "Pigeon", "Wonderchef", "Cello", "Lancer"], 85, 260, "one"),
    ],
    "Stationery & Office Supplies": [
        ("Spiral Notebook A4 200 Pgs", ["Classmate", "Camlin", "Navneet", "Oddy", "Target"], 75, 165, "pack"),
        ("Single Line Ruled Notebook", ["Classmate", "Camlin", "Navneet", "Oddy", "Target"], 32, 95, "pack"),
        ("Smooth Gel Pen Blue", ["Reynolds", "Cello", "Pilot", "Montex", "Pentel"], 55, 155, "pack"),
        ("Smooth Ball Pen Pack", ["Reynolds", "Cello", "Linc", "Flair", "Hauser"], 32, 125, "pack"),
        ("Extra Dark Pencil HB", ["Natraj", "Camlin", "Apsara", "Faber-Castell", "Doms"], 32, 95, "pack"),
        ("Dust Free Eraser Pack", ["Natraj", "Camlin", "Apsara", "Faber-Castell", "Doms"], 12, 42, "pack"),
        ("Dual Hole Sharpener", ["Natraj", "Camlin", "Apsara", "Faber-Castell", "Doms"], 12, 42, "pack"),
        ("Permanent Marker Pens", ["Camlin", "Luxor", "Faber-Castell", "Reynolds", "Sharpie"], 85, 210, "pack"),
        ("Fluorescent Highlighter Pack", ["Camlin", "Luxor", "Faber-Castell", "Reynolds", "Stabilo"], 115, 185, "pack"),
        ("Self Stick Notes Pad", ["Post-it", "Oddy", "Kangaro", "Camlin", "Deli"], 55, 125, "pack"),
        ("Desktop Heavy Duty Stapler", ["Kangaro", "Maped", "Camlin", "Oddy", "Deli"], 98, 210, "color"),
        ("Clean Apply Glue Stick", ["Fevistik", "Camlin", "Kangaro", "Oddy", "Doms"], 38, 75, "pack"),
        ("Complete Geometry Box", ["Camlin", "Classmate", "Navneet", "Faber-Castell", "Doms"], 95, 260, "one"),
        ("A4 Copier Paper Ream 500s", ["JK Copier", "Navneet", "Oddy", "Camlin", "B2G"], 230, 390, "var"),
    ],
    "Clothing & Fashion": [
        ("Pure Cotton Round Neck T-Shirt", ["Max", "Jockey", "U.S. Polo", "Allen Solly", "Levi's", "Roadster"], 370, 720, "cloth"),
        ("Classic Collar Polo T-Shirt", ["Van Heusen", "U.S. Polo", "Allen Solly", "Levi's", "Louis Philippe"], 570, 1250, "cloth"),
        ("Stretchable Slim Fit Jeans", ["Levi's", "Max", "U.S. Polo", "Pepe", "Wrangler"], 1050, 2250, "cloth"),
        ("Cotton Blend Track Pants", ["Max", "Jockey", "U.S. Polo", "Puma", "HRX"], 520, 1050, "cloth"),
        ("Formal Executive Shirt", ["Van Heusen", "Allen Solly", "Peter England", "Raymond", "Arrow"], 820, 1650, "cloth"),
        ("Cotton Ankle Socks 3 Pairs", ["Jockey", "Max", "Puma", "Adidas", "Nike"], 170, 310, "var"),
        ("Casual Canvas Sneakers", ["Max", "Puma", "Adidas", "Campus", "Bata"], 920, 1950, "var"),
        ("Ethnic Cotton Kurta", ["Max", "Fabindia", "Libas", "Biba", "Manyavar"], 520, 1650, "cloth"),
        ("Cotton Innerwear Vest", ["Jockey", "Lux Cozi", "Rupa", "Dollar", "Machoman"], 105, 410, "cloth"),
        ("Fleece Hoodie Sweatshirt", ["Max", "U.S. Polo", "Puma", "Adidas", "Wildcraft"], 820, 2050, "cloth"),
    ],
    "Seasonal, Pooja & Festival": [
        ("Fragrant Incense Dhoop Cones", ["Cycle", "Zed Black", "Patanjali", "Hem", "Mangaldeep"], 42, 165, "pack"),
        ("Agarbatti Scented Sticks", ["Cycle", "Zed Black", "Patanjali", "Hem", "Mangaldeep"], 32, 125, "pack"),
        ("Solid Brass Diya Set", ["LocalCraft", "Prestige Decor", "Gala", "FestiveGlow", "Borosil"], 190, 360, "pack"),
        ("Handcrafted Clay Diya Set", ["LocalCraft", "Gala", "FestiveGlow", "Phool", "Earthy"], 55, 210, "pack"),
        ("Warm White LED String Lights", ["Gala", "FestiveGlow", "Philips", "Wipro", "Havells"], 125, 260, "var"),
        ("Aromatherapy Scented Candle", ["Phool", "Gala", "FestiveGlow", "Prestige Decor", "Iris"], 160, 310, "var"),
        ("Automatic Windproof Umbrella", ["Gala", "Prestige Decor", "Popy", "John's", "Citizen"], 260, 490, "color"),
        ("Organic Rangoli Colors Pack", ["Gala", "LocalCraft", "Phool", "FestiveGlow"], 42, 155, "pack"),
        ("Brass Pooja Thali Plate Set", ["LocalCraft", "Prestige Decor", "Gala", "Cello", "Borosil"], 260, 950, "var"),
    ],
    "Ready to Eat": [
        ("Instant Poha Cup", ["MTR", "Tata Sampann", "Haldiram", "Kwality", "iD"], 42, 62, "var"),
        ("Instant Upma Cup", ["MTR", "Tata Sampann", "Haldiram", "Kwality", "iD"], 42, 62, "var"),
        ("Ready Dal Makhani Meal", ["MTR", "Haldiram", "Kitchens of India", "Tasty Bite", "Kohinoor"], 95, 135, "var"),
        ("Paneer Butter Masala Ready", ["MTR", "Haldiram", "Kitchens of India", "Tasty Bite", "Kohinoor"], 115, 165, "var"),
        ("Masala Instant Cup Noodles", ["Maggi", "Top Ramen", "Cup Noodles", "Yippee", "Wai Wai"], 48, 62, "var"),
        ("2-Minute Instant Noodles", ["Maggi", "Top Ramen", "Yippee", "Knorr", "Wai Wai"], 14, 125, "pack"),
        ("Instant Veg Biryani Pack", ["MTR", "Haldiram", "Kwality", "Tasty Bite", "Kohinoor"], 98, 150, "var"),
        ("Instant Gulab Jamun Mix", ["MTR", "Haldiram", "Gits", "Tata Sampann", "Bikaji"], 65, 125, "g"),
        ("Fresh Idli Dosa Batter Pack", ["iD Fresh", "MTR", "Gits", "Kwality", "Ashirvad"], 42, 95, "g"),
        ("Frozen Veg French Fries", ["McCain", "Mother Dairy", "Safal", "Kwality", "Godrej Yummiez"], 95, 185, "g"),
        ("Rich Tomato Ketchup Bottle", ["Maggi", "Kissan", "Del Monte", "Heinz", "Cremica"], 75, 165, "g"),
    ],
    "Sports & Fitness": [
        ("Durable Rubber Football", ["Nivia", "Cosco", "Strauss", "Decathlon", "Kipsta"], 410, 820, "var"),
        ("Badminton Racquet Pair Set", ["Yonex", "Cosco", "Nivia", "Li-Ning", "Silver's"], 570, 2600, "var"),
        ("Nylon Shuttlecocks Box", ["Yonex", "Cosco", "Nivia", "Li-Ning", "Silver's"], 145, 410, "pack"),
        ("Anti-Slip Yoga Mat 6mm", ["Boldfit", "Strauss", "Decathlon", "Nivia", "Kobo"], 520, 980, "color"),
        ("Speed Skipping Rope", ["Boldfit", "Strauss", "Cosco", "Nivia", "Decathlon"], 165, 330, "color"),
        ("Hand Grip Adjustable Exerciser", ["Boldfit", "Strauss", "Cosco", "Nivia", "Decathlon"], 155, 310, "var"),
        ("Protein Gym Shaker Bottle", ["Boldfit", "Strauss", "Decathlon", "Cosco", "BlenderBottle"], 210, 420, "color"),
        ("Kashmir Willow Cricket Bat", ["SG", "SS", "Cosco", "Nivia", "DSC"], 620, 2600, "var"),
        ("Heavy Rubber Dumbbell Pair", ["Boldfit", "Strauss", "Decathlon", "Cosco", "Aurion"], 420, 1850, "var"),
    ],
}

NON_VEG_WORDS = [
    "egg", "chicken", "mutton", "fish", "prawn", "meat", "beef", "pork",
    "lamb", "keema", "gelatin", "bacon", "ham", "salami", "crab", "tuna", "nonveg"
]


def build_all_items():
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
                        if re.search(rf"\b{bad}s?\b", low):
                            raise ValueError(f"Non-veg word '{bad}' detected in product: {name}")

                    price = round(random.uniform(p_min, p_max) * mult, 2)
                    stock = random.randint(15, 150)
                    all_items.append((name, category, price, stock))

    return all_items


def generate_items(target_count=10000):
    all_items = build_all_items()
    print(f"Total generated unique vegetarian products: {len(all_items)}")

    if target_count > len(all_items):
        print(f"Using max unique items: {len(all_items)}")
        chosen = all_items
    else:
        chosen = random.sample(all_items, target_count)

    chosen.sort(key=lambda x: (x[1], x[0]))
    return chosen


def insert_bulk_inventory(target_count=10000):
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

        print(f"Successfully inserted {len(items)} 100% vegetarian products into MySQL 'inventory' table!")
    except Exception as e:
        print(f"Error populating inventory: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    insert_bulk_inventory(target_count=10000)